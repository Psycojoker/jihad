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

generic_view_template = """\
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


class WithGenericView(Extension):
    tags = set(['with_tree', 'with_form', 'with_search'])

    def parse(self, parser):
        view_type = parser.stream.next()
        lineno = view_type.lineno
        self.view_type = view_type.value[len("with_"):]

        self.model_name = parser.parse_expression().value
        self.options = {"name": self.model_name + "." + self.view_type}
        self._id = "view_" + self.model_name.replace(".", "_")
        self.string = None

        while parser.stream.current.type != 'block_end':
            key = parser.parse_assign_target().name
            parser.stream.expect('assign')
            value = parser.parse_tuple().value
            self.options[key] = value

        if self.options.has_key("id"):
            self._id = self.options.get('id')
            del self.options["id"]

        if self.options.has_key("string"):
            self.string = self.options["string"]
            del self.options["string"]

        body = parser.parse_statements(['name:endwith_tree'], drop_needle=True)

        return nodes.CallBlock(self.call_method('_generate_view', []), [], [], body).set_lineno(lineno)

    def _generate_view(self, caller):
        return env.hamlish_from_string(generic_view_template).render(body=caller().strip() + "\n", type=self.view_type, id=self._id, description=self.string, model_name=self.model_name, options=self.options)


class FieldShortcut(Extension):
    tags = set(['f'])
    template = '%field name="{{ name }}"{% for key, value in options.items() %} {{ key }}="{{ value }}"{% endfor %}.'

    def parse(self, parser):
        lineno = parser.stream.next().lineno

        self.name = parser.parse_expression().value
        options = {}

        while parser.stream.current.type != 'block_end':
            key = parser.parse_assign_target().name
            parser.stream.expect('assign')
            value = parser.parse_tuple().value
            options[key] = value

        self.options = options

        return nodes.CallBlock(self.call_method('_generate_view', []), [], [], []).set_lineno(lineno)

    def _generate_view(self, caller):
        return env.hamlish_from_string(self.template).render(name=self.name, options=self.options)

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
