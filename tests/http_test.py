import unittest
from unittest import mock
from unittest.mock import patch, Mock, call

import pytest
import requests
import requests_mock
from hamcrest import assert_that, instance_of, is_in, none, equal_to, is_
from jsonpickle import json

from sequoia import auth, http, error


class HttpExecutorTest(unittest.TestCase):
    def setUp(self):
        self.session_mock = requests.Session()
        self.adapter = requests_mock.Adapter()
        self.session_mock.mount('mock', self.adapter)

    @patch('requests.Session')
    def test_request_given_a_list_of_parameters_then_they_are_added_to_the_request(self, session_mock):
        # There is an issue where parameters won't be added to the request if the prefix does not start
        # with http https://bugs.launchpad.net/requests-mock/+bug/1518497. So request-mock can't be used here
        # to check parameters
        session_mock.request.return_value.url = 'mock://some_url'
        session_mock.request.return_value.status_code = 200
        session_mock.request.return_value.is_redirect = False

        http_executor = http.HttpExecutor(auth.AuthFactory.create(grant_client_id="client_id",
                                                                  grant_client_secret="client_secret"),
                                          session=session_mock, correlation_id="my_correlation_id",
                                          content_type="application/json")

        http_executor.request("POST", "mock://some_url",
                              data='some data',
                              headers={'New-Header': 'SomeValue'},
                              params={'key1': 'value1'})

        expected_headers = {
            'User-Agent': http_executor.user_agent,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Correlation-ID": "my_correlation_id",
            "New-Header": 'SomeValue'
        }

        session_mock.request.assert_called_with('POST', 'mock://some_url', allow_redirects=False, data='some data',
                                                headers=expected_headers, params={'key1': 'value1'}, timeout=240)

    @staticmethod
    def match_request_text(request):
        return 'some data' in (request.text or '')

    def test_request_given_additional_headers_and_data_then_they_are_added_to_the_request(self):
        self.adapter.register_uri('POST', 'mock://some_url', text='{"key_1": "value_1"}',
                                  request_headers={'New-Header': 'SomeValue'},
                                  additional_matcher=HttpExecutorTest.match_request_text)

        http_executor = http.HttpExecutor(auth.AuthFactory.create(grant_client_id="client_id",
                                                                  grant_client_secret="client_secret"),
                                          session=self.session_mock)
        response = http_executor.request("POST", "mock://some_url",
                                         headers={'New-Header': 'SomeValue'},
                                         data='some data')

        assert_that(response.data, equal_to({"key_1": "value_1"}))

    def test_request_given_get_method_and_an_unreachable_url_then_a_connectivity_error_should_be_raised(self):
        self.adapter.register_uri('GET', 'mock://some_url',
                                  exc=requests.exceptions.ConnectionError('some error desc'))

        http_executor = http.HttpExecutor(auth.AuthFactory.create(grant_client_id="client_id",
                                                                  grant_client_secret="client_secret"),
                                          session=self.session_mock)

        with pytest.raises(error.ConnectionError) as sequoia_error:
            http_executor.request("GET", "mock://some_url")

        assert_that('some error desc', is_in(sequoia_error.value.args))
        assert_that(sequoia_error.value.cause, instance_of(requests.exceptions.ConnectionError))

    def test_request_given_server_returns_too_many_redirects_then_error_should_be_raised(self):
        self.adapter.register_uri('GET', 'mock://some_url',
                                  exc=requests.exceptions.TooManyRedirects('some error desc'))

        http_executor = http.HttpExecutor(auth.AuthFactory.create(grant_client_id="client_id",
                                                                  grant_client_secret="client_secret"),
                                          session=self.session_mock)

        with pytest.raises(error.TooManyRedirects) as sequoia_error:
            http_executor.request("GET", "mock://some_url")

        assert_that('some error desc', is_in(sequoia_error.value.args))
        assert_that(sequoia_error.value.cause, instance_of(requests.exceptions.TooManyRedirects))

    def test_request_given_get_method_and_server_throw_connection_timeout_then_a_connection_error_should_be_raised(
        self):
        self.adapter.register_uri('GET', 'mock://some_url',
                                  exc=requests.exceptions.ConnectTimeout('some error desc'))

        http_executor = http.HttpExecutor(auth.AuthFactory.create(grant_client_id="client_id",
                                                                  grant_client_secret="client_secret"),
                                          session=self.session_mock)

        with pytest.raises(error.ConnectionError) as sequoia_error:
            http_executor.request("GET", "mock://some_url")

        assert_that('some error desc', is_in(sequoia_error.value.args))
        assert_that(sequoia_error.value.cause, instance_of(requests.exceptions.ConnectionError))

    def test_request_given_get_method_and_server_throw_timeout_then_a_timeout_error_should_be_raised(self):
        self.adapter.register_uri('GET', 'mock://some_url',
                                  exc=requests.exceptions.Timeout('some error desc'))

        http_executor = http.HttpExecutor(auth.AuthFactory.create(grant_client_id="client_id",
                                                                  grant_client_secret="client_secret"),
                                          session=self.session_mock)

        with pytest.raises(error.Timeout) as sequoia_error:
            http_executor.request("GET", "mock://some_url")

        assert_that('some error desc', is_in(sequoia_error.value.args))
        assert_that(sequoia_error.value.cause, instance_of(requests.exceptions.Timeout))

    def test_request_given_get_method_and_server_returns_an_error_code_then_that_error_should_be_populated(self):
        self.adapter.register_uri('GET', 'mock://test.com', text='some json value', status_code=403)

        http_executor = http.HttpExecutor(auth.AuthFactory.create(grant_client_id="client_id",
                                                                  grant_client_secret="client_secret"),
                                          session=self.session_mock)

        with pytest.raises(error.HttpError) as sequoia_error:
            http_executor.request("GET", "mock://test.com")

        assert_that(sequoia_error.value.status_code, 403)
        assert_that(sequoia_error.value.message, 'some json value')
        assert_that(sequoia_error.value.cause, none())

    def test_request_given_post_method_and_server_returns_an_error_code_then_that_error_should_be_populated(self):
        self.adapter.register_uri('POST', 'mock://test.com', text='{"error": "some json value"}', status_code=403)

        http_executor = http.HttpExecutor(auth.AuthFactory.create(grant_client_id="client_id",
                                                                  grant_client_secret="client_secret"),
                                          session=self.session_mock)

        with pytest.raises(error.HttpError) as sequoia_error:
            http_executor.request("POST", "mock://test.com")

        assert_that(sequoia_error.value.status_code, is_(403))
        assert_that(sequoia_error.value.message, is_({'error': 'some json value'}))
        assert_that(sequoia_error.value.cause, none())

    def test_request_given_server_returns_an_error_then_the_request_should_be_retried(self):
        json_response = '{"resp2": "resp2"}'

        self.adapter.register_uri('GET', 'mock://test.com', [{'text': 'resp1', 'status_code': 500},
                                                             {'text': json_response, 'status_code': 200}])

        http_executor = http.HttpExecutor(auth.AuthFactory.create(grant_client_id="client_id",
                                                                  grant_client_secret="client_secret"),
                                          session=self.session_mock)

        response = http_executor.request("GET", "mock://test.com")

        assert_that(response.data, equal_to(json.loads(json_response)))

    def test_request_given_server_returns_an_error_then_the_request_should_be_retried_10_times_by_default(self):
        json_response = '{"resp2": "resp2"}'

        self.adapter.register_uri('GET', 'mock://test.com', [{'text': 'resp1', 'status_code': 500},
                                                             {'text': 'resp1', 'status_code': 500},
                                                             {'text': 'resp1', 'status_code': 500},
                                                             {'text': 'resp1', 'status_code': 500},
                                                             {'text': 'resp1', 'status_code': 500},
                                                             {'text': 'resp1', 'status_code': 500},
                                                             {'text': 'resp1', 'status_code': 500},
                                                             {'text': 'resp1', 'status_code': 500},
                                                             {'text': 'resp1', 'status_code': 500},
                                                             {'text': 'resp1', 'status_code': 500},
                                                             {'text': json_response, 'status_code': 200}])

        http_executor = http.HttpExecutor(auth.AuthFactory.create(grant_client_id="client_id",
                                                                  grant_client_secret="client_secret"),
                                          session=self.session_mock)
        with pytest.raises(error.HttpError) as sequoia_error:
            http_executor.request("GET", "mock://test.com")

        assert_that(sequoia_error.value.status_code, is_(500))

    def test_request_given_server_returns_an_error_then_the_request_should_be_retried_configured_times_by_default(self):
        json_response = '{"resp2": "resp2"}'

        self.adapter.register_uri('GET', 'mock://test.com', [{'text': 'resp1', 'status_code': 500},
                                                             {'text': 'resp1', 'status_code': 500},
                                                             {'text': 'resp1', 'status_code': 500},
                                                             {'text': 'resp1', 'status_code': 500},
                                                             {'text': 'resp1', 'status_code': 500},
                                                             {'text': 'resp1', 'status_code': 500},
                                                             {'text': 'resp1', 'status_code': 500},
                                                             {'text': 'resp1', 'status_code': 500},
                                                             {'text': 'resp1', 'status_code': 500},
                                                             {'text': 'resp1', 'status_code': 500},
                                                             {'text': json_response, 'status_code': 200}])

        http_executor = http.HttpExecutor(auth.AuthFactory.create(grant_client_id="client_id",
                                                                  grant_client_secret="client_secret"),
                                          session=self.session_mock,
                                          backoff_strategy={'interval': 0, 'max_tries': 11})
        response = http_executor.request("GET", "mock://test.com")

        assert_that(response.data, equal_to(json.loads(json_response)))

    def test_request_given_server_returns_an_error_then_the_request_should_be_retried(self):
        json_response = '{"resp2": "resp2"}'

        mock_response_500 = Mock()
        mock_response_500.is_redirect = False
        mock_response_500.status_code = 500
        mock_response_500.json.return_value = {}
        mock_response_500.return_value.text = json_response

        mock_response_200 = Mock()
        mock_response_200.is_redirect = False
        mock_response_200.status_code = 200
        mock_response_200.return_value.text = json_response
        mock_response_200.json.return_value = {"resp2": "resp2"}

        mock_auth = Mock()
        mock_session = Mock()
        mock_session.request.side_effect = [error.TokenExpiredError('Token Expired'),
                                            mock_response_500,
                                            mock_response_200]

        http_executor = http.HttpExecutor(mock_auth,
                                          session=mock_session,
                                          backoff_strategy={'interval': 0, 'max_tries': 2})
        response = http_executor.request("GET", "mock://test.com")

        assert_that(response.data, equal_to(json.loads(json_response)))

        call_list = [call('GET', 'mock://test.com', allow_redirects=False, data=None, headers={'User-Agent': mock.ANY, 'Content-Type': 'application/vnd.piksel+json', 'Accept': 'application/vnd.piksel+json', 'X-Correlation-ID': None}, params=None, timeout=240),
                     call('GET', 'mock://test.com', allow_redirects=False, data=None, headers={'User-Agent': mock.ANY, 'Content-Type': 'application/vnd.piksel+json', 'Accept': 'application/vnd.piksel+json', 'X-Correlation-ID': None}, params=None, timeout=240),
                     call('GET', 'mock://test.com', allow_redirects=False, data=None, headers={'User-Agent': mock.ANY, 'Content-Type': 'application/vnd.piksel+json', 'Accept': 'application/vnd.piksel+json', 'X-Correlation-ID': None}, params=None, timeout=240)]

        assert_that(mock_session.request.call_count, is_(3))
        mock_session.request.assert_has_calls(call_list)

        assert_that(mock_session.auth.update_token.call_count, is_(1))

    def test_request_given_server_returns_an_token_expired_error_then_the_request_should_be_retried(self):
        """
        Testing the use of an invalid token and how the client-sdk should automatically get a new token.
        There are two type of errors when a new token is automatically retrieved: getting the TokenExpiredError exception
        and getting a valid response from the service with a 401 and using the auth method of providing credentials.

        This unit test checks both types: the exception and the 401 status error.
        """
        json_response = '{"resp2": "resp2"}'

        mock_response_401 = Mock()
        mock_response_401.is_redirect = False
        mock_response_401.status_code = 401
        mock_response_401.json.return_value = {"statusCode":401,"error":"Unauthorized","message":"Invalid token","attributes":{"error":"Invalid token"}}
        mock_response_401.return_value.text = '{"statusCode":401,"error":"Unauthorized","message":"Invalid token","attributes":{"error":"Invalid token"}}'

        mock_response_200 = Mock()
        mock_response_200.is_redirect = False
        mock_response_200.status_code = 200
        mock_response_200.return_value.text = json_response
        mock_response_200.json.return_value = {"resp2": "resp2"}

        mock_auth = Mock()
        mock_session = Mock()
        mock_session.request.side_effect = [error.TokenExpiredError('Token Expired'),
                                            mock_response_401,
                                            mock_response_200]

        http_executor = http.HttpExecutor(mock_auth,
                                          session=mock_session,
                                          backoff_strategy={'interval': 0, 'max_tries': 2})
        response = http_executor.request("GET", "mock://test.com")

        assert_that(response.data, equal_to(json.loads(json_response)))

        call_list = [call('GET', 'mock://test.com', allow_redirects=False, data=None, headers={'User-Agent': mock.ANY, 'Content-Type': 'application/vnd.piksel+json', 'Accept': 'application/vnd.piksel+json', 'X-Correlation-ID': None}, params=None, timeout=240),
                     call('GET', 'mock://test.com', allow_redirects=False, data=None, headers={'User-Agent': mock.ANY, 'Content-Type': 'application/vnd.piksel+json', 'Accept': 'application/vnd.piksel+json', 'X-Correlation-ID': None}, params=None, timeout=240),
                     call('GET', 'mock://test.com', allow_redirects=False, data=None, headers={'User-Agent': mock.ANY, 'Content-Type': 'application/vnd.piksel+json', 'Accept': 'application/vnd.piksel+json', 'X-Correlation-ID': None}, params=None, timeout=240)]

        assert_that(mock_session.request.call_count, is_(3))
        mock_session.request.assert_has_calls(call_list)

        assert_that(mock_session.auth.update_token.call_count, is_(2))

    def test_request_given_server_returns_an_token_expired_error_ever_then_the_request_should_fail(self):
        """
        Testing the max. number of retries when requesting new token and getting 401.
        """
        json_response = '{"resp2": "resp2"}'

        mock_response_401 = Mock()
        mock_response_401.is_redirect = False
        mock_response_401.status_code = 401
        mock_response_401.json.return_value = {"statusCode":401,"error":"Unauthorized","message":"Invalid token","attributes":{"error":"Invalid token"}}
        mock_response_401.return_value.text = '{"statusCode":401,"error":"Unauthorized","message":"Invalid token","attributes":{"error":"Invalid token"}}'

        mock_auth = Mock()
        mock_session = Mock()
        mock_session.request.return_value = mock_response_401

        http_executor = http.HttpExecutor(mock_auth,
                                          session=mock_session,
                                          backoff_strategy={'interval': 0, 'max_tries': 2})

        with pytest.raises(error.HttpError):
            http_executor.request("GET", "mock://test.com")

        single_call = call('GET', 'mock://test.com', allow_redirects=False, data=None,
                          headers={'User-Agent': mock.ANY, 'Content-Type': 'application/vnd.piksel+json',
                                   'Accept': 'application/vnd.piksel+json', 'X-Correlation-ID': None},
                          params=None,
                          timeout=240)

        call_list = [single_call, single_call, single_call, single_call]

        mock_session.request.assert_has_calls(call_list)

    def test_request_given_server_returns_an_authorisation_error_fetching_the_token_then_error_is_not_retried(self):

        mock_auth = Mock()
        mock_session = Mock()
        mock_session.request.side_effect = error.AuthorisationError('Auth error')

        http_executor = http.HttpExecutor(mock_auth,
                                          session=mock_session,
                                          backoff_strategy={'interval': 0, 'max_tries': 3})

        with pytest.raises(error.AuthorisationError):
            http_executor.request("GET", "mock://test.com")

        mock_session.request.assert_called_once_with('GET', 'mock://test.com', allow_redirects=False, data=None,
                                                     headers={
                                                         'User-Agent': mock.ANY,
                                                         'Content-Type': 'application/vnd.piksel+json',
                                                         'Accept': 'application/vnd.piksel+json',
                                                         'X-Correlation-ID': None}, params=None, timeout=240)

    def test_request_given_server_returns_an_authorisation_error_then_fetch_token_does_not_count_as_retry(self):

        json_response = 'Error getting resource'

        mock_auth = Mock()
        mock_session = Mock()
        mock_session.request.side_effect = [error.AuthorisationError('Auth error'),
                                            {'text': json_response, 'status_code': 500},
                                            {'text': json_response, 'status_code': 200}]

        http_executor = http.HttpExecutor(mock_auth,
                                          session=mock_session,
                                          backoff_strategy={'interval': 0, 'max_tries': 1})

        with pytest.raises(error.AuthorisationError) as e:
            http_executor.request("GET", "mock://test.com")

        assert_that(e.value.args[0], is_('Auth error'))

        mock_session.request.assert_called_once_with('GET', 'mock://test.com', allow_redirects=False, data=None,
                                                     headers={
                                                         'User-Agent': mock.ANY,
                                                         'Content-Type': 'application/vnd.piksel+json',
                                                         'Accept': 'application/vnd.piksel+json',
                                                         'X-Correlation-ID': None}, params=None, timeout=240)

    def test_request_given_byo_type_and_server_returns_an_authorisation_error_then_error_is_propagated(self):
        json_response = '{"resp2": "resp2"}'

        self.adapter.register_uri('GET', 'mock://test.com', [{'text': 'resp1', 'status_code': 401},
                                                             {'text': json_response, 'status_code': 200}])

        http_executor = http.HttpExecutor(auth.AuthFactory.create(auth_type=auth.AuthType.BYO_TOKEN, byo_token='asdf'),
                                          session=self.session_mock,
                                          backoff_strategy={'interval': 0, 'max_tries': 1})
        with pytest.raises(error.HttpError) as e:
            http_executor.request("GET", "mock://test.com")

        assert_that(e.value.args[0], is_('An unexpected error occurred. HTTP Status code: 401.'
                                         ' Error message: Expecting value: line 1 column 1 (char 0). '))

    def test_request_given_a_resource_name_for_a_request_then_it_should_be_returned_with_the_request_result(self):
        self.adapter.register_uri('GET', 'mock://test.com', status_code=200)

        http_executor = http.HttpExecutor(auth.AuthFactory.create(grant_client_id="client_id",
                                                                  grant_client_secret="client_secret"),
                                          session=self.session_mock)

        resource_name_expected = 'resource_name_test'
        response = http_executor.request("GET", "mock://test.com", resource_name=resource_name_expected)

        assert_that(response.resource_name, equal_to(resource_name_expected))

    def test_given_none_content_type_property_then_header_should_contain_none_content_type(self):
        http_executor = http.HttpExecutor(None, content_type=None)
        assert_that(http_executor.common_headers['Content-Type'], is_('application/vnd.piksel+json'))
        assert_that(http_executor.common_headers['Accept'], is_('application/vnd.piksel+json'))

    def test_given_a_content_type_property_then_header_should_contain_that_content_type(self):
        http_executor = http.HttpExecutor(None, content_type='abc')
        assert_that(http_executor.common_headers['Content-Type'], is_('abc'))
        assert_that(http_executor.common_headers['Accept'], is_('abc'))
