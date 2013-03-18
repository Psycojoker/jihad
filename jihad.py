# Jihad - enable haml and jinja2 in OpenERP views
# Copyright (C) 2013 Laurent Peuch <cortex@worlddomination.be>
#                    Railnova SPRL <railnova@railnova.eu>
#
# This file is part of Jihad.
#
# Jihad is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# Jihad is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Jihad.  If not, see <http://www.gnu.org/licenses/>.

import os
import re
import sys
import subprocess
from jinja2 import Environment, FileSystemLoader, nodes
from jinja2.ext import Extension
from hamlish_jinja import HamlishExtension, Hamlish

# monkey patching because hamlish doesn't provide a clean way to do that :(
Hamlish._self_closing_html_tags.add("newline")
Hamlish._self_closing_html_tags.add("menuitem")

Hamlish._self_closing_jinja_tags.add("f")
Hamlish._self_closing_jinja_tags.add("fields")


class BaseExtension(Extension):
    def extract_argument(self, argument, options, default=None):
        to_return = default
        if options.has_key(argument):
            to_return = options.get(argument)
            del options[argument]

        return to_return

    def parse_options(self, parser):
        options = {}
        while parser.stream.current.type != 'block_end':
            key = parser.parse_assign_target().name
            parser.stream.expect('assign')
            value = parser.parse_tuple().value
            options[key] = value

        return options


GENERIC_VIEW_TEMPLATE = """\
%record id="{{ id }}" model="ir.ui.view"
              %field name="model" << {{ model_name }}
              %field name="type" << {{ type }}
              -for key, value in options.items()
                %field name="{{ key }}" << {{ value }}
              %field name="arch" type="xml"
                <{{ type }}{% if description %} string="{{ description }}"{% endif %}>
                  =body
                </{{ type }}>

-if has_action
            %record id="{{ action_id }}" model="ir.actions.act_window"
              %field name="type" << ir.actions.act_window
              %field name="res_model" << {{ model_name }}
              %field name="view_id" ref="{{ id }}".
              -if search_view_id:
                  %field name="search_view_id" ref="{{ search_view_id }}".
              -for key, value in action_options.items()
                %field name="{{ key }}" << {{ value }}

-if has_menu
              %menuitem id="{{ menu_id }}" action="{{ action_id }}" {% for key, value in menu_options.items() %} {{ key }}="{{ value }}"{% endfor %}
"""


class WithGenericView(BaseExtension):
    tags = set(['tree', 'form', 'search', 'list'])

    def parse(self, parser):
        args = {}

        view_type = parser.stream.next()
        lineno = view_type.lineno
        args["view_type"] = view_type.value

        args["model_name"] = parser.parse_expression().value

        # TODO: write doc for {% list %}

        args["options"] = {"name": args["model_name"] + "." + args["view_type"]}
        args["options"].update(self.parse_options(parser))

        args["_id"] = self.extract_argument("id", args["options"], default="view_" + args["model_name"].replace(".", "_") + "_" + args["view_type"])
        args["string"] = self.extract_argument("string", args["options"])

        args["has_menu"] = self.extract_argument("has_menu", args["options"], False) or\
                            len(filter(lambda x: x.startswith("menu_"), args["options"])) > 0
        args["has_action"] = self.extract_argument("has_action", args["options"], False) or\
                            len(filter(lambda x: x.startswith("action_"), args["options"])) > 0 or\
                            args["has_menu"]

        args["action_options"] = {
            "name": " ".join(args["model_name"].split(".")[1:]).title(),
            "view_type": args["view_type"] if args["view_type"] != "list" else "form",
        }
        args["menu_options"] = {
            "name": " ".join(args["model_name"].split(".")[1:]).title(),
        }

        for key in args["options"]:
            if key.startswith("action_"):
                args["action_options"][key.replace("action_", "", 1)] = args["options"][key]
            elif key.startswith("menu_"):
                args["menu_options"][key.replace("menu_", "", 1)] = args["options"][key]

        args["options"] = dict(filter(lambda x: not x[0].startswith("action_") and x[0].startswith("menu_"), args["options"].items()))

        args["action_id"] = self.extract_argument("id", options=args["action_options"], default="action_" + args["model_name"].replace(".", "_") + "_" + args["view_type"])
        args["menu_id"] = self.extract_argument("id", options=args["menu_options"], default="menu_" + args["model_name"].replace(".", "_") + "_" + args["view_type"])

        args["search_view_id"] = self.extract_argument("search_view_id", options=args["action_options"])

        body = parser.parse_statements(['name:end%s' % args["view_type"]], drop_needle=True)

        return nodes.CallBlock(self.call_method('_generate_view', [nodes.Const(args)]), [], [], body).set_lineno(lineno)

    def _generate_view(self, args, caller):
        template = env.hamlish_from_string(GENERIC_VIEW_TEMPLATE)
        return template.render(body=caller().strip() + "\n",
                               type=args["view_type"] if args["view_type"] != "list" else "tree",
                               id=args["_id"],
                               description=args["string"],
                               model_name=args["model_name"],
                               options=args["options"],
                               has_action=args["has_action"],
                               has_menu=args["has_menu"],
                               action_options=args["action_options"],
                               menu_options=args["menu_options"],
                               action_id=args["action_id"],
                               menu_id=args["menu_id"],
                               search_view_id=args["search_view_id"],
                              )


