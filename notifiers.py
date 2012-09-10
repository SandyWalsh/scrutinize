class Statsd(object):
    def __init__(self, configuration):
        print "Statsd", configuration

    def send(self, label, data):
        print "Statsd.send '%(label)s' = %(data)s" % locals()

