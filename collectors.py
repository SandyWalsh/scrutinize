import time
import cProfile


class Collector(object):
    def __init__(self, configuration):
        self.configuration = configuration
        print self.__class__.__name__, configuration

    def start(self):
        # NOTE: Don't store any state in this collector.
        # It will be reused many times. Return a state object
        # here and it will be given back to you in stop()
        return None

    def stop(self, state):
        pass

    def call_target(self, bundle, *args, **kwargs):
        return bundle.target_impl(*args, **kwargs)


class Profile(Collector):
    def call_target(self, bundle, *args, **kwargs):
        p = cProfile.Profile()
        result = p.runcall(bundle.target_impl, *args, **kwargs)
        stats = p.getstats()
        for entry in stats:
            print cProfile.label(entry.code)
        return result


class Time(Collector):
    def start(self):
        return time.time()

    def stop(self, state):
        elapsed = time.time() - state
        return elapsed
