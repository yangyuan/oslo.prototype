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

from oslo_context import context
from prototype.common.i18n import _,_LW
from oslo_log import log as logging
from prototype.common import wsgi


CONF = cfg.CONF

LOG = logging.getLogger(__name__)

class PrototypeKeystoneContext(wsgi.Middleware):
    """Make a request context from keystone headers."""

    @webob.dec.wsgify(RequestClass=wsgi.Request)
    def __call__(self, req):
        # X_USER_ID
        user_id = req.headers.get('X_USER')
        user_id = req.headers.get('X_USER_ID', user_id)
        if user_id is None:
            LOG.debug("Neither X_USER_ID nor X_USER found in request")
            return webob.exc.HTTPUnauthorized()
        
        # X_TENANT_ID
        tenant_id = req.headers['X_TENANT']
        tenant_id = req.headers.get('X_TENANT_ID', tenant_id)
        
        # ENV_REQUEST_ID
        req_id = req.environ.get(request_id.ENV_REQUEST_ID)

        # X_AUTH_TOKEN
        auth_token = req.headers.get('X_AUTH_TOKEN', req.headers.get('X_STORAGE_TOKEN'))

        ctx = context.RequestContext(auth_token=auth_token,
                                    user=user_id,
                                    tenant=tenant_id,
                                    request_id=req_id)
        req.environ['prototype.context'] = ctx
        req.context = ctx
        return self.application

class NoAuthMiddleware(wsgi.Middleware):
    """Return a fake token if one isn't specified."""
    @webob.dec.wsgify(RequestClass=wsgi.Request)
    def __call__(self, req):
        ctx = context.RequestContext(is_admin=True)
        req.environ['prototype.context'] = ctx
        return self.application