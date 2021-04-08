import enum
import logging

import requests
import requests_oauthlib
from oauthlib.oauth2 import BackendApplicationClient, OAuth2Token, OAuth2Error, TokenExpiredError
from requests.auth import HTTPBasicAuth

from sequoia import error

AUTHORIZATION_HEADER = 'Authorization'


class AuthType(enum.Enum):
    """The enumeration of supported OAuth2 Authorization Types"""
    CLIENT_GRANT = 1
    NO_AUTH = 2
    BYO_TOKEN = 3
    MUTUAL = 4


class AuthFactory:
    @staticmethod
    # pylint: disable-msg=too-many-arguments
    def create(grant_client_id=None,
               grant_client_secret=None,
               auth_type=AuthType.CLIENT_GRANT,
               byo_token=None,
               token_url=None,
               request_timeout=0,
               client_cert=None,
               client_key=None,
               server_cert=None):
        if auth_type == AuthType.CLIENT_GRANT and grant_client_id is not None and grant_client_secret is not None:
            logging.debug('Client credential grant scheme used')
            return ClientGrantAuth(grant_client_id, grant_client_secret, token_url, byo_token=byo_token,
                                   request_timeout=request_timeout)

        if auth_type == AuthType.NO_AUTH:
            logging.debug('No auth schema used')
            return NoAuth()

        if auth_type == AuthType.BYO_TOKEN:
            logging.debug('BYO token scheme used')
            return BYOTokenAuth(byo_token)

        if auth_type == AuthType.MUTUAL:
            logging.debug('Mutual auth used')
            return MutualAuth(client_cert, client_key, server_cert)

        raise ValueError('No valid authentication sources found')


class Auth:
    def __init__(self):
        self.session = None

    def __call__(self, r):
        """
        Intercept the request and apply any custom logic to the request.
        Useful for applying custom authorization logic such as HMACs.

        :param r: the request
        :return: the updated request
        """
        return r

    def init_session(self):
        pass

    def register_adapters(self, adapters):
        if adapters:
            for adapter_registration in adapters:
                self.session.mount(adapter_registration[0],
                                   adapter_registration[1])

    def update_token(self):
        raise NotImplementedError("Auth type does not support refresh token")


class TokenCache:
    _token_storage = {}

    def get_token(self, grant_client_id, token_url):
        if grant_client_id in self._token_storage and token_url in self._token_storage[grant_client_id]:
            return self._token_storage[grant_client_id][token_url]
        return None

    def add_token(self, grant_client_id, token_url, token):
        if grant_client_id not in self._token_storage:
            self._token_storage[grant_client_id] = {}
        self._token_storage[grant_client_id][token_url] = token


class ClientGrantAuth(Auth):

    def __init__(self, grant_client_id, grant_client_secret, token_url, byo_token=None, request_timeout=0):
        super().__init__()
        self.grant_client_id = grant_client_id
        self.grant_client_secret = grant_client_secret
        self.auth = HTTPBasicAuth(self.grant_client_id,
                                  self.grant_client_secret)
        self.token_cache = TokenCache()
        self.token_url = token_url
        self.token = self.get_token(byo_token)
        self.request_timeout = request_timeout
        self.session = self._session(self.token)

    def get_token(self, byo_token):
        if byo_token:
            self.token_cache.add_token(self.grant_client_id, self.token_url, oauth_token(byo_token))
            return self.token_cache.get_token(self.grant_client_id, self.token_url)
        if self.token_cache.get_token(self.grant_client_id, self.token_url):
            return self.token_cache.get_token(self.grant_client_id, self.token_url)
        return None

    def init_session(self):
        if not self.token:
            self.update_token()

    def _session(self, token=None):
        client = BackendApplicationClient(client_id=self.grant_client_id)
        return OAuth2SessionTokenManagementWrapper(client=client,
                                                   token=token)

    def update_token(self):
        try:
            self.session.fetch_token(token_url=self.token_url,
                                     auth=self.auth, timeout=self.request_timeout)
            self.token_cache.add_token(self.grant_client_id, self.token_url, self.session.token)
        except OAuth2Error as oauth2_error:
            raise error.AuthorisationError(str(oauth2_error.args[0]), cause=oauth2_error)


class NoAuth(Auth):
    def __init__(self):
        super().__init__()
        self.auth = None

    def register_adapters(self, adapters):
        self.session = requests.Session() if adapters else None
        super().register_adapters(adapters)


class BYOTokenAuth(Auth):
    def __init__(self, byo_token):
        super().__init__()
        self.token = oauth_token(byo_token)
        self.session = OAuth2SessionTokenManagementWrapper(token=self.token)


class MutualAuth(Auth):
    def __init__(self, client_cert, client_key, server_cert):
        if client_cert is None or client_key is None or server_cert is None:
            raise ValueError('client_cert, client_key, server_cert must be provided when using AuthType.MUTUAL')
        super().__init__()
        self.auth = None
        self.session = requests.Session()
        self.session.cert =  (client_cert, client_key)
        self.session.verify =  server_cert


def oauth_token(access_token):
    data = {'token_type': 'bearer',
            'access_token': access_token}
    return OAuth2Token(data)


class OAuth2SessionTokenManagementWrapper(requests_oauthlib.OAuth2Session):

    def request(
        self,
        method,
        url,
        data=None,
        headers=None,
        withhold_token=False,
        client_id=None,
        client_secret=None,
        **kwargs
    ):
        try:
            return super().request(method, url, data, headers, withhold_token, client_id, client_secret, **kwargs)
        except TokenExpiredError as e:
            raise error.TokenExpiredError('Request could not be performed. Token is expired', cause=e)
