from __future__ import print_function
import re
import six
import os
import sys

from oslo_utils import encodeutils
def exit(msg='', exit_code=1):
    if msg:
        print(encodeutils.safe_decode(msg), file=sys.stderr)
    sys.exit(exit_code)

def env(*vars, **kwargs):
    """Search for the first defined of possibly many env vars
    Returns the first environment variable defined in vars, or
    returns the default defined in kwargs.
    """
    for v in vars:
        value = os.environ.get(v)
        if value:
            return value
    return kwargs.get('default', '')

def arg(*args, **kwargs):
    def _decorator(func):
        # Because of the semantics of decorator composition if we just append
        # to the options list positional options will appear to be backwards.
        func.__dict__.setdefault('arguments', []).insert(0, (args, kwargs))
        return func
    return _decorator


def strip_version(endpoint):
    """Strip version from the last component of endpoint if present."""
    if not isinstance(endpoint, six.string_types):
        raise ValueError("Expected endpoint")

    version = None
    # Get rid of trailing '/' if present
    endpoint = endpoint.rstrip('/')
    url_bits = endpoint.split('/')
    # regex to match 'v1' or 'v2.0' etc
    if re.match('v\d+\.?\d*', url_bits[-1]):
        version = float(url_bits[-1].lstrip('v'))
        endpoint = '/'.join(url_bits[:-1])
    return endpoint, version

def exception_to_str(exc):
    try:
        error = six.text_type(exc)
    except UnicodeError:
        try:
            error = str(exc)
        except UnicodeError:
            error = ("Caught '%(exception)s' exception." %
                     {"exception": exc.__class__.__name__})
    return encodeutils.safe_decode(error, errors='ignore')