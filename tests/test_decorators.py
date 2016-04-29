import re
from unittest import TestCase

from flags import Flags, unique, unique_bits


class TestUniqueDecorator(TestCase):
    def test_with_no_duplicates(self):
        @unique
        class MyFlags(Flags):
            f0 = 1
            f1 = 2
            f2 = 4
            f3 = 8
            f4 = f2 | f3

    def test_with_duplicates(self):
        with self.assertRaisesRegex(ValueError,
                                    re.escape(r"duplicate values found in <flags MyFlags>: f1 -> f0, f4 -> f2")):
            @unique
            class MyFlags(Flags):
                f0 = 1
                f1 = 1
                f2 = 4
                f3 = 8
                f4 = f2

    def test_all_flags_is_excluded_from_unique_check(self):
        @unique
        class MyFlags(Flags):
            # all_flags is also 1 in this case
            f0 = 1

        @unique
        class MyFlags2(Flags):
            f0 = 1
            f1 = 2
            # all_flags is also 3 in this case
            f2 = 3

    def test_decorator_fails_with_non_final_flags_class(self):
        with self.assertRaisesRegex(TypeError,
                                    re.escape(r"unique check can be applied only to flags classes that have members")):
            @unique
            class MyFlags(Flags):
                pass


class TestUniqueBitsDecorator(TestCase):
    def test_with_no_overlapping_bits(self):
        @unique_bits
        class MyFlags(Flags):
            f0 = 1
            f1 = 2
            f2 = 4
            f3 = 8

    def test_with_overlapping_bits(self):
        with self.assertRaisesRegex(ValueError,
                                    r"<flags MyFlags>: '\w+' and '\w+' have overlapping bits"):
            @unique_bits
            class MyFlags(Flags):
                f0 = 1
                f1 = 2
                f2 = 3

        with self.assertRaisesRegex(ValueError,
                                    r"<flags MyFlags>: '\w+' and '\w+' have overlapping bits"):
            @unique_bits
            class MyFlags(Flags):
                f0 = 1
                f1 = 2
                f2 = 5

    def test_decorator_fails_with_non_final_flags_class(self):
        with self.assertRaisesRegex(TypeError,
                                    re.escape(r"unique check can be applied only to flags classes that have members")):
            @unique_bits
            class MyFlags(Flags):
                pass
