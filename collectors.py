import time
import cProfile


class Collector(object):
    def __init__(self, configuration):
        self.configuration = configuration
        print self.__class__.__name__, configuration

    def start(self, label):
        # NOTE: Don't store any state in this collector.
        # It will be reused many times. Return a state object
        # here and it will be given back to you in stop()
        return label

    def stop(self, state):
        return []

    def call_target(self, __state, __bundle, *args, **kwargs):
        return __bundle.target_impl(*args, **kwargs)


class Profile(Collector):

    def start(self, label):
        return dict(label=label)

    def stop(self, state):
        metrics = state['metrics']
        label = state['label']
        final = []
        for total, callcount, this_label in metrics:
            final.append(("%s.%s" % (label, this_label), total))
        return final

    def _scrub(self, value):
        value = value.replace(".", "_")
        value = value.replace("|", "_")
        return value.replace(":", "_")

    def _label(self, code):
        if isinstance(code, str):
            return None    # built-in function
        filename = self._scrub(code.co_filename)
        name = self._scrub(code.co_name)
        return "%s.%s.line_%04d" % (filename, name, code.co_firstlineno)

    def call_target(self, __state, __bundle, *args, **kwargs):
        p = cProfile.Profile()
        result = p.runcall(__bundle.target_impl, *args, **kwargs)
        stats = p.getstats()
        filtered = [(entry.totaltime, entry.callcount,
                         self._label(entry.code)) for entry in stats]
        filtered = [(total, callcount, label) for total, callcount, label in
                     filtered if label]
        filtered.sort()
        filtered.reverse()
        __state['metrics'] = filtered
        for total, callcount, label in filtered:
            print label, total, callcount
        return result


class Time(Collector):
    def start(self, label):
        return (label, time.time())

    def stop(self, state):
        label, start_time = state
        elapsed = time.time() - start_time
        return [(label, elapsed),]
