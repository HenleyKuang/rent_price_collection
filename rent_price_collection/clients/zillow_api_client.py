"""
:author: Henley Kuang
:since: 04/27/2019
"""

import argparse
import logging
import json
import urllib

from collections import namedtuple

from rent_price_collection.utils.config import (
    DEFAULT_LOG_FORMAT_STRING,
    ZILLOW_API_KEY,
    ZILLOW_LATITUDE_MAP_DIFF,
    ZILLOW_LONGITUDE_MAP_DIFF,
)
from rent_price_collection.utils.exceptions import (
    APIResponseException,
    APIRequestTimedOutException,
)
from rent_price_collection.utils.decorators import (
    retry_decorator,
)
from rent_price_collection.clients.zillow_rest_client import (
    ZILLOW_DOMAIN,
    ZillowRestClient,
)

LOGGER = logging.getLogger(__name__)

ZillowApiResponse = namedtuple('ZillowApiResponse', ['listings', 'pages'])
ZillowRegionResponse = namedtuple('ZillowRegionResponse', ['region_id', 'latitude', 'longitude'])

class ZillowApiClient(ZillowRestClient):

    def __init__(self, client=None, proxy_ip=None, proxy_port=None, proxy_user=None, proxy_pass=None):
        super(ZillowApiClient, self).__init__(client)

    def _api_search_parameters(self, location, page_num):
        url_params = []
        # Get region-id and default lat and long
        region_data = self.get_region_id_and_default_lat_lng(location)
        region_id = region_data.region_id
        default_lat = region_data.latitude
        default_lng = region_data.longitude
        search_query_state_dict = {
            "mapBounds": {
                "west": default_lng - ZILLOW_LONGITUDE_MAP_DIFF,
                "east": default_lng + ZILLOW_LONGITUDE_MAP_DIFF,
                "south": default_lat - ZILLOW_LONGITUDE_MAP_DIFF,
                "north": default_lat + ZILLOW_LONGITUDE_MAP_DIFF,
            },
            "regionSelection": [{
                "regionId": region_id,
                "regionType": 6
            }],
            "usersSearchTerm": location,
            "isMapVisible": False,
            "mapZoom": 11,
            "filterState": {
                "sortSelection": {"value": "days"},
                "isForSaleByAgent": {"value": False},
                "isForSaleByOwner": {"value": False},
                "isNewConstruction": {"value": False},
                "isForSaleForeclosure": {"value": False},
                "isComingSoon": {"value": False},
                "isPreMarketForeclosure": {"value": False},
                "isPreMarketPreForeclosure": {"value": False},
                "isMakeMeMove": {"value": False},
                "isForSaleForeclosure": {"value": False},
                "isForRent": {"value": True},
            },
            "isListVisible": True,
            "pagination": {"currentPage": page_num}
        }
        search_query_state_args = {
            "search_query_state_dict": urllib.quote(json.dumps(search_query_state_dict))
        }
        search_query_state_format = "GetSearchPageState.htm?searchQueryState=%(search_query_state_dict)s&includeMap=false&includeList=true"
        search_query_state_param = search_query_state_format % search_query_state_args
        url_params.append(search_query_state_param)
        return url_params

    def _api_region_child_parameters(self, state, city):
        url_params = []
        region_child_args = {
            'zillow_api_key': ZILLOW_API_KEY,
            'state_code': state,
            'city': urllib.quote(city)
        }
        region_child_format = "GetRegionChildren.htm?zws-id=%(zillow_api_key)s&state=%(state_code)s&city=%(city)s"
        region_child_param = region_child_format % region_child_args
        url_params.append(region_child_param)
        return url_params

    def _api_dots_parameters(self):
        raise NotImplementedError

    @retry_decorator((APIResponseException,), tries=10, delay=60, backoff=1, logger=LOGGER)
    @retry_decorator((APIRequestTimedOutException,), tries=3, delay=5, backoff=2, logger=LOGGER)
    def get_listings_by_search_api(self, location, page_num):
        """
        :param location: name of the location
        :type location: string
        :param page_num: page number
        :type page_num: int
        """
        LOGGER.info('Fetching listings with url api by location: %s and page_num: %s', location, page_num)
        api_name = 'search'
        api_parameters = self._api_search_parameters(location, page_num)
        api_path = self.get_api_path(api_name, *api_parameters)
        response = self.make_get_request(api_path)
        listings = response["searchResults"]["listResults"]
        pages = response["searchList"]["totalPages"]
        return ZillowApiResponse(listings=listings, pages=pages)

    def get_region_id_and_default_lat_lng(self, location):
        city = location.split(",")[0].strip()
        state = location.split(",")[1].strip()
        LOGGER.info('Fetching region id for state=%s, city=%s', state, city)
        api_name = 'webservice'
        api_parameters = self._api_region_child_parameters(state, city)
        api_path = self.get_api_path(api_name, *api_parameters)
        xml_response = self.make_get_request_xml(api_path)
        region_data = xml_response.find("response").find("region")
        region_id = int(region_data.find("id").text)
        latitude = float(region_data.find("latitude").text)
        longitude = float(region_data.find("longitude").text)
        return ZillowRegionResponse(region_id=region_id, latitude=latitude, longitude=longitude)

    @retry_decorator((APIResponseException,), tries=10, delay=60, backoff=1, logger=LOGGER)
    @retry_decorator((APIRequestTimedOutException,), tries=3, delay=5, backoff=2, logger=LOGGER)
    def get_listings_by_dots_api(self):
        LOGGER.info('Fetching listings with dots api')
        raise NotImplementedError

def _parse_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

    base_parser = argparse.ArgumentParser(add_help=False)
    base_parser.add_argument('--location', required=True)
    base_parser.add_argument('--page-num', type=int, default=1)

    command_subparser = parser.add_subparsers(dest='sub_command')
    command_subparser.required = True

    command_subparser.add_parser('get', parents=[base_parser])
    command_subparser.add_parser('get-region-id', parents=[base_parser])

    return parser.parse_args()

def _main():
    options = _parse_args()
    location = options.location
    page_num = options.page_num

    zillow_rpc_client = ZillowApiClient()

    if options.sub_command == 'get':
        zillow_api_response = zillow_rpc_client.get_listings_by_search_api(location, page_num)
        LOGGER.info("Listings: %s", zillow_api_response.listings)
        LOGGER.info("Pages: %s", zillow_api_response.pages)
    if options.sub_command == 'get-region-id':
        zillow_api_response = zillow_rpc_client.get_region_id_and_default_lat_lng(location)
        LOGGER.info(zillow_api_response)


if __name__ == '__main__':
    logging.basicConfig(format=DEFAULT_LOG_FORMAT_STRING, datefmt="%Y-%m-%d %H:%M:%S", level=logging.INFO)
    _main()
