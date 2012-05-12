
from unittest import TestCase

from fom.db import FluidDB
from fom.utils import fom_request_sent, fom_response_received, _DummyNamespace

class SignalsTests(TestCase):

    def test_signals(self):
        """Test the logging signals
        """
        called = []
        @fom_request_sent.connect
        def on_req(db, request, called=called):
            called.append(request)
        @fom_response_received.connect
        def on_resp(db, response, called=called):
            called.append(response)
        db = FluidDB('http://sandbox.fluidinfo.com')
        r = db('GET', ['users', 'aliafshar'])
        self.assertEqual(len(called), 2)

    def test_dummy_signals_cant_connect(self):
        """Test that dummy signals dont work for connection
        """
        ns = _DummyNamespace()
        s = ns.signal('test')
        self.assertRaises(RuntimeError, s.connect)

    def test_dummy_signals_send_noop(self):
        """Test that dummy signals can be sent
        """
        ns = _DummyNamespace()
        s = ns.signal('test')
        s.send()
        s.send(1)



