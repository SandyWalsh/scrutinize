import logging


LOG = logging.getLogger(__name__)


class NovaRPC(object):
    def __init__(self, configuration):
        self.configuration = configuration
        LOG.debug("NovaRPC.extract %s, %s" % (args, kwargs))

    def extract(self, *args, **kwargs):
        return args[0]

