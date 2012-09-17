import unittest2 as unittest
import sys

import stubout

import scrutinize
import collectors

#--------------------------
# test functions/methods

def level_2():
    pass


def level_1():
    pass


class Foo(object):
    def method_a(self, a, b, c, d):
        level_1()


class Blah(Foo):
    def method_a(self, a, b, c, d):
        pass

    def method_b(self, a, b, c, e):
        return a + b + c + e


def function_a(a, b, c, d):
    pass

#--------------------------


class TestCase(unittest.TestCase):

    def setUp(self):
        self.stubs = stubout.StubOutForTesting()

    def tearDown(self):
        self.stubs.UnsetAll()


class TestMonkeyPatching(TestCase):
    def test_bad_targets(self):
        self.assertRaises(scrutinize.MissingModule, scrutinize.get_module,
                          "missing.py")
        self.assertRaises(scrutinize.MissingModule, scrutinize.get_module,
                          "missing.py|")

        self.assertRaises(scrutinize.MissingModule, scrutinize.get_module,
                          "test/mymodule.py|")
        self.assertRaises(scrutinize.MissingModule,
                          scrutinize.get_module, "test/mymodule.py|Foo")

        self.assertFalse("AnyModuleName" in sys.modules)
        self.assertRaises(scrutinize.MissingMethodOrFunction,
                          scrutinize.get_module,
                          "test/mymodule.py|AnyModuleName:")
        self.assertTrue("AnyModuleName" in sys.modules)

    def test_good_external_targets(self):
        self.assertEquals(("test.mymodule", "Foo", "method_a"),
                scrutinize.get_module(
                            "test/mymodule.py|test.mymodule:Foo.method_a"))

        self.assertEquals(("that_module", "", "function_a"),
                scrutinize.get_module(
                            "test/mymodule.py|that_module:function_a"))

    def test_bad_find_code(self):
        self.assertRaises(AttributeError,
                    scrutinize.find_code, "test_scrutinize:missing")

    def test_good_find_code(self):
        self.assertEquals(level_1,
                    scrutinize.find_code("test_scrutinize:level_1"))
        self.assertEquals(Foo.method_a,
                    scrutinize.find_code("test_scrutinize:Foo.method_a"))

        # Note: if we're comparing references, they have to come
        # from the same module. So we have to make sure we name
        # the module used in find_code() the same as the one in the
        # import statement. Otherwise, it'll re-import the module
        # and the references will be different.
        diff = scrutinize.find_code("test/external/test_module.py|"
                                 "some_random_name:Blah.method_b")
        same = scrutinize.find_code("test/external/test_module.py|"
                                 "external.test_module:Blah.method_b")
        import external.test_module
        self.assertEqual(same, external.test_module.Blah.method_b)
        self.assertNotEqual(diff, external.test_module.Blah.method_b)


    def test_load_plugins(self):
        self.assertEquals({}, scrutinize.load_plugins(None))
        self.assertEquals({}, scrutinize.load_plugins({}))
        # No need to test the rest of the function since
        # it's dealt with elsewhere.

    def test_plugin_wrapper_no_collector(self):
        class TestBundle(object):
            label = 'test'
            label_extractor = None
            collector = None

        wrapped = scrutinize.plugin_wrapper(TestBundle())
        self.assertRaises(scrutinize.NoCollector, wrapped)

    def test_plugin_wrapper_happy_day(self):
        collected_metrics =  [('label_a', 10), ('label_b', 20)]

        class TestCollector(collectors.Collector):
            called = []

            def start(iself, label):
                iself.called.append(1)
                return super(TestCollector, iself).start(label)

            def stop(iself, state):
                iself.called.append(2)
                super(TestCollector, iself).stop(state)
                return collected_metrics

            def call_target(iself, __state, __bundle, *args, **kwargs):
                iself.called.append(3)
                self.assertEquals(__state, "test")
                return __bundle.target_impl(*args, **kwargs)

        class TestBundle(object):
            label = 'test'
            label_extractor = None
            collector = TestCollector({})

            def target_impl(iself, a, b, c=3):
                return a + b + c

            def notify(iself, metrics):
                self.assertEquals(collected_metrics, metrics)

        bundle = TestBundle()
        wrapped = scrutinize.plugin_wrapper(bundle)
        result = wrapped(1, 2)
        self.assertEquals(result, 6)
        self.assertEquals([1,3,2], bundle.collector.called)


def simple_function(a, b, c=3):
    return a + b + c


class TestExtractor(object):
    def extract(self, *args, **kwargs):
        return "label_a=%d" % args[0]


class TestCollector(collectors.Collector):
    called = False
    def call_target(self, __state, __bundle, *args, **kwargs):
        self.called = True
        return super(TestCollector, self).call_target(__state, __bundle,
                     *args, **kwargs)


class TestNotifier(object):
    pass


class TestBundle(TestCase):

    def setUp(self):
        super(TestBundle, self).setUp()
        label_extractors = {'extractor': TestExtractor()}
        collectors = {'collector': TestCollector({})}
        notifiers = {'notifier': TestNotifier()}

        config = dict(target='test_scrutinize:simple_function',
                      collector='collector',
                      label_extractor='extractor', notifiers=[])
        label = "undefined"
        self.bundle = scrutinize.Bundle(label, config, collectors,
                                        label_extractors, notifiers)

    def test_function(self):
        self.assertFalse(self.bundle.collector.called)
        self.bundle.inject()
        self.assertEquals(6, simple_function(1, 2))
        self.assertTrue(self.bundle.collector.called)
        self.bundle.collector.called = False
        self.bundle.reset()
        self.assertEquals(6, simple_function(1, 2))
        self.assertFalse(self.bundle.collector.called)

if False:
    filename = 'test.json'
    state = scrutinize.scrutinize(filename)

    # Try some
    function_a("label.from.extractor", 2, 3, 4)
    b = Blah()
    print b.method_b(10, 20, 30, 40)
    f = Foo()
    print f.method_a("scrutinize", 10, 10, 10)

    scrutinize.unwind(state)

    function_a("label.from.extractor", 2, 3, 4)
    print b.method_b(10, 20, 30, 40)
