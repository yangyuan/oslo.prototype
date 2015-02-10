# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
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

# Interactive shell based on Django:
#
# Copyright (c) 2005, the Lawrence Journal-World
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     1. Redistributions of source code must retain the above copyright notice,
#        this list of conditions and the following disclaimer.
#
#     2. Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#
#     3. Neither the name of Django nor the names of its contributors may be
#        used to endorse or promote products derived from this software without
#        specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


"""
  CLI interface for prototype management.
"""

from __future__ import print_function

import argparse
import os
import sys

import decorator
import netaddr
from oslo_config import cfg
import oslo_messaging as messaging
from oslo_utils import importutils
import six

from prototype import config
from oslo_context import context
from prototype import db
from prototype.db import migration
from prototype.common import exception
from prototype.common.i18n import _
from prototype.openstack.common import cliutils
from oslo_log import log as logging
from prototype.common import utils
from prototype import version

CONF = cfg.CONF

# Decorators for actions
def args(*args, **kwargs):
    def _decorator(func):
        func.__dict__.setdefault('args', []).insert(0, (args, kwargs))
        return func
    return _decorator

class ShellCommands(object):
    def bpython(self):
        """Runs a bpython shell.

        Falls back to Ipython/python shell if unavailable
        """
        self.run('bpython')

    def ipython(self):
        """Runs an Ipython shell.

        Falls back to Python shell if unavailable
        """
        self.run('ipython')

    def python(self):
        """Runs a python shell.

        Falls back to Python shell if unavailable
        """
        self.run('python')

    @args('--shell', metavar='<bpython|ipython|python >',
            help='Python shell')
    def run(self, shell=None):
        """Runs a Python interactive interpreter."""
        if not shell:
            shell = 'bpython'

        if shell == 'bpython':
            try:
                import bpython
                bpython.embed()
            except ImportError:
                shell = 'ipython'
        if shell == 'ipython':
            try:
                from IPython import embed
                embed()
            except ImportError:
                try:
                    # Ipython < 0.11
                    # Explicitly pass an empty list as arguments, because
                    # otherwise IPython would use sys.argv from this script.
                    import IPython

                    shell = IPython.Shell.IPShell(argv=[])
                    shell.mainloop()
                except ImportError:
                    # no IPython module
                    shell = 'python'

        if shell == 'python':
            import code
            try:
                # Try activating rlcompleter, because it's handy.
                import readline
            except ImportError:
                pass
            else:
                # We don't have to wrap the following import in a 'try',
                # because we already know 'readline' was imported successfully.
                readline.parse_and_bind("tab:complete")
            code.interact()

    @args('--path', metavar='<path>', help='Script path')
    def script(self, path):
        """Runs the script from the specified path with flags set properly.

        arguments: path
        """
        exec(compile(open(path).read(), path, 'exec'), locals(), globals())


def _db_error(caught_exception):
    print(caught_exception)
    print(_("The above error may show that the database has not "
            "been created.\nPlease create a database using "
            "'prototype-manage db sync' before running this command."))
    exit(1)

