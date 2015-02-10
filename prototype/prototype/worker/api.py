from oslo_config import cfg

from prototype.db import base

CONF = cfg.CONF


class API(base.Base):
    """API for spinning up or down console proxy connections."""

    def __init__(self, **kwargs):
        super(API, self).__init__(**kwargs)


