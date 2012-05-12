# -*- coding: utf-8 -*-
"""
    test_base
    ~~~~~~~~~

    A way of faking out FluidDB in fom, for testing.

    :copyright: (c) 2010 by AUTHOR.
    :license: MIT, see LICENSE_FILE for more details.
"""

from collections import deque


from fom.db import FluidDB, _generate_endpoint_url, NO_CONTENT, FluidResponse


class FakeHttpLibResponse(dict):

    def __init__(self, status, content_type, content=None):
        # yeah, I know, blame httplib2 for this API
        self.status_code = status
        self.headers = {}
        self.headers['content-type'] = content_type
        self.text = content


class FakeHttpLibRequest(object):

    def __init__(self, response):
        self.response = response

    def __call__(self, *args):
        self.args = args
        return self.response


class FakeFluidDB(FluidDB):

    def __init__(self):
        FluidDB.__init__(self, 'http://testing')
        self.reqs = []
        self.resps = deque()
        self.default_response = FakeHttpLibResponse(200, 'text/plain', 'empty')

    def add_resp(self, status, content_type, content):
        hresp = FakeHttpLibResponse(status, content_type, content)
        self.resps.append(hresp)

    def __call__(self, method, path, payload=NO_CONTENT, urlargs=None,
                       content_type=None, is_value=False):
        path = _generate_endpoint_url('', path, '')
        req = (method, path, payload, urlargs, content_type)
        self.reqs.append(req)
        try:
            resp = self.resps.popleft()
        except IndexError:
            resp = self.default_response
        return FluidResponse(resp, resp.text, is_value)
