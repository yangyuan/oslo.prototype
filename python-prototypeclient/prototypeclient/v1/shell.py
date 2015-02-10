import copy
import functools
import six

from oslo_utils import encodeutils
from oslo_utils import strutils

from prototypeclient import utils
import prototypeclient.v1.sample


_bool_strict = functools.partial(strutils.bool_from_string, strict=True)


@utils.arg('--param', metavar='<DEBUG>', dest='sample_param', help='A Sample Param')
def do_sample_debug(client, args):

    print args.sample_param

    print client.sample.debug()
