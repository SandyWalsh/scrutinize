import time


class Collector(object):
    def __init__(self, configuration):
        self.configuration = configuration
        self.notifiers = configuration.get('notifiers', [])
        self.notifier_dict = {}  # {name: handle}
        print self.__class__.__name__, configuration

    def send_to_notifiers(self, label, value):
        for name in self.notifiers:
            notifier = self.notifier_dict.get(name)
            if notifier:
                notifier.send(label, value)

    def start(self, target_config):
        # NOTE: Don't store any state in this collector.
        # It will be reused many times. Return a state object
        # here and it will be given back to you in stop()
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
        return time.time()

    def stop(self, state, target_config):
        elapsed = time.time() - state
        print "Time.stop", target_config, elapsed
        return elapsed