class ServiceCommands(object):
    """Enable and disable running services."""

    @args('--host', metavar='<host>', help='Host')
    @args('--service', metavar='<service>', help='Prototype service')
    def list(self, host=None, service=None):
        """Show a list of all running services. Filter by host & service
        name
        """
        servicegroup_api = servicegroup.API()
        ctxt = context.get_admin_context()
        services = db.service_get_all(ctxt)
        services = availability_zones.set_availability_zones(ctxt, services)
        if host:
            services = [s for s in services if s['host'] == host]
        if service:
            services = [s for s in services if s['binary'] == service]
        print_format = "%-16s %-36s %-16s %-10s %-5s %-10s"
        print(print_format % (
                    _('Binary'),
                    _('Host'),
                    _('Zone'),
                    _('Status'),
                    _('State'),
                    _('Updated_At')))
        for svc in services:
            alive = servicegroup_api.service_is_up(svc)
            art = (alive and ":-)") or "XXX"
            active = 'enabled'
            if svc['disabled']:
                active = 'disabled'
            print(print_format % (svc['binary'], svc['host'],
                                  svc['availability_zone'], active, art,
                                  svc['updated_at']))

    @args('--host', metavar='<host>', help='Host')
    @args('--service', metavar='<service>', help='Prototype service')
    def enable(self, host, service):
        """Enable scheduling for a service."""
        ctxt = context.get_admin_context()
        try:
            svc = db.service_get_by_args(ctxt, host, service)
            db.service_update(ctxt, svc['id'], {'disabled': False})
        except exception.NotFound as ex:
            print(_("error: %s") % ex)
            return(2)
        print((_("Service %(service)s on host %(host)s enabled.") %
               {'service': service, 'host': host}))

    @args('--host', metavar='<host>', help='Host')
    @args('--service', metavar='<service>', help='Prototype service')
    def disable(self, host, service):
        """Disable scheduling for a service."""
        ctxt = context.get_admin_context()
        try:
            svc = db.service_get_by_args(ctxt, host, service)
            db.service_update(ctxt, svc['id'], {'disabled': True})
        except exception.NotFound as ex:
            print(_("error: %s") % ex)
            return(2)
        print((_("Service %(service)s on host %(host)s disabled.") %
               {'service': service, 'host': host}))

    def _show_host_resources(self, context, host):
        """Shows the physical/usage resource given by hosts.

        :param context: security context
        :param host: hostname
        :returns:
            example format is below::

                {'resource':D, 'usage':{proj_id1:D, proj_id2:D}}
                D: {'vcpus': 3, 'memory_mb': 2048, 'local_gb': 2048,
                    'vcpus_used': 12, 'memory_mb_used': 10240,
                    'local_gb_used': 64}

        """
        # Getting compute node info and related instances info
        service_ref = db.service_get_by_compute_host(context, host)
        instance_refs = db.instance_get_all_by_host(context,
                                                    service_ref['host'])

        # Getting total available/used resource
        compute_ref = service_ref['compute_node'][0]
        resource = {'vcpus': compute_ref['vcpus'],
                    'memory_mb': compute_ref['memory_mb'],
                    'local_gb': compute_ref['local_gb'],
                    'vcpus_used': compute_ref['vcpus_used'],
                    'memory_mb_used': compute_ref['memory_mb_used'],
                    'local_gb_used': compute_ref['local_gb_used']}
        usage = dict()
        if not instance_refs:
            return {'resource': resource, 'usage': usage}

        # Getting usage resource per project
        project_ids = [i['project_id'] for i in instance_refs]
        project_ids = list(set(project_ids))
        for project_id in project_ids:
            vcpus = [i['vcpus'] for i in instance_refs
                     if i['project_id'] == project_id]

            mem = [i['memory_mb'] for i in instance_refs
                   if i['project_id'] == project_id]

            root = [i['root_gb'] for i in instance_refs
                    if i['project_id'] == project_id]

            ephemeral = [i['ephemeral_gb'] for i in instance_refs
                         if i['project_id'] == project_id]

            usage[project_id] = {'vcpus': sum(vcpus),
                                 'memory_mb': sum(mem),
                                 'root_gb': sum(root),
                                 'ephemeral_gb': sum(ephemeral)}

        return {'resource': resource, 'usage': usage}

    @args('--host', metavar='<host>', help='Host')
    def describe_resource(self, host):
        """Describes cpu/memory/hdd info for host.

        :param host: hostname.

        """
        try:
            result = self._show_host_resources(context.get_admin_context(),
                                               host=host)
        except exception.PrototypeException as ex:
            print(_("error: %s") % ex)
            return 2

        if not isinstance(result, dict):
            print(_('An unexpected error has occurred.'))
            print(_('[Result]'), result)
        else:
            # Printing a total and used_now
            # (NOTE)The host name width 16 characters
            print('%(a)-25s%(b)16s%(c)8s%(d)8s%(e)8s' % {"a": _('HOST'),
                                                         "b": _('PROJECT'),
                                                         "c": _('cpu'),
                                                         "d": _('mem(mb)'),
                                                         "e": _('hdd')})
            print(('%(a)-16s(total)%(b)26s%(c)8s%(d)8s' %
                   {"a": host,
                    "b": result['resource']['vcpus'],
                    "c": result['resource']['memory_mb'],
                    "d": result['resource']['local_gb']}))

            print(('%(a)-16s(used_now)%(b)23s%(c)8s%(d)8s' %
                   {"a": host,
                    "b": result['resource']['vcpus_used'],
                    "c": result['resource']['memory_mb_used'],
                    "d": result['resource']['local_gb_used']}))

            # Printing a used_max
            cpu_sum = 0
            mem_sum = 0
            hdd_sum = 0
            for p_id, val in result['usage'].items():
                cpu_sum += val['vcpus']
                mem_sum += val['memory_mb']
                hdd_sum += val['root_gb']
                hdd_sum += val['ephemeral_gb']
            print('%(a)-16s(used_max)%(b)23s%(c)8s%(d)8s' % {"a": host,
                                                             "b": cpu_sum,
                                                             "c": mem_sum,
                                                             "d": hdd_sum})

            for p_id, val in result['usage'].items():
                print('%(a)-25s%(b)16s%(c)8s%(d)8s%(e)8s' % {
                        "a": host,
                        "b": p_id,
                        "c": val['vcpus'],
                        "d": val['memory_mb'],
                        "e": val['root_gb'] + val['ephemeral_gb']})




