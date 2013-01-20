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
import sys
from jinja2 import Environment, FileSystemLoader, nodes
from jinja2.ext import Extension
from hamlish_jinja import HamlishExtension, Hamlish

# monkey patching because hamlish doesn't provide a clean way to do that :(
Hamlish._self_closing_html_tags.add("newline")
Hamlish._self_closing_html_tags.add("menuitem")

#Hamlish._self_closing_jinja_tags.add("with_tree")

tree_template = """\
%record#view_some_module_some_oerp_object model="ir.ui.view"
  %field name="name" << {{ model_name }}.tree
  %field name="model" << {{ model_name }}
  %field name="type" << tree
  %field name="arch" type="xml"
    %tree{% if description %} string="{{ description }}"{% endif %}
      =body
"""


class WithTree(Extension):
    tags = set(['with_tree'])

    def parse(self, parser):
        # skip tag name
        lineno = parser.stream.next().lineno
        model_name = parser.parse_expression().value
        #from ipdb import set_trace; set_trace()
        options = {"model_name": model_name}
        while parser.stream.current.type != 'block_end':
            key = parser.parse_assign_target().name
            parser.stream.expect('assign')
            value = parser.parse_tuple().value
            options[key] = value
        self.tag_options = options
        body = parser.parse_statements(['name:endwith_tree'], drop_needle=True)
        return nodes.CallBlock(self.call_method('_generate_view', []), [], [], body).set_lineno(lineno)

    def _generate_view(self, caller):
        return env.hamlish_from_string(tree_template).render(body=caller().strip() + "\n", **self.tag_options)


env = Environment(extensions=[WithTree, HamlishExtension])


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
        open(os.path.join(module_directory, xml_file), "w").write(env.get_template(haml_file).render())
