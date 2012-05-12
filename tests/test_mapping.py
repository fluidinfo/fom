import unittest
import json

from fom.db import NO_CONTENT
from fom.session import Fluid
from fom.api import FluidApi, ItemPermissionsApi
from fom.mapping import (path_split, path_child, Namespace, Tag, Object,
    tag_relation, tag_value, tag_collection, Permission, Permissions,
    tag_relations, readonly_tag_value, UNKNOWN_VALUE)
from fom.errors import Fluid404Error


from _base import FakeFluidDB


class _MappingTestCase(unittest.TestCase):

    def setUp(self):
        self.db = FakeFluidDB()
        self.api = FluidApi(self.db)
        Fluid.bound = self.api

    @property
    def last(self):
        return self.db.reqs[0]


class TestGetTagValues(_MappingTestCase):
    """Checks that the recursive function for extracting readonly_tag_value
    based fields works as expected
    """

    def testGetTagValues(self):

        class a(Object):

            t1 = tag_value('foo/bar')

        class b(a):

            t2 = tag_value('baz/qux')

        x = a()
        y = b()

        self.assertEquals(2, len(x._path_map))
        self.assertEquals(3, len(y._path_map))

        self.assertTrue('fluiddb/about' in x._path_map)
        self.assertTrue('fluiddb/about' in y._path_map)
        self.assertTrue('foo/bar' in x._path_map)
        self.assertTrue('foo/bar' in y._path_map)
        self.assertFalse('baz/qux' in x._path_map)
        self.assertTrue('baz/qux' in y._path_map)


class TestPath(unittest.TestCase):
    """Checks that functions for creating/splitting paths work as expected
    """

    def test_parent(self):
        self.assertEquals(path_split(u'goo/moo'), [u'goo', u'moo'])

    def test_child(self):
        self.assertEquals(path_child(u'foo', u'blah'), u'foo/blah')

    def test_empty(self):
        self.assertEquals(path_child(u'', 'foo'), u'foo')


class PermissionTest(unittest.TestCase):
    """Checks that the Policy class behaves as expected
    """

    def test_init(self):
        # default
        p = Permission()
        self.assertEquals('open', p.policy)
        self.assertEquals([], p.exceptions)
        # overridden
        p = Permission(policy='closed', exceptions=['foo', ])
        self.assertEquals('closed', p.policy)
        self.assertEquals(['foo', ], p.exceptions)

    def test_set_policy(self):
        p = Permission(policy='closed')
        # good
        p.policy = 'open'
        self.assertEquals('open', p.policy)
        p.policy = 'closed'
        self.assertEquals('closed', p.policy)

    def test_set_exceptions(self):
        p = Permission(policy='open', exceptions=['foo'])
        # good
        p.exceptions = ['foo', 'bar']
        self.assertEqual(['foo', 'bar'], p.exceptions)
        p.exceptions.append('baz')
        self.assertEqual(['foo', 'bar', 'baz'], p.exceptions)


class PermissionsTest(_MappingTestCase):
    """Checks the Permissions class works as expected
    """

    def testInit(self):
        p = Permissions(self.api.permissions.namespaces['test'])
        self.assertTrue(isinstance(p.api, ItemPermissionsApi))

    def testGet(self):
        p = Permissions(self.api.permissions.namespaces['test'])
        # good
        self.db.add_resp(200, 'application/json',
            '{"policy": "closed", "exceptions": ["test"]}')
        policy = p['create']
        self.assertTrue(isinstance(policy, Permission))

    def testSet(self):
        p = Permissions(self.api.permissions.namespaces['test'])
        policy = Permission(policy='closed', exceptions=['test', ])
        # good
        p['create'] = policy
        self.assertEquals(self.db.reqs[0], (
            'PUT',
            '/permissions/namespaces/test',
            {u'policy': 'closed', u'exceptions': ['test']},
            {u'action': 'create'},
            None))
        self.db.add_resp(200, 'application/json',
            '{"policy": "closed", "exceptions": ["test"]}')
        check_policy = p['create']
        self.assertEquals(self.db.reqs[1], (
            'GET',
            '/permissions/namespaces/test',
            NO_CONTENT,
            {u'action': 'create'},
            None))
        self.assertEquals(policy.policy, check_policy.policy)
        self.assertEquals(policy.exceptions, check_policy.exceptions)


