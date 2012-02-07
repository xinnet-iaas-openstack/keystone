import unittest2 as unittest
import uuid

import keystone.common.exception
import keystone.backends.api as db_api
from keystone.test.functional import common
from keystone.test import client as client_tests

#
#   Auth Token
#
from keystone.middleware import auth_token


class TestAuthTokenMiddleware(common.MiddlewareTestCase):
    """
    Tests for Keystone WSGI middleware: Auth Token
    """

    def setUp(self):
        super(TestAuthTokenMiddleware, self).setUp(auth_token)


class TestAuthTokenMiddlewareWithNoAdminToken(common.MiddlewareTestCase):
    """
    Tests for Keystone WSGI middleware: Auth Token
    """

    def setUp(self):
        settings = {'delay_auth_decision': '0',
            'auth_host': client_tests.TEST_TARGET_SERVER_ADMIN_ADDRESS,
            'auth_port': client_tests.TEST_TARGET_SERVER_ADMIN_PORT,
            'auth_protocol':
                client_tests.TEST_TARGET_SERVER_ADMIN_PROTOCOL,
            'auth_uri': ('%s://%s:%s/' % \
                         (client_tests.TEST_TARGET_SERVER_SERVICE_PROTOCOL,
                          client_tests.TEST_TARGET_SERVER_SERVICE_ADDRESS,
                          client_tests.TEST_TARGET_SERVER_SERVICE_PORT)),
            'admin_user': self.admin_username,
            'admin_password': self.admin_password}
        super(TestAuthTokenMiddlewareWithNoAdminToken, self).setUp(auth_token,
              settings)

#
#   Glance
#
try:
    from keystone.middleware import glance_auth_token
except ImportError as e:
    print 'Could not load glance_auth_token: %s' % e


@unittest.skipUnless('glance_auth_token' in vars(),
                     "Glance Auth Token not imported")
class TestGlanceMiddleware(common.MiddlewareTestCase):
    """
    Tests for Keystone WSGI middleware: Glance
    """

    def setUp(self):
        super(TestGlanceMiddleware, self).setUp(
                                (auth_token, glance_auth_token))


#
#   Quantum
#
from keystone.middleware import quantum_auth_token


class TestQuantumMiddleware(common.MiddlewareTestCase):
    """
    Tests for Keystone WSGI middleware: Glance
    """

    def setUp(self):
        access = self.authenticate(self.admin_username, self.admin_password).\
            json['access']
        self.admin_token = access['token']['id']
        settings = {'delay_auth_decision': '0',
                'auth_host': client_tests.TEST_TARGET_SERVER_ADMIN_ADDRESS,
                'auth_port': client_tests.TEST_TARGET_SERVER_ADMIN_PORT,
                'auth_protocol':
                    client_tests.TEST_TARGET_SERVER_ADMIN_PROTOCOL,
                'auth_uri': ('%s://%s:%s/' % \
                             (client_tests.TEST_TARGET_SERVER_SERVICE_PROTOCOL,
                              client_tests.TEST_TARGET_SERVER_SERVICE_ADDRESS,
                              client_tests.TEST_TARGET_SERVER_SERVICE_PORT)),
                'auth_version': '2.0',
                'admin_token': self.admin_token,
                'admin_user': self.admin_username,
                'admin_password': self.admin_password}
        super(TestQuantumMiddleware, self).setUp(quantum_auth_token, settings)


#
#   Swift
#
try:
    from keystone.middleware import swift_auth
except ImportError as e:
    print 'Could not load swift_auth: %s' % e

#TODO(Ziad): find out how to disable swift logging
#@unittest.skipUnless('swift_auth' in vars(),
#                     "swift_auth not imported")
#class TestSwiftMiddleware(common.MiddlewareTestCase):
#    """
#    Tests for Keystone WSGI middleware: Glance
#    """
#
#    def setUp(self):
#        settings = {'delay_auth_decision': '0',
#                'auth_host': '127.0.0.1',
#                'auth_port': '35357',
#                'auth_protocol': 'http',
#                'auth_uri': 'http://localhost:35357/',
#                'admin_token': self.admin_token,
#                'set log_facility': 'LOG_NULL'}
#        super(TestSwiftMiddleware, self).setUp(swift_auth, settings)


if __name__ == '__main__':
    unittest.main()
