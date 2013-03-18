Jihad
=====

This lib allows you to use a derivate of the way shorter [haml
syntaxe](http://haml.info/) and the power of the [jinja2 templating
engine](http://jinja.pocoo.org/docs/) in OpenERP views.

Example
-------

Tired of writing long and repetitive code like this?
```xml
<?xml version="1.0"?>
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

You can now write it like this:
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

Which you could also write like this:
```haml
%openerp
  %data
    -tree "some_module.some_oerp_object" string="Some title"
      %field name='name'.
      %field name='description'.
      %field name='type'.
```

Or even like this (because writting \<openerp\>\<data\> all the time is useless and boring):
```haml
-tree "some_module.some_oerp_object" string="Some title"
  %field name='name'.
  %field name='description'.
  %field name='type'.
```

Style too much for you? Here you go:
```haml
-tree "some_module.some_oerp_object" string="Some title"
  -f "name"
  -f "description"
  -f "type"
```

The exact haml syntax can be found [on the hamlish-jinja github's page](https://github.com/Pitmairen/hamlish-jinja).

Installation
============

    git clone git://github.com/Psycojoker/Jihad.git
    cd Jihad
    sudo python setup.py install

Haven't pushed on pypi yet.

Usage
=====

In an OpenERP module, edit the *\_\_init\_\_.py* file and add this:

```python
from jihad import purify
purify()

# your usual imports
import openerp_objects_file1
import openerp_objects_file2
import openerp_objects_file3
...
```

Then, everytime you install/update your module in OpenERP:
* Jihad will look for every *.xml* file declared in the module's *\_\_openerp\_\_.py*
* if a corresponding *.haml* file exists, Jihad will compile it into the corresponding *.xml* file.

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
don't have to edit the *\_\_openerp\_\_.py* everytime you want to split a *.xml*
file.

Example (you can include both *.haml* files and *.xml* files):

```haml
%openerp
  %data
    -include "views.haml"
    -include "actions.haml"
    -include "menus.xml"
```

Useless \<openerp\>\<data\>
-----------------------

You don't need to write \<openep\>\<data\> (or more exactly: %openerp%data) at the
beginning of a view, Jihad, before compiling a declared view in
the \_\_openerp\_\_.py, will check if it's present and if it's not the case,
will include it.

You should not have the need to repeat yourself all the time.

**This does not affect files included via the -include so you won't have any
\<openerp\>\<data\> appearing out of nowhere if you use it.**

Shortcut for \<field name="..." ... /\>
---------------------------------------

Since you'll spend
[alot](http://hyperboleandahalf.blogspot.be/2010/04/alot-is-better-than-you-at-everything.html)
of time writing \<field name="..." ... /\>, this lib provide an handy shortcut:

Instead of writing:
```xml
<field name="field_name" option1="value1" option2="value2" ... />
```

You can simply write:
```haml
-f "field_name" option1="value1" option2="value2" ...
```

*field_name* is the only mandatory value to provide to this shortcut.

Advanced usage
==============

OpenERP often ask you to write of lot of repetitive code, by chance, Jinja2
allows us to write some cool extensions to save us from this burden.

Generic view wrapper
--------------------

Allow you to write classical form/search/tree view in a way shorter manner:

```haml
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

Can be written:
```haml
-tree "some_module.some_oerp_object" string="Some title"
  %field name='name'.
  %field name='description'.
  %field name='type'.
```

The syntax is:
```haml
-(tree,search,form) "model _name" option1="value1" option2="value2" ...
  %field name='name'.
  %field name='description'.
  %field name='type'.
```

Every option you add will be added to the view option next to the
name/model/type options. The 2 only exceptions are: id and string that will
take their expected places.

Here are the options that came with default values:
* **id**: the id of the view, the default value is "view_" + model_name.replace(".", "_") + "_" + view_type
* **name**: the name of the view, the default value is: model_name + "." + view_type (for example "some_module.some_oerp_object.tree" in a tree view)

You don't have to supply any option, you can only write *-tree "model_name"* if you want to.

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
