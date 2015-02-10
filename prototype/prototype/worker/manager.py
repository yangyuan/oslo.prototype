# Copyright (c) 2010 OpenStack Foundation
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


from oslo_config import cfg
import oslo_messaging as messaging

from prototype.common import service
from oslo_log import log as logging



CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class WorkerManager(service.Manager):
    target = messaging.Target(version='2.0')
    
    def __init__(self, *args, **kwargs):
        super(WorkerManager, self).__init__(service_name='worker', *args, **kwargs)
        pass
        
    def init_host(self):
        from prototype import db
        from oslo_context import context
        ctxt = context.get_admin_context()
        LOG.error("init worker")

    def debug(self, context):
        return 'debug!'
