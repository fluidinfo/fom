
"""
    fom.db
    ~~~~~~

    Raw connection and querying.

    :copyright: 2009-2010 Fom Authors.
    :license: MIT, see LICENSE for more information.

    .. attribute:: BASE_URL

        The default FluidDB URL

    .. attribute:: SERIALIZABLE_TYPES

        A set of serializable content types

    .. attribute:: ITERABLE_TYPES

        A set of iterable types of primitive

    .. attribute:: PRIMITIVE_CONTENT_TYPE

        The primitive FluidDB content type

    .. attribute:: DESERIALIZABLE_CONTENT_TYPES

        Content types which can be deserialized
"""

import types
import urllib

import requests

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        # For Google AppEngine
        from django.utils import simplejson as json

from errors import raise_error
from utils import fom_request_sent, fom_response_received
from version import version


BASE_URL = 'https://fluiddb.fluidinfo.com'
NO_CONTENT = object()
PRIMITIVE_CONTENT_TYPE = 'application/vnd.fluiddb.value+json'
DESERIALIZABLE_CONTENT_TYPES = set(
    (PRIMITIVE_CONTENT_TYPE, 'application/json'))
ITERABLE_TYPES = set((list, tuple))
SERIALIZABLE_TYPES = set((types.NoneType, bool, int, float, str, unicode,
                          list, tuple))


def _generate_endpoint_url(base, path, urlargs):
    path_parts = [base]
    for part in path:
        if isinstance(part, unicode):
            part = part.encode('utf-8')
        path_parts.append(urllib.quote(part, safe=''))
    url = '/'.join(path_parts)
    if urlargs:
        if isinstance(urlargs, dict):
            # convert the dict to tuple pairs
            urlargs = tuple(urlargs.items())
        # make sure we handle unicode characters as possible values
        # NOTE: only use UTF-8 unicode for urlargs values. Anything else will
        # break.
        clean_urlargs = []
        for (tag, value) in urlargs:
            if isinstance(value, unicode):
                clean_urlargs.append((tag, value.encode('utf-8')))
            else:
                clean_urlargs.append((tag, value))
        urlargs = tuple(clean_urlargs)
        url = '?'.join([url, urllib.urlencode(urlargs)])
    return url


def _get_body_and_type(payload, content_type):
    if content_type:
        if content_type == 'application/json':
            return json.dumps(payload), content_type
        return payload, content_type
    if payload is NO_CONTENT:
        return None, None
    if isinstance(payload, dict):
        return json.dumps(payload), 'application/json'
    pt = type(payload)
    if pt in SERIALIZABLE_TYPES:
        if pt in ITERABLE_TYPES:
            if not all(isinstance(x, basestring) for x in payload):
                raise ValueError('Non-string in list payload %r.' % (payload,))
        return json.dumps(payload), PRIMITIVE_CONTENT_TYPE
    raise ValueError("Can't handle payload %r of type %s" % (payload, pt))


class FluidResponse(object):
    """A response to a FluidDB request.

    These are generally created by the API, and returned, and there is little
    use to create them manually.

    :param response: A response instance, which is a dict with an
        additional status attribute.
    :param content: The body of the HTTP response.
    :param is_value: A boolean flag to indicate whether the response is from a
        *value* request. Value requests are not deserialized unless they are
        of the primitive content type: `application/vnd.fluiddb.value+json`
        even if they are of a deserializable content type such as
        `application/json`

    .. attribute:: content_type

        The content type of the response.

    .. attribute:: value

        The deserialized value of the response body, if it is appropriate for
        deserialization.

    .. attribute:: content

        The raw content of the response body.

    .. attribute:: request_id

        The request id of the response. This is only available during errors.

    .. attribute:: error

        The error from the response. This is only available during errors.
    """

    def __init__(self, response, content, is_value):
        self.content_type = response.headers['content-type']
        if ((is_value and self.content_type == PRIMITIVE_CONTENT_TYPE) or
            (self.content_type in DESERIALIZABLE_CONTENT_TYPES)):
            try:
                self.value = json.loads(content)
            except ValueError:
                self.value = content
        else:
            self.value = content
        self.status = response.status_code
        self.response = response
        self.content = content
        self.request_id = self.response.headers.get('x-fluiddb-request-id')
        self.error = self.response.headers.get('x-fluiddb-error-class')
        if self.status >= 400:
            raise_error(self)

    def __repr__(self):
        return '<FluidResponse (%s, %r, %r, %r)>' % (self.status,
            self.content_type, self.error, self.value)

    __str__ = __repr__

    # XXX Backwards Compatibility layer
    def __iter__(self):
        print 'Depravacamated use of status, response'
        yield self.status
        yield self.value


class FluidDB(object):
    """HTTP client.

    Could/Should be swapped out for other implementations. Although is
    generally synchronous.

    :param base_url: The base FluidDB url to use. Currently, this can only be
        either the main FluidDB instance, or the sandbox instance.
    """

    def __init__(self, base_url=BASE_URL):
        if base_url.endswith('/'):
            raise ValueError('The domain for FluidDB must *not* end with'\
                             ' "/". Correct example:'\
                             ' https://fluiddb.fluidinfo.com')
        self.base_url = base_url
        self.headers = {
            'User-agent': 'fom/%s' % version,
        }
        self.session = requests.session(headers=self.headers)
        # XXX Backwards compat
        self.client = self

    def __call__(self, method, path, payload=NO_CONTENT, urlargs=None,
                       content_type=None, is_value=False):
        """Make a request and return a response.

        >>> db = FluidDB()
        >>> r = db('GET', '/users/aliafshar')
        >>> print r.value
        {u'name': u'aliafshar', u'id': u'11e00b96-e346-44e7-af7f-e1a3575ff43e'}

        :param method: The HTTP method
        :param path: The path to make the request to
        :param payload: The body of the request
        :param urlargs: URL arguments to be applied to the request
        :param content_type: The content type of the payload
        :param is_value: A boolean flag to indicate whether the response is
            from a *value* request. Value requests are not deserialized unless
            they are of the primitive content type:
            `application/vnd.fluiddb.value+json` even if they are of a
            deserializable content type such as `application/json`
        """
        payload, content_type = _get_body_and_type(payload, content_type)
        urlargs = urlargs or {}
        headers = self._get_headers(content_type)
        url = self._get_url(path, urlargs)
        fom_request_sent.send(self, request=(url, method, payload, headers))
        response = self.session.request(method, url, data=payload,
            headers=headers)
        fom_response_received.send(self, response=(response.status_code,
                                   response.text, None))
        return FluidResponse(response, response.text, is_value)

    def _get_headers(self, content_type):
        headers = self.headers.copy()
        if content_type:
            headers['content-type'] = content_type
        return headers

    def _get_url(self, path, urlargs=None):
        return _generate_endpoint_url(self.base_url, path, urlargs)

    def login(self, username, password):
        """Log in to this instance of FluidDB

        :param username: The username to log in with.
        :param password: The password to log in with.
        """
        userpass = username + ':' + password
        auth = 'Basic ' + userpass.encode('base64').strip()
        self.headers['Authorization'] = auth

    def login_oauth2(self, token):
        """Prepare to make OAuth2 calls to Fluidinfo.

        :param token: The OAuth token to pass in calls to Fluidinfo.
        """
        self.headers['Authorization'] = 'oauth2'
        self.headers['X-FluidDB-Access-Token'] = token

    def logout(self):
        """Log out of this FluidDB instance
        """
        # Use pop here, to avoid catching KeyError if login was never called.
        self.headers.pop('Authorization', None)
        self.headers.pop('X-FluidDB-Access-Token', None)
