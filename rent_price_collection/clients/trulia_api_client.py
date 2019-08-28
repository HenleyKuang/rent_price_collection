"""
:author: Henley Kuang
:since: 04/27/2019
"""

import argparse
import logging

from rent_price_collection.utils.config import (
    DEFAULT_LOG_FORMAT_STRING,
)
from rent_price_collection.utils.exceptions import (
    APIResponseException,
    APIRequestTimedOutException,
)
from rent_price_collection.utils.decorators import (
    retry_decorator,
)
from rent_price_collection.clients.trulia_rest_client import (
    TRULIA_DOMAIN,
    TruliaRestClient,
)

LOGGER = logging.getLogger(__name__)

LISTING_TYPES = {
    "rent": "for_rent",
}

class TruliaApiClient(TruliaRestClient):

    def __init__(self, client=None, proxy_ip=None, proxy_port=None, proxy_user=None, proxy_pass=None):
        super(TruliaApiClient, self).__init__(client)

    def _format_location_str(self, location):
        return location.replace(" ", "_")

    def _api_url_parameters(self, location, page_num):
        url_params = []
        url_args = {
            "domain": TRULIA_DOMAIN,
            "listing_type": LISTING_TYPES["rent"],
            "location": self._format_location_str(location),
            "page_num": page_num,
        }
        url_format = "https://%(domain)s/%(listing_type)s/%(location)s/date;d_sort/%(page_num)s_p"
        url_path = url_format % url_args
        url_params.append("?url=%s" % url_path)
        return url_params

    def _api_dots_parameters(self):
        raise NotImplementedError

    @retry_decorator((APIResponseException,), tries=10, delay=60, backoff=1, logger=LOGGER)
    @retry_decorator((APIRequestTimedOutException,), tries=3, delay=5, backoff=2, logger=LOGGER)
    def get_listings_by_url_api(self, location, page_num):
        """
        :param location: name of the location
        :type location: string
        :param page_num: page number
        :type page_num: int
        """
        LOGGER.info('Fetching listings with url api by location: %s and page_num: %s', location, page_num)
        api_name = 'json/search/url'
        api_parameters = self._api_url_parameters(location, page_num)
        api_path = self.get_api_path(api_name, *api_parameters)
        response = self.make_get_request(api_path)
        listings = response["page"]["cards"]
        return listings

    @retry_decorator((APIResponseException,), tries=10, delay=60, backoff=1, logger=LOGGER)
    @retry_decorator((APIRequestTimedOutException,), tries=3, delay=5, backoff=2, logger=LOGGER)
    def get_listings_by_dots_api(self):
        LOGGER.info('Fetching listings with dots api')
        raise NotImplementedError

def _parse_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

    base_parser = argparse.ArgumentParser(add_help=False)
    base_parser.add_argument('--location', required=True)
    base_parser.add_argument('--page-num', type=int, required=True)

    command_subparser = parser.add_subparsers(dest='sub_command')
    command_subparser.required = True

    command_subparser.add_parser('get', parents=[base_parser])

    return parser.parse_args()

def _main():
    options = _parse_args()
    location = options.location
    page_num = options.page_num

    trulia_rpc_client = TruliaApiClient()

    if options.sub_command == 'get':
        response = trulia_rpc_client.get_listings_by_url_api(location, page_num)
        LOGGER.info(response)


if __name__ == '__main__':
    logging.basicConfig(format=DEFAULT_LOG_FORMAT_STRING, datefmt="%Y-%m-%d %H:%M:%S", level=logging.INFO)
    _main()
