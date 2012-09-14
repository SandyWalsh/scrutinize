import scrutinize

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
