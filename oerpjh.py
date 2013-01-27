# OpenERP-Jinja2-Haml - enable haml and jinja2 in OpenERP views
# Copyright (C) 2013 Laurent Peuch <cortex@worlddomination.be>
#                    Railnova SPRL <railnova@railnova.eu>
#
# This file is part of Openerp-Jinja2-Haml.
#
# OpenERP-Jinja2-Haml is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# OpenERP-Jinja2-Haml is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# OpenERP-Jinja2-Haml.  If not, see <http://www.gnu.org/licenses/>.

import os
import re
import sys
from jinja2 import Environment, FileSystemLoader, nodes
from jinja2.ext import Extension
from hamlish_jinja import HamlishExtension, Hamlish

# monkey patching because hamlish doesn't provide a clean way to do that :(
Hamlish._self_closing_html_tags.add("newline")
Hamlish._self_closing_html_tags.add("menuitem")

Hamlish._self_closing_jinja_tags.add("f")


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
"""


class WithGenericView(BaseExtension):
    tags = set(['tree', 'form', 'search', 'list'])

    def parse(self, parser):
        arguments = {}

        view_type = parser.stream.next()
        lineno = view_type.lineno
        arguments["view_type"] = view_type.value

        arguments["model_name"] = parser.parse_expression().value


        arguments["options"] = {"name": arguments["model_name"] + "." + arguments["view_type"]}
        arguments["options"].update(self.parse_options(parser))

        arguments["_id"] = self.extract_argument("id", arguments["options"], default="view_" + arguments["model_name"].replace(".", "_") + "_" + arguments["view_type"])
        arguments["string"] = self.extract_argument("string", arguments["options"])




        body = parser.parse_statements(['name:end%s' % arguments["view_type"]], drop_needle=True)

        return nodes.CallBlock(self.call_method('_generate_view', [nodes.Const(arguments)]), [], [], body).set_lineno(lineno)

    def _generate_view(self, arguments, caller):
        template = env.hamlish_from_string(GENERIC_VIEW_TEMPLATE)
        return template.render(body=caller().strip() + "\n",
                               type=arguments["view_type"] if arguments["view_type"] != "list" else "tree",
                               id=arguments["_id"],
                               description=arguments["string"],
                               model_name=arguments["model_name"],
                               options=arguments["options"],
                               has_action=arguments["has_action"],
                               has_menu=arguments["has_menu"],
                               action_options=arguments["action_options"],
                               menu_options=arguments["menu_options"],
                               action_id=arguments["action_id"],
                               menu_id=arguments["menu_id"],
                               search_view_id=arguments["search_view_id"],
                              )


FIELD_TEMPLATE = '%field name="{{ name }}"{% for key, value in options.items() %} {{ key }}="{{ value }}"{% endfor %}.'


class FieldShortcut(BaseExtension):
    tags = set(['f'])

    def parse(self, parser):
        arguments = {}
        lineno = parser.stream.next().lineno
        arguments["name"] = parser.parse_expression().value
        arguments["options"] = self.parse_options(parser)
        return nodes.CallBlock(self.call_method('_generate_view', [nodes.Const(arguments)]), [], [], []).set_lineno(lineno)

    def _generate_view(self, arguments, caller):
        return env.hamlish_from_string(FIELD_TEMPLATE).render(name=arguments["name"], options=arguments["options"])


env = Environment(extensions=[WithGenericView, FieldShortcut, HamlishExtension])


def modernize(indent=False):
    called_from = sys._getframe(1).f_globals["__file__"]
    module_directory = os.path.split(called_from)[0]

    if not os.path.exists(os.path.join(module_directory, "__openerp__.py")):
        return

    env.loader = FileSystemLoader(module_directory)
    if indent:
        env.hamlish_mode = 'indented'

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
        open(os.path.join(module_directory, xml_file), "w").write(to_write)
