import re
from unittest import TestCase

from flags import BitFlags


class TestAutoAssignedBits(TestCase):
    def test_auto_assign_with_none(self):
        class MyFlags(BitFlags):
            f0 = 0b001
            f1 = None
            f2 = 0b010

        self.assertListEqual([MyFlags.f0.bits, MyFlags.f1.bits, MyFlags.f2.bits], [0b001, 0b100, 0b010])
        self.assertIsNone(MyFlags.f0.data)
        self.assertIsNone(MyFlags.f1.data)
        self.assertIsNone(MyFlags.f2.data)

    def test_auto_assign_with_empty_tuple(self):
        class MyFlags(BitFlags):
            f0 = 0b0011
            f1 = ()
            f2 = 0b1000

        self.assertListEqual([MyFlags.f0.bits, MyFlags.f1.bits, MyFlags.f2.bits], [0b0011, 0b0100, 0b1000])
        self.assertIsNone(MyFlags.f0.data)
        self.assertIsNone(MyFlags.f1.data)
        self.assertIsNone(MyFlags.f2.data)

    def test_auto_assign_with_empty_list(self):
        class MyFlags(BitFlags):
            f0 = 0b0011
            f1 = []
            f2 = 0b0110

        self.assertListEqual([MyFlags.f0.bits, MyFlags.f1.bits, MyFlags.f2.bits], [0b0011, 0b1000, 0b0110])
        self.assertIsNone(MyFlags.f0.data)
        self.assertIsNone(MyFlags.f1.data)
        self.assertIsNone(MyFlags.f2.data)

    def test_auto_assign_with_none_in_tuple(self):
        class MyFlags(BitFlags):
            f0 = 0b0011
            f1 = (None,)
            f2 = 0b0110

        self.assertListEqual([MyFlags.f0.bits, MyFlags.f1.bits, MyFlags.f2.bits], [0b0011, 0b1000, 0b0110])
        self.assertIsNone(MyFlags.f0.data)
        self.assertIsNone(MyFlags.f1.data)
        self.assertIsNone(MyFlags.f2.data)

    def test_auto_assign_with_none_in_list(self):
        class MyFlags(BitFlags):
            f0 = 0b0011
            f1 = [None]
            f2 = 0b0110

        self.assertListEqual([MyFlags.f0.bits, MyFlags.f1.bits, MyFlags.f2.bits], [0b0011, 0b1000, 0b0110])
        self.assertIsNone(MyFlags.f0.data)
        self.assertIsNone(MyFlags.f1.data)
        self.assertIsNone(MyFlags.f2.data)

    def test_auto_assign_with_none_and_data_in_tuple(self):
        class MyFlags(BitFlags):
            f0 = 0b0011
            f1 = (None, 'data1')
            f2 = 0b0110

        self.assertListEqual([MyFlags.f0.bits, MyFlags.f1.bits, MyFlags.f2.bits], [0b0011, 0b1000, 0b0110])
        self.assertIsNone(MyFlags.f0.data)
        self.assertEqual(MyFlags.f1.data, 'data1')
        self.assertIsNone(MyFlags.f2.data)

    def test_auto_assign_with_none_and_data_in_list(self):
        class MyFlags(BitFlags):
            f0 = 0b0011
            f1 = [None, 'data1']
            f2 = 0b0110

        self.assertListEqual([MyFlags.f0.bits, MyFlags.f1.bits, MyFlags.f2.bits], [0b0011, 0b1000, 0b0110])
        self.assertIsNone(MyFlags.f0.data)
        self.assertEqual(MyFlags.f1.data, 'data1')
        self.assertIsNone(MyFlags.f2.data)


class TestBitFlagsDeclarationErrors(TestCase):
    def test_data_tuple_longer_than_2(self):
        with self.assertRaisesRegex(
                ValueError,
                re.escape(r"Expected a tuple/list of at most 2 items (bits, data) "
                          r"for flag 'f0', received (None, None, None)")):
            class MyFlags(BitFlags):
                f0 = (None, None, None)

    def test_data_list_longer_than_2(self):
        with self.assertRaisesRegex(
                ValueError,
                re.escape(r"Expected a tuple/list of at most 2 items (bits, data) "
                          r"for flag 'f0', received [None, None, None]")):
            class MyFlags(BitFlags):
                f0 = [None, None, None]

    def test_bits_is_str(self):
        with self.assertRaisesRegex(
                TypeError,
                re.escape(r"Expected None or an int object for the bits of flag 'f0', received 'str_bits'")):
            class MyFlags(BitFlags):
                f0 = 'str_bits'

    def test_bits_is_str_in_1_long_tuple(self):
        with self.assertRaisesRegex(
                TypeError,
                re.escape(r"Expected None or an int object for the bits of flag 'f0', received False")):
            class MyFlags(BitFlags):
                f0 = (False,)

    def test_bits_is_str_in_2_long_tuple(self):
        with self.assertRaisesRegex(
                TypeError,
                re.escape(r"Expected None or an int object for the bits of flag 'f0', received 5.5")):
            class MyFlags(BitFlags):
                f0 = 5.5, 'data0'
