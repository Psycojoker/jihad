#!/usr/bin/python
# -*- coding:Utf-8 -*-

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

from setuptools import setup

setup(name='jihad',
      version='0.1.1',
      description='Use haml and jinja2 in OpenERP views',
      author='Laurent Peuch',
      #long_description='',
      author_email='cortex@worlddomination.be',
      url='https://github.com/Psycojoker/jihad',
      install_requires=['Hamlish-Jinja'],
      packages=[],
      py_modules=['jihad'],
      license= 'GPLv3+',
      scripts=[],
      keywords='',
     )
