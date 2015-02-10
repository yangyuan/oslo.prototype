from prototypeclient.openstack.common.apiclient import client
from prototypeclient.openstack.common.apiclient import auth
from prototypeclient.openstack.common.apiclient import exceptions

from keystoneclient.v2_0 import client as keystoneclient

from prototypeclient.v1.sample import SampleManager


class KeystoneAuthPlugin(auth.BaseAuthPlugin):

    opt_names = [
        "username",
        "password",
        "tenant_name",
        "token",
        "auth_url",
        "endpoint"
    ]

    def _do_authenticate(self, http_client):
        if self.opts.get('token') is None:
            ks_kwargs = {
                'username': self.opts.get('username'),
                'password': self.opts.get('password'),
                'tenant_name': self.opts.get('tenant_name'),
                'auth_url': self.opts.get('auth_url'),
            }
            self.client = keystoneclient.Client(**ks_kwargs)

    def token_and_endpoint(self, endpoint_type, service_type):
        token = endpoint = None

        if self.opts.get('token') and self.opts.get('endpoint'):
            token = self.opts.get('token')
            endpoint = self.opts.get('endpoint')

        elif hasattr(self, 'client'):
            token = self.client.auth_token
            endpoint = (self.opts.get('endpoint') or
                        self.client.service_catalog.url_for(
                            service_type=service_type,
                            endpoint_type=endpoint_type))
        return (token, endpoint)

    def sufficient_options(self):
        """Check if all required options are present.
        :raises: AuthPluginOptionsMissing
        """

        if self.opts.get('token'):
            lookup_table = ["token", "endpoint"]
        else:
            lookup_table = ["username", "password", "tenant_name", "auth_url"]

        missing = [opt
                   for opt in lookup_table
                   if not self.opts.get(opt)]
        if missing:
            raise exceptions.AuthPluginOptionsMissing(missing)

class Client(object):

    def __init__(self, endpoint, version, *args, **kwargs):
        self.version = version
        
        token = kwargs.pop('token', None)
        username = kwargs.pop('username', None)
        password = kwargs.pop('password', None)
        tenant_name = kwargs.pop('tenant_name', None)
        auth_url = kwargs.pop('auth_url', None)
        auth_system = kwargs.pop('auth_system', None)
        
        auth_plugin = KeystoneAuthPlugin(token=token,
            username=username,password=password,tenant_name=tenant_name,
            auth_url=auth_url,auth_system=auth_system,endpoint=endpoint)
       
        self.http_client = client.HTTPClient(auth_plugin, *args, **kwargs)
        self.client = client.BaseClient(self.http_client)
        
        
        self.sample = SampleManager(self.client)