class NamespaceTest(_MappingTestCase):
    """Makes sure the Namespace class behaves as expected
    """

    def testNew(self):
        n = Namespace(u'test')
        self.assertEquals(n.path, u'test')
        self.assertTrue(n.fluid is self.api)

    def testCreate(self):
        ns = Namespace(u'test/test')
        ns.create(u'fomtest description')
        self.assertEqual(self.last, (
            'POST',
            u'/namespaces/test',
            {'name': u'test',
             'description': u'fomtest description'},
            None,
            None))

    def testDescription(self):
        ns = Namespace(u'test/test')
        ns.description = u'testDesc'
        self.assertEqual(self.last, (
            'PUT',
            u'/namespaces/test/test',
            {u'description': u'testDesc'},
            None,
            None))

    def test_create_child(self):
        n = Namespace(u'test')
        self.db.add_resp(201, 'application/json',
            '{"id": "4", "URI": "https')
        child = n.create_namespace(u'test', u'fomtest description')
        self.assertEquals(child.path, u'test/test')
        self.assertEqual(self.last, (
            'POST',
            u'/namespaces/test',
            {'name': u'test', 'description': u'fomtest description'},
            None,
            None))

    def testChildNamespace(self):
        n = Namespace(u'test')
        child = n.namespace(u'test')
        self.assertTrue(isinstance(child, Namespace))
        self.assertEquals(child.path, u'test/test')

    def testChildTag(self):
        n = Namespace(u'test')
        child = n.tag(u'test')
        self.assertTrue(isinstance(child, Tag))
        self.assertEquals(child.path, u'test/test')

    def testCreateTag(self):
        n = Namespace(u'test')
        self.db.add_resp(201, 'application/json',
            '{"id": "4", "URI": "https')
        new_tag = n.create_tag(u'test', 'a test')
        self.assertTrue(isinstance(new_tag, Tag))
        self.assertEqual(self.last, (
            'POST',
            u'/tags/test',
            {u'indexed': False,
             u'name': u'test',
             u'description': 'a test'},
            None,
            None))

    def testPermissions(self):
        n = Namespace(u'test')
        # Get good
        self.db.add_resp(200, 'application/json',
            '{"policy": "closed", "exceptions": ["test"]}')
        p = n.permissions['create']
        self.assertTrue(isinstance(p, Permission))
        self.assertEquals(self.db.reqs[0], (
            'GET',
            '/permissions/namespaces/test',
            NO_CONTENT,
            {u'action': 'create'},
            None))


