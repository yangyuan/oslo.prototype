# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

"""Starter script for Prototype API.

Starts both the EC2 and OpenStack APIs in separate greenthreads.

"""

import sys

from oslo_config import cfg

from prototype import config
from oslo_log import log as logging
from prototype.common import service
from prototype.common import utils
from prototype import version

CONF = cfg.CONF
CONF.import_opt('enabled_apis', 'prototype.service')
CONF.import_opt('enabled_ssl_apis', 'prototype.service')


def main():
    logging.register_options(CONF)
    config.parse_args(sys.argv)
    logging.setup(CONF, "prototype")
    
    utils.monkey_patch()


    launcher = service.process_launcher()
    for api in CONF.enabled_apis:
        should_use_ssl = api in CONF.enabled_ssl_apis
        server = service.WSGIService(api, use_ssl=should_use_ssl)
        launcher.launch_service(server, workers=server.workers or 1)
    launcher.wait()
