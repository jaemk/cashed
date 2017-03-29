import time
from itertools import chain, repeat
from cashed import cached


pairs = [('james', None),
         ('james', 'bean'),
         ('bob', 'bill'),
         ('lauren', 'bailey'),
         ('lauren', None),]


@cached(capacity=10, seconds=30)
def slow_op(name, pet_name=None):
    time.sleep(1)
    pet = pet_name if pet_name else 'no pet!'
    return '{name} : {pet}'.format(name=name, pet=pet)


print('** Examples 1 **')
for name, pet in chain(*repeat(pairs, 3)):
    start = time.time()
    ans = slow_op(name, pet_name=pet)
    print('{} -> {}'.format(time.time()-start, ans))
print(slow_op.cache_info())


######


def fib_slow(n):
    if n == 0 or n == 1:
        return n
    return fib_slow(n-1) + fib_slow(n-2)


@cached(capacity=100)
def fib_fast(n):
    if n == 0 or n == 1:
        return n
    return fib_fast(n-1) + fib_fast(n-2)


print('** Examples 2 **')
for _type, func in [('uncached', fib_slow), ('cached', fib_fast)]:
    start = time.time()
    for n in range(30):
        v = func(n)
    print(' ** {} -> {}s **'.format(_type, time.time()-start))
    print(fib_fast.cache_info())

