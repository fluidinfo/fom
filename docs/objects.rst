
Fom object-orientated layer
===========================

The Fom object-mapping API attempts to place an object-orinetated layer over
the low-level REST api. The API is designed to be more natural to use as a
Python developer than the low-level API and for this reason departs in some
areas from the FluidDB API to aid usability.

All instances are "bound" to an api and a FluidDB instance. This binding to
the low-level API ensures that at all times there can be seamless switching
between the two levels of API to aid maximum flexibility. This is not a new
idea, and borrows heavily from how SQLAlchemy does things.


.. contents::
    :backlinks: none


Testing things out
------------------

The best source of reference information is the API documentation, and for
this article, I encourage the hands on use of the :command:`fdbc` script which you should
have if you have Fom installed (or in bin/fdbc of a source distribution). It
uses bpython for syntax loveliness, so you should install that.

Then launch the script::

    fdbc -s

The :option:`fdbc -s` parameter tells the shell to use the sandbox instance of FluidDB not
the main instance, and also logs you into the sandbox as the `test` user.


Namespaces
----------

Namespace functionality allows you to perform the common actions on
namespaces, namely manage child namespaces, or child tags.

A namespace must be instantiated with it's path::

    >>> Namespace(u'test') # the test user's namespace
    <Namespace path=u'test'>


Namespace descriptions
~~~~~~~~~~~~~~~~~~~~~~

All namespaces have a description, and this is accessible and settable using
the :attr:`~fom.mapping.Namespace.description` attribute::

    >>> Namespace(u'test').description
    u"FluidDB user 'test' top-level namespace."


Creating namespaces
~~~~~~~~~~~~~~~~~~~

A namespace is created using the :meth:`~fom.mapping.Namespace.create` method,
for example::

    >>> ns = Namespace(u'test/banana')
    >>> ns.create(u'This is a tag of a banana')
    <FluidResponse (201, 'application/json', None,
        {u'id': u'feae24cf-25fa-4d29-b579-405e2b505dee',
         u'URI': u'https://fluiddb.fluidinfo.com/namespaces/test/banana'})>
    >>> ns.description
    u'This is a tag of a banana'

.. note:: there is no FluidDB access from just instantiating a Fom namespace
          object. And the server is accessed when the tag is created.

If we try to create the same namespace again, we will not be allowed to::

    >>> ns.create(u'This is a tag of a banana')
    Traceback (most recent call last):
    ...
    Fluid412Error: <TNamespaceAlreadyExists (412 Precondition Failed)>

As we can see, the namespace already exists, and cannot be created again.


Deleting namespaces
~~~~~~~~~~~~~~~~~~~

A namespace can be deleted using the :meth:`~fom.mapping.Namespace.delete`
method, for example::

    >>> Namespace('test/banana').delete()
    <FluidResponse (204, 'text/html', None, '')>

You can't delete a namespace that doesn't exist::

    >>> Namespace('test/manana').delete()
    Traceback (most recent call last):
    ...
    Fluid404Error: <TNonexistentNamespace (404 Not Found)>


Accessing child namespaces in a namespace
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A child namespace can be accessed using the
:meth:`~fom.mapping.Namespace.namespace` method. Using the namespace of the
example above::

    >>> ns = Namespace(u'fluiddb') # fluiddb's own master namespace
    >>> ns.namespace(u'users')
    <Namespace path=u'fluiddb/users'>


Listing child namespaces in a namespace
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can get a list of all the namespaces in a namespace using the
:attr:`~fom.mapping.Namespace.namespaces` property::

    >>> Namespace(u'fluiddb').namespaces
    [<Namespace path=u'fluiddb/default'>, <Namespace path=u'fluiddb/tags'>,
     <Namespace path=u'fluiddb/users'>, ...]

Or if you want the paths of the namespaces, use the
:attr:`~fom.mapping.Namespace.namespace_paths` property::

    >>> Namespace(u'fluiddb').namespace_paths
    [u'fluiddb/default', u'fluiddb/tags', u'fluiddb/tag-values',
     u'fluiddb/namespaces', u'fluiddb/users', u'fluiddb/test']

Or if you just want the names of the namespaces, use the namespace_names
property::

    >>> Namespace(u'fluiddb').namespace_names
    [u'default', u'tags', u'tag-values', u'namespaces', u'users']


