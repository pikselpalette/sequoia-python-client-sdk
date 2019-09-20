import copy
import logging
import os
import sys
import unittest

import pytest
from hamcrest import assert_that, empty, has_length, instance_of, equal_to, none, is_
from oauthlib.oauth2 import InvalidGrantError
from requests import Response

from sequoia import criteria, auth
from sequoia import error
from sequoia.client import Client, ResponseBuilder
from sequoia.criteria import Criteria, Inclusion
from tests import mocking

if sys.version_info[0] == 2:
    import mock
    from mock import patch
else:
    from unittest import mock
    from unittest.mock import patch

logging.basicConfig(level=logging.DEBUG)


class TestPaginationWithContinue(unittest.TestCase):

    def setUp(self):
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
        self.mock = mocking.bootstrap_mock()
        self.client = Client('http://mock-registry/services/testmock',
                             grant_client_id='piksel-workflow',
                             grant_client_secret='blablabla',
                             adapters=[('http://', self.mock)])

    def test_browse_assets_with_paging_returns_mocked_assets(self):
        # Query
        # curl -X GET \
        #   'https://metadata.integration.eu-west-1.palettedev.aws.pikselpalette.com/data/contents?owner=test&perPage=2&continue=true' \
        #   -H 'Authorization: Bearer 7b8cbdcc694a7b8c7f2c2b32964c2a2d9a3005a2' \
        #   -H 'Content-Type: application/vnd.piksel+json'cm

        mocking.add_get_mapping_for_url(self.mock,
                                        'data/contents\?continue=true&perPage=2&owner=testmock',
                                        'pagination_continue_page_1')
        mocking.add_get_mapping_for_url(self.mock,
                                        '/data/contents?continue=00abcdefghijklmnopqrstuvwxyz11&owner=test&perPage=2',
                                        'pagination_continue_page_2')
        under_test = self.client.metadata.contents

        response_list = [response
                         for response in under_test.browse('testmock',
                                                           query_string='continue=true&perPage=2')]

        # assert_that(response_list, has_length(2))
        # assert_that(response_list[0].resources, has_length(2))
        # assert_that(response_list[1].resources, has_length(2))
        # assert_that(response_list[0].resources[0]['name'], is_('001436b2-93b7-43c5-89a3-b95ceb50aa73'))
        # assert_that(response_list[0].resources[1]['name'], is_('001436b2-93b7-43c5-89a3-b95ceb50aa73_aligned_primary'))
        # assert_that(response_list[1].resources[0]['name'], is_('001436b2-93b7-43c5-89a3-b95ceb50aa73_primary'))
        # assert_that(response_list[1].resources[1]['name'], is_('001436b2-93b7-43c5-89a3-b95ceb50aa73_textless'))

        assert_that(response_list, has_length(1))
        assert_that(response_list[0].resources, has_length(2))
        assert_that(response_list[0].resources[0]['name'], is_('001436b2-93b7-43c5-89a3-b95ceb50aa73'))
        assert_that(response_list[0].resources[1]['name'], is_('001436b2-93b7-43c5-89a3-b95ceb50aa73_aligned_primary'))
