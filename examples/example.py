import sys
import time
from itertools import repeat, chain
from cashed.cache import cached


def fib_slow(n):
    if n == 0 or n == 1:
        return n
    return fib_slow(n-1) + fib_slow(n-2)


@cached(capacity=100)
def fib_fast(n):
    if n == 0 or n == 1:
        return n
    return fib_fast(n-1) + fib_fast(n-2)


@cached(seconds=5)
def slow_hello(name, color='brown'):
    time.sleep(1)
    return 'Hello, {}! ({})'.format(name, color)


def run(a=0, b=35):
    # fibs
    for m, f in [('uncached', fib_slow), ('cached', fib_fast)]:
        print(' ** {m} [{a}->{b}] **'.format(m=m, a=a, b=b))
        start = time.time()
        for n in range(a, b):
            v = f(n)
        print(' ** {m} -> {t}s **'.format(m=m, t=time.time()-start))

    # slow funcs
    for _ in range(10):
        start = time.time()
        resp = slow_hello('James', color='green')
        dur = time.time() - start
        print(' ** {} -> {}s'.format(resp, dur))


if __name__ == '__main__':
    args = sys.argv[1:]
    a_b = {}
    if len(args) == 2:
        a, b = args
        a_b = {'a': int(a), 'b': int(b)}
    run(**a_b)

