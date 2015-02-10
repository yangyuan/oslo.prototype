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

"""Implementation of SQLAlchemy backend."""

import collections
import copy
import datetime
import functools
import sys
import threading
import time
import uuid

from oslo_config import cfg
from oslo_db import exception as db_exc
from oslo_db.sqlalchemy import session as db_session
from oslo_db.sqlalchemy import utils as db_utils
from oslo_utils import excutils
from oslo_utils import timeutils
import retrying
import six
from sqlalchemy import and_
from sqlalchemy import Boolean
from sqlalchemy.exc import NoSuchTableError
from sqlalchemy import Integer
from sqlalchemy import MetaData
from sqlalchemy import or_
from sqlalchemy.orm import aliased
from sqlalchemy.orm import contains_eager
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import joinedload_all
from sqlalchemy.orm import noload
from sqlalchemy.orm import undefer
from sqlalchemy.schema import Table
from sqlalchemy import sql
from sqlalchemy.sql.expression import asc
from sqlalchemy.sql.expression import desc
from sqlalchemy.sql import false
from sqlalchemy.sql import func
from sqlalchemy.sql import null
from sqlalchemy.sql import true
from sqlalchemy import String

from prototype.db.sqlalchemy import models
from prototype.common import exception
from prototype.common.i18n import _, _LI, _LE, _LW
from oslo_log import log as logging

CONF = cfg.CONF
LOG = logging.getLogger(__name__)

_ENGINE_FACADE = None
_LOCK = threading.Lock()

def _retry_on_deadlock(f):
    """Decorator to retry a DB API call if Deadlock was received."""
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        while True:
            try:
                return f(*args, **kwargs)
            except db_exc.DBDeadlock:
                LOG.warning(_LW("Deadlock detected when running "
                                "'%(func_name)s': Retrying..."),
                            dict(func_name=f.__name__))
                # Retry!
                time.sleep(0.5)
                continue
    functools.update_wrapper(wrapped, f)
    return wrapped

def _create_facade_lazily():
    global _LOCK, _ENGINE_FACADE
    if _ENGINE_FACADE is None:
        with _LOCK:
            if _ENGINE_FACADE is None:
                _ENGINE_FACADE = db_session.EngineFacade.from_config(CONF)
    return _ENGINE_FACADE


def get_engine(use_slave=False):
    facade = _create_facade_lazily()
    return facade.get_engine(use_slave=use_slave)


def get_session(use_slave=False, **kwargs):
    facade = _create_facade_lazily()
    return facade.get_session(use_slave=use_slave, **kwargs)

def get_backend():
    """The backend is this module itself. required for oslo_db."""
    return sys.modules[__name__]
    
###################

def service_get(context, id, session=None):
    if session == None:
        session = get_session()
    query = db_utils.model_query(models.Service, session=session).filter_by(id=id)
    return query.first()

def service_create(context, values):
    ref = models.Service()
    ref.update(values)
    ref.save()
    return ref

@_retry_on_deadlock
def service_update(context, id, values):
    session = get_session()
    with session.begin():
        ref = service_get(context, id, session=session)
        values['updated_at'] = timeutils.utcnow()
        ref.update(values)
    return ref

def service_delete(context, id):
    session = get_session()
    with session.begin():
        count = db_utils.model_query(models.Service, session=session).\
                    filter_by(id=id).\
                    delete()
    return count

def service_destroy(context, id):
    session = get_session()
    with session.begin():
        count = db_utils.model_query(models.Service, session=session).\
                    filter_by(id=id).\
                    soft_delete(synchronize_session=False)
    return count

def service_list(context, **kwargs):
    session = get_session()
    query = db_utils.model_query(models.Service, session=session)
    
    if 'topic' in kwargs:
        query = query.filter_by(topic=kwargs['topic'])
    if 'type' in kwargs:
        query = query.filter_by(type=kwargs['type'])
    if 'host' in kwargs:
        query = query.filter_by(host=kwargs['host'])
        
    return query.all()