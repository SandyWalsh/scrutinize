import sys

import scrutinize
import collectors

import common


def dummy_function():
    pass


class DummyClass(object):
    def method_a(self):
        pass


class TestMonkeyPatching(common.TestCase):
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
        self.assertEquals(dummy_function,
                    scrutinize.find_code("test_scrutinize:dummy_function"))
        self.assertEquals(DummyClass.method_a,
                    scrutinize.find_code(
                                    "test_scrutinize:DummyClass.method_a"))

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


class FakeClass(object):
    def simple_method(self, a, b, c=3):
        return a + b + c


class FakeFunctionExtractor(object):
    def extract(self, *args, **kwargs):
        return "label_a=%s" % args[0]


class FakeMethodExtractor(object):
    def extract(self, classself, *args, **kwargs):
        return "label_a=%s" % args[0]


class FakeCollector(collectors.Collector):
    called = False
    label = None
    def call_target(self, __state, __bundle, *args, **kwargs):
        self.called = True
        self.label = __state
        return super(FakeCollector, self).call_target(__state, __bundle,
                     *args, **kwargs)


class FakeNotifier(object):
    called = False
    def send(self, metrics):
        self.called = True


class TestBundle(common.TestCase):

    def _set_bundle(self, target, extractor):
        label_extractors = {'function': FakeFunctionExtractor(),
                            'method': FakeMethodExtractor()}
        collectors = {'collector': FakeCollector({})}
        notifiers = {'notifier': FakeNotifier()}

        config = dict(target=target,
                      collector='collector',
                      notifiers=['notifier',],
                      label_extractor=extractor)
        label = "undefined"
        self.bundle = scrutinize.Bundle(label, config, collectors,
                                        label_extractors, notifiers)

    def test_function(self):
        self._set_bundle('test_scrutinize:simple_function', 'function')

        self.assertFalse(self.bundle.collector.called)
        self.assertFalse(self.bundle.send_list[0].called)
        self.bundle.inject()
        self.assertEquals(6, simple_function(1, 2))
        self.assertTrue(self.bundle.collector.called)
        self.assertTrue(self.bundle.send_list[0].called)

        # Also make sure we extracted the label correctly
        self.assertEqual("label_a=1", self.bundle.collector.label)

        # Reset and make sure it's all unwound again.
        self.bundle.collector.called = False
        self.bundle.reset()
        self.assertEquals(6, simple_function(1, 2))
        self.assertFalse(self.bundle.collector.called)

    def test_method(self):
        self._set_bundle('test_scrutinize:FakeClass.simple_method', 'method')

        self.assertFalse(self.bundle.collector.called)
        self.assertFalse(self.bundle.send_list[0].called)
        self.bundle.inject()
        fake = FakeClass()
        self.assertEquals(6, fake.simple_method(1, 2))
        self.assertTrue(self.bundle.collector.called)
        self.assertTrue(self.bundle.send_list[0].called)

        # Also make sure we extracted the label correctly
        self.assertEqual("label_a=1", self.bundle.collector.label)

        # Reset and make sure it's all unwound again.
        self.bundle.collector.called = False
        self.bundle.reset()
        fake = FakeClass()
        self.assertEquals(6, fake.simple_method(1, 2))
        self.assertFalse(self.bundle.collector.called)
