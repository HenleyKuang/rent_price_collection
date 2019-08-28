"""
:author: Henley Kuang
:since: 04/28/2019
"""

import argparse
import collections
import logging
import json
import re

from random import randint
from time import sleep

from rent_price_collection.clients.zillow_api_client import (
    ZillowApiClient,
)
from rent_price_collection.misc.email import (
    GMailNotify,
)
from rent_price_collection.storage.zillow_mysql import (
    ZillowMySql,
)
from rent_price_collection.utils.config import (
    DEFAULT_LOG_FORMAT_STRING,
    GMAIL_USER,
    GMAIL_PASSWORD,
    GMAIL_SENT_TO_EMAILS,
    SLEEP_BETWEEN_API_REQUESTS_MAX,
    SLEEP_BETWEEN_API_REQUESTS_MIN,
    SLEEP_BETWEEN_LOCATIONS_MAX,
    SLEEP_BETWEEN_LOCATIONS_MIN,
)
from rent_price_collection.utils.exceptions import (
    EmailSendingException,
    StoreListingResultsException,
)

LOGGER = logging.getLogger(__name__)

ZillowListing = collections.namedtuple('ZillowListing',
    [
        'listing_id',
        'detail_url',
        'street_address',
        'city',
        'state',
        'building_name',
        'zip_code',
        'beds',
        'baths',
        'lat',
        'lng',
        'sqft',
        'price',
    ],
)

