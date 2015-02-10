# Copyright 2012 OpenStack Foundation.
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

from prototype.api.v1 import manager
from prototype.common import wsgi
import routes

class APIMapper(routes.Mapper):
    """
    Handle route matching when url is '' because routes.Mapper returns
    an error in this case.
    """

    def routematch(self, url=None, environ=None):
        if url is "":
            result = self._match("", environ)
            return result[0], result[1]
        return routes.Mapper.routematch(self, url, environ)

class APIRouter(wsgi.Router):
    """Routes requests on the OpenStack API to the appropriate controller
    and method.
    """
    @classmethod
    def factory(cls, global_config, **local_config):
        return cls()

    def __init__(self):
        mapper = APIMapper()
        self._setup_routes(mapper)
        super(APIRouter, self).__init__(mapper)

    def _setup_routes(self, mapper):
        controller = manager.create_resource()

        mapper.connect("/",
                       controller=controller,
                       action="debug")

        mapper.connect("/debug",
                       controller=controller,
                       action='debug1',
                       conditions={'method': ['GET']})
                       
        mapper.connect("/debug",
                       controller=controller,
                       action='debug2',
                       conditions={'method': ['POST']})