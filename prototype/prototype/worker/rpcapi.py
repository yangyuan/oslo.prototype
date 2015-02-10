# Copyright 2013 Red Hat, Inc.
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
Client side of the console RPC API.
"""

from oslo_config import cfg
import oslo_messaging as messaging

from prototype.common import rpc

rpcapi_opts = [
    cfg.StrOpt('worker_topic',
               default='worker',
               help='The topic console proxy nodes listen on'),
]

CONF = cfg.CONF
CONF.register_opts(rpcapi_opts)

class WorkerRPCAPI(object):


    def __init__(self, topic=None, server=None):
        super(WorkerRPCAPI, self).__init__()
        topic = topic if topic else CONF.worker_topic
        target = messaging.Target(topic=topic, version='2.0')
        self.client = rpc.get_client(target)

    def debug(self, ctxt):
        cctxt = self.client.prepare(server='ubuntu')
        return cctxt.call(ctxt, 'debug')
