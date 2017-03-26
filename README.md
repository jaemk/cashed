# python-cashed [![Build Status](https://travis-ci.org/jaemk/cashed.svg?branch=master)](https://travis-ci.org/jaemk/cashed) [![PyPI version](https://badge.fury.io/py/cashed.svg)](https://badge.fury.io/py/cashed)

> Simple caching using decorators

## Intallation

`pip install cashed`

## Usage

The `cached` decorator requires the arguments of the wrapped function to be hashable.
`cached` accepts arguments `capacity` and `seconds` to limit the size of the cache and limit age of cached items.

```python
from cashed import cached

@cached(capacity=100)
def fib(n):
    if n == 0 or n == 1:
        return n
    return fib(n-1) + fib(n-2)
```
