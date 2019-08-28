"""
:author: Henley Kuang
:since: 04/28/2019

Table SCHEMA:
CREATE TABLE `zillow_listings` (
	`listing_id` varchar(255) NOT NULL,
	`detail_url` varchar(255) NOT NULL,
	`street_address` varchar(255) NOT NULL,
	`city` varchar(255) NOT NULL,
	`state` varchar(255) NOT NULL,
	`building_name` varchar(255) NOT NULL,
	`zip_code` mediumint(6) signed NOT NULL,
	`beds` varchar(255) NOT NULL,
	`baths` varchar(255) NOT NULL,
	`lat` double(10,7) NOT NULL,
	`lng` double(10,7) NOT NULL,
	`sqft` varchar(255) NOT NULL,
	`price` varchar(255) NOT NULL,
	`date_collected` datetime DEFAULT CURRENT_TIMESTAMP,
	`date_updated` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (`listing_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 ROW_FORMAT=COMPRESSED;
"""

import argparse
import logging
import MySQLdb

from rent_price_collection.utils.config import (
    DEFAULT_LOG_FORMAT_STRING,
    MYSQL_HOST,
    MYSQL_USER,
    MYSQL_PASS,
    MYSQL_DB,
    MYSQL_PORT,
)
from rent_price_collection.utils.exceptions import (
    StoreListingResultsException,
)

LOGGER = logging.getLogger(__name__)

class ZillowMySql():

    DB_TABLE_NAME = 'zillow_listings'
    QUERY_SELECT = '''select * from {table_name}'''.format(table_name=DB_TABLE_NAME)
    QUERY_UPSERT = '''insert into {table_name}
(listing_id, detail_url, street_address, city, state, building_name, zip_code, beds, baths, lat, lng, sqft, price)
VALUES (
%(listing_id)s,
%(detail_url)s,
%(street_address)s,
%(city)s,
%(state)s,
%(building_name)s,
%(zip_code)s,
%(beds)s,
%(baths)s,
%(lat)s,
%(lng)s,
%(sqft)s,
%(price)s
)
ON DUPLICATE KEY UPDATE price=%(price)s, sqft=%(sqft)s, date_updated=CURRENT_TIMESTAMP;'''.format(table_name=DB_TABLE_NAME)

    def __init__(self):
        db_selector = {'host': MYSQL_HOST,
                       'user': MYSQL_USER,
                       'passwd': MYSQL_PASS,
                       'db': MYSQL_DB,
                       'port': MYSQL_PORT,
                       'use_unicode': False,
                       'charset': 'latin1',
                      }
        self.db_handle = MySQLdb.connect(**db_selector)

    def select_zillow_listings(self, limit=None):
        cursor = None
        results = None
        try:
            cursor = self.db_handle.cursor(MySQLdb.cursors.DictCursor)
            query_select = self.QUERY_SELECT
            if limit:
                query_select = "%s limit %s" % (query_select, limit)
            cursor.execute(query_select)
            results = cursor.fetchall()
            cursor.connection.commit()
        except Exception as e:
            LOGGER.exception(e)
            raise Exception(e)
        finally:
            if cursor is not None:
                cursor.close()
        return results

    def upsert_zillow_listings(self, zillow_listings_tuple):
        cursor = None
        try:
            cursor = self.db_handle.cursor(MySQLdb.cursors.DictCursor)
            value_list = [{
                "listing_id": zillow_listing.listing_id,
                "detail_url": zillow_listing.detail_url,
                "street_address": zillow_listing.street_address,
                "city": zillow_listing.city,
                "state": zillow_listing.state,
                "building_name": zillow_listing.building_name,
                "zip_code": zillow_listing.zip_code,
                "beds": zillow_listing.beds,
                "baths": zillow_listing.baths,
                "lat": zillow_listing.lat,
                "lng": zillow_listing.lng,
                "sqft": zillow_listing.sqft,
                "price": zillow_listing.price,
            } for zillow_listing in zillow_listings_tuple]
            cursor.executemany(self.QUERY_UPSERT, value_list)
            cursor.connection.commit()
        except Exception as e:
            LOGGER.exception(e)
            raise StoreListingResultsException(e)
        finally:
            if cursor is not None:
                cursor.close()

    def close(self):
        self.db_handle.close()

def _parse_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

    command_subparser = parser.add_subparsers(dest='sub_command')
    command_subparser.required = True

    command_subparser.add_parser('upsert')
    command_subparser.add_parser('select')

    return parser.parse_args()

def _main():
    options = _parse_args()

    zillow_mysql = ZillowMySql()

    if options.sub_command == 'upsert':
        from rent_price_collection.app.zillow_rpc import ZillowListing
        zillow_listings_tuple = [
            ZillowListing(listing_id=u'4062640115', detail_url=u'test/url/test', street_address=u'1226 Haight St',
                        city=u'San Francisco', state=u'CA', building_name="Hawthorne Apartments", zip_code=94117,
                        beds=3, baths=1, lat=37.77085, lng=-122.44257, sqft=2400, price=5500),
            ZillowListing(listing_id=u'4062648395', detail_url=u'test/url/test', street_address=u'471 Colon Ave',
                        city=u'San Francisco', state=u'CA', building_name="Hawthorne Apartments", zip_code=94127,
                        beds=4, baths=4, lat=37.733303, lng=-122.45824, sqft=2450, price=6450),
        ]
        zillow_mysql.upsert_zillow_listings(zillow_listings_tuple)
    elif options.sub_command == 'select':
        results = zillow_mysql.select_zillow_listings(limit=100)
        LOGGER.info(results)


if __name__ == '__main__':
    logging.basicConfig(format=DEFAULT_LOG_FORMAT_STRING, datefmt="%Y-%m-%d %H:%M:%S", level=logging.INFO)
    _main()
