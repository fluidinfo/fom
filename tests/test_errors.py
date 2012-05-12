
import unittest

from fom.api import FluidApi

from fom.errors import (
    Fluid400Error,
    Fluid401Error,
    Fluid404Error,
    Fluid406Error,
    Fluid412Error,
    Fluid413Error,
    Fluid500Error,
)

from _base import FakeFluidDB


class ErrorTest(unittest.TestCase):

    def setUp(self):
        self.db = FakeFluidDB()
        self.api = FluidApi(self.db)

    def test400(self):
        self.db.add_resp(400, 'application/json', 'Not Found')
        self.assertRaises(Fluid400Error,
                          self.api.namespaces['test'].delete)

    def test401(self):
        self.db.add_resp(401, 'text/plain', 'Unauthorized')
        self.assertRaises(Fluid401Error,
                          self.api.namespaces['test'].delete)

    def test404(self):
        self.db.add_resp(404, 'text/plain', 'Not Found')
        self.assertRaises(Fluid404Error,
                          self.api.namespaces['test'].delete)

    def test406(self):
        self.db.add_resp(406, 'text/plain', 'Not Acceptable')
        self.assertRaises(Fluid406Error,
                          self.api.namespaces['test'].delete)

    def test412(self):
        self.db.add_resp(412, 'text/plain', 'Precondition Failed')
        self.assertRaises(Fluid412Error,
                          self.api.namespaces['test'].delete)

    def test413(self):
        self.db.add_resp(413, 'text/plain', 'Request Entity Too Large')
        self.assertRaises(Fluid413Error,
                          self.api.namespaces['test'].delete)

    def test500(self):
        self.db.add_resp(500, 'text/plain', 'Internal Server Error')
        self.assertRaises(Fluid500Error,
                          self.api.namespaces['test'].delete)



if __name__ == '__main__':
    unittest.main()
