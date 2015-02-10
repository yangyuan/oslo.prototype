import contextlib
import datetime
import functools
import hashlib
import hmac
import inspect
import os
import pyclbr
import random
import re
import shutil
import socket
import struct
import sys
import tempfile
from xml.sax import saxutils

import eventlet
import netaddr
from oslo_config import cfg
import oslo_messaging as messaging
from oslo_utils import excutils
from oslo_utils import importutils
from oslo_utils import timeutils
from oslo_concurrency import lockutils
from oslo_concurrency import processutils
import six

from prototype.common import exception
from prototype.common.i18n import _, _LE, _LW
from oslo_log import log as logging


monkey_patch_opts = [
    cfg.BoolOpt('monkey_patch',
                default=False,
                help='Whether to log monkey patching'),
    cfg.ListOpt('monkey_patch_modules',
                default=[],
                help='List of modules/decorators to monkey patch'),
]
utils_opts = [
    cfg.IntOpt('password_length',
               default=12,
               help='Length of generated instance admin passwords'),
    cfg.StrOpt('rootwrap_config',
               default="rootwrap.conf",
               help='Path to the rootwrap configuration file to use for '
                    'running commands as root'),
    cfg.StrOpt('tempdir',
               help='Explicitly specify the temporary working directory'),
]

""" This group is for very specific reasons.

If you're:
- Working around an issue in a system tool (e.g. libvirt or qemu) where the fix
  is in flight/discussed in that community.
- The tool can be/is fixed in some distributions and rather than patch the code
  those distributions can trivially set a config option to get the "correct"
  behavior.
This is a good place for your workaround.

Please use with care!
Document the BugID that your workaround is paired with."""

workarounds_opts = [
    cfg.BoolOpt('disable_rootwrap',
                default=False,
                help='This option allows a fallback to sudo for performance '
                     'reasons. For example see '
                     'https://bugs.launchpad.net/prototype/+bug/1415106'),
    ]
CONF = cfg.CONF
CONF.register_opts(monkey_patch_opts)
CONF.register_opts(utils_opts)
CONF.register_opts(workarounds_opts, group='workarounds')

LOG = logging.getLogger(__name__)

# used in limits
TIME_UNITS = {
    'SECOND': 1,
    'MINUTE': 60,
    'HOUR': 3600,
    'DAY': 86400
}


def monkey_patch():
    """If the CONF.monkey_patch set as True,
    this function patches a decorator
    for all functions in specified modules.
    You can set decorators for each modules
    using CONF.monkey_patch_modules.
    The format is "Module path:Decorator function".
    Example:
    'prototype.api.ec2.cloud:prototype.notifications.notify_decorator'

    Parameters of the decorator is as follows.
    (See prototype.notifications.notify_decorator)

    name - name of the function
    function - object of the function
    """
    # If CONF.monkey_patch is not True, this function do nothing.
    if not CONF.monkey_patch:
        return
    # Get list of modules and decorators
    for module_and_decorator in CONF.monkey_patch_modules:
        module, decorator_name = module_and_decorator.split(':')
        # import decorator function
        decorator = importutils.import_class(decorator_name)
        __import__(module)
        # Retrieve module information using pyclbr
        module_data = pyclbr.readmodule_ex(module)
        for key in module_data.keys():
            # set the decorator for the class methods
            if isinstance(module_data[key], pyclbr.Class):
                clz = importutils.import_class("%s.%s" % (module, key))
                for method, func in inspect.getmembers(clz, inspect.ismethod):
                    setattr(clz, method,
                        decorator("%s.%s.%s" % (module, key, method), func))
            # set the decorator for the function
            if isinstance(module_data[key], pyclbr.Function):
                func = importutils.import_class("%s.%s" % (module, key))
                setattr(sys.modules[module], key,
                    decorator("%s.%s" % (module, key), func))
                    
@contextlib.contextmanager
def tempdir(**kwargs):
    argdict = kwargs.copy()
    if 'dir' not in argdict:
        argdict['dir'] = CONF.tempdir
    tmpdir = tempfile.mkdtemp(**argdict)
    try:
        yield tmpdir
    finally:
        try:
            shutil.rmtree(tmpdir)
        except OSError as e:
            LOG.error(_LE('Could not remove tmpdir: %s'), e)
            

def utf8(value):
    """Try to turn a string into utf-8 if possible.

    Code is directly from the utf8 function in
    http://github.com/facebook/tornado/blob/master/tornado/escape.py

    """
    if isinstance(value, unicode):
        return value.encode('utf-8')
    assert isinstance(value, str)
    return value
    

def _get_root_helper():
    if CONF.workarounds.disable_rootwrap:
        cmd = 'sudo'
    else:
        cmd = 'sudo prototype-rootwrap %s' % CONF.rootwrap_config
    return cmd


def execute(*cmd, **kwargs):
    """Convenience wrapper around oslo's execute() method."""
    if 'run_as_root' in kwargs and 'root_helper' not in kwargs:
        kwargs['root_helper'] = _get_root_helper()
    return processutils.execute(*cmd, **kwargs)
    
class LazyPluggable(object):
    """A pluggable backend loaded lazily based on some value."""

    def __init__(self, pivot, config_group=None, **backends):
        self.__backends = backends
        self.__pivot = pivot
        self.__backend = None
        self.__config_group = config_group

    def __get_backend(self):
        if not self.__backend:
            if self.__config_group is None:
                backend_name = CONF[self.__pivot]
            else:
                backend_name = CONF[self.__config_group][self.__pivot]
            if backend_name not in self.__backends:
                msg = _('Invalid backend: %s') % backend_name
                raise exception.NovaException(msg)

            backend = self.__backends[backend_name]
            if isinstance(backend, tuple):
                name = backend[0]
                fromlist = backend[1]
            else:
                name = backend
                fromlist = backend

            self.__backend = __import__(name, None, None, fromlist)
        return self.__backend

    def __getattr__(self, key):
        backend = self.__get_backend()
        return getattr(backend, key)
