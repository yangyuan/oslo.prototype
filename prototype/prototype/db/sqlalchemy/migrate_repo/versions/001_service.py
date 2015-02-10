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

from sqlalchemy import schema

from sqlalchemy import Table, Column, ForeignKey, Index, MetaData
from sqlalchemy import DateTime, Integer, String, BigInteger, Boolean, Text, Unicode, Float

def upgrade(migrate_engine):
    meta = schema.MetaData()
    meta.bind = migrate_engine
    table = Table('service', meta,
        Column('created_at', DateTime),
        Column('updated_at', DateTime),
        Column('deleted_at', DateTime),
        Column('deleted', Integer),
        Column('id', Integer, primary_key=True, nullable=False),
        Column('host', String(length=255)),
        Column('type', String(length=255)),
        Column('topic', String(length=255)),
        Column('disabled', Boolean),
        mysql_engine='InnoDB',
        mysql_charset='utf8'
    )
    table.create()

def downgrade(migrate_engine):
    meta = schema.MetaData()
    meta.bind = migrate_engine
    table = schema.Table('service', meta, autoload=True)
    table.drop()