class ObjectTest(_MappingTestCase):
    """Checks that the Object class behaves as expected
    """

    def testNew(self):
        """Make sure a new object is in the correct state
        """
        o = Object()
        self.assertTrue(o.uid is None)

    def testCreate(self):
        """Creating an object works!
        """
        o = Object()
        self.db.add_resp(201, 'application/json',
            '{"id": "9d4", "URI": "https"}')
        o.create()
        self.assert_(o.uid)
        self.assertEqual(self.last, (
            'POST',
            '/objects',
            {},
            None,
            None))

    def testCreateWithAbout(self):
        """Make sure creating an object with an about tag value works
        """
        self.db.add_resp(201, 'application/json',
            '{"id": "9d4", "URI": "https"}')
        o = Object(about="foo")
        self.assert_(o.uid)
        self.assertEqual(self.last, (
            'POST',
            '/objects',
            {u'about': 'foo'},
            None,
            None))

    def testCreateCheckPathMap(self):
        """Makes sure the meta-class correctly build up the _path_map dict
        that's used to link tag paths to field names
        """

        class UserClass(Object):
            username = tag_value('fluiddb/users/username')
            name = tag_value('fluiddb/users/name')

        u = UserClass()
        self.assertTrue('fluiddb/users/username' in u._path_map)
        self.assertTrue('fluiddb/users/name' in u._path_map)
        self.assertTrue('fluiddb/about' in u._path_map)
        self.assertEqual('username', u._path_map['fluiddb/users/username'])
        self.assertEqual('name', u._path_map['fluiddb/users/name'])
        self.assertEqual('about', u._path_map['fluiddb/about'])

    def testCreateWithInitialValueDictionary(self):
        """Ensure that an initial value dictionary (based upon the results of
        a call to the /values resource) correctly sets up the object's values
        """

        class UserClass(Object):
            username = tag_value('fluiddb/users/username')
            name = tag_value('fluiddb/users/name')

        self.db.add_resp(201, 'application/json',
            '{"id": "9d4", "URI": "https"}')
        initial_vals = {"fluiddb/users/username": {"value": "ntoll"},
            "fluiddb/users/name": {"value": "Nicholas H.Tollervey"},
            "fluiddb/about": {"value": "Object for the user named ntoll"}}
        u = UserClass('9d4', initial=initial_vals)
        # check the about value has been correctly extracted
        self.assertEquals("Object for the user named ntoll", u.about)
        self.assert_(u.uid)
        # the other two fields have not been saved
        self.assertEquals(2, len(u._dirty_fields))
        # but the values are in place
        self.assertEquals('ntoll', u.username)
        self.assertEquals('Nicholas H.Tollervey', u.name)

    def testLazySaveNoAbout(self):
        """Make sure save() *won't* work without an about tag value
        """

        class UserClass(Object):
            username = tag_value('fluiddb/users/username')
            name = tag_value('fluiddb/users/name')

        u = UserClass(uid='12345')
        u.username = 'foo'
        u.name = 'bar'
        u.about = None
        self.assertRaises(ValueError, u.save)

    def testLazySave(self):
        """Ensure the save() method works correctly
        """

        class UserClass(Object):
            username = tag_value('fluiddb/users/username')
            name = tag_value('fluiddb/users/name')

        self.db.add_resp(201, 'application/json',
            '{"id": "9d4", "URI": "https"}')
        initial_vals = {"fluiddb/users/username": {"value": "ntoll"},
            "fluiddb/users/name": {"value": "Nicholas H.Tollervey"}}
        u = UserClass(initial=initial_vals)
        u.about = 'foo'
        # the other two fields have not been saved
        self.assertEquals(2, len(u._dirty_fields))
        # save them and check the PUT has worked
        u.save()
        self.assertEquals(self.last, (
            'PUT',
            '/values',
            {'queries': [['fluiddb/about = "foo"', {
                'fluiddb/users/username': {'value': 'ntoll'},
                'fluiddb/users/name': {'value': 'Nicholas H.Tollervey'}}]]},
            None,
            None))

    def testDirtyFields(self):
        """Make sure the dirtyfields set is updated correctly throughout the
        lifecycle of the object
        """

        class UserClass(Object):
            username = tag_value('fluiddb/users/username')
            name = tag_value('fluiddb/users/name')

        self.db.add_resp(201, 'application/json',
            '{"id": "9d4", "URI": "https"}')
        u = UserClass(about="foo")
        # Nothing set
        self.assertEquals(0, len(u._dirty_fields))
        # check the _dirty_fields set is updated as changes are made
        u.username = 'foo'
        self.assertEquals(1, len(u._dirty_fields))
        u.name = 'foo'
        self.assertEquals(2, len(u._dirty_fields))
        # the _dirty_fields are cleared when we save
        u.save()
        self.assertEquals(0, len(u._dirty_fields))

    def testOpaqueFieldsInLazySave(self):
        """
        Ensures that opaque tag values are not included as part of a /values
        based api call.
        """
        class Foo(Object):
            baz = tag_value('foo/baz', content_type='text/html')

        self.db.add_resp(201, 'application/json',
            '{"id": "9d4", "URI": "https"}')
        f = Foo(about='qux')
        f.uid = '123'
        # Nothing set
        self.assertEquals(0, len(f._dirty_fields))
        # If you try to save an opaque type it doesn't affect the
        # _dirty_fields but is updated on the fly
        self.db.add_resp(204, 'text/html', None)
        f.baz = '<html><body><p>Hello!</p></body></html>'
        self.assertEquals(0, len(f._dirty_fields))

    def testGet(self):
        o = Object()
        o.uid = '9'
        o.get(u'test/test')
        self.assertEqual(self.last, (
            'GET',
            u'/objects/9/test/test',
            NO_CONTENT,
            None,
            None))

    def testGetUnsavedNoneValue(self):
        class mockClass(Object):
            foo = tag_value('foo/bar')

        o = mockClass()
        o.uid = '9'
        value = o.foo
        self.assertEqual(self.last, (
            'GET',
            u'/objects/9/foo/bar',
            NO_CONTENT,
            None,
            None))
        # reset the request list to empty
        self.db.reqs = []
        o = mockClass()
        o.uid = '9'
        o.foo = None
        value = o.foo
        self.assertEquals(None, value)
        self.assertFalse(self.db.reqs)

    def testSetPrimitive(self):
        o = Object()
        o.uid = '9'
        for i, value in enumerate(
            (None, True, False, 123, 45.67, 'hey')):
            o.set(u'test/test', value)
            self.assertEqual(value, o._cache[u'test/test'])
            self.assertEqual(self.db.reqs[i], (
                'PUT',
                u'/objects/9/test/test',
                value,
                None,
                None))

    def testSetExistingTagValue(self):
        """ Ensures that set will check that the tag path isn't already handled
        by a tag_value instance on the class and behave appropriately as a
        result.
        """
        # The default case

        class TestClass(Object):

            t = tag_value(u'test/test')

        x = TestClass()
        x.set(u'test/test', 'foo')
        # the field has been marked dirty
        self.assertEquals(1, len(x._dirty_fields))
        # the value is cached
        self.assertEquals(1, len(x._cache))
        self.assertEquals('foo', x._cache[u'test/test'])
        # no call was made to FluidDB (only happens on save)
        self.assertEquals([], self.db.reqs)

        # The non-default case where the tag_value is lazy_save=False
        class TestClass2(Object):

            t = tag_value(u'test/test', lazy_save=False)

        x = TestClass2()
        x.uid = '1'
        x.set(u'test/test', 'foo')
        # check the request went through
        self.assertEqual(self.db.reqs[0], (
            'PUT',
            u'/objects/1/test/test',
            'foo',
            None,
            None))
        # and the lazy_save related stuff remains un-affected
        self.assertEqual(0, len(x._dirty_fields))

    def testSetLazyTagValue(self):
        """ Ensures Object's set_lazy_tag_value works correctly.
        """

        class TestClass(Object):

            t = tag_value(u'test/test')

        x = TestClass()
        tv = x.__class__.__dict__['t']
        # the good case (with a primitive type)
        x.set_lazy_tag_value(tv, 'foo')
        self.assertEqual(1, len(x._dirty_fields))
        self.assertEqual(1, len(x._cache))
        self.assertEqual('foo', x._cache[u'test/test'])
        # make sure the validation works as expected
        # 1 - fail upon non-primitive value
        self.assertRaises(ValueError, x.set_lazy_tag_value, tv, x)
        # 2 - fail upon non-primitive list like object
        self.assertRaises(ValueError, x.set_lazy_tag_value, tv, [x, 'foo'])

    def testSetOpaque(self):
        o = Object()
        o.uid = '7'
        o.set(u'test/test', 'xyz', 'application/bananas')
        self.assertEqual(self.last, (
            'PUT',
            u'/objects/7/test/test',
            'xyz',
            None,
            'application/bananas'))

    def testHas(self):
        o = Object()
        o.uid = '0'
        self.db.add_resp(404, 'application/json', 'TNoInstanceOnObject')
        self.assertFalse(o.has('test/fomtest'))
        self.assertEqual(self.db.reqs[0], (
            'HEAD',
            '/objects/0/test/fomtest',
            NO_CONTENT,
            None,
            None))
        self.db.add_resp(200, 'application/vnd.fluiddb.value+json', '')
        self.assertTrue(o.has('test/fomtest'))
        self.assertEqual(self.db.reqs[1], (
            'HEAD',
            '/objects/0/test/fomtest',
            NO_CONTENT,
            None,
            None))

    def testTags(self):
        o = Object()
        o.uid = '3'
        self.db.add_resp(200, 'application/json',
            '{"tagPaths": []}')
        self.assertEqual(o.tag_paths, [])
        self.assertEqual(self.db.reqs[0], (
            'GET',
            '/objects/3',
            NO_CONTENT,
            {'showAbout': False},
            None))
        self.db.add_resp(200, 'application/json',
            '{"tagPaths": []}')
        self.assertEquals(o.tags, [])
        self.assertEqual(self.db.reqs[1], (
            'GET',
            '/objects/3',
            NO_CONTENT,
            {'showAbout': False},
            None))
        self.db.add_resp(200, 'application/json',
            '{"tagPaths": ["test\\/fomtest"]}')
        self.assertTrue('test/fomtest' in o.tag_paths)
        self.assertEqual(self.db.reqs[2], (
            'GET',
            '/objects/3',
            NO_CONTENT,
            {'showAbout': False},
            None))
        self.db.add_resp(200, 'application/json',
            '{"tagPaths": ["test\\/fomtest"]}')
        self.assertEquals(o.tags[0].path, 'test/fomtest')
        self.assertEqual(self.db.reqs[3], (
            'GET',
            '/objects/3',
            NO_CONTENT,
            {'showAbout': False},
            None))

    def testFilter(self):
        self.db.add_resp(200, 'application/json',
            '{"ids": ["466"]}')
        results = Object.filter('fluiddb/users/username = "ntoll"')
        self.assertEquals(1, len(results))
        # the _dirty_fields have not been added to
        self.assertEquals(0, len(results[0]._dirty_fields))
        self.assertEquals(self.db.reqs[0], (
            'GET',
            '/objects',
            NO_CONTENT,
            {'query': 'fluiddb/users/username = "ntoll"'},
            None))
        self.db.add_resp(200, 'application/vnd.fluiddb.value+json',
            u'test')
        self.assertEquals(u'test', results[0].about)
        self.assertEquals(self.db.reqs[1], (
            'GET',
            u'/objects/466/fluiddb/about',
            NO_CONTENT,
            None,
            None))

    def testFilterCustomType(self):

        class UserClass(Object):
            username = tag_value('fluiddb/users/username')
            name = tag_value('fluiddb/users/name')

        response = {'results': {'id': {'05eee31e-fbd1-43cc-9500-0469707a9bc3': {
                'fluiddb/users/username':{'value': 'ntoll'},
                'fluiddb/users/name':{'value': 'Nicholas'},
                'fluiddb/about': {'value': 'Object about the user ntoll'}
                }}}}

        self.db.add_resp(200, 'application/json', json.dumps(response))
        results = UserClass.filter('fluiddb/users/username = "ntoll"')
        self.assertEquals(1, len(results))
        # the _dirty_fields have not been added to
        self.assertEquals(0, len(results[0]._dirty_fields))
        self.assertEquals(self.db.reqs[0], (
            'GET',
            '/values',
            NO_CONTENT,
            (('query', 'fluiddb/users/username = "ntoll"'),
            ('tag', 'fluiddb/about'),
            ('tag', 'fluiddb/users/username'),
            ('tag', 'fluiddb/users/name')),
            None))
        user = results[0]
        self.assertTrue('fluiddb/about' in user._cache)
        self.assertTrue('fluiddb/users/name' in user._cache)
        self.assertTrue('fluiddb/users/username' in user._cache)
        self.assertEquals('Object about the user ntoll', user.about)
        self.assertEquals('Nicholas', user.name)
        self.assertEquals('ntoll', user.username)

    def testFilterResultType(self):

        class UserClass(Object):
            username = tag_value('fluiddb/users/username')
            name = tag_value('fluiddb/users/name')

        response = {'results': {'id': {'05eee31e-fbd1-43cc-9500-0469707a9bc3': {
                'fluiddb/users/username':{'value': 'ntoll'},
                'fluiddb/users/name':{'value': 'Nicholas'},
                'fluiddb/about': {'value': 'Object about the user ntoll'}
                }}}}

        self.db.add_resp(200, 'application/json', json.dumps(response))
        results = Object.filter('fluiddb/users/username = "ntoll"',
                               result_type=UserClass)
        self.assertEquals(1, len(results))
        # the _dirty_fields have not been added to
        self.assertEquals(0, len(results[0]._dirty_fields))
        self.assertEquals(self.db.reqs[0], (
            'GET',
            '/values',
            NO_CONTENT,
            (('query', 'fluiddb/users/username = "ntoll"'),
            ('tag', 'fluiddb/about'),
            ('tag', 'fluiddb/users/username'),
            ('tag', 'fluiddb/users/name')),
            None))
        user = results[0]
        self.assertTrue('fluiddb/about' in user._cache)
        self.assertTrue('fluiddb/users/name' in user._cache)
        self.assertTrue('fluiddb/users/username' in user._cache)
        self.assertEquals('Object about the user ntoll', user.about)
        self.assertEquals('Nicholas', user.name)
        self.assertEquals('ntoll', user.username)

    def testEquality(self):
        b = Object()
        b.uid = '7'
        a = Object(b.uid)
        self.assertEqual(a, b)


