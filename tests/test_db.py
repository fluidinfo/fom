# -*- coding: utf-8 -*-
import unittest
import uuid
from fom.db import (FluidDB, _get_body_and_type, _generate_endpoint_url,
    NO_CONTENT)

TEST_INSTANCE = 'https://sandbox.fluidinfo.com'
TEST_USER = 'test'
TEST_PASSWORD = 'test'


def random_username():
    return str(uuid.uuid4()).replace('-', '')


class TestDBModule(unittest.TestCase):
    """
    Contains tests that check the logic of each function in the db layer. Any
    tests that require network based calls should be made in the
    TestIntegration class above.
    """

    def testGetBodyAndType(self):
        """
        Make sure FOM is sending the right sort of thing down the wire to
        FluidDB
        """
        # good
        # with mime-type
        content, content_type = _get_body_and_type('foo', 'text/plain')
        self.assertEquals('foo', content)
        self.assertEquals('text/plain', content_type)
        # dict -> json
        content, content_type = _get_body_and_type({'foo': 'bar'}, None)
        # returns a string representation of json
        self.assertTrue(isinstance(content, basestring))
        self.assertEquals('application/json', content_type)
        # primitive types
        values = [1, 1.2, 'string', u'string', ['foo', 'bar'],
                  (u'foo', u'bar'), True, False, None]
        for val in values:
            content, content_type = _get_body_and_type(val, None)
            # returns a string representation (of json)
            self.assertTrue(isinstance(content, basestring))
            self.assertEqual('application/vnd.fluiddb.value+json',
                             content_type)
        # json
        body = [{'foo': 'bar'}, 1, "two"]
        content, content_type = _get_body_and_type(body, 'application/json')
        self.assertTrue(isinstance(content, basestring))
        self.assertEquals('application/json', content_type)
        # bad
        # can't handle the type without a mime
        self.assertRaises(ValueError, _get_body_and_type, FluidDB(), None)
        # list or tuple contains something other than a string
        self.assertRaises(ValueError, _get_body_and_type, [1, 2, 3], None)
        # test NO_CONTENT as argument
        expected = None, None
        actual = _get_body_and_type(NO_CONTENT, None)
        self.assertEquals(expected, actual)

    def testDefault(self):
        """Ensure that init sets the instance's URL correctly
        """
        db = FluidDB('http://sandbox.fluidinfo.com')
        self.assertEquals(db.base_url, 'http://sandbox.fluidinfo.com')

    def testGeneratedEndpointUrlQuoted(self):
        """
        Ensures that a path is properly "quoted" so, for example, a space
        maps to %20
        """
        base = 'http://foo.com'
        path = ['users', 'a name']
        urlargs = None
        expected = 'http://foo.com/users/a%20name'
        actual = _generate_endpoint_url(base, path, urlargs)
        self.assertEquals(expected, actual)

    def testGeneratedEndpointUrlQuotedSlash(self):
        """
        Ensures that a path is properly "quoted" for a slash
        """
        base = 'http://foo.com'
        path = ['us/ers', 'a/name']
        urlargs = None
        expected = 'http://foo.com/us%2Fers/a%2Fname'
        actual = _generate_endpoint_url(base, path, urlargs)
        self.assertEquals(expected, actual)

    def testTrailingSlashHandling(self):
        """
        Make sure we get a complaint if the base URL for the instance
        of fluiddb ends with a slash.

        BAD: http://fluiddb.fluidinfo.com/
        GOOD: http://fluiddb.fluidinfo.com

        Why not knock off the trailing slash..? Well, it's easy to complain
        but hard to second guess the caller's intention
        """
        # Bad
        self.assertRaises(ValueError, FluidDB,
                          'http://sandbox.fluidinfo.com/')
        # Good
        self.assertTrue(FluidDB('http://sandbox.fluidinfo.com'))

    def testGenerateEndpointUrl(self):
        """
        Make sure that the endpoint URL is generated correctly with various
        types of url arguments
        """
        base = 'http://foo.com'
        # path contains unicode
        path = [u'users', u'\u03bb\u03bb']
        urlargs = None
        expected = 'http://foo.com/users/%CE%BB%CE%BB'
        actual = _generate_endpoint_url(base, path, urlargs)
        self.assertEquals(expected, actual)
        # urlargs contain unicode
        path = [u'objects']
        urlargs = {u'query': u'fluidinfo/about="\u03bb\u03bb"'}
        expected = 'http://foo.com/objects?query=fluidinfo%2Fabout%3D%22%CE%BB%CE%BB%22'
        actual = _generate_endpoint_url(base, path, urlargs)
        self.assertEquals(expected, actual)
        # path contains already encoded unicode
        path = [u'users', u'\u03bb\u03bb'.encode('utf-8')]
        urlargs = None
        expected = 'http://foo.com/users/%CE%BB%CE%BB'
        actual = _generate_endpoint_url(base, path, urlargs)
        self.assertEquals(expected, actual)
        # urlargs contain already encoded unicode
        path = [u'objects']
        urlargs = {u'query': u'fluidinfo/about="\u03bb\u03bb"'.encode('utf-8')}
        expected = 'http://foo.com/objects?query=fluidinfo%2Fabout%3D%22%CE%BB%CE%BB%22'
        actual = _generate_endpoint_url(base, path, urlargs)
        self.assertEquals(expected, actual)
        # base and path no urlargs
        expected = "http://foo.com/bar/baz"
        actual = _generate_endpoint_url("http://foo.com", ["bar", "baz"], None)
        self.assertEqual(expected, actual)
        # base and path with unicode
        expected = "http://foo.com/b%CE%B1r"
        actual = _generate_endpoint_url("http://foo.com", [u"bαr"], None)
        self.assertEqual(expected, actual)
        # make sure everything is properly URL encoded
        expected = "http://foo.com/b%CE%B1r%20baz"
        actual = _generate_endpoint_url("http://foo.com", [u"bαr baz"], None)
        self.assertEqual(expected, actual)
        # add urlargs as a dict
        args = {'foo': '1', 'bar': '2'}
        expected = "http://foo.com/path?foo=1&bar=2"
        actual = _generate_endpoint_url("http://foo.com", ["path"], args)
        self.assertEqual(expected, actual)
        # add urlargs as tuple pairs
        args = (('foo', '1'), ('bar', '2'))
        expected = "http://foo.com/path?foo=1&bar=2"
        actual = _generate_endpoint_url("http://foo.com", ["path"], args)
        self.assertEqual(expected, actual)
        # make sure unicode in urlargs is handled
        args = (('foo', '1'), ('bar', u'α'))
        expected = "http://foo.com/path?foo=1&bar=%CE%B1"
        actual = _generate_endpoint_url("http://foo.com", ["path"], args)
        self.assertEqual(expected, actual)
        # add urlargs as tuple pairs with duplicates
        args = (('foo', '1'), ('bar', '2'), ('bar', '3'))
        expected = "http://foo.com/path?foo=1&bar=2&bar=3"
        actual = _generate_endpoint_url("http://foo.com", ["path"], args)
        self.assertEqual(expected, actual)

    def testLoginLogout(self):
        """
        Make sure login and logout functions set things up correctly
        """
        db = FluidDB(TEST_INSTANCE)
        # start from a blank slate
        self.assertFalse('Authorization' in db.headers)
        # Login
        db.login(TEST_USER, TEST_PASSWORD)
        userpass = TEST_USER + ':' + TEST_PASSWORD
        auth = 'Basic ' + userpass.encode('base64').strip()
        self.assertEquals(db.headers['Authorization'], auth)
        # Logout
        db.logout()
        self.assertFalse('Authorization' in db.headers)

    def testLoginLogoutOAuth2(self):
        """
        Make sure login and logout functions set things up correctly
        when we use OAuth2.
        """
        token = 'kajfjowijmssafuwoisflsjlfsoieuossfh'
        db = FluidDB(TEST_INSTANCE)
        # start from a blank slate
        self.assertFalse('Authorization' in db.headers)
        self.assertFalse('X-FluidDB-Access-Token' in db.headers)
        # Login
        db.login_oauth2(token)
        self.assertEquals(db.headers['Authorization'], 'oauth2')
        self.assertEquals(db.headers['X-FluidDB-Access-Token'], token)
        # Logout
        db.logout()
        self.assertFalse('Authorization' in db.headers)
        self.assertFalse('X-FluidDB-Access-Token' in db.headers)


if __name__ == '__main__':
    unittest.main()
