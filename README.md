OpenERP-Jinja2-Haml
===================

This lib allows you to use a derivate of the way shorter [haml
syntaxe](http://haml.info/) and the power of the [jinja2 templating
engine](http://jinja.pocoo.org/docs/) in OpenERP views.

Example
-------

```haml
%openerp
  %data
    %record#view_some_module_some_oerp_object model="ir.ui.view"
      %field name="name" << some_module.some_oerp_object.tree
      %field name="model" << some_module.some_oerp_object
      %field name="type"
        tree
      %field name="arch" type="xml"
        %tree string="Some title"
          %field name='name'.
          %field name='description'.
          %field name='type'.
```

Which you could also write:
```haml
%openerp
  %data
    -with_tree "some_module.some_oerp_object" string="Some title"
      %field name='name'.
      %field name='description'.
      %field name='type'.
```

Become:
```xml
<openerp>
  <data>
    <record id="view_some_module_some_oerp_object" model="ir.ui.view">
      <field name="name">some_module.some_oerp_object.tree</field>
      <field name="model">some_module.some_oerp_object</field>
      <field name="type">tree</field>
      <field name="arch" type="xml">
        <tree string="Some title">
          <field name='name'/>
          <field name='description'/>
          <field name='type'/>
        </tree>
      </field>
    </record>
  </data>
</openerp>
```

The exact haml syntax can be found [on the hamlish-jinja github's page](https://github.com/Pitmairen/hamlish-jinja).

Installation
============

    git clone git://github.com/Psycojoker/openerp-jinja2-haml.git
    cd openerp-jinja2-haml
    sudo python setup.py install

Haven't pushed on pypi yet.

Usage
=====

In an OpenERP module, edit the *__init__.py* file and add this:

```python
from oerpjh import import modernize
modernize()

# your usual imports
import openerp_objects_file1
import openerp_objects_file2
import openerp_objects_file3
...
```

Then, everytime you install/update your module in OpenERP:
* OpenERP-jinja2-haml will look for every *.xml* file declared in the module's *__openerp__.py*
* if a corresponding *.haml* file exists, OpenERP-jinja2-haml will compile it into the corresponding *.xml* file.

So, if you want to have a *foobar.xml* file generated by this lib, write your haml into *foobar.haml*.

Self closing tags
-----------------

So you know that:

```haml
%field name="description"
```

Will compile to:
```xml
<field name="description"></field>
```

But what you want is:
```xml
<field name="description"/>
```

The solution is to add a "." at the end of the haml line:

```haml
%field name="description".
```

Will compile to what you want.

**You don't need to do that with the list of the following tags**:

* newline
* menuitem

Some jinja2 goodness
--------------------

You can use any jinja2 tags like **include** or **extends**. Like that you
don't have to edit the *__openerp__.py* everytime you want to split a *.xml*
file.

Example (you can include both *.haml* files and *.xml* files):

```haml
%openerp
  %data
    -include "views.haml"
    -include "actions.haml"
    -include "menus.xml"
```

Indenting the generated XML
===========================

By default, OpenERP-Jinja2-haml doesn't indent the generated xml because their
is a bug in OpenERP server (at least the 6.0 version).

For example, if you write:

```xml
<field name="type">
    tree
</field>
```

Instead of:

```xml
<field name="type">tree</field>
```

You'll get an error message that will looks like this:

    osv.orm.except_orm: ('ValidateError', 'The value "\n                tree\n            " for the field "type" is not in the selection')

Yes, OpenERP is too stupid to do a .strip() on the string.

Yes, I want indented xml files
------------------------------

So, if you really want indented xml files (for debugging purpose for example), there is a simple workarround.

To activate indent mode, simply do this:

```python
from oerpjh import import modernize
modernize(indent=True)
```

The problem is that, in indented mode, this *.haml*:

```haml
%field name="type"
  tree
```

Will be compiled to this:

```xml
<field name="type">
    tree
</field>
```

The solution is to write:

```haml
%field name="type" << tree
```

That will compile to:

```xml
<field name="type">tree</field>
```

Thanks
======

This lib has been made possible by
[hamlish-jinja](https://github.com/Pitmairen/hamlish-jinja). Thanks to its
authors!
