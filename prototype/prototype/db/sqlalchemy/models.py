# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# Copyright 2011 Piston Cloud Computing, Inc.
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
from oslo_db.sqlalchemy import models
from oslo_utils import timeutils
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import orm
from sqlalchemy import Table, Column, ForeignKey, Index, MetaData
from sqlalchemy import DateTime, Integer, String, BigInteger, Boolean, Text, Unicode, Float

CONF = cfg.CONF
BASE = declarative_base()


class PrototypeBase(models.SoftDeleteMixin, models.TimestampMixin, models.ModelBase):
    metadata = None

    def __copy__(self):
        """Implement a safe copy.copy()."""
        session = orm.Session()
        copy = session.merge(self, load=False)
        session.expunge(copy)
        return copy

    def save(self, session=None):
        from prototype.db.sqlalchemy import api
        if session is None:
            session = api.get_session()
        super(PrototypeBase, self).save(session=session)


class Service(BASE, PrototypeBase):
    __tablename__ = 'service'
    id = Column(Integer, primary_key=True)
    host = Column(String(255))
    type = Column(String(255))
    topic = Column(String(255))
    disabled = Column(Boolean, default=False)
