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


def plugin_wrapper(inner, plugin, config):
    def defer(*args, **kwargs):
        state = plugin.start(config)
        inner(*args, **kwargs)
        plugin.stop(state, config)

    return defer


def inject_code(target, new_impl, command_config):
    module, klass, function = get_module(target)
    if not klass:
        orig = getattr(sys.modules[module], function)
        setattr(sys.modules[module], function, plugin_wrapper(orig, new_impl, command_config))
        return orig

    klass_object = getattr(sys.modules[module], klass)
    orig = getattr(klass_object, function)
    setattr(klass_object, function, plugin_wrapper(orig, new_impl, command_config))
    return orig


def reset_code(target, old_impl, command_config):
    module, klass, function = get_module(target)
    if not klass:
        orig = getattr(sys.modules[module], function)
        setattr(sys.modules[module], function, old_impl)
        return orig

    klass_object = getattr(sys.modules[module], klass)
    orig = getattr(klass_object, function)
    setattr(klass_object, function, old_impl)
    return orig


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


def load_plugins(config):
    if config:
        for name, info in config.iteritems():
            code = info['code']
            plugin_config = info['config']
            collector_class = find_code(code)
            print "Loaded plugin '%(name)s' from %(code)s" % locals()
            collector = collector_class(plugin_config)
            info['impl'] = collector
    return config


def inject_collectors(collectors, config):
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
            command_config = command.get('config', {})
            print "Monkeypatching '%s' plugin on %s" % (name, target)
            target_impl = inject_code(target, plugin_impl, command_config)
            original_impls.append(target_impl)

        info['original_impls'] = original_impls


def reset_collectors(collectors, config):
    for name, info in collectors.iteritems():
        # See if we have any hooks for this collector in the
        # global configuration.
        plugin_commands = config.get(name)
        if not plugin_commands:
            continue

        # a 1-1 list of plugin_config that holds underlying impls
        original_impls = info['original_impls']
        for command in plugin_commands:
            original_impl = original_impls.pop(0)
            target = command['target']
            print "Rewinding '%s' plugin on %s" % (name, target)
            target_impl = reset_code(target, original_impl, None)


if __name__ == '__main__':
    filename = 'sample.json'
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    config = None
    with open(filename) as f:
        config = json.load(f)

    notifiers = load_plugins(config.get('notifiers'))
    collectors = load_plugins(config.get('collectors'))

    inject_collectors(collectors, config)

    # Try some
    function_a(1, 2, 3, 4)

    reset_collectors(collectors, config)

    function_a(1, 2, 3, 4)