Creating child namespaces in a namespace
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you have an existing namespace, you can create child namespaces of it by
using the :meth:`~fom.mapping.Namespace.create_namespace` method of a
namespace, for example::

    >>> ns = Namespace(u'test')
    >>> ns.create_namespace(u'apple', u'The apple namespace')
    <Namespace path=u'test/apple'>

Which is exactly equivalent to having done::

    >>> ns = Namespace(u'test/apple')
    >>> ns.create(u'The apple namespace')
    <Namespace path=u'test/apple'>


Accessing child tags in a namespace
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Child tags in a namespace can be accessed using the
:meth:`~fom.mapping.Namespace.tag` method, passing the tag name, for example::

    >>> Namespace('fluiddb').tag('about')
    <Tag path='fluiddb/about'>

This returns an instance of :class:`~fom.mapping.Tag` which will be described
later in this document.


Listing child tags in a namespace
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In addition to child namespaces, namespaces can contain tags. These can be
listed similarly to child namespaces. Firstly to list the tags themselves, use
the :attr:`~fom.mapping.Namespace.tags` property::

    >>> Namespace(u'fluiddb').tags
    [<Tag path=u'fluiddb/about'>, <Tag path=u'fluiddb/activation-token'>,
     <Tag path=u'fluiddb/activation-pending'>, ...]

Or if you want the paths of the tags in the namespace, use the
:attr:`~fom.mapping.Namespace.tag_paths` property::

    >>> Namespace(u'fluiddb').tag_paths
    [u'fluiddb/about', u'fluiddb/activation-token',
     u'fluiddb/activation-pending', ...]

Or if you want the names of the tags in the namespace, user the
:attr:`~fom.mapping.Namespace.tag_names` property::

    >>> Namespace(u'fluiddb').tag_names
    [u'about', u'activation-token', u'activation-pending', u'created-at']


Creating child tags
~~~~~~~~~~~~~~~~~~~

Tags can be created in a namespace using the
:meth:`~fom.mapping.Namespace.create_tag` method::

    >>> Namespace('test').create_tag('my_review', u'My test review', indexed=False)
    <Tag path='test/my_review'>

Tags can also be created using the :class:`~fom.mapping.Tag` methods, as we will
see later.

Defining FluidDB Objects
~~~~~~~~~~~~~~~~~~~~~~~~

Inherit from the Object class and define fields with the tag_value class to
create ORM like classes/objects::

    >>> from fom.mapping import Object, tag_value
    >>> class User(Object):
    ...     username = tag_value('fluiddb/users/username')
    ...     fullname = tag_value('fluiddb/users/name')
    ...

Notice how the tag_value class takes an argument that contains the path to the
tag in FluidDB you want FOM to use to annotate the object within FluidDB.

Once the class is defined instantiated objects work as expected::

    >>> # Create a dictionary that represents the results for an individual
    >>> # object from a GET call to /values. See
    >>> # http://api.fluidinfo.com/html/api.html#values_GET
    >>> # for an example of what I mean.
    >>> initial_vals = {"fluiddb/users/username": {"value": "ntoll"}, "fluiddb/users/name": {"value": "Nicholas H.Tollervey"}, "fluiddb/about": {"value": "Object for the user named ntoll"}}
    >>> # instantiate the class with the initial values passed in
    >>> u = User(initial=initial_vals)
    >>> u.username
    'ntoll'
    >>> # BUT! The values associated with the object 'u' have not been saved
    >>> # so lets call save() which does exactly what you'd expect
    >>> u.save()

It's important to note that the `save()` method will only work with objects
that have a `fluiddb/about` tag value (the Object class defines this tag_value by default). This will change as FluidDB's `/values` API matures in the
not-too-distant future.

If the objects you're using in FluidDB don't have a `fluiddb/about` value you
can pass a special lazy_save=False argument. This forces FOM to use an
alternative API resource in FluidDB *but* it'll mean that FOM will call the
database every time a value is changed on the instantiated object::

    >>> class User(Object):
    ...     username = tag_value('fluiddb/users/username', lazy_save=False)
    ...     fullname = tag_value('fluiddb/users/name', lazy_save=False)
    ...
