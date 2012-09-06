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
        raise Exception("Need a module path for %s" % namespace)

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


class Profile(object):
    def __init__(self, configuration):
        print "Profile", configuration


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
            print "Name", name
            driver_name = info['driver']
            driver_config = info['config']
            plugin_class = find_code(driver_name)
            plugin = plugin_class(driver_config)

            print "Plugin=", plugin
            info['impl'] = plugin
    return config


def _monkeypatch(config):
    if config:
        pass


def _inject_plugins(plugins, config):
    pass


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
