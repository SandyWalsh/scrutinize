import json
import imp
import inspect
import os
import sys
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


def _plugin_wrapper(inner, plugin, config):
    def defer(*args, **kwargs):
        state = plugin.start(config)
        inner(*args, **kwargs)
        plugin.stop(state, config)

    return defer


def inject_code(target, plugin_impl, command_config):
    """Get the actual implementation of the target."""
    module, klass, function = get_module(target)
    if not klass:
        orig = getattr(sys.modules[module], function)
        setattr(sys.modules[module], function, _plugin_wrapper(orig, plugin_impl, command_config))
        return orig

    klass_object = getattr(sys.modules[module], klass)
    orig = getattr(klass_object, function)
    setattr(klass_object, function, _plugin_wrapper(orig, plugin_impl, command_config))
    return orig


class Statsd(object):
    def __init__(self, configuration):
        print "Statsd", configuration

    def send(self, data):
        print "Statsd.send", data


class Profile(object):
    def __init__(self, configuration):
        print "Profile", configuration

    def start(self, target_config):
        print "Profile.start", target_config

    def stop(self, state, target_config):
        print "Profile.stop", target_config


class Time(object):
    def __init__(self, configuration):
        print "Time", configuration

    def start(self, target_config):
        print "Time.start", target_config

    def stop(self, state, target_config):
        print "Time.stop",

#--------------------------
# Sample functions/methods for testing

class Foo(object):
    def method_a(self, a, b, c, d):
        pass


class Blah(Foo):
    def method_a(self, a, b, c, d):
        pass

    def method_b(self, a, b, c, e):
        pass


def function_a(a, b, c, d):
    print "__main__:function_a(%s, %s, %s, %s)" % (a, b, c, d)

#--------------------------


def _load_plugins(config):
    if config:
        for name, info in config.iteritems():
            code = info['code']
            plugin_config = info['config']
            collector_class = find_code(code)
            print "Loaded plugin '%(name)s' from %(code)s" % locals()
            collector = collector_class(plugin_config)
            info['impl'] = collector
    return config


def _monkeypatch(config):
    if config:
        pass


def _inject_collectors(collectors, config):
    for name, info in collectors.iteritems():
        plugin_impl = info['impl']

        # See if we have any hooks for this collector in the
        # global configuration.
        plugin_commands = config.get(name)
        if not plugin_commands:
            continue

        # a 1-1 list of plugin_config that holds underlying impls
        original_impls = []
        for command in plugin_commands:
            target = command['target']
            command_config = command.get('config')
            print "Monkeypatching '%s' plugin on %s" % (name, target)
            target_impl = inject_code(target, plugin_impl, command_config)
            original_impls.append(target_impl)

        info['original_impls'] = original_impls


if __name__ == '__main__':
    filename = 'sample.json'
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    config = None
    with open(filename) as f:
        config = json.load(f)

    notifiers = _load_plugins(config.get('notifiers'))
    collectors = _load_plugins(config.get('collectors'))
    _monkeypatch(config.get('monkeypatch'))

    _inject_collectors(collectors, config)

    # Try some
    function_a(1, 2, 3, 4)
