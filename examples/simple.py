import time
from itertools import chain, repeat
from cashed import cached

pairs = [('james', None),
         ('james', 'bean'),
         ('bob', 'bill'),
         ('lauren', 'bailey'),
         ('lauren', None),]

@cached(capacity=10)
def slow(name, pet_name=None):
    time.sleep(1)
    pet = pet_name if pet_name else 'no pet!'
    return '{name} : {pet}'.format(name=name, pet=pet)

for name, pet in chain(*repeat(pairs, 3)):
    ans = slow(name, pet_name=pet)
    print(ans)
