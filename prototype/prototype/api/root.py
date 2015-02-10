# Copyright (c) 2011 OpenStack Foundation
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
"""
Common Auth Middleware.

"""

from oslo_config import cfg
from oslo_middleware import request_id
from oslo_serialization import jsonutils
import webob.dec
import webob.exc

from prototype.common.i18n import _,_LW
from oslo_log import log as logging
from prototype.common import wsgi


auth_opts = [
    cfg.StrOpt('auth_strategy',
               default='keystone',
               help='The strategy to use for auth: noauth or keystone.'),
]

CONF = cfg.CONF
CONF.register_opts(auth_opts)

LOG = logging.getLogger(__name__)


def _load_pipeline(loader, pipeline):
    filters = [loader.get_filter(n) for n in pipeline[:-1]]
    app = loader.get_app(pipeline[-1])
    filters.reverse()
    for filter in filters:
        app = filter(app)
    return app


def pipeline_factory(loader, global_conf, **local_conf):
    """A paste pipeline replica that keys off of auth_strategy."""
    return _load_pipeline(loader, local_conf[CONF.auth_strategy].split())
