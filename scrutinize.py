import json
import imp
import inspect
import os
import sys
import time
import traceback


def get_module(target):
    """Import a named class, module, method or function.

    Accepts these formats:
        ".../file/path|path.to.namespace:Class.method"
        ".../file/path|path.to.namespace:function"
    """

    filename, sep, namespace= target.rpartition('|')
    module, sep, klass_or_function = namespace.rpartition(':')
    if filename:
        if not module in sys.modules:
            if os.path.isfile(filename):
                imp.load_source(module, filename)

    if not module:
        raise Exception("Need a module path for %s (%s)" % (namespace, target))

    if not module in sys.modules:
        __import__(module)

    klass, sep, function = klass_or_function.rpartition('.')
    return module, klass, function


def find_code(target):
    """Get the actual implementation of the target."""
    module, klass, function = get_module(target)
    if not klass:
        return getattr(sys.modules[module], function)

    klass_object = getattr(sys.modules[module], klass)
    return getattr(klass_object, function)


def load_plugins(config):
    plugin_dict = {}
    if config:
        for name, info in config.iteritems():
            code = info['code']
            plugin_config = info.get('config', {})
            plugin_class = find_code(code)
            plugin = plugin_class(plugin_config)
            plugin_dict[name] = plugin
    return plugin_dict


def plugin_wrapper(bundle):
    def defer(*args, **kwargs):
        result = None
        label = bundle.label
        if bundle.label_extractor:
            label = bundle.label_extractor.extract(*args, **kwargs) or \
                                            bundle.label
        state = bundle.collector.start(label)
        try:
            result = bundle.collector.call_target(state, bundle,
                                                  *args, **kwargs)
        finally:
            metrics = bundle.collector.stop(state)
            bundle.notify(metrics)
        return result

    return defer


class Bundle(object):
    """A Bundle is, essentially, a fancy tuple of:
       - a Collector (the thing that extracts a measurement)
       - a list of Notifiers (to send extracted data somewhere)
       - a Target (the code you want to measure)
       - a Label Extractor (for pulling the label name from a live call)
    """
    def __init__(self, label, bundle, collectors, label_extractors, notifiers):
        self.label = label
        self.target = bundle["target"]
        collector_name = bundle["collector"]
        label_extractor_name = bundle.get("label_extractor")
        notifier_names = bundle.get("notifiers", [])

        self.label_extractor = None
        if label_extractor_name:
            self.label_extractor = label_extractors.get(label_extractor_name)

        self.send_list = [notifiers.get(name) for name in notifier_names
                                                       if name]
        self.collector = collectors.get(collector_name)

        self.target_impl = None  # to be replaced on patch.

    def inject(self):
        print "Monkeypatching '%s' plugin on %s" % \
                        (self.collector.__class__.__name__, self.target)

        module, klass, function = get_module(self.target)
        if not klass:
            self.target_impl = getattr(sys.modules[module], function)
            setattr(sys.modules[module], function, plugin_wrapper(self))
            return

        klass_object = getattr(sys.modules[module], klass)
        self.target_impl = getattr(klass_object, function)
        setattr(klass_object, function, plugin_wrapper(self))

    def reset(self):
        print "Resetting '%s' plugin from %s" % \
                        (self.collector.__class__.__name__, self.target)
        module, klass, function = get_module(bundle.target)
        if not klass:
            setattr(sys.modules[module], function, bundle.target_impl)
        else:
            klass_object = getattr(sys.modules[module], klass)
            setattr(klass_object, function, bundle.target_impl)

        bundle.target_impl = None

    def notify(self, metrics):
        for notifier in self.send_list:
            if notifier:
                notifier.send(metrics)


#--------------------------
# Sample functions/methods for testing

def level_2():
    for x in xrange(3):
        time.sleep(1)


def level_1():
    for x in xrange(3):
        time.sleep(1)
        level_2()


class Foo(object):
    def method_a(self, a, b, c, d):
        level_1()


class Blah(Foo):
    def method_a(self, a, b, c, d):
        pass

    def method_b(self, a, b, c, e):
        return a + b + c + e


def function_a(a, b, c, d):
    print "__main__:function_a(%s, %s, %s, %s)" % (a, b, c, d)

#--------------------------


if __name__ == '__main__':
    filename = 'sample.json'
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    config = None
    with open(filename) as f:
        config = json.load(f)

    notifiers = load_plugins(config.get('notifiers'))
    collectors = load_plugins(config.get('collectors'))
    label_extractors = load_plugins(config.get('label_extractors'))

    del config['notifiers']
    del config['collectors']
    del config['label_extractors']

    bundles = [Bundle(label, bundle, collectors, label_extractors, notifiers)
                    for label, bundle in config.iteritems()]

    for bundle in bundles:
        bundle.inject()

    # Try some
    function_a("label.from.extractor", 2, 3, 4)
    b = Blah()
    print b.method_b(10, 20, 30, 40)
    f = Foo()
    print f.method_a("scrutinize", 10, 10, 10)

    for bundle in bundles:
        bundle.reset()

    function_a("label.from.extractor", 2, 3, 4)
    print b.method_b(10, 20, 30, 40)
