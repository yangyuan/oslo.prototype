import warnings


from oslo_utils import importutils
from prototypeclient import utils

def Client(endpoint, version=None, *args, **kwargs):

    endpoint_host, url_version = utils.strip_version(endpoint)
    if not url_version and not version:
        msg = ("Please provide either the version or an url with the form "
               "http://$HOST:$PORT/v$VERSION_NUMBER")
        raise RuntimeError(msg)
    version = int(version or url_version)

    module = 'prototypeclient.v%s' % version
    module = '.'.join((module, 'client'))
    module = importutils.import_module(module)
    
    client_class = getattr(module, 'Client')
    return client_class(endpoint,version, *args, **kwargs)
