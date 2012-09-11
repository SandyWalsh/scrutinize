class Statsd(object):
    def __init__(self, configuration):
        self.configuration = configuration

    def send(self, label, data):
        print "Statsd.send '%(label)s' = %(data)s" % locals()

