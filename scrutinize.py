import json
import imp
import inspect
import os
import sys
import traceback


def find_code(target):
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
    if not klass:
        return getattr(sys.modules[module], function)

    klass_object = getattr(sys.modules[module], klass)
    return getattr(klass_object, function)


class Statsd(object):
    def __init__(self, configuration):
        print "Statsd", configuration

    def start(self, target_config):
        print "Statsd.start", target_config

    def stop(self, target_config):
        print "Statsd.stop", target_config


class Profile(object):
    def __init__(self, configuration):
        print "Profile", configuration

    def start(self, target_config):
        print "Profile.start", target_config

    def stop(self, target_config):
        print "Profile.stop", target_config


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
    pass

#--------------------------


def _load_plugins(config):
    if config:
        for name, info in config.iteritems():
            driver_name = info['driver']
            driver_config = info['config']
            plugin_class = find_code(driver_name)
            print "Loaded plugin '%(name)s' from %(driver_name)s" % locals()
            plugin = plugin_class(driver_config)
            info['impl'] = plugin
    return config


def _plugin_wrapper(inner, plugin, config):
    def defer(*args, **kwargs):
        state = plugin.start(config)
        inner(*args, **kwargs)
        plugin.stop(state, config)

    return defer


def _monkeypatch(config):
    if config:
        pass


def _inject_plugins(plugins, config):
    for name, info in plugins.iteritems():
        plugin_impl = info['impl']

        plugin_commands = config.get(name)
        if not plugin_commands:
            continue

        # a 1-1 list of plugin_config that holds underlying impls
        original_impls = []
        for target in plugin_commands:
            target_impl = find_code(target)
            print "Monkeypatching %s plugin on %s" % (name, target)
            # Need to keep the old impl around
            # and need to keep all the plugin wrapper references
            # and, ideally, impose functools on each different patch
            # (likely impossible).
            original_impls.append(target_impl)
            target_impl = _plugin_wrapper(target_impl, plugin_impl, info)

        info['original_impls'] = original_impls


if __name__ == '__main__':
    filename = 'sample.json'
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    config = None
    with open(filename) as f:
        config = json.load(f)

    plugins = _load_plugins(config.get('plugins'))
    _monkeypatch(config.get('monkeypatch'))

    _inject_plugins(plugins, config)
