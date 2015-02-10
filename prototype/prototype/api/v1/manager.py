# Copyright 2011 OpenStack Foundation
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

from prototype.api import wsgi

class Controller(object):
    def __init__(self):
        pass
    
    def debug(self, req):
        return {'debug': "hehe"}
        
    def debug1(self, req):
        from prototype.worker import rpcapi
        worker_rpc_api = rpcapi.WorkerRPCAPI()
        return {'debug': worker_rpc_api.debug(req.context)}
        
    def debug2(self, req):
        return 'debug2'

def create_resource():
    return wsgi.Resource(Controller())