import time

import collectors
import common

# The "self" would normally be eaten by the wrapper.
def slow_function(self, count):
    n = 1.0
    for x in xrange(count):
        n = n / 2.0
    return n


class TestProfile(common.TestCase):
    def test_start(self):
        profile = collectors.Profile({})
        self.assertEquals({"label":"hi"}, profile.start("hi"))

    def test_stop(self):
        profile = collectors.Profile({})
        state = dict(label='hi', metrics=[(10, 1, "foo"), (20, 2, "blah")])
        expected = [('hi.foo', 10), ('hi.blah', 20)]
        self.assertEquals(expected, profile.stop(state))

    def test_scrub(self):
        profile = collectors.Profile({})
        self.assertEquals("v_w_x_y_z", profile._scrub("v/w.x|y:z"))

    def test_label(self):
        class Code(object):
            co_filename = "/usr/home/foo/my_filename.txt"
            co_name = "my_function"
            co_firstlineno = 100

        profile = collectors.Profile({})
        self.assertEquals(None, profile._label("xxx"))
        self.assertEquals(
                    "_usr_home_foo_my_filename_txt.my_function.line_0100",
                    profile._label(Code()))

    def test_call(self):
        class FakeBundle(object):
            target_impl = slow_function

        # Do two profilings and make sure the second is
        # a smaller answer and takes longer than the first one.
        profile = collectors.Profile({})
        state = {}
        bundle = FakeBundle()
        answer1 = profile.call_target(state, bundle, 100)
        self.assertTrue(answer1 < 0.000005)
        metrics = state['metrics']
        self.assertEquals(1, len(metrics))
        value1, count1, label1 = metrics[0]
        self.assertEquals(1, count1)

        answer2 = profile.call_target(state, bundle, 1000)
        self.assertTrue(answer2 < answer1)
        metrics = state['metrics']
        self.assertEquals(1, len(metrics))
        value2, count2, label2 = metrics[0]
        self.assertEquals(1, count2)

        self.assertEquals(label1, label2)
        self.assertTrue(value2 > value1)


class TestTimer(common.TestCase):
    def test_diff(self):
        profile = collectors.Time({})
        state = profile.start("foo")
        time.sleep(.1)
        metrics = profile.stop(state)
        self.assertEquals(1, len(metrics))
        label, elapsed = metrics[0]
        self.assertEquals(label, "foo")
        self.assertTrue(elapsed > .10)
        self.assertTrue(elapsed < .15)