class TagValueTest(_MappingTestCase):
    """Checks the tag_value class works as expected
    """

    def testLazySaveType(self):

        class fomtest(Object):
            ft = tag_value('test1')
            ft2 = tag_value('test2', 'text/html')

        obj = fomtest()
        obj.uid = '1'
        obj.about = '1'
        obj.ft = 1
        self.assertEqual(1, len(obj._dirty_fields))
        obj.save()
        self.assertEqual(self.db.reqs[0], (
            'PUT',
            '/values',
            {'queries': [['fluiddb/about = "1"',
                {'test1': {'value': 1}}]]},
            None,
            None))

    def testEagerType(self):

        class fomtest(Object):
            ft = tag_value('test1', lazy_save=False)
            ft2 = tag_value('test2', 'text/html', lazy_save=False)

        obj = fomtest()
        obj.uid = '1'
        obj.ft = 1
        self.assertEqual(self.db.reqs[0], (
            'PUT',
            '/objects/1/test1',
            1,
            None,
            None))
        obj.ft2 = '<html />'
        self.assertEqual(self.db.reqs[1], (
            'PUT',
            '/objects/1/test2',
            '<html />',
            None,
            'text/html'))
        self.db.add_resp(200, 'application/vnd.fluiddb.value+json',
            u'test')
        ft_result = obj.get('test1')
        self.assertEqual(self.db.reqs[2], (
            'GET',
            '/objects/1/test1',
            NO_CONTENT,
            None,
            None))
        self.db.add_resp(200, 'text/html',
            u'<html />')
        ft2_result = obj.get('test2')
        self.assertEqual(self.db.reqs[3], (
            'GET',
            '/objects/1/test2',
            NO_CONTENT,
            None,
            None))
        self.assertEquals('application/vnd.fluiddb.value+json',
                          ft_result[1])
        self.assertEquals('text/html',
                          ft2_result[1])
        obj.set('test2', '<html />', None)
        self.assertEqual(self.db.reqs[4], (
            'PUT',
            '/objects/1/test2',
            '<html />',
            None,
            None))
        obj.refresh()
        self.db.add_resp(200, 'application/vnd.fluiddb.value+json',
            u'<html />')
        self.assertEquals('<html />', obj.ft2)
        self.assertEqual(self.db.reqs[5], (
            'GET',
            '/objects/1/test2',
            NO_CONTENT,
            None,
            None))
        self.db.add_resp(200, 'application/vnd.fluiddb.value+json',
            u'<html />')
        ft2_result = obj.get('test2')
        self.assertEqual(self.db.reqs[6], (
            'GET',
            '/objects/1/test2',
            NO_CONTENT,
            None,
            None))
        self.assertEquals('application/vnd.fluiddb.value+json',
                          ft2_result[1])


