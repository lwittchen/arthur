"""
Generic calculations 
"""
import logging
import numpy as np
import pytz
from datetime import datetime
from functools import wraps
from time import time

#### setup
logger = logging.getLogger(__name__)


def parse_unix_ts(timestamp: int) -> datetime:
    """
    convert unix timestamp to datetime object and localize it to 
    CET timezone
    """
    tz_utc = pytz.utc
    temp_datetime = datetime.utcfromtimestamp(int(timestamp))
    return tz_utc.localize(temp_datetime)


def get_log_msg(results: dict) -> str:
    """
    Merge all results to one large string to log the results in the command line
    """
    str_fmt = "{:<12}".format
    num_fmt = "{:<6.2f}".format
    sep = f"\n {'*'*50}"
    msg = ""
    for key, item in results.items():
        key_str = str_fmt(key)
        if item is not None:
            val_str = num_fmt(item) if isinstance(item, float) else str_fmt(item)
        else:
            val_str = "None"
        msg += f"\n {key_str}: {val_str}"
    return msg + sep


def timing(func):
    @wraps(func)
    def wrap(*args, **kwargs):
        ts = time()
        result = func(*args, **kwargs)
        te = time()
        print(f"func:{func.__name__} took: {te-ts:2.4f} sec")
        return result

    return wrap
