=====================
Rent Price Collection
=====================
By Henley Kuang

Pre-requisites
--------------

.. code-block:: bash

    https://www.python.org/downloads/release/python-2712/
    https://pip.pypa.io/en/stable/installing/
    https://sourceforge.net/projects/mysql-python/
    https://nodejs.org/en/download/
    https://www.atlassian.com/git/tutorials/install-git#windows

Installation
------------

.. code-block:: bash

    git clone https://github.com/HenleyKuang/rent_price_collection.git
    cd rent_price_collection
    pip install -r requirements.txt

Configuration
-------------

Set up your configuration for email notifications & connection for mysql storage

.. code-block:: bash

    # To send gmail notifications
    GMAIL_USER = '<user>@gmail.com'
    GMAIL_PASSWORD = '<password_here>'
    GMAIL_SENT_TO_EMAILS = ['<user>@gmail.com'] # [..., ..., ...]

    # mysql connection for storage of crawled data
    MYSQL_HOST = '<mysql_host>'
    MYSQL_USER = '<mysql_user>'
    MYSQL_PASS = '<mysql_pass>'
    MYSQL_DB = '<mysql_db>'
    MYSQL_PORT = <mysql_port>

Create the MySql table for Trulia RPC Data

.. code-block:: bash

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

Options
-------

.. csv-table::
    :header: "Name", "Description", "Required", "Type", "Accepted Values", "Default Value"
    :widths: 30, 75, 5, 5, 5, 5

    "--location", "Location Name", "Yes", "String"
    "--start-page-num", "Page number to start crawling from", "No", "Integer", "", "1"
    "--proxy-ip", "Proxy Host [Optional]", "No", "String", "", ""
    "--proxy-port", "Proxy Port [Optional]", "No", "Integer", "", ""
    "--proxy-user", "Proxy User Auth for proxy [Optional]", "No", "String", "", ""
    "--proxy-pass", "Proxy Password Auth for proxy [Optiona]", "No", "String", "", ""

How to Run
----------

1. Collect Data

.. code-block:: bash

    python .\rent_price_collection\app\trulia_rpc.py --location "Hanover Park,IL"
    python .\rent_price_collection\app\trulia_rpc.py --location "Bolingbrook,IL"
    python .\rent_price_collection\app\trulia_rpc.py --location "Round Lake,IL"
    python .\rent_price_collection\app\trulia_rpc.py --location-file "location_file.txt"

    python .\rent_price_collection\app\zillow_rpc.py --location "Round Lake,IL"
    python .\rent_price_collection\app\zillow_rpc.py --location-file "location_file.txt"

2. Post Process Data (Merge data into 1 table)

.. code-block:: bash

    python .\rent_price_collection\storage\all_listings_mysql.py union

3. Run API & Database UI

.. code-block:: bash

    .\rent_price_collection\scripts\run_api_and_ui.sh
