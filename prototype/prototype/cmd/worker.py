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

"""Starter script for Prototype Console Proxy."""

import sys

from oslo_config import cfg

from prototype import config
from oslo_log import log as logging
from prototype.common import service
from prototype import version

CONF = cfg.CONF
CONF.import_opt('worker_topic', 'prototype.worker.rpcapi')


def main():
    logging.register_options(CONF)
    config.parse_args(sys.argv)
    logging.setup(CONF, "prototype")
    server = service.RPCService.create(topic=CONF.worker_topic)
    service.serve(server)
    service.wait()
