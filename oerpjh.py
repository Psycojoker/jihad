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
from jinja2 import Environment, FileSystemLoader
from hamlish_jinja import HamlishExtension

def modernize(indent=False):
    called_from = sys._getframe(1).f_globals["__file__"]
    module_directory = os.path.split(called_from)[0]

    if not os.path.exists(os.path.join(module_directory, "__openerp__.py")):
        return

    env = Environment(extensions=[HamlishExtension], loader=FileSystemLoader(module_directory))
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
