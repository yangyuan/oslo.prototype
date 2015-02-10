# Copyright 2010 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import collections
import functools
import itertools
import os
import re

from oslo_config import cfg
import six.moves.urllib.parse as urlparse
import webob
from webob import exc

from prototype.common.i18n import _,_LE,_LW
from oslo_log import log as logging

osapi_opts = [
    cfg.IntOpt('osapi_max_limit', default=1000, help='The maximum number of items returned in a single response from a collection resource'),
]
CONF = cfg.CONF
CONF.register_opts(osapi_opts)

LOG = logging.getLogger(__name__)


# NOTE(cyeoh): A common regexp for acceptable names (user supplied)
# that we want all new extensions to conform to unless there is a very
# good reason not to.
VALID_NAME_REGEX = re.compile("^(?! )[\w. _-]+(?<! )$", re.UNICODE)

XML_NS_V11 = 'http://docs.openstack.org/compute/api/v1.1'




def get_sort_params(input_params, default_key='created_at',
                    default_dir='desc'):
    """Retrieves sort keys/directions parameters.

    Processes the parameters to create a list of sort keys and sort directions
    that correspond to the 'sort_key' and 'sort_dir' parameter values. These
    sorting parameters can be specified multiple times in order to generate
    the list of sort keys and directions.

    The input parameters are not modified.

    :param input_params: webob.multidict of request parameters (from
                         prototype.wsgi.Request.params)
    :param default_key: default sort key value, added to the list if no
                        'sort_key' parameters are supplied
    :param default_dir: default sort dir value, added to the list if no
                        'sort_dir' parameters are supplied
    :returns: list of sort keys, list of sort dirs
    """
    params = input_params.copy()
    sort_keys = []
    sort_dirs = []
    while 'sort_key' in params:
        sort_keys.append(params.pop('sort_key').strip())
    while 'sort_dir' in params:
        sort_dirs.append(params.pop('sort_dir').strip())
    if len(sort_keys) == 0 and default_key:
        sort_keys.append(default_key)
    if len(sort_dirs) == 0 and default_dir:
        sort_dirs.append(default_dir)
    return sort_keys, sort_dirs


def get_pagination_params(request):
    """Return marker, limit tuple from request.

    :param request: `wsgi.Request` possibly containing 'marker' and 'limit'
                    GET variables. 'marker' is the id of the last element
                    the client has seen, and 'limit' is the maximum number
                    of items to return. If 'limit' is not specified, 0, or
                    > max_limit, we default to max_limit. Negative values
                    for either marker or limit will cause
                    exc.HTTPBadRequest() exceptions to be raised.

    """
    params = {}
    if 'limit' in request.GET:
        params['limit'] = _get_int_param(request, 'limit')
    if 'page_size' in request.GET:
        params['page_size'] = _get_int_param(request, 'page_size')
    if 'marker' in request.GET:
        params['marker'] = _get_marker_param(request)
    return params


def _get_int_param(request, param):
    """Extract integer param from request or fail."""
    try:
        int_param = int(request.GET[param])
    except ValueError:
        msg = _('%s param must be an integer') % param
        raise webob.exc.HTTPBadRequest(explanation=msg)
    if int_param < 0:
        msg = _('%s param must be positive') % param
        raise webob.exc.HTTPBadRequest(explanation=msg)
    return int_param


def _get_marker_param(request):
    """Extract marker id from request or fail."""
    return request.GET['marker']


def limited(items, request, max_limit=CONF.osapi_max_limit):
    """Return a slice of items according to requested offset and limit.

    :param items: A sliceable entity
    :param request: ``wsgi.Request`` possibly containing 'offset' and 'limit'
                    GET variables. 'offset' is where to start in the list,
                    and 'limit' is the maximum number of items to return. If
                    'limit' is not specified, 0, or > max_limit, we default
                    to max_limit. Negative values for either offset or limit
                    will cause exc.HTTPBadRequest() exceptions to be raised.
    :kwarg max_limit: The maximum number of items to return from 'items'
    """
    try:
        offset = int(request.GET.get('offset', 0))
    except ValueError:
        msg = _('offset param must be an integer')
        raise webob.exc.HTTPBadRequest(explanation=msg)

    try:
        limit = int(request.GET.get('limit', max_limit))
    except ValueError:
        msg = _('limit param must be an integer')
        raise webob.exc.HTTPBadRequest(explanation=msg)

    if limit < 0:
        msg = _('limit param must be positive')
        raise webob.exc.HTTPBadRequest(explanation=msg)

    if offset < 0:
        msg = _('offset param must be positive')
        raise webob.exc.HTTPBadRequest(explanation=msg)

    limit = min(max_limit, limit or max_limit)
    range_end = offset + limit
    return items[offset:range_end]


def get_limit_and_marker(request, max_limit=CONF.osapi_max_limit):
    """get limited parameter from request."""
    params = get_pagination_params(request)
    limit = params.get('limit', max_limit)
    limit = min(max_limit, limit)
    marker = params.get('marker')

    return limit, marker