class DbCommands(object):
    """Class for managing the database."""

    def __init__(self):
        pass

    @args('--version', metavar='<version>', help='Database version')
    def sync(self, version=None):
        """Sync the database up to the most recent version."""
        return migration.db_sync(version)

    def version(self):
        """Print the current database version."""
        print(migration.db_version())


CATEGORIES = {
    'db': DbCommands,
    'shell': ShellCommands,
    'service': ServiceCommands,
}


def methods_of(obj):
    """Get all callable methods of an object that don't start with underscore

    returns a list of tuples of the form (method_name, method)
    """
    result = []
    for i in dir(obj):
        if callable(getattr(obj, i)) and not i.startswith('_'):
            result.append((i, getattr(obj, i)))
    return result


def add_command_parsers(subparsers):
    parser = subparsers.add_parser('version')

    parser = subparsers.add_parser('bash-completion')
    parser.add_argument('query_category', nargs='?')

    for category in CATEGORIES:
        command_object = CATEGORIES[category]()

        desc = getattr(command_object, 'description', None)
        parser = subparsers.add_parser(category, description=desc)
        parser.set_defaults(command_object=command_object)

        category_subparsers = parser.add_subparsers(dest='action')

        for (action, action_fn) in methods_of(command_object):
            parser = category_subparsers.add_parser(action, description=desc)

            action_kwargs = []
            for args, kwargs in getattr(action_fn, 'args', []):
                # FIXME(markmc): hack to assume dest is the arg name without
                # the leading hyphens if no dest is supplied
                kwargs.setdefault('dest', args[0][2:])
                if kwargs['dest'].startswith('action_kwarg_'):
                    action_kwargs.append(
                            kwargs['dest'][len('action_kwarg_'):])
                else:
                    action_kwargs.append(kwargs['dest'])
                    kwargs['dest'] = 'action_kwarg_' + kwargs['dest']

                parser.add_argument(*args, **kwargs)

            parser.set_defaults(action_fn=action_fn)
            parser.set_defaults(action_kwargs=action_kwargs)

            parser.add_argument('action_args', nargs='*',
                                help=argparse.SUPPRESS)


category_opt = cfg.SubCommandOpt('category',
                                 title='Command categories',
                                 help='Available categories',
                                 handler=add_command_parsers)


def main():
    """Parse options and call the appropriate class/method."""
    CONF.register_cli_opt(category_opt)
    try:
        logging.register_options(CONF)
        config.parse_args(sys.argv)
        logging.setup(CONF, "prototype")
    except cfg.ConfigFilesNotFoundError:
        cfgfile = CONF.config_file[-1] if CONF.config_file else None
        if cfgfile and not os.access(cfgfile, os.R_OK):
            st = os.stat(cfgfile)
            print(_("Could not read %s. Re-running with sudo") % cfgfile)
            try:
                os.execvp('sudo', ['sudo', '-u', '#%s' % st.st_uid] + sys.argv)
            except Exception:
                print(_('sudo failed, continuing as if nothing happened'))

        print(_('Please re-run prototype-manage as root.'))
        return(2)


    if CONF.category.name == "version":
        print(version.version_string_with_package())
        return(0)

    if CONF.category.name == "bash-completion":
        if not CONF.category.query_category:
            print(" ".join(CATEGORIES.keys()))
        elif CONF.category.query_category in CATEGORIES:
            fn = CATEGORIES[CONF.category.query_category]
            command_object = fn()
            actions = methods_of(command_object)
            print(" ".join([k for (k, v) in actions]))
        return(0)

    fn = CONF.category.action_fn
    fn_args = [arg.decode('utf-8') for arg in CONF.category.action_args]
    fn_kwargs = {}
    for k in CONF.category.action_kwargs:
        v = getattr(CONF.category, 'action_kwarg_' + k)
        if v is None:
            continue
        if isinstance(v, six.string_types):
            v = v.decode('utf-8')
        fn_kwargs[k] = v

    # call the action with the remaining arguments
    # check arguments
    try:
        cliutils.validate_args(fn, *fn_args, **fn_kwargs)
    except cliutils.MissingArgs as e:
        # NOTE(mikal): this isn't the most helpful error message ever. It is
        # long, and tells you a lot of things you probably don't want to know
        # if you just got a single arg wrong.
        print(fn.__doc__)
        CONF.print_help()
        print(e)
        return(1)
    try:
        ret = fn(*fn_args, **fn_kwargs)
        return(ret)
    except Exception:
        print(_("Command failed, please check log for more info"))
        raise