class ObjectCachingTest(_MappingTestCase):
    """Ensures the caching mechanism works in the Object class
    """

    def testSetCaching(self):

        class fomtest(Object):
            ft = tag_value(u'test')

        obj = fomtest()
        obj.uid = '0'
        obj.ft = 1
        self.assertEquals(obj.get_cached(u'test'), 1)

    def testGetCaching(self):

        class fomtest(Object):
            ft = tag_value(u'test')

        obj = fomtest()
        obj.uid = '0'
        obj.ft = 1
        obj2 = fomtest()
        obj2.uid = '0'
        self.assertTrue(isinstance(obj2.get_cached(u'test'), UNKNOWN_VALUE))
        self.db.add_resp(200, 'application/vnd.fluiddb.value+json',
            u'1')
        self.assertEquals(obj2.ft, 1)
        self.assertEquals(obj.get_cached(u'test'), 1)

    def testNoCacheGet(self):
        """
        Ensures that values are grabbed from FluidDB as they are referenced
        from Object classes with tag_value instances.
        """
        class fomtest(Object):
            ft = tag_value(u'test', cached=False)

        self.db.add_resp(200, 'application/vnd.fluiddb.value+json',
            u'1')
        obj = fomtest()
        obj.uid = '0'
        self.assertEquals(obj.ft, 1)

    def testCacheDeleting(self):

        class fomtest(Object):
            ft = tag_value('test/fomtest')

        obj = fomtest()
        obj.uid = '0'
        obj.ft = 1
        self.assertEquals(obj.get_cached('test/fomtest'), 1)
        obj.refresh()
        self.assertTrue(isinstance(obj.get_cached('test/fomtest'),
            UNKNOWN_VALUE))

    def testCacheDeletingSingle(self):

        class fomtest(Object):
            ft = tag_value('test/fomtest')

        obj = fomtest()
        obj.uid = '0'
        obj.ft = 1
        self.assertEquals(obj.get_cached('test/fomtest'), 1)
        obj.refresh('test/fomtest')
        self.assertTrue(isinstance(obj.get_cached('test/fomtest'),
            UNKNOWN_VALUE))


