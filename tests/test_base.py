# -*- coding: utf-8 -*-
import unittest
from fom.db import (FluidDB, _get_body_and_type, _generate_endpoint_url,
    NO_CONTENT)
from _base import FakeFluidDB


class TestFakeFluidDB(unittest.TestCase):
    """
    Contains tests that ensure that the FakeFluidDB class and related functions
    work in a way that is exactly the same as related functions in db.py
    """

    def testGenerateEndpointUrl(self):
        """
        Ensures that the URL built by the FakeFluidDB class is exactly the
        same (escaped etc...) as that produced by the real FluidDB class
        """
        fake = FakeFluidDB()
        method = 'POST'
        path = ['foo/bar', 'baz', 'qux']
        payload = 'fluiddb'
        urlargs = {'ham': 'eggs'}
        content_type = 'text/plain'
        fake(method, path, payload, urlargs, content_type)
        self.assertEqual('/foo%2Fbar/baz/qux', fake.reqs[0][1])
