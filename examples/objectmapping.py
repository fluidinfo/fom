

from fom.dev import sandbox_fluid
from fom.mapping import Object, Namespace, tag_value, tag_relation

# Use and bind the sandbox (for playing)
fluid = sandbox_fluid()

# let's start by creating a new Namespace for this application and then some
# tags

# Use the test user's namespace
ns = Namespace(u'test')

# create a child namespace for ourselves
ns.create_namespace(u'maptest', u'a test namespace')

# use our child namespace
ns = Namespace(u'test/maptest')

# create some tags
ns.create_tag(u'description', u'description', indexed=False)
ns.create_tag(u'timestamp', u'description', indexed=False)
ns.create_tag(u'username', u'description', indexed=False)


# Now we will define some behaviours mapping to groups of individual tags

class Describable(Object):
    """Mixin to provide describable behaviour
    """
    description = tag_value(u'test/maptest/description')


class Auditable(Object):
    """Mixin to provide auditable behaviour
    """
    timestamp = tag_value(u'test/maptest/timestamp')
    username = tag_value(u'test/maptest/username')


# And combine our mixins into our concrete model

class Meeting(Describable, Auditable):
    """A Meeting
    """
    def __repr__(self):
        return 'Meeting: %s' % self.timestamp


# Now we shall use it:

# create a new meeting
m = Meeting(about="a meeting")

# set some attributes
m.description = u'This meeting was boring'
m.timestamp = 123456
m.username = u'aliafshar'

# read some attributes
print m.description
print m.timestamp
print m.username

# so far the changes have not been saved to FluidDB, call save() to update
m.save()

# next we can play with relations.
# FluidDB has no built-int relationships, but fom adds some:

ns.create_tag(u'newspaper', u'description', False)
ns.create_tag(u'name', u'description', False)
ns.create_tag(u'title', u'description', False)

# These examples override the lazy_save flag so that when a field's value is
# updated FOM saves the change immediately (probably not a good idea but used
# here for illustrative purposes)

class Newspaper(Object):

    name = tag_value(u'test/maptest/name', lazy_save=False)

class Article(Object):

    title = tag_value(u'test/maptest/title', lazy_save=False)
    newspaper = tag_relation('test/maptest/newspaper', Newspaper,
        lazy_save=False)

n = Newspaper()
n.create()
n.name = u'Foss Weekly News'

a = Article()
a.create()
a.title = 'FluidDB, awesomeness in a can'
a.newspaper = n

# now load our object from the database
l = Article(a.uid)
print l.newspaper