class TagTest(_MappingTestCase):
    """Tests to ensure the Tag class behaves as expected
    """

    def testNew(self):
        t = Tag(u'test/fomtest')
        self.assertEquals(t.path, 'test/fomtest')

    def testGetDescription(self):
        t = Tag(u'test/fomtest')
        t.description = u'banana'
        self.assertEquals(self.db.reqs[0], (
            'PUT',
            u'/tags/test/fomtest',
            {u'description': u'banana'},
            None,
            None))
        self.db.add_resp(200, 'application/json',
            '{"indexed": false, "id": "9", "description": "banana"}')
        self.assertEquals(t.description, u'banana')
        self.assertEquals(self.db.reqs[1], (
            'GET',
            u'/tags/test/fomtest',
            NO_CONTENT,
            {u'returnDescription': True},
            None))

    def testSetDescription(self):
        t = Tag('test/fomtest')
        t.description = u'melon'
        self.assertEquals(self.db.reqs[0], (
            'PUT',
            u'/tags/test/fomtest',
            {u'description': u'melon'},
            None,
            None))


class RelationTest(_MappingTestCase):
    """Ensures that the tag_relation class works as expected
    """

    def testRelation(self):

        class A(Object):
            fomtest = tag_relation(u'test/fomtest')

        a1 = A()
        a1.uid = '1'
        a1.about = 'test1'
        a2 = A()
        a2.uid = '2'
        a2.about = 'test2'
        a1.fomtest = a2
        a2.save()
        a1.save()
        # save() uses the /values api
        self.assertEquals(self.db.reqs[0], (
            'PUT',
            '/values',
            {'queries': [['fluiddb/about = "test1"',
                {u'test/fomtest': {'value': '2'}}]]},
            None,
            None))
        a1.refresh()
        self.db.add_resp(200, 'application/vnd.fluiddb.value+json',
            u'"2"')
        self.assertEquals(a1.fomtest.uid, a2.uid)
        self.assertEquals(self.db.reqs[1], (
            'GET',
            u'/objects/1/test/fomtest',
            NO_CONTENT,
            None,
            None))

    def testMissingValue(self):

        class A(Object):
            fomtest = tag_value(u'test/fomtest', lazy_save=False)

        a1 = A()
        a1.uid = '1'
        self.db.add_resp(404, 'application/json', 'Not Found')
        try:
            a1.fomtest
        except Fluid404Error:
            pass
        else:
            self.fail('Failed to raise Fluid404Error')

    def testValue(self):

        class A(Object):
            fomtest = tag_value(u'test/fomtest', lazy_save=False)

        a1 = A()
        a1.uid = '1'
        a1.fomtest = 'hello'
        self.assertEquals(self.db.reqs[0], (
            'PUT',
            u'/objects/1/test/fomtest',
            'hello',
            None,
            None))
        a1.refresh()
        self.db.add_resp(200, 'application/vnd.fluiddb.value+json',
            u'"hello"')
        self.assertEquals(a1.fomtest, 'hello')
        self.assertEquals(self.db.reqs[1], (
            'GET',
            u'/objects/1/test/fomtest',
            NO_CONTENT,
            None,
            None))


