from collections import OrderedDict
from collections import namedtuple
from functools import wraps
import time


class CacheError(Exception):
    pass


class Sized(object):
    """
    Expects existence of:
        - self.size      -> current size (int)
        - self.capacity  -> max cache size (int)
        - self.store -> implements dict interface: __getitem__, __setitem__, __delitem__
    """
    def sized_get(self, key):
        v = self.store[key]
        self.move_to_last(key, v)
        return v

    def sized_set(self, key, value):
        if key not in self.store:
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

    def sized_del(self, key):
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
        - self.limit -> seconds (int)
        - self.store -> implements dict interface: __getitem__, __setitem__, __delitem__
    """
    def timed_get(self, key):
        now = time.time()
        then, val = self.store[key]
        if (now - then) > self.limit:
            self.__delitem__(key)
            raise KeyError
        return val

    def timed_set(self, key, value, return_dont_set=False):
        now = time.time()
        stamped_val = (now, value)
        if return_dont_set:
            return stamped_val
        self.store[key] = stamped_val

    def timed_del(self, key):
        del self.store[key]


class TimedCache(Timed):
    """
    Timed cache
     - Expects a `seconds` kwargs to limit age of cache items
    """
    def __init__(self, seconds=None):
        """
        :param seconds: int, required
        """
        if seconds is None:
            raise CacheError("TimedCache expects a single argument: `seconds`")
        self.store = {}
        self.limit = seconds
        self.size = 0

    def __getitem__(self, key):
        return self.timed_get(key)

    def __setitem__(self, key, value):
        if key not in self.store:
            self.size += 1
        return self.timed_set(key, value)

    def __delitem__(self, key):
        self.size -= 1
        return self.timed_del(key)

    def __repr__(self):
        return '<TimedCache[{}s]>'.format(self.limit)

    def _safe_get(self, k):
        try:
            return self[k]
        except KeyError:
            return None

    def items(self):
        keys = list(self.store.keys())
        return (pair for pair in ((k, self._safe_get(k)) for k in keys)
                if pair[-1] is not None)

    def clean(self):
        [_ for _ in self.items()]


class SizedCache(Sized):
    """
    Simple `sized` cache
     - Expects a `capacity` kwarg to limit cache size
     - Will evict the least recently set or read k, v pair
    """
    def __init__(self, capacity=None):
        """
        :param capacity: int, required
        """
        if capacity is None:
            raise CacheError("SizedCache expects a single argument: `capacity`")
        self.capacity = capacity
        self.size = 0
        self.store = OrderedDict()

    def __getitem__(self, key):
        return self.sized_get(key)

    def __setitem__(self, key, value):
        return self.sized_set(key, value)

    def __delitem__(self, key):
        return self.sized_del(key)

    def __repr__(self):
        return '<SizedCache[{}cap : {}size]>'\
               .format(self.capacity, self.size)

    def items(self):
        return ((k, self[k]) for k in self.store)


class TimedSizedCache(Timed, Sized):
    """
    Enforces `Timed` and `Sized` cache constraints
    """
    def __init__(self, capacity=None, seconds=None):
        """
        :param capacity: int, required
        :param seconds: int, required
        """
        if capacity is None or seconds is None:
            raise CacheError("TimedSizedCache expects a two arguments: `capacity`, `seconds`")
        self.limit = seconds
        self.capacity = capacity
        self.size = 0
        self.store = OrderedDict()

    def __getitem__(self, key):
        _ = self.timed_get(key)
        t, value = self.sized_get(key)
        return value

    def __setitem__(self, key, value):
        stamped_val = self.timed_set(key, value, return_dont_set=True)
        return self.sized_set(key, stamped_val)

    def __delitem__(self, key):
        return self.sized_del(key)

    def __repr__(self):
        return '<TimedSizedCache[{}cap, {}size, {}s]>'\
                .format(self.capacity, self.size, self.limit)

    def _safe_get(self, k):
        try:
            return self[k]
        except KeyError:
            return None

    def items(self):
        keys = list(self.store.keys())
        return (pair for pair in ((k, self._safe_get(k)) for k in keys)
                if pair[-1] is not None)

    def clean(self):
        [_ for _ in self.items()]


class CountDict(dict):
    def __init__(self):
        self.size = 0
        super(CountDict, self).__init__()

    def __setitem__(self, key, value):
        if key not in self:
            self.size += 1
        super(CountDict, self).__setitem__(key, value)

    def __delitem__(self, key):
        self.size -= 1
        super(CountDict, self).__delitem__(key, value)


def cached(capacity=None, seconds=None, debug=False):
    """ Decorator to wrap a function with an optionally sized or timed cache. """
    info = {'hits': 0, 'misses': 0}
    if capacity is not None and seconds is not None:
        cache = TimedSizedCache(capacity=capacity, seconds=seconds)
        info['capacity'] = capacity
        info['seconds'] = seconds
    elif capacity is not None:
        cache = SizedCache(capacity=capacity)
        info['capacity'] = capacity
    elif seconds is not None:
        cache = TimedCache(seconds=seconds)
        info['seconds'] = seconds
    else:
        cache = CountDict()

    def _cached(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = (tuple(args), tuple((k, v) for k, v in kwargs.items()))
            try:
                v = cache[key]
                was_cached = True
                info['hits'] += 1
            except TypeError:
                raise CacheError('Inputs args: {}, kwargs: {} are not cacheable. All arguments must be hashable'\
                                 .format(args, kwargs))
            except KeyError:
                v = func(*args, **kwargs)
                cache[key] = v
                was_cached = False
                info['misses'] += 1
            if debug:
                return v, was_cached
            return v

        def _cache_info():
            if hasattr(cache, 'clean'):
                cache.clean()
            info.update({'size': cache.size})
            return info
        wrapper.cache_info = _cache_info
        wrapper.cache_access = cache
        return wrapper
    return _cached

