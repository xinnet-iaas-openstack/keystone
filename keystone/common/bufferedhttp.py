# Copyright (c) 2010-2011 OpenStack, LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Monkey Patch httplib.HTTPResponse to buffer reads of headers. This can improve
performance when making large numbers of small HTTP requests.  This module
also provides helper functions to make HTTP connections using
BufferedHTTPResponse.

.. warning::

    If you use this, be sure that the libraries you are using do not access
    the socket directly (xmlrpclib, I'm looking at you :/), and instead
    make all calls through httplib.
"""

from urllib import quote
import logging
import time

# pylint: disable=E0611
from eventlet.green.httplib import CONTINUE, HTTPConnection, HTTPMessage, \
    HTTPResponse, HTTPSConnection, _UNKNOWN

DEFAULT_TIMEOUT = 30

logger = logging.getLogger(__name__)  # pylint: disable=C0103


# pylint: disable=R0902
class BufferedHTTPResponse(HTTPResponse):
    """HTTPResponse class that buffers reading of headers"""

    # pylint: disable=C0103
    def __init__(self, sock, debuglevel=0, strict=0,
                 method=None):          # pragma: no cover
        self.sock = sock
        self.fp = sock.makefile('rb')
        self.debuglevel = debuglevel
        self.strict = strict
        self._method = method

        self.msg = None

        # from the Status-Line of the response
        self.version = _UNKNOWN         # HTTP-Version
        self.status = _UNKNOWN          # Status-Code
        self.reason = _UNKNOWN          # Reason-Phrase

        self.chunked = _UNKNOWN         # is "chunked" being used?
        self.chunk_left = _UNKNOWN      # bytes left to read in current chunk
        self.length = _UNKNOWN          # number of bytes left in response
        self.will_close = _UNKNOWN      # conn will close at end of response

    # pylint: disable=E1101,E0203,W0201
    def expect_response(self):
        self.fp = self.sock.makefile('rb', 0)
        version, status, reason = self._read_status()
        if status != CONTINUE:
            self._read_status = lambda: (version, status, reason)
            self.begin()
        else:
            self.status = status
            self.reason = reason.strip()
            self.version = 11
            self.msg = HTTPMessage(self.fp, 0)
            self.msg.fp = None


# pylint: disable=W0232
class BufferedHTTPConnection(HTTPConnection):
    """HTTPConnection class that uses BufferedHTTPResponse"""
    response_class = BufferedHTTPResponse

    # pylint: disable=W0201
    def connect(self):
        self._connected_time = time.time()
        return HTTPConnection.connect(self)

    # pylint: disable=W0201
    def putrequest(self, method, url, skip_host=0, skip_accept_encoding=0):
        self._method = method
        self._path = url
        return HTTPConnection.putrequest(self, method, url, skip_host,
                                         skip_accept_encoding)

    # pylint: disable=E1101
    def getexpect(self):
        response = BufferedHTTPResponse(self.sock, strict=self.strict,
                                       method=self._method)
        response.expect_response()
        return response

    def getresponse(self):
        response = HTTPConnection.getresponse(self)
        logger.debug(("HTTP PERF: %(time).5f seconds to %(method)s "
                        "%(host)s:%(port)s %(path)s)"),
           {'time': time.time() - self._connected_time, 'method': self._method,
            'host': self.host, 'port': self.port, 'path': self._path})
        return response


# pylint: disable=R0913
def http_connect(ipaddr, port, device, partition, method, path,
                 headers=None, query_string=None, ssl=False, key_file=None,
                 cert_file=None, timeout=None):
    """
    Helper function to create an HTTPConnection object. If ssl is set True,
    HTTPSConnection will be used. However, if ssl=False, BufferedHTTPConnection
    will be used, which is buffered for backend Swift services.

    :param ipaddr: IPv4 address to connect to
    :param port: port to connect to
    :param device: device of the node to query
    :param partition: partition on the device
    :param method: HTTP method to request ('GET', 'PUT', 'POST', etc.)
    :param path: request path
    :param headers: dictionary of headers
    :param query_string: request query string
    :param ssl: set True if SSL should be used (default: False)
    :param key_file: Private key file (not needed if cert_file has private key)
    :param cert_file: Certificate file (Keystore)
    :returns: HTTPConnection object
    """
    path = quote('/' + device + '/' + str(partition) + path)
    # pylint: disable=E1121, E1124
    return http_connect_raw(ipaddr, port, device, partition, method, path,
                            headers, query_string, ssl, key_file, cert_file,
                            timeout=timeout)


# pylint: disable=W0201
def http_connect_raw(ipaddr, port, method, path, headers=None,
                     query_string=None, ssl=False, key_file=None,
                     cert_file=None, timeout=None):
    """
    Helper function to create an HTTPConnection object. If ssl is set True,
    HTTPSConnection will be used. However, if ssl=False, BufferedHTTPConnection
    will be used, which is buffered for backend Swift services.

    :param ipaddr: IPv4 address to connect to
    :param port: port to connect to
    :param method: HTTP method to request ('GET', 'PUT', 'POST', etc.)
    :param path: request path
    :param headers: dictionary of headers
    :param query_string: request query string
    :param ssl: set True if SSL should be used (default: False)
    :param key_file: Private key file (not needed if cert_file has private key)
    :param cert_file: Certificate file (Keystore)
    :returns: HTTPConnection object
    """
    if timeout is None:
        timeout = DEFAULT_TIMEOUT
    if ssl:
        conn = HTTPSConnection('%s:%s' % (ipaddr, port), key_file=key_file,
                               cert_file=cert_file, timeout=timeout)
    else:
        conn = BufferedHTTPConnection('%s:%s' % (ipaddr, port),
                                      timeout=timeout)
    if query_string:
        path += '?' + query_string
    conn.path = path
    conn.putrequest(method, path)
    if headers:
        # pylint: disable=E1103
        for header, value in headers.iteritems():
            conn.putheader(header, value)
    # pylint: disable=E1103
    conn.endheaders()
    return conn