class ManagerTest(_MappingTestCase):
    """Ensures that the tag_collection class behaves as expected
    """

    def testAdd(self):

        class A(Object):
            fomtest = tag_collection(u'test/fomtest', lazy_save=False)

        a1 = A()
        a1.uid = 'a1'
        a2 = A()
        a2.uid = 'a2'
        self.db.add_resp(200, 'application/vnd.fluiddb.value+json',
            u'"test/fommanager"')
        a1.fomtest.add(a2)
        self.assertEquals(self.db.reqs[0], (
            'GET',
            u'/objects/a1/test/fomtest',
            NO_CONTENT,
            None,
            None))
        self.assertEquals(self.db.reqs[1], (
            'PUT',
            u'/objects/a2/test/fommanager',
            'a1',
            None,
            None))
        a2.refresh()
        a1.refresh()
        self.db.add_resp(200, 'application/vnd.fluiddb.value+json',
            u'"test/fommanager"')
        self.db.add_resp(200, 'application/json',
            '{"ids": ["a2"]}')
        self.assertTrue(a2 in a1.fomtest)
        self.assertEquals(self.db.reqs[2], (
            'GET',
            u'/objects/a1/test/fomtest',
            NO_CONTENT,
            None,
            None))
        self.assertEquals(self.db.reqs[3], (
            'GET',
            '/objects',
            NO_CONTENT,
            {'query': u'has test/fommanager'},
            None))

    def testDel(self):

        class A(Object):
            fomtest = tag_collection(u'test/fomtest')

        a1 = A()
        a1.uid = 'a1'
        a2 = A()
        a2.uid = 'a2'
        self.db.add_resp(200, 'application/vnd.fluiddb.value+json',
            u'"test/fommanager"')
        a1.fomtest.remove(a2)
        self.assertEquals(self.db.reqs[0], (
            'GET',
            u'/objects/a1/test/fomtest',
            NO_CONTENT,
            None,
            None))
        self.assertEquals(self.db.reqs[1], (
            'DELETE',
            u'/objects/a2/test/fommanager',
            NO_CONTENT,
            None,
            None))
        a2.refresh()
        a1.refresh()
        self.db.add_resp(200, 'application/vnd.fluiddb.value+json',
            u'"test/fommanager"')
        self.db.add_resp(200, 'application/json',
            '{"ids": []}')
        self.assertFalse(a2 in a1.fomtest)
        self.assertEquals(self.db.reqs[2], (
            'GET',
            u'/objects/a1/test/fomtest',
            NO_CONTENT,
            None,
            None))
        self.assertEquals(self.db.reqs[3], (
            'GET',
            '/objects',
            NO_CONTENT,
            {'query': u'has test/fommanager'},
            None))

    def testForeign(self):

        class A(Object):
            fomtest = tag_collection(u'test/fomtest')

        class B(Object):
            fomtestrev = tag_collection(u'test/fomtestrev',
                            map_type=A, foreign_tagpath=u'test/fomtest')

        a = A()
        a.uid = 'a'
        b = B()
        b.uid = 'b'
        self.db.add_resp(200, 'application/vnd.fluiddb.value+json',
            u'"test/fommanager"')
        self.db.add_resp(200, 'application/vnd.fluiddb.value+json',
            u'"test/fommanager"')
        self.db.add_resp(200, 'application/vnd.fluiddb.value+json',
            u'"test/fommanager"')
        self.db.add_resp(200, 'application/vnd.fluiddb.value+json',
            u'"test/fommanager"')
        b.fomtestrev.add(a)
        self.assertEquals(self.db.reqs[0], (
            'GET',
            u'/objects/b/test/fomtestrev',
            NO_CONTENT,
            None,
            None))
        self.assertEquals(self.db.reqs[1], (
            'PUT',
            u'/objects/a/test/fommanager',
            'b',
            None,
            None))
        self.assertEquals(self.db.reqs[2], (
            'GET',
            u'/objects/a/test/fomtest',
            NO_CONTENT,
            None,
            None))
        self.assertEquals(self.db.reqs[3], (
            'PUT',
            u'/objects/b/test/fommanager',
            'a',
            None,
            None))
        a.refresh()
        b.refresh()
        self.db.add_resp(200, 'application/vnd.fluiddb.value+json',
            u'"test/fommanager"')
        self.db.add_resp(200, 'application/json',
            '{"ids": ["b"]}')
        self.assertTrue(b in a.fomtest)
        self.assertEquals(self.db.reqs[4], (
            'GET',
            u'/objects/a/test/fomtest',
            NO_CONTENT,
            None,
            None))
        self.assertEquals(self.db.reqs[5], (
            'GET',
            '/objects',
            NO_CONTENT,
            {'query': u'has test/fommanager'},
            None))
        self.db.add_resp(200, 'application/vnd.fluiddb.value+json',
            u'"test/fommanager"')
        self.db.add_resp(200, 'application/json',
            '{"ids": ["a"]}')
        self.assertTrue(a in b.fomtestrev)
        self.assertEquals(self.db.reqs[6], (
            'GET',
            u'/objects/b/test/fomtestrev',
            NO_CONTENT,
            None,
            None))
        self.assertEquals(self.db.reqs[7], (
            'GET',
            '/objects',
            NO_CONTENT,
            {'query': u'has test/fommanager'},
            None))

    def testForeignDelete(self):

        class A(Object):
            fomtest = tag_collection(u'test/fomtest')

        class B(Object):
            fomtestrev = tag_collection(u'test/fomtestrev',
                            map_type=A, foreign_tagpath=u'test/fomtest')

        a = A()
        a.uid = 'a'
        b = B()
        b.uid = 'b'
        self.db.add_resp(200, 'application/vnd.fluiddb.value+json',
            u'"test/fommanager"')
        self.db.add_resp(200, 'application/vnd.fluiddb.value+json',
            u'"test/fommanager"')
        self.db.add_resp(200, 'application/vnd.fluiddb.value+json',
            u'"test/fommanager"')
        self.db.add_resp(200, 'application/vnd.fluiddb.value+json',
            u'"test/fommanager"')
        b.fomtestrev.remove(a)
        self.assertEquals(self.db.reqs[0], (
            'GET',
            u'/objects/b/test/fomtestrev',
            NO_CONTENT,
            None,
            None))
        self.assertEquals(self.db.reqs[1], (
            'DELETE',
            u'/objects/a/test/fommanager',
            NO_CONTENT,
            None,
            None))
        self.assertEquals(self.db.reqs[2], (
            'GET',
            u'/objects/a/test/fomtest',
            NO_CONTENT,
            None,
            None))
        self.assertEquals(self.db.reqs[3], (
            'DELETE',
            u'/objects/b/test/fommanager',
            NO_CONTENT,
            None,
            None))
        a.refresh()
        b.refresh()
        self.db.add_resp(200, 'application/vnd.fluiddb.value+json',
            u'"test/fommanager"')
        self.db.add_resp(200, 'application/json',
            '{"ids": []}')
        self.assertFalse(b in a.fomtest)
        self.assertEquals(self.db.reqs[4], (
            'GET',
            u'/objects/a/test/fomtest',
            NO_CONTENT,
            None,
            None))
        self.assertEquals(self.db.reqs[5], (
            'GET',
            '/objects',
            NO_CONTENT,
            {'query': u'has test/fommanager'},
            None))
        self.db.add_resp(200, 'application/vnd.fluiddb.value+json',
            u'"test/fommanager"')
        self.db.add_resp(200, 'application/json',
            '{"ids": []}')
        self.assertFalse(a in b.fomtestrev)
        self.assertEquals(self.db.reqs[6], (
            'GET',
            u'/objects/b/test/fomtestrev',
            NO_CONTENT,
            None,
            None))
        self.assertEquals(self.db.reqs[7], (
            'GET',
            '/objects',
            NO_CONTENT,
            {'query': u'has test/fommanager'},
            None))


class TagRelationsTest(_MappingTestCase):
    """Ensures that the tag_relations class behaves correctly
    """

    def testSetRelations(self):

        class A(Object):
            fomtest = tag_value(u'test/fomtest', lazy_save=False)

        class B(Object):
            fomtest2 = tag_relations(u'test/fomtest2', lazy_save=False)

        a1 = A()
        a1.uid = 'a1'
        a2 = A()
        a2.uid = 'a2'
        a3 = A()
        a3.uid = 'a3'
        b = B()
        b.uid = 'b'
        b.fomtest2 = [a1, a2, a3]
        self.assertEqual(self.db.reqs[0], (
            'PUT',
            u'/objects/b/test/fomtest2',
            ['a1', 'a2', 'a3'],
            None,
            None))
        b.refresh()
        self.db.add_resp(200, 'application/vnd.fluiddb.value+json',
            '["a1", "a2", "a3"]')
        self.assertEqual(b.fomtest2, [a1, a2, a3])
        self.assertEqual(self.db.reqs[1], (
            'GET',
            u'/objects/b/test/fomtest2',
            NO_CONTENT,
            None,
            None))


if __name__ == '__main__':
    unittest.main()
