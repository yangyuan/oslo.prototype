import functools
import sys

from oslo_config import cfg
from oslo_utils import excutils
import webob.exc

from prototype.common.i18n import _, _LE
from oslo_log import log as logging

LOG = logging.getLogger(__name__)

CONF = cfg.CONF




class PrototypeException(Exception):
    """Base Prototype Exception

    To correctly use this class, inherit from it and define
    a 'msg_fmt' property. That msg_fmt will get printf'd
    with the keyword arguments provided to the constructor.

    """
    msg_fmt = _("An unknown exception occurred.")
    code = 500
    headers = {}
    safe = False

    def __init__(self, message=None, **kwargs):
        self.kwargs = kwargs

        if 'code' not in self.kwargs:
            try:
                self.kwargs['code'] = self.code
            except AttributeError:
                pass

        if not message:
            try:
                message = self.msg_fmt % kwargs

            except Exception:
                exc_info = sys.exc_info()
                # kwargs doesn't match a variable in the message
                # log the issue and the kwargs
                LOG.exception(_LE('Exception in string format operation'))
                for name, value in kwargs.iteritems():
                    LOG.error("%s: %s" % (name, value))    # noqa

                if CONF.fatal_exception_format_errors:
                    raise exc_info[0], exc_info[1], exc_info[2]
                else:
                    # at least get the core message out if something happened
                    message = self.msg_fmt

        super(PrototypeException, self).__init__(message)

    def format_message(self):
        # NOTE(mrodden): use the first argument to the python Exception object
        # which should be our full PrototypeException message, (see __init__)
        return self.args[0]