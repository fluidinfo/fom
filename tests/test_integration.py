# -*- coding: utf8 -*-
import unittest
from fom.db import FluidDB

TEST_INSTANCE = 'https://sandbox.fluidinfo.com'
TEST_USER = 'test'
TEST_PASSWORD = 'test'


class TestIntegration(unittest.TestCase):
    """
    Checks that requests that are sent to FluidDB are done correctly.

    ONLY use this class for tests that are directly affected by calls to the
    network. All other tests (for application logic) should be confined to the
    TestDB class.
    """

    def testCall(self):
        """Makes the simplest possible request to the sandbox
        """
        db = FluidDB(TEST_INSTANCE)
        r = db('GET', ['users', TEST_USER])
        # expect a 200 response
        self.assertEquals(200, r.status)
        # and we get the expected payload
        self.assertEquals(u'%s' % TEST_USER, r.value['name'])

    def testLogin(self):
        """Makes sure that authentication works correctly for FluidDB
        """
        db = FluidDB(TEST_INSTANCE)
        db.login(TEST_USER, TEST_PASSWORD)
        r = db('GET', ['users', TEST_USER])
        # a correctly authenticated user will result in a 200 response
        self.assertEquals(200, r.status)
