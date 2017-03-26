import unittest
import time
from cashed import cached


class BasicCacheTest(unittest.TestCase):
    def setUp(self):
        @cached()
        def cached_op(n):
            time.sleep(1)
            return n
        self.cached_op = cached_op

    @staticmethod
    def uncached_op(n):
        time.sleep(1)

    def test_basic_cache(self):
        n = 5
        start = time.time()
        [self.uncached_op(1) for _ in range(n)]
        elap1 = time.time() - start

        start = time.time()
        [self.cached_op(1) for _ in range(n)]
        elap2 = time.time() - start

        self.assertTrue(elap1 > elap2, "cached op is faster")


class SizedCacheTest(unittest.TestCase):
    def setUp(self):
        @cached(capacity=3, debug=True)
        def cached_op(k, value=None):
            time.sleep(1)
            return value
        self.cached_op = cached_op

    def test_sized_cache(self):
        [self.cached_op(n) for n in range(3)]
        _, was_cached = self.cached_op(2)
        self.assertTrue(was_cached)
        _, was_cached = self.cached_op(20)
        self.assertFalse(was_cached)
        _, was_cached = self.cached_op(0)
        self.assertFalse(was_cached)


class TimedCacheTest(unittest.TestCase):
    def setUp(self):
        @cached(seconds=3, debug=True)
        def cached_op(n):
            time.sleep(1)
            return n
        self.cached_op = cached_op

    def test_timed_cache(self):
        self.cached_op(1)
        _, was_cached = self.cached_op(1)
        self.assertTrue(was_cached)
        time.sleep(3)
        _, was_cached = self.cached_op(1)
        self.assertFalse(was_cached)


class TimedSizedCacheTest(unittest.TestCase):
    def setUp(self):
        @cached(seconds=3, capacity=2, debug=True)
        def cached_op(n):
            time.sleep(1)
            return n
        self.cached_op = cached_op

    def test_timedsized_cache(self):
        [self.cached_op(n) for n in range(2)]
        _, was_cached = self.cached_op(2)
        self.assertFalse(was_cached)
        _, was_cached = self.cached_op(0)
        self.assertFalse(was_cached)
        time.sleep(3)
        _, was_cached = self.cached_op(2)
        self.assertFalse(was_cached)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(BasicCacheTest, 'test_basic'))
    suite.addTest(unittest.makeSuite(SizedCacheTest, 'test_sized'))
    suite.addTest(unittest.makeSuite(TimedCacheTest, 'test_timed'))
    suite.addTest(unittest.makeSuite(TimedSizedCacheTest, 'test_timedsized'))
    return suite

