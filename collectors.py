class Collector(object):
    def __init__(self, configuration):
        self.configuration = configuration
        self.notifiers = configuration.get('notifiers', [])
        print self.__class__.__name__, configuration

    def start(self, target_config):
        return None

    def stop(self, state, target_config):
        pass


class Profile(Collector):
    def start(self, target_config):
        print "Profile.start", target_config

    def stop(self, state, target_config):
        print "Profile.stop", target_config


class Time(Collector):
    def start(self, target_config):
        print "Time.start", target_config

    def stop(self, state, target_config):
        print "Time.stop",


