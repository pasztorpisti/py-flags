"""
This module is excluded from the test discovery by the load_tests() function in this file.
You can use this module to declare reusable test base classes/mixins.
"""

import pickle
import sys
from unittest import TestCase, TestSuite


class PicklingTestCase(TestCase):
    def _pickle_and_unpickle(self, flags):
        # Python3.3 and earlier pickle doesn't seem to handle __qualname__.
        # In python3.4 we already have protocol 4 that handles the __qualname__
        # of inner classes but we have to specify protocol 4 explicitly.
        # In python3.5 pickling inner classes works without specifying the protocol.
        if sys.version_info[:2] == (3, 4):
            pickled = pickle.dumps(flags, 4)
        else:
            pickled = pickle.dumps(flags)
        unpickled = pickle.loads(pickled)
        self.assertEqual(unpickled, flags)
        # Just making sure...
        self.assertEqual(int(unpickled), int(flags))


class PicklingSuccessTestBase(PicklingTestCase):
    FlagsClass = None

    def test_pickling_zero_flags(self):
        self._pickle_and_unpickle(self.FlagsClass.no_flags)

    def test_pickling_all_flags(self):
        self._pickle_and_unpickle(self.FlagsClass.all_flags)

    def test_pickling_single_flag(self):
        self._pickle_and_unpickle(self.FlagsClass.f0)
        self._pickle_and_unpickle(self.FlagsClass.f1)
        self._pickle_and_unpickle(self.FlagsClass.f2)
        self._pickle_and_unpickle(self.FlagsClass.f3)

    def test_pickling_two_flags(self):
        self._pickle_and_unpickle(self.FlagsClass.f1 | self.FlagsClass.f2)


def load_tests(loader, tests, pattern):
    return TestSuite()
