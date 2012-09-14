import unittest2 as unittest
import sys

import stubout

import scrutinize

#--------------------------
# test functions/methods

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
    pass
    # print "__main__:function_a(%s, %s, %s, %s)" % (a, b, c, d)

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
