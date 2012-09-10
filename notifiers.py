class Statsd(object):
    def __init__(self, configuration):
        print "Statsd", configuration

    def send(self, data):
        print "Statsd.send", data