def get_id_from_href(href):
    """Return the id or uuid portion of a url.

    Given: 'http://www.foo.com/bar/123?q=4'
    Returns: '123'

    Given: 'http://www.foo.com/bar/abc123?q=4'
    Returns: 'abc123'

    """
    return urlparse.urlsplit("%s" % href).path.split('/')[-1]


def remove_version_from_href(href):
    """Removes the first api version from the href.

    Given: 'http://www.prototype.com/v1.1/123'
    Returns: 'http://www.prototype.com/123'

    Given: 'http://www.prototype.com/v1.1'
    Returns: 'http://www.prototype.com'

    """
    parsed_url = urlparse.urlsplit(href)
    url_parts = parsed_url.path.split('/', 2)

    # NOTE: this should match vX.X or vX
    expression = re.compile(r'^v([0-9]+|[0-9]+\.[0-9]+)(/.*|$)')
    if expression.match(url_parts[1]):
        del url_parts[1]

    new_path = '/'.join(url_parts)

    if new_path == parsed_url.path:
        LOG.debug('href %s does not contain version' % href)
        raise ValueError(_('href %s does not contain version') % href)

    parsed_url = list(parsed_url)
    parsed_url[2] = new_path
    return urlparse.urlunsplit(parsed_url)


def dict_to_query_str(params):
    # TODO(throughnothing): we should just use urllib.urlencode instead of this
    # But currently we don't work with urlencoded url's
    param_str = ""
    for key, val in params.iteritems():
        param_str = param_str + '='.join([str(key), str(val)]) + '&'

    return param_str.rstrip('&')


class ViewBuilder(object):
    """Model API responses as dictionaries."""

    def _get_project_id(self, request):
        """Get project id from request url if present or empty string
        otherwise
        """
        project_id = request.environ["prototype.context"].project_id
        if project_id in request.url:
            return project_id
        return ''

    def _get_links(self, request, identifier, collection_name):
        return [{
            "rel": "self",
            "href": self._get_href_link(request, identifier, collection_name),
        },
        {
            "rel": "bookmark",
            "href": self._get_bookmark_link(request,
                                            identifier,
                                            collection_name),
        }]

    def _get_next_link(self, request, identifier, collection_name):
        """Return href string with proper limit and marker params."""
        params = request.params.copy()
        params["marker"] = identifier
        prefix = self._update_compute_link_prefix(request.application_url)
        url = os.path.join(prefix,
                           self._get_project_id(request),
                           collection_name)
        return "%s?%s" % (url, dict_to_query_str(params))

    def _get_href_link(self, request, identifier, collection_name):
        """Return an href string pointing to this object."""
        prefix = self._update_compute_link_prefix(request.application_url)
        return os.path.join(prefix,
                            self._get_project_id(request),
                            collection_name,
                            str(identifier))

    def _get_bookmark_link(self, request, identifier, collection_name):
        """Create a URL that refers to a specific resource."""
        base_url = remove_version_from_href(request.application_url)
        base_url = self._update_compute_link_prefix(base_url)
        return os.path.join(base_url,
                            self._get_project_id(request),
                            collection_name,
                            str(identifier))

    def _get_collection_links(self,
                              request,
                              items,
                              collection_name,
                              id_key="uuid"):
        """Retrieve 'next' link, if applicable. This is included if:
        1) 'limit' param is specified and equals the number of items.
        2) 'limit' param is specified but it exceeds CONF.osapi_max_limit,
        in this case the number of items is CONF.osapi_max_limit.
        3) 'limit' param is NOT specified but the number of items is
        CONF.osapi_max_limit.
        """
        links = []
        max_items = min(
            int(request.params.get("limit", CONF.osapi_max_limit)),
            CONF.osapi_max_limit)
        if max_items and max_items == len(items):
            last_item = items[-1]
            if id_key in last_item:
                last_item_id = last_item[id_key]
            elif 'id' in last_item:
                last_item_id = last_item["id"]
            else:
                last_item_id = last_item["flavorid"]
            links.append({
                "rel": "next",
                "href": self._get_next_link(request,
                                            last_item_id,
                                            collection_name),
            })
        return links

    def _update_link_prefix(self, orig_url, prefix):
        if not prefix:
            return orig_url
        url_parts = list(urlparse.urlsplit(orig_url))
        prefix_parts = list(urlparse.urlsplit(prefix))
        url_parts[0:2] = prefix_parts[0:2]
        url_parts[2] = prefix_parts[2] + url_parts[2]
        return urlparse.urlunsplit(url_parts).rstrip('/')

    def _update_glance_link_prefix(self, orig_url):
        return self._update_link_prefix(orig_url,
                                        CONF.osapi_glance_link_prefix)

    def _update_compute_link_prefix(self, orig_url):
        return self._update_link_prefix(orig_url,
                                        CONF.osapi_compute_link_prefix)



def check_cells_enabled(function):
    @functools.wraps(function)
    def inner(*args, **kwargs):
        if not CONF.cells.enable:
            msg = _("Cells is not enabled.")
            raise webob.exc.HTTPNotImplemented(explanation=msg)
        return function(*args, **kwargs)
    return inner
