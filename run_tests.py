import unittest
from tests import test_simple


def suite():
    suite = unittest.TestSuite()
    suite.addTest(test_simple.suite())
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

