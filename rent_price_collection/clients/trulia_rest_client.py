"""
:author: Henley Kuang
:since: 04/27/2019
"""

import logging

from rent_price_collection.utils.exceptions import (
    ResponseMissingPageCardsKeyException,
    ResponseMissingPageKeyException,
    ResponseSuccessFalseException,
    ZeroListingsReturnedException,
)
from rent_price_collection.utils.rest_client import (
    get_client
)

LOGGER = logging.getLogger(__name__)

CODE_EXCEPTIONS = {
    """
    List of exceptions that can be returned from API
    <Exception Code>: <Exception Name>
    """
}

TRULIA_DOMAIN = "www.trulia.com"

def _get_api_path(api_name, *args):
    """Return api_path_with_version

    >>> _get_api_path('test', '12345')
    '/test/12345'
    """
    str_args = [str(v) for v in args]
    return '/%s/%s' % (api_name, '/'.join(str_args))

class TruliaRestClient(object):

    def __init__(self, client=None, proxy_ip=None, proxy_port=None, proxy_user=None, proxy_pass=None):
        self._client = client if client else get_client(proxy_ip, proxy_port, proxy_user, proxy_pass)

    def get_api_path(self, api_name, *args):
        """Return api_path"""
        return _get_api_path(api_name, *args)

    def handle_api_error(self, api_response):
        """Trulia API ERROR Handler"""
        if "success" in api_response and api_response["success"] is False:
            LOGGER.warn('API RESPONSE has error ==> %s', api_response)
            raise ResponseSuccessFalseException("Please double check your input location spelling")
        if "page" not in api_response:
            LOGGER.warn('API RESPONSE does not have "pages" key ==> %s', api_response)
            raise ResponseMissingPageKeyException("Response format may have change. Missing 'pages' in response")
        if "cards" not in api_response["page"]:
            LOGGER.warn('API RESPONSE does not have "cards" key in response["pages"] ==> %s', api_response)
            raise ResponseMissingPageCardsKeyException("Response format may have changed. Missing 'cards' in response['pages']")
        if len(api_response["page"]["cards"]) == 0:
            raise ZeroListingsReturnedException

    def make_post_request(self, api_path, data):
        LOGGER.info('POST request ==> %s', api_path)
        response = self._client.post(TRULIA_DOMAIN, api_path, dict(data=data))
        self.handle_api_error(response)
        return response

    def make_get_request(self, api_path):
        LOGGER.info('GET request ==> %s', api_path)
        response = self._client.get(TRULIA_DOMAIN, api_path)
        self.handle_api_error(response)
        return response
