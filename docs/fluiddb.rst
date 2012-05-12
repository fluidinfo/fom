
Fom REST layer
==============

This API is designed to be a clone of the actual FluidDB API. The only
difference is that it is available over Python, rather than http.

The API is presented as a component tree where:

    * some parts are callable,
    * some parts are accessible using attribute (dotted) lookup, and
    * some parts are accessible using dict-like lookup.

How these parts interlink is slightly complex, but again attempts to clone the
feel of the actual FluidDB API as much as possible.

Individual API components are constructable, and bindable to a database
instance so they can be used. The type of API component dictates how and when
these components are constructed.

The entire API is presented in the Fluid class which also takes care of
binding to a database. We can examine it:

    >>> from fom.session import Fluid
    >>> f = Fluid()
    >>> f.tags
    <fom.api.TagsApi object at ...>

So exactly in the same way that FluidDB presents the tags API at the
toplevel path `/tags` so does the fom api present it at `.tags`. This is an
example of the attribute based API component lookup and fom uses this when
there are a finite and known number of children, whose names are safe as
python attributes.

A TagsApi instance provides dict-like lookup for tag paths. And when called,
returns a TagApi component that is bound to that specific tag, and can be used
as such::

    >>> f.tags[u'fluiddb/about']
    <fom.api.TagApi object at ...>

It is this individual TagApi component that provides the per-tag calls in the
FluidDB API, for example::

    >>> f.tags[u'fluiddb/about'].get(returnDescription=True)
    (200, {u'indexed': False, u'id': ..., u'description': u'A description...')

This way, the entire FluidDB API is presented in Python in a way that is
faithful, yet tries to be Pythonic.

.. seealso::

    * Fom API documentation: http://bytebucket.org/aafshar/fom-main/wiki/api.html#fom-api
    * The FluidDB API documentation: `<http://api.fluidinfo.com/fluidDB/api/*/*/*>`_