class ZillowRpc(object):

    def __init__(self, proxy_ip=None, proxy_port=None, proxy_user=None, proxy_pass=None):
        self.zillow_api_client = ZillowApiClient(
            proxy_ip=proxy_ip,
            proxy_port=proxy_port,
            proxy_user=proxy_user,
            proxy_pass=proxy_pass,
        )
        self.zillow_storage = ZillowMySql()
        self.email_client = GMailNotify(GMAIL_USER, GMAIL_PASSWORD)

    def _get_dict_key_value_no_exception(self, _dict, key, skip_string_conversion=False, return_val='-1'):
        try:
            val = _dict[key]
            if skip_string_conversion:
                return val
            if val is None:
                return return_val
            return str(_dict[key])
        except Exception as e:
            # LOGGER.warn("%s, %s, %s, %s", _dict, type(_dict), key, e)
            return return_val

    def _get_listings_named_tuple(self, listing):
        """
        Extract relevant info from api's listing dict.
        Below are all values provided by API with examples of the values
        """
        zillow_named_tuples_list = []

        listing_id = self._get_dict_key_value_no_exception(listing, "id")  # "3318837",
        detail_url = self._get_dict_key_value_no_exception(listing, "detailUrl")  # "https://www.zillow.com/homedetails/821-N-Salem-Ave-Arlington-Heights-IL-60004/3318837_zpid/",
        price = self._get_dict_key_value_no_exception(listing, "price")  # "$2,600/mo",
        address = self._get_dict_key_value_no_exception(listing, "address")  # "821 N Salem Ave, Arlington Heights, IL",
        street_address = address.split(",")[0].strip()
        city = address.split(",")[1].strip()
        state_code = self._get_dict_key_value_no_exception(listing, "addressState")  # "IL",
        building_name = self._get_dict_key_value_no_exception(listing, "buildingName")  # "Hawthorne Apartments",
        address_with_zip_code = self._get_dict_key_value_no_exception(listing, "addressWithZip")  # "821 N Salem Ave, Arlington Heights, IL 60004",
        beds = self._get_dict_key_value_no_exception(listing, "beds")  # 4,
        baths = self._get_dict_key_value_no_exception(listing, "baths")  # 3,
        sqft = self._get_dict_key_value_no_exception(listing, "area")  # 2318,
        lat_lng = self._get_dict_key_value_no_exception(listing, "latLong", skip_string_conversion=True)  # {u'latitude': 47.688611, u'longitude': -122.209039},
        latitude = self._get_dict_key_value_no_exception(lat_lng, "latitude")
        longitude = self._get_dict_key_value_no_exception(lat_lng, "longitude")
        units = self._get_dict_key_value_no_exception(listing, "units", skip_string_conversion=True)  # [{u'beds': u'0', u'price': u'$1,785+'}]
        # zip is never available for apartment complex listings
        zip_code = -1
        try:
            # apartment complex listings do not have zip nor city data
            if 'units' in listing:
                for unit in units:
                    price = self._get_dict_key_value_no_exception(unit, "price")
                    beds = self._get_dict_key_value_no_exception(unit, "beds")
                    state_code = address.split(",")[2].strip()
                    unit_listing_id = '%s-%s' % (listing_id, beds)
                    zillow_listing = ZillowListing(
                        listing_id=unit_listing_id,
                        detail_url=detail_url.encode('utf-8'),
                        street_address=street_address.encode('utf-8'),
                        city=city.encode('utf-8'),
                        state=state_code.encode('utf-8'),
                        building_name=building_name.encode('utf-8'),
                        zip_code=int(zip_code),
                        beds=beds.encode('utf-8'),
                        baths=baths.encode('utf-8'),
                        lat=latitude,
                        lng=longitude,
                        sqft=sqft.encode('utf-8'),
                        price=price.encode('utf-8'),
                    )
                    zillow_named_tuples_list.append(zillow_listing)
            else:
                # zip code is usually avaialble for non-apartment complex listings
                try:
                    zip_code = int(address_with_zip_code[-6:])
                except:
                    # hdp_data is sometimes available
                    hdp_data = self._get_dict_key_value_no_exception(listing, "hdpData", skip_string_conversion=True)
                    home_info = self._get_dict_key_value_no_exception(hdp_data, "homeInfo", skip_string_conversion=True)
                    zip_code = int(self._get_dict_key_value_no_exception(hdp_data, "zipcode"))
                    if state_code == '-1':
                        state_code = self._get_dict_key_value_no_exception(hdp_data, "state")
                    if city == '-1':
                        city = self._get_dict_key_value_no_exception(hdp_data, "city")
                zillow_listing = ZillowListing(
                    listing_id=listing_id,
                    detail_url=detail_url.encode('utf-8'),
                    street_address=street_address.encode('utf-8'),
                    city=city.encode('utf-8'),
                    state=state_code.encode('utf-8'),
                    zip_code=zip_code,
                    building_name=building_name.encode('utf-8'),
                    beds=beds.encode('utf-8'),
                    baths=baths.encode('utf-8'),
                    lat=latitude,
                    lng=longitude,
                    sqft=sqft.encode('utf-8'),
                    price=price.encode('utf-8'),
                )
                zillow_named_tuples_list.append(zillow_listing)
        except Exception as e:
            raise Exception("[ERROR] Listing: %s, error: %s", listing, e)
        return zillow_named_tuples_list

    def run(self, locations_list, start_page_num):
        success_count = 0
        success_list = []
        fail_count = 0
        fail_list = []
        for location in locations_list:
            zillow_listings_tuple = []
            # Paginate for all listings
            page_num = start_page_num
            while True:
                try:
                    api_response = self.zillow_api_client.get_listings_by_search_api(location, page_num)
                    listings = api_response.listings
                    total_pages = api_response.pages
                    LOGGER.info("current location: %s, current_page: %s, total pages: %s", location, page_num, total_pages)
                    for listing_dict in listings:
                        zillow_listing = self._get_listings_named_tuple(listing_dict)
                        zillow_listings_tuple += zillow_listing
                    page_num += 1
                    if total_pages < page_num:
                        LOGGER.info("No more results. Next Step: store %s results into MySQL", len(zillow_listings_tuple))
                        break
                    # Random sleep between each api request
                    sleep_time_seconds = randint(SLEEP_BETWEEN_API_REQUESTS_MIN, SLEEP_BETWEEN_API_REQUESTS_MAX)
                    LOGGER.info("Sleep between api request for %s seconds", sleep_time_seconds)
                    sleep(sleep_time_seconds)
                except Exception as e:
                    LOGGER.error("There was a problem crawling the API: %s", e)
                    raise
                    fail_count += 1
                    fail_error_set = (type(e).__name__, location, e)
                    fail_list.append(fail_error_set)
            # store results into MySQL
            if len(zillow_listings_tuple) > 0:
                try:
                    self.zillow_storage.upsert_zillow_listings(zillow_listings_tuple)
                    LOGGER.info("Stored %s results", len(zillow_listings_tuple))
                    success_count += 1
                    success_list.append((location, len(zillow_listings_tuple)))
                except StoreListingResultsException as e:
                    LOGGER.info("Failed to store listing results into storage: %s", e)
                    fail_count += 1
                    fail_error_set = (type(e).__name__, location, e)
                    fail_list.append(fail_error_set)
            # Random sleep between each location
            sleep_time_seconds = randint(SLEEP_BETWEEN_LOCATIONS_MIN, SLEEP_BETWEEN_LOCATIONS_MAX)
            LOGGER.info("Sleep between locations for %s seconds", sleep_time_seconds)
            sleep(sleep_time_seconds)
        # Email results of the run
        try:
            email_subject = "[Zillow Complete] %s Successful | %s Failed" % (success_count, fail_count)
            success_list_formatted = json.dumps(success_list, sort_keys=True, indent=4)
            failed_list_formatted = json.dumps(fail_list, sort_keys=True, indent=4)
            email_message = "success_list: %s\nfailed_list: %s" % (success_list_formatted, failed_list_formatted)
            self.email_client.send_email(GMAIL_SENT_TO_EMAILS, email_subject, email_message)
            LOGGER.info("Emailed completion of crawling %s location(s)", len(locations_list))
        except EmailSendingException as e:
            LOGGER.info("Failed email results: %s", e)
        # close database handle
        self.zillow_storage.close()

def _parse_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--location', help='single location name, only specify if you do not use location-file options')
    parser.add_argument('--location-file', help='file containing list of location names, line by line')
    parser.add_argument('--start-page-num', type=int, default=1)

    parser.add_argument('--proxy-ip')
    parser.add_argument('--proxy-port')
    parser.add_argument('--proxy-user')
    parser.add_argument('--proxy-pass')

    return parser.parse_args()

def _main():
    options = _parse_args()
    location = options.location
    location_file = options.location_file
    start_page_num = options.start_page_num

    # optional proxy
    proxy_ip = options.proxy_ip
    proxy_port = options.proxy_port
    proxy_user = options.proxy_port
    proxy_pass = options.proxy_pass

    if location_file:
        locations_list = open(location_file, "r").read().splitlines()
    else:
        locations_list = [location]

    zillow_rpc = ZillowRpc(proxy_ip, proxy_port, proxy_user, proxy_pass)

    zillow_rpc.run(locations_list, start_page_num)


if __name__ == '__main__':
    logging.basicConfig(format=DEFAULT_LOG_FORMAT_STRING, datefmt="%Y-%m-%d %H:%M:%S", level=logging.INFO)
    _main()
