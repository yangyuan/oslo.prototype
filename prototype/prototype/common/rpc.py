import oslo_messaging as messaging
from oslo_serialization import jsonutils
from oslo_config import cfg
from oslo_context import context as ctx


TRANSPORT = None

def init(conf):
    global TRANSPORT
    TRANSPORT = messaging.get_transport(conf)
    
def set_defaults(control_exchange):
    messaging.set_transport_defaults(control_exchange)
    
class RequestContextSerializer(messaging.Serializer):

    def __init__(self, base):
        self._base = base

    def serialize_entity(self, context, entity):
        if not self._base:
            return entity
        return self._base.serialize_entity(context, entity)

    def deserialize_entity(self, context, entity):
        if not self._base:
            return entity
        return self._base.deserialize_entity(context, entity)

    def serialize_context(self, context):
        return context.to_dict()

    def deserialize_context(self, context):
        return ctx.RequestContext.from_dict(context)

def get_client(target, version_cap=None, serializer=None):
    assert TRANSPORT is not None
    serializer = RequestContextSerializer(serializer)
    return messaging.RPCClient(TRANSPORT,
                               target,
                               version_cap=version_cap,
                               serializer=serializer)
                               
def get_server(target, endpoints, serializer=None):
    assert TRANSPORT is not None
    serializer = RequestContextSerializer(serializer)
    return messaging.get_rpc_server(TRANSPORT,
                                    target,
                                    endpoints,
                                    executor='eventlet',
                                    serializer=serializer)
                                    
                                    



_NAMESPACE = 'baseapi'


class BaseAPI(object):
    """Client side of the base rpc API.

    API version history:

        1.0 - Initial version.
        1.1 - Add get_backdoor_port
    """

    VERSION_ALIASES = {
        # baseapi was added in havana
    }

    def __init__(self, topic):
        super(BaseAPI, self).__init__()
        target = messaging.Target(topic=topic,
                                  namespace=_NAMESPACE,
                                  version='1.0')
        version_cap = self.VERSION_ALIASES.get(CONF.upgrade_levels.baseapi,
                                               CONF.upgrade_levels.baseapi)
        self.client = rpc.get_client(target, version_cap=version_cap)

    def ping(self, context, arg, timeout=None):
        arg_p = jsonutils.to_primitive(arg)
        cctxt = self.client.prepare(timeout=timeout)
        return cctxt.call(context, 'ping', arg=arg_p)

    def get_backdoor_port(self, context, host):
        cctxt = self.client.prepare(server=host, version='1.1')
        return cctxt.call(context, 'get_backdoor_port')


class BaseRPCAPI(object):
    """Server side of the base RPC API."""

    target = messaging.Target(namespace=_NAMESPACE, version='1.1')

    def __init__(self, service_name, backdoor_port):
        self.service_name = service_name
        self.backdoor_port = backdoor_port

    def ping(self, context, arg):
        resp = {'service': self.service_name, 'arg': arg}
        return jsonutils.to_primitive(resp)

    def get_backdoor_port(self, context):
        return self.backdoor_port