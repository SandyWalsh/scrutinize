class NovaRPC(object):
    def __init__(self, configuration):
        print "NovaRPC", configuration

    def extract(self, *args, **kwargs):
        print "NovaRPC.extract", args, kwargs
        return args[0]

