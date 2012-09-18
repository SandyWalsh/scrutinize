import logging


LOG = logging.getLogger(__name__)


class ArgExtract(object):
    def __init__(self, configuration):
        self.configuration = configuration
        self.arg = int(self.configuration.get('position', 0))
        self.prefix = self.configuration.get('prefix', "label_"))
        LOG.debug("ArgExtract position %d" % self.arg)

    def extract(self, *args, **kwargs):
        return "%s%s" % (self.prefix, args[self.arg])

