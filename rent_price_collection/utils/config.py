"""
:author: Henley Kuang
:since: 04/27/2019
"""

DEFAULT_LOG_FORMAT_STRING = "%(asctime)s (%(filename)s, %(funcName)s, %(lineno)d) [%(levelname)8s] %(message)s"

# To send gmail notifications
GMAIL_USER = '<user>@gmail.com'
GMAIL_PASSWORD = '<password_here>'
GMAIL_SENT_TO_EMAILS = ['<user>@gmail.com'] # [..., ..., ...]

# mysql connection for storage of crawled data
MYSQL_HOST = '<mysql_host>'
MYSQL_USER = '<mysql_user>'
MYSQL_PASS = '<mysql_pass>'
MYSQL_DB = '<mysql_db>'
MYSQL_PORT = 3306

SLEEP_BETWEEN_LOCATIONS_MIN = 10
SLEEP_BETWEEN_LOCATIONS_MAX = 30

SLEEP_BETWEEN_API_REQUESTS_MIN = 5
SLEEP_BETWEEN_API_REQUESTS_MAX = 10


ZILLOW_LATITUDE_MAP_DIFF = -0.21148681640624
ZILLOW_LONGITUDE_MAP_DIFF = 0.12619630485463

ZILLOW_API_KEY = "X1-ZWz17ym4xojpqj_9prl8"
