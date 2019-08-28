"""
:author: Henley Kuang
:since: 04/28/2019
"""

import logging
import smtplib

from rent_price_collection.utils.config import DEFAULT_LOG_FORMAT_STRING
from rent_price_collection.utils.exceptions import (
    EmailSendingException,
)

LOGGER = logging.getLogger(__name__)

GMAIL_SMTP_HOST = 'smtp.gmail.com'
GMAIL_PORT = 465

# https://support.google.com/accounts/answer/6010255?
# Read this article to learn how to activate automatic email priveledges to your GMail account
# https://www.google.com/settings/security/lesssecureapps
# This 2nd link is to allow the python app to use the gmail

class GMailNotify(object):

    def __init__(self, gmail_user, gmail_password):
        self.gmail_user = gmail_user
        self.gmail_password = gmail_password

    def send_email(self, to_emails_list, subject, body):
        try:
            server = smtplib.SMTP_SSL(GMAIL_SMTP_HOST, GMAIL_PORT)
            server.ehlo()
            server.login(self.gmail_user, self.gmail_password)
            message = 'Subject: {}\n\n{}'.format(subject, body)
            server.sendmail(
                from_addr=self.gmail_user,
                to_addrs=to_emails_list,
                msg=message,
            )
            server.close()
            LOGGER.info("Email sent to: %s", to_emails_list)
        except Exception as e:
            LOGGER.error("Email failed to send to: %s | Error: %s", to_emails_list, e)
            raise EmailSendingException(e)
