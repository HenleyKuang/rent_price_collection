"""
:author: Henley Kuang
:since: 04/27/2019
"""

class APIResponseException(Exception):
    pass

class APIRequestTimedOutException(Exception):
    pass

class EmailSendingException(Exception):
    pass

class MergeQueryAllListingsException(Exception):
    pass

class ResponseMissingKeyException(Exception):
    pass

# TODO: merge into ResponseMissingKeyException
class ResponseMissingPageCardsKeyException(Exception):
    pass

# TODO: merge into ResponseMissingKeyException
class ResponseMissingPageKeyException(Exception):
    pass

class ResponseSuccessFalseException(Exception):
    pass

class StoreListingResultsException(Exception):
    pass

class ZeroListingsReturnedException(Exception):
    pass
