# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
# Copyright 2012 Red Hat, Inc.
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
from oslo_db import options
from oslo_log import log

from prototype.common import rpc
from prototype import version

import socket
from oslo_utils import netutils

CONF = cfg.CONF



netconf_opts = [
    cfg.StrOpt('my_ip',
               default=netutils.get_my_ipv4(),
               help='IP address of this host'),
    cfg.StrOpt('host',
               default=socket.gethostname(),
               help='Name of this node.  This can be an opaque identifier.  '
                    'It is not necessarily a hostname, FQDN, or IP address. '
                    'However, the node name must be valid within '
                    'an AMQP key, and if using ZeroMQ, a valid '
                    'hostname, FQDN, or IP address'),
    cfg.BoolOpt('use_ipv6',
                default=False,
                help='Use IPv6'),
]

CONF.register_opts(netconf_opts)

_DEFAULT_SQL_CONNECTION = 'sqlite://prototype.sqlite'

_DEFAULT_LOG_LEVELS = ['amqp=WARN', 'amqplib=WARN', 'boto=WARN',
                       'qpid=WARN', 'sqlalchemy=WARN', 'suds=INFO',
                       'oslo.messaging=INFO', 'iso8601=WARN',
                       'requests.packages.urllib3.connectionpool=WARN',
                       'urllib3.connectionpool=WARN', 'websocket=WARN',
                       'keystonemiddleware=WARN', 'routes.middleware=WARN',
                       'stevedore=WARN']

_DEFAULT_LOGGING_CONTEXT_FORMAT = ('%(asctime)s.%(msecs)03d %(process)d '
                                   '%(levelname)s %(name)s [%(request_id)s '
                                   '%(user_identity)s] %(instance)s'
                                   '%(message)s')


def parse_args(argv, default_config_files=None):
    log.set_defaults(_DEFAULT_LOGGING_CONTEXT_FORMAT, _DEFAULT_LOG_LEVELS)
    options.set_defaults(CONF, connection=_DEFAULT_SQL_CONNECTION,
                         sqlite_db='prototype.sqlite')
    rpc.set_defaults(control_exchange='prototype')
    CONF(argv[1:],
         project='prototype',
         version=version.version_string(),
         default_config_files=default_config_files)
    rpc.init(CONF)

