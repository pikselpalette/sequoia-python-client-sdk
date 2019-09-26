import enum
import logging

import requests
import requests_oauthlib
from oauthlib.oauth2 import BackendApplicationClient, OAuth2Token, OAuth2Error
from requests.auth import HTTPBasicAuth

from sequoia import error

AUTHORIZATION_HEADER = 'Authorization'


class AuthType(enum.Enum):
    """The enumeration of supported OAuth2 Authorization Types"""
    CLIENT_GRANT = 1
    NO_AUTH = 2
    BYO_TOKEN = 3


class AuthFactory:
    @staticmethod
    def get_auth(grant_client_id=None,
                 grant_client_secret=None,
                 auth_type=AuthType.CLIENT_GRANT,
                 byo_token=None,
                 token_url=None):

        if auth_type == AuthType.CLIENT_GRANT and grant_client_id is not None and grant_client_secret is not None:
            logging.debug('Client credential grant scheme used')
            return AuthClientGrant(grant_client_id, grant_client_secret, token_url, byo_token=byo_token)

        elif auth_type == AuthType.NO_AUTH:
            logging.debug('No auth schema used')
            return AuthNoAuth()

        elif auth_type == AuthType.BYO_TOKEN:
            logging.debug('BYO token scheme used')
            return AuthByoToken(byo_token)

        else:
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

    def create_session(self, request_timeout=0):
        return None

    def register_adapters(self, adapters):
        if adapters:
            for adapter_registration in adapters:
                self.session.mount(adapter_registration[0],
                                   adapter_registration[1])

    def refresh_token(self, request_timeout=0):
        raise NotImplementedError("Auth type does not support refresh token")


class AuthClientGrant(Auth):
    def __init__(self, grant_client_id, grant_client_secret, token_url, byo_token=None):
        super().__init__()
        self.grant_client_id = grant_client_id
        self.grant_client_secret = grant_client_secret
        self.auth = HTTPBasicAuth(self.grant_client_id,
                                  self.grant_client_secret)
        self.token = oauth_token(byo_token) if byo_token else None
        self.token_url = token_url

    def create_session(self, request_timeout=0):
        self.session = self._session(self.token)
        if not self.token:
            self.refresh_token(request_timeout)

        return self.session

    def _session(self, token=None):
        client = BackendApplicationClient(client_id=self.grant_client_id)
        return requests_oauthlib.OAuth2Session(client=client,
                                               token=token)

    def refresh_token(self, request_timeout=0):
        try:
            self.session.fetch_token(token_url=self.token_url,
                                     auth=self.auth, timeout=request_timeout)
        except OAuth2Error as oauth2_error:
            raise error.AuthorisationError(str(oauth2_error.args[0]), cause=oauth2_error)


class AuthNoAuth(Auth):
    def __init__(self):
        super().__init__()
        self.auth = None

    def register_adapters(self, adapters):
        self.session = requests.Session() if adapters else None
        super().register_adapters(adapters)

    def refresh_token(self, request_timeout=0):
        super().refresh_token(request_timeout)


class AuthByoToken(Auth):
    def __init__(self, byo_token):
        super().__init__()
        self.token = oauth_token(byo_token)

    def create_session(self, request_timeout=0):
        self.session = requests_oauthlib.OAuth2Session(token=self.token)
        return self.session

    def refresh_token(self, request_timeout=0):
        super().refresh_token(request_timeout)


def oauth_token(access_token):
    data = {'token_type': 'bearer',
            'access_token': access_token}
    return OAuth2Token(data)
