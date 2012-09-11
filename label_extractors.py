class NovaRPC(object):
    def __init__(self, configuration):
        self.configuration = configuration

    def extract(self, *args, **kwargs):
        print "NovaRPC.extract", args, kwargs
        return args[0]

