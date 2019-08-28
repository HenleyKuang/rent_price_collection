"""
:author: Henley Kuang
:since: 04/27/2019
"""
import time

from functools import wraps

def retry_decorator(exceptionstocheck, tries=4, delay=3, backoff=2, logger=None):
    """
    Retry calling the decorated function using an exponential backoff.
    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry

    :param ExceptionToCheck: the exception to check. may be a tuple of
        exceptions to check
    :type ExceptionToCheck: Exception or tuple
    :param tries: number of times to try (not retry) before giving up
    :type tries: int
    :param delay: initial delay between retries in seconds
    :type delay: int
    :param backoff: backoff multiplier e.g. value of 2 will double the delay
        each retry
    :type backoff: int
    :param logger: logger to use. If None, use getLogger call
    :type logger: logging.Logger instance
    """

    if logger is None:
        try:
            logger = logging.getLogger(__name__)
            if not logger.root.handlers:
                # no handler was set up
                logger = None
        except Exception:
            logger = None

    def deco_retry(f):
        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except exceptionstocheck as e:
                    msg = "[%s][%s] %s, Retrying in %d seconds..." % (f.__name__, type(e).__name__, str(e), mdelay)
                    if logger is not None:
                        logger.warning(msg, exc_info=1)
                    else:
                        print(msg)
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry