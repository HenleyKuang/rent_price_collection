"""
:author: Henley Kuang
:since: 04/28/2019
"""

import logging

from rent_price_collection.utils.exceptions import (
    ResponseMissingKeyException,
    ResponseSuccessFalseException,
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

ZILLOW_DOMAIN = "www.zillow.com"

def _get_api_path(api_name, *args):
    """Return api_path_with_version

    >>> _get_api_path('test', '12345')
    '/test/12345'
    """
    str_args = [str(v) for v in args]
    return '/%s/%s' % (api_name, '/'.join(str_args))

class ZillowRestClient(object):

    def __init__(self, client=None, proxy_ip=None, proxy_port=None, proxy_user=None, proxy_pass=None):
        self._client = client if client else get_client(proxy_ip, proxy_port, proxy_user, proxy_pass)

    def get_api_path(self, api_name, *args):
        """Return api_path"""
        return _get_api_path(api_name, *args)

    def handle_api_error(self, api_response):
        """Zillow API ERROR Handler"""
        if "searchResults" not in api_response:
            raise ResponseMissingKeyException("'searchResults' key not in api_response")
        if "listResults" not in api_response["searchResults"]:
            raise ResponseMissingKeyException("'listResults' key not in api_response['searchResults']")
        if "searchList" not in api_response:
            raise ResponseMissingKeyException("'searchList' key not in api_response")
        if "totalPages" not in api_response['searchList']:
            LOGGER.info(api_response)
            raise ResponseMissingKeyException("'totalPages' key not in api_response['searchList']")

    def handle_xml_error(self, xml_response):
        response_code = xml_response.find("message").find("code")
        if response_code != 0:
            raise ResponseSuccessFalseException("XML Response Code is not 0")

    def make_post_request(self, api_path, data):
        LOGGER.info('POST request ==> %s', api_path)
        response = self._client.post(ZILLOW_DOMAIN, api_path, dict(data=data))
        self.handle_api_error(response)
        return response

    def make_get_request(self, api_path):
        LOGGER.info('GET request ==> %s', api_path)
        response = self._client.get(ZILLOW_DOMAIN, api_path)
        self.handle_api_error(response)
        return response

    def make_get_request_xml(self, api_path):
        LOGGER.info('GET request ==> %s', api_path)
        response = self._client.get(ZILLOW_DOMAIN, api_path)
        return response
