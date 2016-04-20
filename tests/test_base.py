"""
This module is excluded from the test discovery by the load_tests() function in this file.
You can use this module to declare reusable test base classes/mixins.
"""

import pickle
from unittest import TestCase, TestSuite


class PicklingTestCase(TestCase):
    def _pickle_and_unpickle(self, flags):
        pickled = pickle.dumps(flags)
        unpickled = pickle.loads(pickled)
        self.assertEqual(unpickled, flags)
        # Just making sure...
        self.assertEqual(unpickled.bits, flags.bits)


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
