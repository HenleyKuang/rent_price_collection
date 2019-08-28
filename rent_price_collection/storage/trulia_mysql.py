"""
:author: Henley Kuang
:since: 04/28/2019

Table SCHEMA:
CREATE TABLE `trulia_listings` (
	`listing_id` bigint(20) unsigned NOT NULL,
	`card_url` varchar(255) NOT NULL,
	`street_address` varchar(255) NOT NULL,
	`city` varchar(255) NOT NULL,
	`state` varchar(255) NOT NULL,
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

class TruliaMySql():

    DB_TABLE_NAME = 'trulia_listings'
    QUERY_SELECT = '''select * from {table_name}'''.format(table_name=DB_TABLE_NAME)
    QUERY_UPSERT = '''insert into {table_name}
(listing_id, card_url, street_address, city, state, zip_code, beds, baths, lat, lng, sqft, price)
VALUES (
%(listing_id)s,
%(card_url)s,
%(street_address)s,
%(city)s,
%(state)s,
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

    def select_trulia_listings(self, limit=None):
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

    def upsert_trulia_listings(self, trulia_listings_tuple):
        cursor = None
        try:
            cursor = self.db_handle.cursor(MySQLdb.cursors.DictCursor)
            value_list = [{
                "listing_id": trulia_listing.listing_id,
                "card_url": trulia_listing.card_url,
                "street_address": trulia_listing.street_address,
                "city": trulia_listing.city,
                "state": trulia_listing.state,
                "zip_code": trulia_listing.zip_code,
                "beds": trulia_listing.beds,
                "baths": trulia_listing.baths,
                "lat": trulia_listing.lat,
                "lng": trulia_listing.lng,
                "sqft": trulia_listing.sqft,
                "price": trulia_listing.price,
            } for trulia_listing in trulia_listings_tuple]
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

    trulia_mysql = TruliaMySql()

    if options.sub_command == 'upsert':
        from rent_price_collection.app.trulia_rpc import TruliaListing
        trulia_listings_tuple = [
            TruliaListing(listing_id=u'4062640115', card_url=u'test/url/test', street_address=u'1226 Haight St',
                        city=u'San Francisco', state=u'CA', zip_code=94117,
                        beds=3, baths=1, lat=37.77085, lng=-122.44257, sqft=2400, price=5500),
            TruliaListing(listing_id=u'4062648395', card_url=u'test/url/test', street_address=u'471 Colon Ave',
                        city=u'San Francisco', state=u'CA', zip_code=94127,
                        beds=4, baths=4, lat=37.733303, lng=-122.45824, sqft=2450, price=6450),
        ]
        trulia_mysql.upsert_trulia_listings(trulia_listings_tuple)
    elif options.sub_command == 'select':
        results = trulia_mysql.select_trulia_listings(limit=100)
        LOGGER.info(results)


if __name__ == '__main__':
    logging.basicConfig(format=DEFAULT_LOG_FORMAT_STRING, datefmt="%Y-%m-%d %H:%M:%S", level=logging.INFO)
    _main()
