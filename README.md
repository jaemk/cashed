# python-cashed [![Build Status](https://travis-ci.org/jaemk/cashed.svg?branch=master)](https://travis-ci.org/jaemk/cashed) [![PyPI version](https://badge.fury.io/py/cashed.svg)](https://badge.fury.io/py/cashed)

> Simple caching using decorators

## Intallation

`pip install cashed`

## Usage

The `cached` decorator requires the arguments of the wrapped function to be hashable.
`cached` accepts arguments `capacity` and `seconds` to limit the size of the cache and limit age of cached items.
`cached` functions similarly to `functools.lru_cache` with the additional of the optional time constraint.

```python
import time
from cashed import cached

@cached(capacity=100, seconds=5)
def fib(n):
    if n == 0 or n == 1:
        return n
    return fib(n-1) + fib(n-2)

fib(100)          # -> 354224848179261915075L
fib.cache_info()  # -> {'seconds': 5, 'hits': 98, 'capacity': 100, 'misses': 101, 'size': 100}
time.sleep(5)
fib.cache_info()  # -> {'hits': 98, 'capacity': 100, 'seconds': 5, 'misses': 101, 'size': 0}
```
