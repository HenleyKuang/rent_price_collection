"""
:author: Henley Kuang
:since: 04/27/2019
"""

import argparse
import collections
import logging
import json
import re

from random import randint
from time import sleep

from rent_price_collection.clients.trulia_api_client import (
    TruliaApiClient,
)
from rent_price_collection.misc.email import (
    GMailNotify,
)
from rent_price_collection.storage.trulia_mysql import (
    TruliaMySql,
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
    ResponseSuccessFalseException,
    StoreListingResultsException,
    ZeroListingsReturnedException,
)

LOGGER = logging.getLogger(__name__)

LISTING_TYPES = {
    "rent": "for_rent",
}

TruliaListing = collections.namedtuple('TruliaListing',
    [
        'listing_id',
        'card_url',
        'street_address',
        'city',
        'state',
        'zip_code',
        'beds',
        'baths',
        'lat',
        'lng',
        'sqft',
        'price',
    ],
)

class TruliaRpc(object):

    def __init__(self, proxy_ip=None, proxy_port=None, proxy_user=None, proxy_pass=None):
        self.trulia_api_client = TruliaApiClient(
            proxy_ip=proxy_ip,
            proxy_port=proxy_port,
            proxy_user=proxy_user,
            proxy_pass=proxy_pass,
        )
        self.trulia_storage = TruliaMySql()
        self.email_client = GMailNotify(GMAIL_USER, GMAIL_PASSWORD)

    def _get_dict_key_value_no_exception(self, dict, key, return_val='-1'):
        try:
            return dict[key]
        except:
            return return_val

    def _get_listing_named_tuple(self, listing):
        """
        Extract relevant info from api's listing dict.
        Below are all values provided by API with examples of the values
        """
        city = self._get_dict_key_value_no_exception(listing, 'city')  # u'San Francisco',
        card_url = self._get_dict_key_value_no_exception(listing, 'cardUrl')  # u'/p/ca/san-francisco/301-main-st-17g-san-francisco-ca-94105--2082855718'
        # highlighted_tags = self._get_dict_key_value_no_exception(listing, 'highlightedTags')  # [u'New']
        # photo_url_for_hd_dpi_display = self._get_dict_key_value_no_exception(listing, 'photoUrlForHdDpiDisplay')  # u'/pictures/thumbs_4/ps.113/3/e/7/e/picture-uh=ac1ab49ccc1aaaab5aea574ef9c8f029-ps=3e7e174814164f4f338291900b0e67.jpg'
        zip_code = self._get_dict_key_value_no_exception(listing, 'zip')  # u'94105'
        # footer = self._get_dict_key_value_no_exception(listing, 'footer')  # {u'addressHash': u'cg12b4usu9fu4lpviw9vtyz3e', u'component': u'ForRentCardFooter'}
        price = self._get_dict_key_value_no_exception(listing, 'price')  # u'$4,200'
        photo_url = self._get_dict_key_value_no_exception(listing, 'photoUrl')  # u'/pictures/thumbs_3/ps.113/3/e/7/e/picture-uh=ac1ab49ccc1aaaab5aea574ef9c8f029-ps=3e7e174814164f4f338291900b0e67.jpg'
        # malone_id = self._get_dict_key_value_no_exception(listing, 'maloneId')  # u'2082855718'
        # savable = self._get_dict_key_value_no_exception(listing, 'savable')  # True
        beds = self._get_dict_key_value_no_exception(listing, 'beds')  # u'1bd'
        street_address = self._get_dict_key_value_no_exception(listing, 'streetAddress')  # u'301 Main St #17G'
        # photo_count = self._get_dict_key_value_no_exception(listing, 'photoCount')  # 31
        lat_lng = self._get_dict_key_value_no_exception(listing, 'latLng')  # [37.789375, -122.39097]
        state_code = self._get_dict_key_value_no_exception(listing, 'stateCode')  # u'CA'
        baths = self._get_dict_key_value_no_exception(listing, 'baths')  # u'1ba'
        # formatted_address = self._get_dict_key_value_no_exception(listing, 'formattedAddress')  # u'301 Main St #17G, SanFrancisco, CA'
        # short_price = self._get_dict_key_value_no_exception(listing, 'shortPrice')  # u'$4.2k'
        sqft = self._get_dict_key_value_no_exception(listing, 'sqft')  # u'809 sqft'
        listing_id = self._get_dict_key_value_no_exception(listing, 'id')  # u'4062672943'
        try:
            trulia_listing = TruliaListing(
                listing_id=int(listing_id),
                card_url=card_url.encode('utf-8'),
                street_address=street_address.encode('utf-8'),
                city=city.encode('utf-8'),
                state=state_code.encode('utf-8'),
                zip_code=int(zip_code),
                beds=beds.encode('utf-8'),
                baths=baths.encode('utf-8'),
                lat=lat_lng[0],
                lng=lat_lng[1],
                sqft=sqft.encode('utf-8'),
                price=price.encode('utf-8'),
            )
        except:
            LOGGER.info(listing)
            raise
        return trulia_listing

    def run(self, locations_list, start_page_num):
        success_count = 0
        success_list = []
        fail_count = 0
        fail_list = []
        for location in locations_list:
            trulia_listings_tuple = []
            # Paginate for all listings
            page_num = start_page_num
            while True:
                try:
                    listings = self.trulia_api_client.get_listings_by_url_api(location, page_num)
                    for listing_dict in listings:
                        trulia_listing = self._get_listing_named_tuple(listing_dict)
                        trulia_listings_tuple.append(trulia_listing)
                    page_num += 1
                    # Random sleep between each api request
                    sleep_time_seconds = randint(SLEEP_BETWEEN_API_REQUESTS_MIN, SLEEP_BETWEEN_API_REQUESTS_MAX)
                    LOGGER.info("Sleep between api request for %s seconds", sleep_time_seconds)
                    sleep(sleep_time_seconds)
                except ZeroListingsReturnedException as e:
                    listings_count = len(trulia_listings_tuple)
                    if listings_count == 0:
                        LOGGER.info("Your search for location: %s, returned 0 total results", location)
                        break
                    LOGGER.info("No more results. Next Step: store %s results into MySQL", len(trulia_listings_tuple))
                    break
                except Exception as e:
                    LOGGER.info("There was a problem crawling the API: %s", e)
                    fail_count += 1
                    fail_error_set = (type(e).__name__, location, e)
                    fail_list.append(fail_error_set)
            # store results into MySQL
            if len(trulia_listings_tuple) > 0:
                try:
                    self.trulia_storage.upsert_trulia_listings(trulia_listings_tuple)
                    LOGGER.info("Stored %s results", len(trulia_listings_tuple))
                    success_count += 1
                    success_list.append((location, len(trulia_listings_tuple)))
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
            email_subject = "[Trulia Complete] %s Successful | %s Failed" % (success_count, fail_count)
            success_list_formatted = json.dumps(success_list, sort_keys=True, indent=4)
            failed_list_formatted = json.dumps(fail_list, sort_keys=True, indent=4)
            email_message = "success_list: %s\nfailed_list: %s" % (success_list_formatted, failed_list_formatted)
            self.email_client.send_email(GMAIL_SENT_TO_EMAILS, email_subject, email_message)
            LOGGER.info("Emailed completion of crawling %s location(s)", len(locations_list))
        except EmailSendingException as e:
            LOGGER.info("Failed email results: %s", e)
        # close database handle
        self.trulia_storage.close()

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

    trulia_rpc = TruliaRpc(proxy_ip, proxy_port, proxy_user, proxy_pass)

    trulia_rpc.run(locations_list, start_page_num)


if __name__ == '__main__':
    logging.basicConfig(format=DEFAULT_LOG_FORMAT_STRING, datefmt="%Y-%m-%d %H:%M:%S", level=logging.INFO)
    _main()
