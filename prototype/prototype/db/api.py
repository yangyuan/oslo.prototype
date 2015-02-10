# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
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

"""Defines interface for DB access.

Functions in this module are imported into the prototype.db namespace. Call these
functions from prototype.db namespace, not the prototype.db.api namespace.

All functions in this module return objects that implement a dictionary-like
interface. Currently, many of these objects are sqlalchemy objects that
implement a dictionary interface. However, a future goal is to have all of
these objects be simple dictionaries.

"""

from oslo_config import cfg
from oslo_db import concurrency

from prototype.common.i18n import _LE
from oslo_log import log as logging

CONF = cfg.CONF

_BACKEND_MAPPING = {'sqlalchemy': 'prototype.db.sqlalchemy.api'}

IMPL = concurrency.TpoolDbapiWrapper(CONF, backend_mapping=_BACKEND_MAPPING)

LOG = logging.getLogger(__name__)

###################

def service_get(context, id):
    return IMPL.service_get(context, id)

def service_create(context, values):
    return IMPL.service_create(context, values)

def service_update(context, id, values):
    return IMPL.service_update(context, id, values)

def service_delete(context, id):
    return IMPL.service_delete(context, id)

def service_destroy(context, id):
    return IMPL.service_destroy(context, id)

def service_list(context, **kwargs):
    return IMPL.service_list(context, **kwargs)