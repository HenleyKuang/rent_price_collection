"""
:author: Henley Kuang
:since: 05/12/2019

Table SCHEMA:
CREATE TABLE `all_listings` (
    `id` varchar(255) NOT NULL,
    `source` varchar(255) NOT NULL,
    `url` varchar(255) NOT NULL,
    `street_address` varchar(255) NOT NULL,
    `city` varchar(255) NOT NULL,
    `state` varchar(255) NOT NULL,
    `zip_code` varchar(10) NOT NULL,
    `beds` varchar(255) NOT NULL,
    `baths` varchar(255) NOT NULL,
    `sqft` varchar(255) NOT NULL,
    `price` varchar(255) NOT NULL,
    `date_collected` datetime DEFAULT CURRENT_TIMESTAMP,
    `date_updated` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 ROW_FORMAT=COMPRESSED;
"""

import argparse
import logging
import MySQLdb

from collections import namedtuple

from rent_price_collection.utils.config import (
    DEFAULT_LOG_FORMAT_STRING,
    MYSQL_HOST,
    MYSQL_USER,
    MYSQL_PASS,
    MYSQL_DB,
    MYSQL_PORT,
)

from rent_price_collection.utils.exceptions import (
    MergeQueryAllListingsException,
)

LOGGER = logging.getLogger(__name__)

SEARCH_PARAMETERS = ['source', 'url', 'street_address', 'city', 'state', 'zip_code',
                    'beds', 'baths', 'sqft', 'price',
                    'date_collected', 'date_updated']
SearchParameterObject = namedtuple('SearchParameterObject', SEARCH_PARAMETERS)

class AllListingsMySql():

    DB_TABLE_NAME = 'all_listings'
    QUERY_SELECT = '''select * from {table_name}'''.format(table_name=DB_TABLE_NAME)
    QUERY_COUNT = '''select count(1) from {table_name}'''.format(table_name=DB_TABLE_NAME)
    QUERY_UNION = '''insert into {table_name}
select * from (
SELECT
CONCAT("zillow-", zillow.listing_id) as `id`,
"zillow" as `source`,
`detail_url` as `url`,
`street_address`,
`city`,
`state`,
`zip_code`,
`beds`,
`baths`,
`sqft`,
`price`,
`date_collected`,
`date_updated`
FROM zillow_listings as zillow
UNION ALL
SELECT
CONCAT("trulia-", trulia.listing_id) as `id`,
"trulia" as `source`,
CONCAT("https://www.trulia.com", trulia.card_url) as `url`,
`street_address`,
`city`,
`state`,
`zip_code`,
`beds`,
`baths`,
`sqft`,
`price`,
`date_collected`,
`date_updated`
FROM trulia_listings as trulia
) all_l ON DUPLICATE KEY UPDATE date_updated=all_l.date_updated;'''.format(table_name=DB_TABLE_NAME)

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

    def union_listings(self):
        cursor = None
        result = None
        try:
            cursor = self.db_handle.cursor(MySQLdb.cursors.DictCursor)
            result = cursor.execute(self.QUERY_UNION)
            cursor.connection.commit()
        except Exception as e:
            LOGGER.exception(e)
            raise MergeQueryAllListingsException(e)
        finally:
            if cursor is not None:
                cursor.close()
        return result

    def search_listings(self, search_parameter_object, limit=20, offset=0, sortby="date_updated", desc=True):
        cursor = None
        results = None
        count = None
        try:
            cursor = self.db_handle.cursor(MySQLdb.cursors.DictCursor)
            query_select = self.QUERY_SELECT
            query_count = self.QUERY_COUNT
            where_clauses = []
            for name, value in search_parameter_object._asdict().iteritems():
                if value is not None:
                    where_clauses.append('{name} like \"%{value}%\"'.format(name=name, value=value))
            if len(where_clauses) > 0:
                where_clause_str = " where %s" % " and ".join(where_clauses)
                query_select += where_clause_str
                query_count += where_clause_str
            query_select += " order by %s" % sortby
            if desc:
                query_select += " desc"
            query_select += " limit %s" % limit
            query_select += " offset %s" % offset
            cursor.execute(query_select)
            results = cursor.fetchall()
            cursor.execute(query_count)
            count = cursor.fetchone()["count(1)"]
            cursor.connection.commit()
        except Exception as e:
            LOGGER.exception("Query: %s | Exception: %s", query_select, e)
            raise Exception(e)
        finally:
            if cursor is not None:
                cursor.close()
        return {"listings": results, "count": count}

    def select_all_listings(self, limit=None):
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

    def close(self):
        self.db_handle.close()

def _parse_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

    command_subparser = parser.add_subparsers(dest='sub_command')
    command_subparser.required = True

    command_subparser.add_parser('union')
    command_subparser.add_parser('search')
    command_subparser.add_parser('select')

    return parser.parse_args()

def _main():
    options = _parse_args()

    all_listings_mysql = AllListingsMySql()

    if options.sub_command == 'union':
        count = all_listings_mysql.union_listings()
        LOGGER.info("Union complete. Total merged: %s", count)
    elif options.sub_command == 'search':
        search_parameter_object = SearchParameterObject(
            source="zill",
            url=None,
            street_address=None,
            city=None,
            state=None,
            zip_code=None,
            beds=None,
            baths=None,
            sqft=None,
            price=None,
            date_collected=None,
            date_updated=None,
        )
        results = all_listings_mysql.search_listings(search_parameter_object)
        LOGGER.info(results)
    elif options.sub_command == 'select':
        results = all_listings_mysql.select_all_listings(limit=100)
        LOGGER.info(results)


if __name__ == '__main__':
    logging.basicConfig(format=DEFAULT_LOG_FORMAT_STRING, datefmt="%Y-%m-%d %H:%M:%S", level=logging.INFO)
    _main()
