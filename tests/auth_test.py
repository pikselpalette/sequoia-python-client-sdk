import unittest
from unittest.mock import Mock, patch

import pytest
from hamcrest import assert_that, is_, equal_to
from oauthlib.oauth2 import TokenExpiredError

from sequoia import error
from sequoia.auth import TokenCache, ClientGrantAuth, AuthFactory, AuthType


class TestClientGrantAuth(unittest.TestCase):
    def setUp(self):
        TokenCache._token_storage = {}

    def test_given_token_is_not_provided_and_it_is_not_in_cache_then_token_is_none(self):
        auth = ClientGrantAuth('user', 'pass', 'http://identity')
        assert_that(auth.token, is_(None))

    def test_given_token_is_provided_then_that_token_is_used_and_added_to_cache(self):
        auth = ClientGrantAuth('user', 'pass', 'http://identity', '1234')
        assert_that(auth.token, is_({'token_type': 'bearer', 'access_token': '1234'}))
        assert_that(TokenCache._token_storage,
                    is_({'user': {'http://identity': {'token_type': 'bearer', 'access_token': '1234'}}}))

    def test_given_token_is_not_provided_and_there_is_a_token_in_cache_then_that_token_is_used(self):
        TokenCache().add_token('user', 'http://identity', {'token_type': 'bearer', 'access_token': '567'})
        auth = ClientGrantAuth('user', 'pass', 'http://identity')
        assert_that(auth.token, is_({'token_type': 'bearer', 'access_token': '567'}))

    @patch('sequoia.auth.HTTPBasicAuth')
    @patch('sequoia.auth.OAuth2SessionTokenManagementWrapper')
    def test_given_token_is_not_provided_and_it_is_not_in_cache_then_token_is_fetched_and_added_to_cache(self,
                                                                                                         mock_session_wrapper,
                                                                                                         mock_basic_auth):
        mock_basic_auth.return_value = 'MyBasicAuth'

        mock_session_wrapper.return_value.token = {'token_type': 'bearer', 'access_token': '789'}
        mock_session_wrapper.fetch_token.return_value = None

        auth = ClientGrantAuth('user', 'pass', 'http://identity')
        auth.init_session()

        assert_that(TokenCache._token_storage,
                    is_({'user': {'http://identity': {'token_type': 'bearer', 'access_token': '789'}}}))

        mock_session_wrapper.return_value.fetch_token.assert_called_once_with(auth='MyBasicAuth', timeout=0,
                                                                              token_url='http://identity')

    @patch('sequoia.auth.HTTPBasicAuth')
    @patch('requests_oauthlib.OAuth2Session.request')
    def test_given_request_return_oauth_token_expired_error_then_except_sequoia_token_expired_error_is_raised(self,
                                                                                                              mock_oauth_request,
                                                                                                              mock_basic_auth):

        mock_basic_auth.return_value = 'MyBasicAuth'

        mock_oauth_request.side_effect = TokenExpiredError('Token expired')

        auth = ClientGrantAuth('user', 'pass', 'http://identity')

        with pytest.raises(error.TokenExpiredError):
            auth.session.request('GET', 'http://mydata')


class TestTokenCache(unittest.TestCase):

    def setUp(self):
        TokenCache._token_storage = {}

    def test_given_a_token_it_is_added_to_cache(self):
        assert_that(TokenCache._token_storage, is_({}))

        TokenCache().add_token('user-1', 'url1', '123')
        TokenCache().add_token('user-1', 'url2', '456')
        TokenCache().add_token('user-2', 'url1', '789')

        assert_that(TokenCache._token_storage,
                    is_({'user-1': {'url1': '123', 'url2': '456'}, 'user-2': {'url1': '789'}}))

        assert_that(TokenCache().get_token('user-1', 'url1'), is_('123'))
        assert_that(TokenCache().get_token('user-1', 'url2'), is_('456'))
        assert_that(TokenCache().get_token('user-1', 'url3'), is_(None))
        assert_that(TokenCache().get_token('user-2', 'url1'), is_('789'))
        assert_that(TokenCache().get_token('user-3', 'url1'), is_(None))

        TokenCache._token_storage = {}


class TestMutualAuth(unittest.TestCase):

    def test_should_raise_value_error_when_client_cert_not_provided(self):
        self.assertRaises(ValueError, AuthFactory.create, auth_type=AuthType.MUTUAL, client_key='/certs/client_key.pem',
                          server_cert='/certs/server_cert.pem')

    def test_should_raise_value_error_when_client_key_not_provided(self):
        self.assertRaises(ValueError, AuthFactory.create, auth_type=AuthType.MUTUAL,
                          client_cert='/certs/client_cert.pem', server_cert='/certs/server_cert.pem')

    def test_should_raise_value_error_when_server_cert_not_provided(self):
        self.assertRaises(ValueError, AuthFactory.create, auth_type=AuthType.MUTUAL,
                          client_cert='/certs/client_cert.pem', client_key='/certs/client_key.pem')

    def test_should_create_auth_with_certificates_on_session(self):
        auth = AuthFactory.create(auth_type=AuthType.MUTUAL, client_cert='/certs/client_cert.pem',
                                  client_key='/certs/client_key.pem', server_cert='/certs/server_cert.pem')
        assert_that(auth.session.cert, equal_to(('/certs/client_cert.pem', '/certs/client_key.pem')))
        assert_that(auth.session.verify, equal_to('/certs/server_cert.pem'))
