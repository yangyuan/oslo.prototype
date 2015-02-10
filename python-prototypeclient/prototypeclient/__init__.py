#NOTE(bcwaldon): this try/except block is needed to run setup.py due to
# its need to import local code before installing required dependencies
try:
    import prototypeclient.client
    Client = prototypeclient.client.Client
except ImportError:
    import warnings
    warnings.warn("Could not import prototypeclient.client", ImportWarning)

import pbr.version

version_info = pbr.version.VersionInfo('python-prototypeclient')

try:
    __version__ = version_info.version_string()
except AttributeError:
    __version__ = None
