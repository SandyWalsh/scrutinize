import random
import sys


def do_it(number):
    x = range(number)
    random.shuffle(x)
    words = 'scrutinize allows you to externally monkey patch ' \
            'python programs with performance and measurement ' \
            'wrappers'.split(' ')
    result = [words[y % len(words)] for y in x]
    return " ".join(result)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "Usage: sample.py <num_iterations>"
        sys.exit(1)

    number = sys.argv[1]
    print do_it(int(number))
