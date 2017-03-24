from collections import OrderedDict
from functools import wraps
import time


class CacheError(Exception):
    pass


class SizedCache(OrderedDict):
    """
    Simple `sized` cache
     - Expects a `capacity` kwarg to limit cache size
     - Will evict the least recently set or read k, v pair
    """
    def __init__(self, capacity=None, *args, **kwargs):
        if capacity is None:
            raise ValueError("SizedCache expects a single argument: `capacity`")
        self.capacity = capacity
        self.size = 0
        super(SizedCache, self).__init__(*args, **kwargs)

    def __getitem__(self, key):
        v = super(SizedCache, self).__getitem__(key)
        self.move_to_last(key, v)
        return v

    def __setitem__(self, key, value):
        try:
            # look for & remove existing duplicate
            super(SizedCache, self).__delitem__(key)
        except KeyError:
            # we're adding a new item to the cache
            self.size += 1

        # ordered dict will insert on the end
        super(SizedCache, self).__setitem__(key, value)

        if  self.size > self.capacity:
            try:
                # drop the first (oldest) item
                to_drop = self.iterkeys().next()
                self.__delitem__(to_drop)
            except StopIteration:
                assert False, "SizedCache size is {size}, but cache is empty.".format(size=self.size)

    def __delitem__(self, key):
        super(SizedCache, self).__delitem__(key)
        self.size -= 1

    def __repr__(self):
        """
        Need to override this since the default will do [(k, self[k]) for k in self]
        which will trigger a reorder of `self` in our patched __getitem__ while we're
        iterating through `self`
        """
        return '<SizedCache[{}cap : {}size]: {}>'\
               .format(self.capacity, self.size, [(k, super(SizedCache, self).__getitem__(k)) for k in self])

    def move_to_last(self, key, value):
        """
        Implement our own move_to_end for old python
        """
        if hasattr(self, 'move_to_end'):
            self.move_to_end(key, last=True)
        else:
            # our patched __setitem__ will first delete existing entries
            self[key] = value

    def items(self):
        raise CacheError("`items` disabled")

    def values(self):
        raise CacheError("`values` disabled")


class TimedCache(dict):
    """
    Simple `timed` cache
     - Expects a `seconds` kwarg to limit age of items
     - Evicts overage items on lookups
    """
    def __init__(self, seconds=None, *args, **kwargs):
        if seconds is None:
            raise ValueError("TimedCached expects a single argument: `seconds`")
        self.limit = seconds
        super(TimedCache, self).__init__(*args, **kwargs)

    def __getitem__(self, key):
        now = time.time()
        then, val = super(TimedCache, self).__getitem__(key)
        if (now - then) > self.limit:
            super(TimedCache, self).__delitem__(key)
            raise KeyError
        return val

    def __setitem__(self, key, value):
        now = time.time()
        stamped_val = (now, value)
        super(TimedCache, self).__setitem__(key, stamped_val)

    def __repr__(self):
        return '<TimedCache[{}s]: {}>'.format(self.limit, [(k, super(TimedCache, self).__getitem__(k)) for k in self])

    def items(self):
        raise CacheError("`items` disabled")

    def values(self):
        raise CacheError("`values` disabled")


def cached(capacity=None, seconds=None):
    """ Decorator to wrap a function with an optionally sized or timed cache. """
    if capacity is not None and seconds is not None:
        raise CacheError("Cache can currently only be sized or timed")
    elif capacity is not None:
        cache = SizedCache(capacity=capacity)
    elif seconds is not None:
        cache = TimedCache(seconds=seconds)
    else:
        cache = {}

    def _cached(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = (tuple(args), tuple((k, v) for k, v in kwargs.items()))
            try:
                v = cache[key]
            except TypeError:
                raise CacheError('Inputs args: {}, kwargs: {} are not cacheable. All arguments must implement __hash__'\
                                 .format(args, kwargs))
            except KeyError:
                v = func(*args, **kwargs)
                cache[key] = v
            return v
        return wrapper
    return _cached

