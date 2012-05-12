
import unittest


from fom.db import NO_CONTENT
from fom.api import (
    FluidApi,
    UsersApi, UserApi,
    NamespacesApi, NamespaceApi,
    TagsApi, TagApi,
    ObjectsApi, ObjectApi,
    AboutObjectsApi, AboutObjectApi,
    PermissionsApi, PoliciesApi,
    ValuesApi,
)

from _base import FakeFluidDB


class _ApiTestCase(unittest.TestCase):

    ApiType = FluidApi

    def setUp(self):
        self.db = FakeFluidDB()
        self.api = self.ApiType(self.db)

    @property
    def last(self):
        return self.db.reqs[0]

class TestUsersApi(_ApiTestCase):

    ApiType = UsersApi

    def testUserApi(self):
        userApi = self.api[u'aliafshar']
        self.assertTrue(isinstance(userApi, UserApi))
        self.assertEquals(userApi.username, u'aliafshar')

    def testGet(self):
        self.api[u'aliafshar'].get()
        self.assertEqual(self.last, (
            'GET', u'/users/aliafshar', NO_CONTENT,
            None, None,
        ))



class TestNamespacesApi(_ApiTestCase):

    ApiType = NamespacesApi

    def testNamespaceApi(self):
        api = self.api[u'test']
        self.assertTrue(isinstance(api, NamespaceApi))
        self.assertEquals(api.namespace_path, u'test')

    def testGet(self):
        self.api[u'test'].get()
        self.assertEqual(self.last, (
            'GET',
            u'/namespaces/test',
            NO_CONTENT,
            {'returnDescription': False,
              'returnNamespaces': False,
              'returnTags': False},
            None
        ))

    def testGetDescription(self):
        self.api[u'test'].get(returnDescription=True)
        self.assertEqual(self.last, (
            'GET',
            u'/namespaces/test',
            NO_CONTENT,
            {'returnDescription': True,
             'returnNamespaces': False,
             'returnTags': False},
            None
        ))

    def testGetTags(self):
        self.api[u'test'].get(returnTags=True)
        self.assertEqual(self.last, (
            'GET',
            u'/namespaces/test',
            NO_CONTENT,
            {'returnDescription': False,
             'returnNamespaces': False,
             'returnTags': True},
            None
        ))

    def testGetNamespaces(self):
        self.api[u'test'].get(returnNamespaces=True)
        self.assertEqual(self.last, (
            'GET',
            u'/namespaces/test',
            NO_CONTENT,
            {'returnDescription': False,
             'returnNamespaces': True,
             'returnTags': False},
            None
        ))

    def testPost(self):
        self.api[u'test'].post(
            name=u'testName', description=u'testDesc')
        self.assertEqual(self.last, (
            'POST',
            u'/namespaces/test',
            {'name': u'testName',
             'description': u'testDesc'},
            None,
            None,
        ))

    def testDelete(self):
        self.api[u'test'].delete()
        self.assertEqual(self.last, (
            'DELETE',
            u'/namespaces/test',
            NO_CONTENT,
            None,
            None,
        ))


class TestTagsApi(_ApiTestCase):

    ApiType = TagsApi

    def testTagApi(self):
        api = self.api[u'test/test']
        self.assertTrue(isinstance(api, TagApi))
        self.assertEquals(api.tag_path, u'test/test')

    def testGet(self):
        self.api[u'test/test'].get()
        self.assertEqual(self.last, (
            'GET',
            u'/tags/test/test',
            NO_CONTENT,
            {u'returnDescription': False},
            None
        ))

    def testPost(self):
        self.api[u'test'].post(u'test', u'testDesc', False)
        self.assertEqual(self.last, (
            'POST',
            u'/tags/test',
            {u'indexed': False,
             u'name': u'test',
             u'description': u'testDesc'},
            None,
            None
        ))

    def testPostIndexed(self):
        self.api[u'test'].post(u'test', u'testDesc', True)
        self.assertEqual(self.last, (
            'POST',
            u'/tags/test',
            {u'indexed': True,
             u'name': u'test',
             u'description': u'testDesc'},
            None,
            None
        ))

    def testPut(self):
        self.api[u'test/test'].put(u'testDesc')
        self.assertEqual(self.last, (
            'PUT', u'/tags/test/test',
            {u'description': u'testDesc'},
            None,
            None
        ))

    def testDelete(self):
        self.api[u'test/test'].delete()
        self.assertEqual(self.last, (
            'DELETE',
            u'/tags/test/test',
            NO_CONTENT,
            None,
            None
        ))


class TestObjectsApi(_ApiTestCase):

    ApiType = ObjectsApi

    def testGet(self):
        self.api.get('fluiddb/about = 1')
        self.assertEqual(self.last, (
            'GET',
            '/objects',
            NO_CONTENT,
            {'query': 'fluiddb/about = 1'},
            None
        ))

    def testPost(self):
        self.api.post()
        self.assertEqual(self.last, (
            'POST',
            '/objects',
            {},
            None,
            None
        ))

    def testPostAbout(self):
        self.api.post(about=u'testAbout')
        self.assertEqual(self.last, (
            'POST',
            '/objects',
            {u'about': u'testAbout'},
            None,
            None
        ))


