import unittest

from hamcrest import assert_that, is_

from sequoia.auth import TokenCache, ClientGrantAuth


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

    def test_given_token_is_not_provided_and_it_is_not_in_cache_then_token_is_fetched_and_added_to_cache(self):
        class MockSession:
            def __init__(self):
                self.token = {'token_type': 'bearer', 'access_token': '789'}

            def fetch_token(self, *args, **kwargs):
                pass

        auth = ClientGrantAuth('user', 'pass', 'http://identity')
        auth.session = MockSession()
        auth.init_session()

        assert_that(TokenCache._token_storage,
                    is_({'user': {'http://identity': {'token_type': 'bearer', 'access_token': '789'}}}))


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