FIELD_TEMPLATE = '%field name="{{ name }}"{% for key, value in options.items() %} {{ key }}="{{ value }}"{% endfor %}.'


class FieldShortcut(BaseExtension):
    tags = set(['f'])

    def parse(self, parser):
        args = {}
        lineno = parser.stream.next().lineno
        args["name"] = parser.parse_expression().value
        args["options"] = self.parse_options(parser)
        return nodes.CallBlock(self.call_method('_generate_view', [nodes.Const(args)]), [], [], []).set_lineno(lineno)

    def _generate_view(self, args, caller):
        return env.hamlish_from_string(FIELD_TEMPLATE).render(name=args["name"], options=args["options"])


FIELDS_LIST_TEMPLATE = '''\
-for field in fields:
  %field name="{{ field }}".
'''

class FieldsListShortcut(BaseExtension):
    tags = set(['fields'])

    def parse(self, parser):
        args = {"fields": []}
        lineno = parser.stream.next().lineno

        while parser.stream.current.type != 'block_end':
            args["fields"].append(parser.stream.current.value)
            parser.stream.next()

        return nodes.CallBlock(self.call_method('_generate_view', [nodes.Const(args)]), [], [], []).set_lineno(lineno)

    def _generate_view(self, args, caller):
        return env.hamlish_from_string(FIELDS_LIST_TEMPLATE).render(fields=args["fields"])


env = Environment(extensions=[WithGenericView, FieldShortcut, FieldsListShortcut, HamlishExtension])


def purify(indent=False):
    called_from = sys._getframe(1).f_globals["__file__"]
    module_directory = os.path.split(called_from)[0]

    if not os.path.exists(os.path.join(module_directory, "__openerp__.py")):
        return

    env.loader = FileSystemLoader(module_directory)

    module_settings = eval(open(os.path.join(module_directory, "__openerp__.py")).read())
    xml_files = list(set(filter(lambda x: x.strip().endswith(".xml"), module_settings.get("init_xml", []) + module_settings.get("data", []) + module_settings.get("update_xml", []))))

    for xml_file in xml_files:
        haml_file = xml_file[:-3] + "haml"
        haml_file_path = os.path.join(module_directory, xml_file[:-3] + "haml")
        if not os.path.exists(haml_file_path):
            continue
        to_write = env.get_template(haml_file).render()
        if not re.match("^\s*<\s*openerp\s*>\s*<\s*data\s*>", to_write):
            to_write = env.hamlish_from_string("%openerp\n  %data\n    =body").render(body=to_write)
        to_write = format_xml(xml_file, to_write)
        open(os.path.join(module_directory, xml_file), "w").write(to_write)


def format_xml(xml_file, to_write):
    xmllint_is_installed = subprocess.Popen(['which', 'xmllint'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
    if not xmllint_is_installed:
        sys.stderr.write("Warning: you don't have xmlllint installed, you won't have nicely formated xml")
        return to_write

    formated, err = subprocess.Popen(['xmllint', '--format', '/dev/stdin'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(to_write)
    if err:
        print "Error while trying to format the xml of %s: '%s'" % (xml_file, err)
    else:
        to_write = formated.replace("</record>", "</record>\n")
    return to_write
