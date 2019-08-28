"""
:author: Henley Kuang
:since: 04/27/2019
"""

import logging
import json
import socket
import ssl
import xml.etree.ElementTree as ET

from httplib import HTTPSConnection

from rent_price_collection.utils.exceptions import (
    APIResponseException,
    APIRequestTimedOutException,
)

LOGGER = logging.getLogger(__name__)

DEFAULT_USERAGENT = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36";

class RestClient(object):

    __slots__ = ('proxy_ip', 'proxy_port', 'proxy_user', 'proxy_pass', 'user_agent', 'request_timeout')

    def __init__(self, proxy_ip=None, proxy_port=None,
                 proxy_user=None, proxy_pass=None,
                 user_agent=DEFAULT_USERAGENT, request_timeout=60):
        self.proxy_ip = proxy_ip
        self.proxy_port = proxy_port
        self.proxy_user = proxy_user
        self.proxy_pass = proxy_pass
        self.user_agent = user_agent
        self.request_timeout = request_timeout

    def request(self, domain, path, method, data=None):
        if self.proxy_ip and self.proxy_port:
            connection = HTTPSConnection(self.proxy_ip, self.proxy_port, timeout=self.request_timeout)
            connection.set_tunnel(domain)
        else:
            connection = HTTPSConnection(domain, timeout=self.request_timeout)
        response_content = None
        try:
            headers = {'User-Agent': self.user_agent}
            if self.proxy_user and self.proxy_pass:
                base64_bytes = b64encode(
                    ("%s:%s" % (self.proxy_user, self.proxy_pass)).encode("ascii")
                ).decode("ascii")
                headers['Authorization'] = 'Basic %s' % base64_bytes
            connection.request(method, path, headers=headers, body=data)
            response = connection.getresponse()
            # In python3, defaultencoding is utf-8.
            # In python2, defaultencoding is ascii.
            response_content = response.read()
            try:
                # JSON
                return json.loads(response_content.decode('utf-8'))
            except:
                # XML
                return ET.fromstring(response_content)
        except ValueError as e:
            LOGGER.error("Value error (%s) in response_content: %s", e, response_content)
            raise APIResponseException(response_content)
        except (socket.timeout, ssl.SSLError) as e:
            LOGGER.error("Timed out request on %s, %s: %s", method, path, e)
            raise APIRequestTimedOutException("Timed out request: %s" % e)
        finally:
            connection.close()

    def get(self, domain, path):
        return self.request(domain, path, 'GET')

    def post(self, domain, path, data):
        if isinstance(data, str):
            data_str = data
        else:
            data_str = json.dumps(data)
        return self.request(path, 'POST', data_str)

def get_client(proxy_ip=None, proxy_port=None, proxy_user=None, proxy_pass=None):
    return RestClient(proxy_ip, proxy_port, proxy_user, proxy_pass)
