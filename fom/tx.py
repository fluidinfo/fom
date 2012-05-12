
from zope.interface import implements


from twisted.internet import reactor, defer, protocol
from twisted.web import client, http_headers, iweb


from fom.db import FluidDB, FluidResponse, NO_CONTENT, _get_body_and_type
from fom import errors


class ResponseConsumer(protocol.Protocol):
    """
    A protocol which knows how Agent likes to give response body data, and
    converts it to how fom likes it
    """

    def __init__(self, response, finished, is_value):
        self.response = response
        self.finished = finished
        self.is_value = is_value
        self.buffer = []

    def dataReceived(self, bytes):
        """
        Called when body data is received back from the http request
        """
        self.buffer.append(bytes)

    def connectionLost(self, reason):
        """
        Always called once data has finished being received or there was a
        problem.
        """
        # XXX Must check the exception type
        try:
            response = FluidResponse(
                self.response,
                ''.join(self.buffer),
                self.is_value,
            )
            self.finished.callback(response)
        except Exception, e:
            self.finished.errback(e)


class StringProducer(object):
    """
    A body producer that pushes a string in one big chunk.
    """
    # XXX This should really stream things, otherwise what's the point!
    implements(iweb.IBodyProducer)

    def __init__(self, body):
        self.body = body
        self.length = len(body)

    def startProducing(self, consumer):
        consumer.write(self.body)
        return defer.succeed(None)

    def pauseProducing(self):
        pass

    def stopProducing(self):
        pass


class TxResponseProxy(dict):
    """
    Proxy twisted response headers in a way that mimics httplib2's headers
    """

    def __init__(self, response):
        self.status_code = response.code
        self.headers = {}
        for k, v in response.headers.getAllRawHeaders():
            self.headers[k.lower()] = v[0]


class TxFluidDB(FluidDB):
    """
    Like fom.db.FluidDB, but twistedified
    """

    def __init__(self, *args, **kw):
        FluidDB.__init__(self, *args, **kw)
        self.agent = client.Agent(reactor)

    def __call__(self, method, path, payload=NO_CONTENT, urlargs=None,
                       content_type=None, is_value=False):
        payload, content_type = _get_body_and_type(payload, content_type)
        urlargs = urlargs or {}
        headers = self._get_headers(content_type)
        url = self._get_url(path, urlargs)

        for k, v in headers.items():
            if isinstance(v, unicode):
                headers[k] = v.encode('utf-8')
            headers[k] = [headers[k]]

        if payload is None:
            body_producer = None
        else:
            body_producer = StringProducer(payload)

        request = self.agent.request(
            method,
            url,
            http_headers.Headers(headers),
            body_producer,
        )

        finished = defer.Deferred()

        def on_response(response):
            responseproxy = TxResponseProxy(response)
            consumer = ResponseConsumer(responseproxy, finished, is_value)
            if response.length:
                response.deliverBody(consumer)
            else:
                consumer.connectionLost(client.ResponseDone())

        request.addCallback(on_response)
        return finished