class TestAboutObjectsApi(_ApiTestCase):

    ApiType = AboutObjectsApi

    def testPost(self):
        self.api.post(about=u'testAbout')
        self.assertEqual(self.last, (
            'POST',
            u'/about/testAbout',
            NO_CONTENT,
            None,
            None
        ))

    def testGet(self):
        self.api[u'testAbout'].get()
        self.assertEqual(self.last, (
            'GET',
            u'/about/testAbout',
            NO_CONTENT,
            None,
            None
        ))

    def testGetUrlEscape(self):
        self.api[u'test/: About'].get()
        self.assertEqual(self.last, (
            'GET',
            u'/about/test%2F%3A%20About',
            NO_CONTENT,
            None,
            None
        ))

    def testGetTagValue(self):
        self.api[u'testAbout']['foo/blah'].get()
        self.assertEqual(self.last, (
            'GET',
            u'/about/testAbout/foo/blah',
            NO_CONTENT,
            None,
            None
        ))

    def testGetTagValueUrlEscape(self):
        self.api[u'test/: About']['foo/blah'].get()
        self.assertEqual(self.last, (
            'GET',
            u'/about/test%2F%3A%20About/foo/blah',
            NO_CONTENT,
            None,
            None
        ))


class TestPermissionApi(_ApiTestCase):

    ApiType = PermissionsApi

    def testGetNamespace(self):
        self.api.namespaces[u'test'].get(u'list')
        self.assertEqual(self.last, (
            'GET',
            u'/permissions/namespaces/test',
            NO_CONTENT,
            {u'action': u'list'},
            None
        ))

    def testPutNamespace(self):
        self.api.namespaces[u'test'].put(u'list', u'open', [])
        self.assertEqual(self.last, (
            'PUT',
            u'/permissions/namespaces/test',
            {u'policy': u'open', u'exceptions': []},
            {u'action': u'list'},
            None
        ))

    def testGetTag(self):
        self.api.tags[u'test/test'].get(u'update')
        self.assertEqual(self.last, (
            'GET',
            u'/permissions/tags/test/test',
            NO_CONTENT,
            {u'action': u'update'},
            None,
        ))

    def testPutTag(self):
        self.api.tags[u'test/test'].put(u'update', u'open', [])
        self.assertEqual(self.last, (
            'PUT',
            u'/permissions/tags/test/test',
            {u'policy': u'open',
             u'exceptions': []},
            {u'action': u'update'},
            None
        ))

    def testGetTagValue(self):
        self.api.tag_values[u'test/test'].get(u'update')
        self.assertEqual(self.last, (
            'GET',
            u'/permissions/tag-values/test/test',
            NO_CONTENT,
            {u'action': u'update'},
            None
        ))

    def testPutTagValue(self):
        self.api.tag_values[u'test'].put(u'update', u'open', [])
        self.assertEqual(self.last, (
            'PUT',
            u'/permissions/tag-values/test',
            {u'policy': u'open',
             u'exceptions': []},
            {u'action': u'update'},
            None
        ))


class TestPoliciesApi(_ApiTestCase):

    ApiType = PoliciesApi

    def testGet(self):
        self.api['test', 'namespaces', 'list'].get()
        self.assertEqual(self.last, (
            'GET',
            '/policies/test/namespaces/list',
            NO_CONTENT,
            None,
            None
        ))

    def testPut(self):
        self.api['test', 'namespaces', 'list'].put(u'open', [])
        self.assertEqual(self.last, (
            'PUT',
            '/policies/test/namespaces/list',
            {u'policy': u'open', u'exceptions': []},
            None,
            None
        ))


class TestValuesApi(_ApiTestCase):

    ApiType = ValuesApi

    def testGet(self):
        self.api.get('fluiddb/users/username = "test"',
                     ['fluiddb/about', 'fluiddb/users/name'])
        self.assertEqual(self.last, (
            'GET',
            '/values',
            NO_CONTENT,
            (('query', 'fluiddb/users/username = "test"'),
             ('tag', 'fluiddb/about'),
             ('tag', 'fluiddb/users/name')), None
        ))

    def testPut(self):
        self.api.put('fluiddb/users/username = "test"',
                     {'test/test1': {'value': 6},
                      'test/test2': {'value': 'Hello'}})
        self.assertEqual(self.last, (
            'PUT',
            '/values',
            {'queries': [[ 'fluiddb/users/username = "test"',
                {'test/test1': {'value': 6},
                'test/test2': {'value': 'Hello'}}]]},
            None,
            None
        ))

    def testDelete(self):
        self.api.delete('fluiddb/users/username = "test"',
                     ['fluiddb/about', 'fluiddb/users/name'])
        self.assertEqual(self.last, (
            'DELETE',
            '/values',
            NO_CONTENT,
            (('query', 'fluiddb/users/username = "test"'),
             ('tag', 'fluiddb/about'),
             ('tag', 'fluiddb/users/name')),
            None
        ))
