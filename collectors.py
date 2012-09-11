import time


class Collector(object):
    def __init__(self, configuration):
        self.configuration = configuration
        self.notifiers = configuration.get('notifiers', [])
        self.notifier_dict = {}  # {name: handle}
        print self.__class__.__name__, configuration

    def start(self):
        # NOTE: Don't store any state in this collector.
        # It will be reused many times. Return a state object
        # here and it will be given back to you in stop()
        return None

    def stop(self, state):
        pass


class Profile(Collector):
    def start(self):
        print "Profile.start"

    def stop(self, state):
        print "Profile.stop"


class Time(Collector):
    def start(self):
        print "Time.start"
        return time.time()

    def stop(self, state):
        elapsed = time.time() - state
        print "Time.stop", elapsed
        return elapsed
