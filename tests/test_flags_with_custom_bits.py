import re
from unittest import TestCase

from flags import Flags, FlagData, UNDEFINED


class TestAutoAssignedBits(TestCase):
    def test_auto_assign_with_flag_data(self):
        class MyFlagData(FlagData):
            pass

        my_flag_data = MyFlagData()

        class MyFlags(Flags):
            f0 = 0b001
            f1 = my_flag_data
            f2 = 0b010

        self.assertListEqual([MyFlags.f0.bits, MyFlags.f1.bits, MyFlags.f2.bits], [0b001, 0b100, 0b010])
        self.assertIsNone(MyFlags.f0.data)
        self.assertIs(MyFlags.f1.data, my_flag_data)
        self.assertIsNone(MyFlags.f2.data)

    def test_auto_assign_with_empty_tuple(self):
        class MyFlags(Flags):
            f0 = 0b0011
            f1 = ()
            f2 = 0b1000

        self.assertListEqual([MyFlags.f0.bits, MyFlags.f1.bits, MyFlags.f2.bits], [0b0011, 0b0100, 0b1000])
        self.assertIsNone(MyFlags.f0.data)
        self.assertIsNone(MyFlags.f1.data)
        self.assertIsNone(MyFlags.f2.data)

    def test_auto_assign_with_empty_list(self):
        class MyFlags(Flags):
            f0 = 0b0011
            f1 = []
            f2 = 0b0110

        self.assertListEqual([MyFlags.f0.bits, MyFlags.f1.bits, MyFlags.f2.bits], [0b0011, 0b1000, 0b0110])
        self.assertIsNone(MyFlags.f0.data)
        self.assertIsNone(MyFlags.f1.data)
        self.assertIsNone(MyFlags.f2.data)


class TestFlagsDeclarationErrors(TestCase):
    def test_data_tuple_longer_than_2(self):
        with self.assertRaisesRegex(
                ValueError,
                re.escape(r"Iterable is expected to have at most 2 items instead of 3 "
                          r"for flag 'f0', iterable: (None, None, None)")):
            class MyFlags(Flags):
                f0 = (None, None, None)

    def test_data_list_longer_than_2(self):
        with self.assertRaisesRegex(
                ValueError,
                re.escape(r"Iterable is expected to have at most 2 items instead of 3 "
                          r"for flag 'f0', iterable: [None, None, None]")):
            class MyFlags(Flags):
                f0 = [None, None, None]

    def test_bits_is_str(self):
        with self.assertRaisesRegex(
                ValueError,
                re.escape(r"Iterable is expected to have at most 2 items instead of 8 "
                          r"for flag 'f0', iterable: 'str_bits'")):
            class MyFlags(Flags):
                f0 = 'str_bits'

    def test_bits_is_bool(self):
        with self.assertRaisesRegex(
                TypeError,
                re.escape(r"Expected an int or an iterable of at most 2 items for flag 'f0', received False")):
            class MyFlags(Flags):
                f0 = False

    def test_bits_is_none(self):
        with self.assertRaisesRegex(
                TypeError,
                re.escape(r"Expected an int or an iterable of at most 2 items for flag 'f0', received None")):
            class MyFlags(Flags):
                f0 = None

    def test_bits_is_bool_in_2_long_tuple(self):
        with self.assertRaisesRegex(
                TypeError,
                re.escape(r"Expected an int value as the bits of flag 'f0', received False")):
            class MyFlags(Flags):
                f0 = (False, 'data0')

    def test_bits_is_str_in_2_long_tuple(self):
        with self.assertRaisesRegex(
                TypeError,
                re.escape(r"Expected an int value as the bits of flag 'f0', received 5.5")):
            class MyFlags(Flags):
                f0 = 5.5, 'data0'

    def test_none_as_bits_in_2_long_tuple(self):
        with self.assertRaisesRegex(
                TypeError,
                re.escape(r"Expected an int value as the bits of flag 'f1', received None")):
            class MyFlags(Flags):
                f0 = 0b0011
                f1 = (None, 'data1')
                f2 = 0b0110

    def test_none_as_bits_in_2_long_list(self):
        with self.assertRaisesRegex(
                TypeError,
                re.escape(r"Expected an int value as the bits of flag 'f1', received None")):
            class MyFlags(Flags):
                f0 = 0b0011
                f1 = [None, 'data1']
                f2 = 0b0110
