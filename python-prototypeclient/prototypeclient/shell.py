"""
Command-line interface to the Prototype API.
"""
from __future__ import print_function

from prototypeclient import utils

import argparse
import copy
import getpass
import logging
import os
import sys
import traceback
from oslo_utils import encodeutils
from oslo_utils import importutils
import six.moves.urllib.parse as urlparse

import prototypeclient
from prototypeclient.openstack.common.apiclient import exceptions as exc

from keystoneclient.auth.identity import v2 as v2_auth
from keystoneclient.auth.identity import v3 as v3_auth
from keystoneclient import discover
from keystoneclient.openstack.common.apiclient import exceptions as ks_exc
from keystoneclient import session



class OpenStackPrototypeShell(object):

    def _append_keystone_args(self, parser):
        ''' keystone will provide it in later version'''
        parser.add_argument('-k', '--insecure', default=False, action='store_true', help='Allow to perform \"insecure SSL\" (https) requests.')
        parser.add_argument('--os-cert', help='Path of certificate file to use in SSL connection.')
        parser.add_argument('--cert-file', dest='os_cert', help='DEPRECATED! Use --os-cert.')
        parser.add_argument('--os-key', help='Path of client key to use in SSL connection.')
        parser.add_argument('--key-file', dest='os_key', help='DEPRECATED! Use --os-key.')
        parser.add_argument('--os-cacert', metavar='<ca-certificate-file>', dest='os_cacert', default=utils.env('OS_CACERT'), help='Path of CA TLS certificate(s).')
        parser.add_argument('--ca-file', dest='os_cacert', help='DEPRECATED! Use --os-cacert.')
        parser.add_argument('--os-username', default=utils.env('OS_USERNAME'), help='Defaults to env[OS_USERNAME].')
        parser.add_argument('--os_username', help=argparse.SUPPRESS)
        parser.add_argument('--os-user-id', default=utils.env('OS_USER_ID'), help='Defaults to env[OS_USER_ID].')
        parser.add_argument('--os-user-domain-id', default=utils.env('OS_USER_DOMAIN_ID'), help='Defaults to env[OS_USER_DOMAIN_ID].')
        parser.add_argument('--os-user-domain-name', default=utils.env('OS_USER_DOMAIN_NAME'), help='Defaults to env[OS_USER_DOMAIN_NAME].')
        parser.add_argument('--os-project-id', default=utils.env('OS_PROJECT_ID'), help='Another way to specify tenant ID.')
        parser.add_argument('--os-project-name', default=utils.env('OS_PROJECT_NAME'), help='Another way to specify tenant name.')
        parser.add_argument('--os-project-domain-id', default=utils.env('OS_PROJECT_DOMAIN_ID'), help='Defaults to env[OS_PROJECT_DOMAIN_ID].')
        parser.add_argument('--os-project-domain-name', default=utils.env('OS_PROJECT_DOMAIN_NAME'), help='Defaults to env[OS_PROJECT_DOMAIN_NAME].')
        parser.add_argument('--os-password', default=utils.env('OS_PASSWORD'), help='Defaults to env[OS_PASSWORD].')
        parser.add_argument('--os_password', help=argparse.SUPPRESS)
        parser.add_argument('--os-tenant-id', default=utils.env('OS_TENANT_ID'), help='Defaults to env[OS_TENANT_ID].')
        parser.add_argument('--os_tenant_id', help=argparse.SUPPRESS)
        parser.add_argument('--os-tenant-name', default=utils.env('OS_TENANT_NAME'), help='Defaults to env[OS_TENANT_NAME].')
        parser.add_argument('--os_tenant_name', help=argparse.SUPPRESS)
        parser.add_argument('--os-auth-url', default=utils.env('OS_AUTH_URL'), help='Defaults to env[OS_AUTH_URL].')
        parser.add_argument('--os_auth_url', help=argparse.SUPPRESS)
        parser.add_argument('--os-region-name', default=utils.env('OS_REGION_NAME'), help='Defaults to env[OS_REGION_NAME].')
        parser.add_argument('--os_region_name', help=argparse.SUPPRESS)
        parser.add_argument('--os-auth-token', default=utils.env('OS_AUTH_TOKEN'), help='Defaults to env[OS_AUTH_TOKEN].')
        parser.add_argument('--os_auth_token', help=argparse.SUPPRESS)
        parser.add_argument('--os-service-type', default=utils.env('OS_SERVICE_TYPE'), help='Defaults to env[OS_SERVICE_TYPE].')
        parser.add_argument('--os_service_type', help=argparse.SUPPRESS)
        parser.add_argument('--os-endpoint-type', default=utils.env('OS_ENDPOINT_TYPE'), help='Defaults to env[OS_ENDPOINT_TYPE].')
        parser.add_argument('--os_endpoint_type', help=argparse.SUPPRESS)

    def get_base_parser(self):
        parser = argparse.ArgumentParser(
            prog='prototype',
            description=__doc__.strip(),
            epilog='See "prototype help COMMAND" for help on a specific command.',
            add_help=False,
            formatter_class=HelpFormatter,
        )

        parser.add_argument('-h', '--help', action='store_true', help=argparse.SUPPRESS)
        parser.add_argument('--version', action='version', version=prototypeclient.__version__)
        parser.add_argument('-d', '--debug', default=bool(utils.env('PROTOTYPECLIENT_DEBUG')), action='store_true', help='Defaults to env[PROTOTYPECLIENT_DEBUG].')
        parser.add_argument('-v', '--verbose', default=False, action="store_true", help="Print more verbose output")
        parser.add_argument('--timeout', default=600, help='Number of seconds to wait for a response')
        
        parser.add_argument('--os-prototype-url', default=utils.env('OS_PROTOTYPE_URL'), help='Defaults to env[OS_PROTOTYPE_URL].')
        parser.add_argument('--os_prototype_url', help=argparse.SUPPRESS)
        parser.add_argument('--os-prototype-api-version', default=utils.env('OS_PROTOTYPE_API_VERSION', default=None), help='Defaults to env[OS_PROTOTYPE_API_VERSION] or 1.')
        parser.add_argument('--os_prototype_api_version', help=argparse.SUPPRESS)

        self._append_keystone_args(parser)

        return parser

    def get_subcommand_parser(self, version):
        parser = self.get_base_parser()

        self.subcommands = {}
        subparsers = parser.add_subparsers(metavar='<subcommand>')
        try:
            module = 'prototypeclient.v%s' % version
            module = '.'.join((module, 'shell'))
            submodule = importutils.import_module(module)
        except ImportError:
            print('"%s" is not a supported API version. Example '
                  'values are "1" or "2".' % version)
            exit()

        self._find_actions(subparsers, submodule)
        self._find_actions(subparsers, self)

        self._add_bash_completion_subparser(subparsers)

        return parser

    def _find_actions(self, subparsers, actions_module):
        for attr in (a for a in dir(actions_module) if a.startswith('do_')):
            # I prefer to be hypen-separated instead of underscores.
            command = attr[3:].replace('_', '-')
            callback = getattr(actions_module, attr)
            desc = callback.__doc__ or ''
            help = desc.strip().split('\n')[0]
            arguments = getattr(callback, 'arguments', [])

            subparser = subparsers.add_parser(command,
                                              help=help,
                                              description=desc,
                                              add_help=False,
                                              formatter_class=HelpFormatter
                                              )
            subparser.add_argument('-h', '--help',
                                   action='help',
                                   help=argparse.SUPPRESS,
                                   )
            self.subcommands[command] = subparser
            for (args, kwargs) in arguments:
                subparser.add_argument(*args, **kwargs)
            subparser.set_defaults(func=callback)

    def _add_bash_completion_subparser(self, subparsers):
        subparser = subparsers.add_parser('bash_completion',
                                          add_help=False,
                                          formatter_class=HelpFormatter)
        self.subcommands['bash_completion'] = subparser
        subparser.set_defaults(func=self.do_bash_completion)

    def _discover_auth_versions(self, session, auth_url):
        # discover the API versions the server is supporting base on the
        # given URL
        v2_auth_url = None
        v3_auth_url = None
        try:
            ks_discover = discover.Discover(session=session, auth_url=auth_url)
            v2_auth_url = ks_discover.url_for('2.0')
            v3_auth_url = ks_discover.url_for('3.0')
        except ks_exc.ClientException as e:
            # Identity service may not support discover API version.
            # Lets trying to figure out the API version from the original URL.
            url_parts = urlparse.urlparse(auth_url)
            (scheme, netloc, path, params, query, fragment) = url_parts
            path = path.lower()
            if path.startswith('/v3'):
                v3_auth_url = auth_url
            elif path.startswith('/v2'):
                v2_auth_url = auth_url
            else:
                # not enough information to determine the auth version
                msg = ('Unable to determine the Keystone version '
                       'to authenticate with using the given '
                       'auth_url. Identity service may not support API '
                       'version discovery. Please provide a versioned '
                       'auth_url instead. error=%s') % (e)
                raise exc.CommandError(msg)

        return (v2_auth_url, v3_auth_url)

    def _get_keystone_session(self, **kwargs):
        ks_session = session.Session.construct(kwargs)

        # discover the supported keystone versions using the given auth url
        auth_url = kwargs.pop('auth_url', None)
        (v2_auth_url, v3_auth_url) = self._discover_auth_versions(
            session=ks_session,
            auth_url=auth_url)

        # Determine which authentication plugin to use. First inspect the
        # auth_url to see the supported version. If both v3 and v2 are
        # supported, then use the highest version if possible.
        user_id = kwargs.pop('user_id', None)
        username = kwargs.pop('username', None)
        password = kwargs.pop('password', None)
        user_domain_name = kwargs.pop('user_domain_name', None)
        user_domain_id = kwargs.pop('user_domain_id', None)
        # project and tenant can be used interchangeably
        project_id = (kwargs.pop('project_id', None) or
                      kwargs.pop('tenant_id', None))
        project_name = (kwargs.pop('project_name', None) or
                        kwargs.pop('tenant_name', None))
        project_domain_id = kwargs.pop('project_domain_id', None)
        project_domain_name = kwargs.pop('project_domain_name', None)
        auth = None

        use_domain = (user_domain_id or
                      user_domain_name or
                      project_domain_id or
                      project_domain_name)
        use_v3 = v3_auth_url and (use_domain or (not v2_auth_url))
        use_v2 = v2_auth_url and not use_domain

        if use_v3:
            auth = v3_auth.Password(
                v3_auth_url,
                user_id=user_id,
                username=username,
                password=password,
                user_domain_id=user_domain_id,
                user_domain_name=user_domain_name,
                project_id=project_id,
                project_name=project_name,
                project_domain_id=project_domain_id,
                project_domain_name=project_domain_name)
        elif use_v2:
            auth = v2_auth.Password(
                v2_auth_url,
                username,
                password,
                tenant_id=project_id,
                tenant_name=project_name)
        else:
            # if we get here it means domain information is provided
            # (caller meant to use Keystone V3) but the auth url is
            # actually Keystone V2. Obviously we can't authenticate a V3
            # user using V2.
            exc.CommandError("Credential and auth_url mismatch. The given "
                             "auth_url is using Keystone V2 endpoint, which "
                             "may not able to handle Keystone V3 credentials. "
                             "Please provide a correct Keystone V3 auth_url.")

        ks_session.auth = auth
        return ks_session

    def _get_endpoint_and_token(self, args, force_auth=False):
        image_url = args.os_prototype_url
        auth_token = args.os_auth_token

        def is_authentication_required(f):
            return getattr(f, 'require_authentication', True)
        
        auth_reqd = force_auth or (is_authentication_required(args.func)
                                   and not (auth_token and image_url))

        if not auth_reqd:
            endpoint = image_url
            token = args.os_auth_token
        else:

            if not args.os_username:
                raise exc.CommandError(
                    ("You must provide a username via"
                      " either --os-username or "
                      "env[OS_USERNAME]"))

            if not args.os_password:
                # No password, If we've got a tty, try prompting for it
                if hasattr(sys.stdin, 'isatty') and sys.stdin.isatty():
                    # Check for Ctl-D
                    try:
                        args.os_password = getpass.getpass('OS Password: ')
                    except EOFError:
                        pass
                # No password because we didn't have a tty or the
                # user Ctl-D when prompted.
                if not args.os_password:
                    raise exc.CommandError(
                        ("You must provide a password via "
                          "either --os-password, "
                          "env[OS_PASSWORD], "
                          "or prompted response"))

            # Validate password flow auth
            project_info = (args.os_tenant_name or
                            args.os_tenant_id or
                            (args.os_project_name and
                            (args.os_project_domain_name or
                                args.os_project_domain_id)) or
                            args.os_project_id)

            if (not project_info):
                # tenant is deprecated in Keystone v3. Use the latest
                # terminology instead.
                raise exc.CommandError(
                    ("You must provide a project_id or project_name ("
                      "with project_domain_name or project_domain_id) "
                      "via "
                      "  --os-project-id (env[OS_PROJECT_ID])"
                      "  --os-project-name (env[OS_PROJECT_NAME]),"
                      "  --os-project-domain-id "
                      "(env[OS_PROJECT_DOMAIN_ID])"
                      "  --os-project-domain-name "
                      "(env[OS_PROJECT_DOMAIN_NAME])"))

            if not args.os_auth_url:
                raise exc.CommandError(
                    ("You must provide an auth url via"
                      " either --os-auth-url or "
                      "via env[OS_AUTH_URL]"))

            kwargs = {
                'auth_url': args.os_auth_url,
                'username': args.os_username,
                'user_id': args.os_user_id,
                'user_domain_id': args.os_user_domain_id,
                'user_domain_name': args.os_user_domain_name,
                'password': args.os_password,
                'tenant_name': args.os_tenant_name,
                'tenant_id': args.os_tenant_id,
                'project_name': args.os_project_name,
                'project_id': args.os_project_id,
                'project_domain_name': args.os_project_domain_name,
                'project_domain_id': args.os_project_domain_id,
                'insecure': args.insecure,
                'cacert': args.os_cacert,
                'cert': args.os_cert,
                'key': args.os_key
            }
            ks_session = self._get_keystone_session(**kwargs)
            token = args.os_auth_token or ks_session.get_token()

            endpoint_type = args.os_endpoint_type or 'public'
            service_type = args.os_service_type or 'prototype'
            endpoint = args.os_prototype_url or ks_session.get_endpoint(
                service_type=service_type,
                interface=endpoint_type,
                region_name=args.os_region_name)
        return endpoint, token

    def _get_versioned_client(self, api_version, args, force_auth=False):
        endpoint, token = self._get_endpoint_and_token(args,
                                                       force_auth=force_auth)

        kwargs = {
            'token': token,
            'timeout': args.timeout,
            'cert': args.os_cert,
        }
        client = prototypeclient.Client(endpoint=endpoint, version=api_version, **kwargs)
        return client

    def main(self, argv):
        # Parse args once to find version

        #NOTE(flepied) Under Python3, parsed arguments are removed
        # from the list so make a copy for the first parsing
        base_argv = copy.deepcopy(argv)
        parser = self.get_base_parser()
        (options, args) = parser.parse_known_args(base_argv)

        try:
            endpoint = options.os_prototype_url
            endpoint, url_version = utils.strip_version(endpoint)
            url_version = 1
        except ValueError:
            # NOTE(flaper87): ValueError is raised if no endpoint is povided
            url_version = None

        # build available subcommands based on version
        try:
            api_version = int(options.os_prototype_api_version or url_version or 1)
        except ValueError:
            print("Invalid API version parameter")
            exit()

        subcommand_parser = self.get_subcommand_parser(api_version)
        self.parser = subcommand_parser

        # Handle top-level --help/-h before attempting to parse
        # a command off the command line
        if options.help or not argv:
            self.do_help(options)
            return 0

        # Parse args again and call whatever callback was selected
        args = subcommand_parser.parse_args(argv)

        # Short-circuit and deal with help command right away.
        if args.func == self.do_help:
            self.do_help(args)
            return 0
        elif args.func == self.do_bash_completion:
            self.do_bash_completion(args)
            return 0

        LOG = logging.getLogger('prototypeclient')
        LOG.addHandler(logging.StreamHandler())
        LOG.setLevel(logging.DEBUG if args.debug else logging.INFO)



        client = self._get_versioned_client(api_version, args,
                                            force_auth=False)

        try:
            args.func(client, args)
        except exc.Unauthorized:
            raise exc.CommandError("Invalid OpenStack Identity credentials.")
        except Exception:
            #NOTE(kragniz) Print any exceptions raised to stderr if the --debug
            # flag is set
            if args.debug:
                traceback.print_exc()
            raise
        finally:
            pass

    @utils.arg('command', metavar='<subcommand>', nargs='?',
               help='Display help for <subcommand>.')
    def do_help(self, args):
        """
        Display help about this program or one of its subcommands.
        """
        if getattr(args, 'command', None):
            if args.command in self.subcommands:
                self.subcommands[args.command].print_help()
            else:
                raise exc.CommandError("'%s' is not a valid subcommand" %
                                       args.command)
        else:
            self.parser.print_help()

    def do_bash_completion(self, _args):
        """
        Prints all of the commands and options to stdout so that the
        bash_completion script doesn't have to hard code them.
        """
        commands = set()
        options = set()
        for sc_str, sc in self.subcommands.items():
            commands.add(sc_str)
            for option in sc._optionals._option_string_actions.keys():
                options.add(option)

        commands.remove('bash_completion')
        commands.remove('bash-completion')
        print(' '.join(commands | options))


class HelpFormatter(argparse.HelpFormatter):
    def start_section(self, heading):
        # Title-case the headings
        heading = '%s%s' % (heading[0].upper(), heading[1:])
        super(HelpFormatter, self).start_section(heading)


def main():
    try:
        OpenStackPrototypeShell().main(map(encodeutils.safe_decode, sys.argv[1:]))
    except KeyboardInterrupt:
        exit('... terminating prototype client', exit_code=130)
    except Exception as e:
        exit(utils.exception_to_str(e))
