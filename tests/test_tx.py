from fom.api import FluidApi
from fom.tx import TxFluidDB
from fom import errors
from twisted.trial import unittest
from twisted.internet import defer


class TestTxFluidDB(unittest.TestCase):

    def setUp(self):
        self.db = TxFluidDB('http://sandbox.fluidinfo.com')

    @defer.inlineCallbacks
    def testRequest(self):
        resp = yield self.db('GET', ['users', 'test'])
        self.assertEqual(resp.value[u'name'], 'test')

    @defer.inlineCallbacks
    def testApi(self):
        fdb = FluidApi(self.db)
        resp = yield fdb.users['test'].get()
        self.assertEqual(resp.value[u'name'], 'test')

    def testError(self):
        fdb = FluidApi(self.db)
        d = fdb.namespaces['test'].put(description='Oh deary')
        return self.assertFailure(d, errors.Fluid401Error)

    @defer.inlineCallbacks
    def testLogin(self):
        fdb = FluidApi(self.db)
        self.db.login('test', 'test')
        resp = yield fdb.namespaces['test'].put(
            description='Test user namespace')
        self.assertEqual(resp.status, 204)
        self.assertEqual(resp.content, '')
