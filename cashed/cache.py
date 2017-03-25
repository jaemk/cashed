from collections import OrderedDict
from functools import wraps
import time


class CacheError(Exception):
    pass


class Sized(object):
    """
    Expects existence of:
        - self.size
        - self.capacity
        - self.store -> implements dict interface: __getitem__, __setitem__, __delitem__
    """
    def __getitem__(self, key):
        v = self.store[k]
        self.move_to_last(key, v)
        return v

    def __setitem__(self, key, value):
        try:
            # look for & remove existing duplicate
            self.store[key]
        except KeyError:
            # we're adding a new item to the cache
            self.size += 1

        # ordered dict will insert on the end
        self.store[key] = value

        if self.size > self.capacity:
            try:
                # drop the first (oldest) item
                to_drop = next(iter(self.store))
                self.__delitem__(to_drop)
            except StopIteration:
                assert False, "SizedCache size is {size}, but cache is empty.".format(size=self.size)

    def __delitem__(self, key):
        del self.store[key]
        self.size -= 1

    def move_to_last(self, key, value):
        """
        Implement our own move_to_end for old python
        """
        if hasattr(self.store, 'move_to_end'):
            self.store.move_to_end(key, last=True)
        else:
            # our patched __setitem__ will first delete existing entries
            self[key] = value


class Timed(object):
    """
    Timed iterface
     - Expects existence of:
        - self.store -> implements dict interface: __getitem__, __setitem__, __delitem__
    """
    def __getitem__(self, key):
        now = time.time()
        then, val = self.store[key]
        if (now - then) > self.limit:
            del self.store[key]
            raise KeyError
        return val

    def __setitem__(self, key, value):
        now = time.time()
        stamped_val = (now, value)
        self.store[key] = stamped_val


class TimedCache(Timed):
    """
    Timed cache
     - Expects a `seconds` kwargs to limit age of cache items
    """
    def __init__(self, seconds=None):
        if seconds is None:
            raise CacheError("TimedCache expects a single argument: `seconds`")
        self.store = {}
        self.limit = seconds

    def __repr__(self):
        return '<TimedCache[{}s]: {}>'.format(self.limit, [(k, self.store[k]) for k in self.store])

    def items(self):
        return self.store.items()


class SizedCache(Sized):
    """
    Simple `sized` cache
     - Expects a `capacity` kwarg to limit cache size
     - Will evict the least recently set or read k, v pair
    """
    def __init__(self, capacity=None):
        if capacity is None:
            raise CacheError("SizedCache expects a single argument: `capacity`")
        self.capacity = capacity
        self.size = 0
        self.store = OrderedDict()

    def __repr__(self):
        return '<SizedCache[{}cap : {}size]: {}>'\
               .format(self.capacity, self.size, [(k, self.store[k]) for k in self.store])

    def items(self):
        return self.store.items()


class TimedSizedCache(Timed, Sized):
    def __init__(self, capacity=None, seconds=None):
        if capacity is None or seconds is None:
            raise CacheError("TimedSizedCache expects a two arguments: `capacity`, `seconds`")
        self.limit = seconds
        self.capacity = capacity
        self.size = 0
        self.store = OrderedDict()

    def __repr__(self):
        return '<TimedSizedCache[{}cap, {}size, {}s]: {}>'\
                .format(self.capacity, self.size, self.limit, [(k, self.store[k]) for k in self.store])

    def items(self):
        return self.store.items()


def cached(capacity=None, seconds=None):
    """ Decorator to wrap a function with an optionally sized or timed cache. """
    if capacity is not None and seconds is not None:
        cache = TimedSizedCache(capacity=capacity, seconds=seconds)
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
                raise CacheError('Inputs args: {}, kwargs: {} are not cacheable. All arguments must be hashable'\
                                 .format(args, kwargs))
            except KeyError:
                v = func(*args, **kwargs)
                cache[key] = v
            return v
        return wrapper
    return _cached

