import collections
import re
from unittest import TestCase

from flags import Flags, FlagProperties, FlagData, Const, PROTECTED_FLAGS_CLASS_ATTRIBUTES, UNDEFINED


class TestUtilities(TestCase):
    """ Testing utility functions and other random stuff to satisfy coverage and make its output more useful. """
    def test_const_repr(self):
        self.assertEqual(repr(Const('name1')), 'name1')
        self.assertEqual(repr(Const('name2')), 'name2')

    def test_readonly_attribute_of_flag_properties(self):
        properties = FlagProperties(name='name', bits=1)
        # setting attributes shouldn't fail because properties.readonly==False
        properties.name = 'name2'
        properties.bits = 2

        del properties.index
        self.assertFalse(hasattr(properties, 'index'))

        # We set readonly=True. This disables modifying and deleting attributes of the object.
        properties.readonly = True

        with self.assertRaisesRegex(AttributeError,
                                    re.escape(r"Can't set attribute 'name' of readonly 'FlagProperties' object")):
            properties.name = 'name3'

        with self.assertRaisesRegex(AttributeError,
                                    re.escape(r"Can't set attribute 'readonly' of readonly 'FlagProperties' object")):
            properties.readonly = False

        with self.assertRaisesRegex(AttributeError,
                                    re.escape(r"Can't set attribute 'bits' of readonly 'FlagProperties' object")):
            properties.bits = 4

        with self.assertRaisesRegex(AttributeError,
                                    re.escape(r"Can't delete attribute 'index_without_aliases' of "
                                              r"readonly 'FlagProperties' object")):
            del properties.index_without_aliases

        # We hope that attempts to modify and delete our readonly attributes have failed.
        self.assertTrue(hasattr(properties, 'index_without_aliases'))
        self.assertEqual(properties.name, 'name2')
        self.assertEqual(properties.bits, 2)
        self.assertTrue(properties.readonly)


class TestFlagsMemberDeclaration(TestCase):
    """ Tests different ways of declaring the members/flags of a flags class. """
    def _test_flags_class(self, flags_class, *, unordered_members=False, has_data=False):
        def test_member(name, bits):
            member = getattr(flags_class, name)
            self.assertIs(type(member), flags_class)
            self.assertEqual(int(member), bits)

        if unordered_members:
            self.assertSetEqual({int(flags_class.f0), int(flags_class.f1), int(flags_class.f2)}, {1, 2, 4})
            for member_name in ('f0', 'f1', 'f2'):
                test_member(member_name, int(getattr(flags_class, member_name)))
        else:
            test_member('f0', 1)
            test_member('f1', 2)
            test_member('f2', 4)

        # special/virtual members
        test_member('no_flags', 0)
        test_member('all_flags', 7)

        self.assertEqual(len(flags_class), 3)
        self.assertSetEqual(set(flags_class), {flags_class.f0, flags_class.f1, flags_class.f2})

        if has_data:
            self.assertEqual(flags_class.f0.data, 'data0')
            self.assertEqual(flags_class.f1.data, 'data1')
            self.assertEqual(flags_class.f2.data, 'data2')

        # TODO: more checks

    def test_flag_names_as_class_members(self):
        class MyFlags(Flags):
            f0 = ['data0']
            f1 = ['data1']
            f2 = ['data2']
        self._test_flags_class(MyFlags, has_data=True)

    def test_flag_names_as_space_separated_list(self):
        class MyFlags(Flags):
            __members__ = 'f0 f1  f2'
        self._test_flags_class(MyFlags)

    def test_flag_names_as_comma_separated_list(self):
        class MyFlags(Flags):
            __members__ = ' f0,f1, f2'
        self._test_flags_class(MyFlags)

    def test_flag_names_as_tuple(self):
        class MyFlags(Flags):
            __members__ = ('f0', 'f1', 'f2')
        self._test_flags_class(MyFlags)

    def test_flag_names_as_list(self):
        class MyFlags(Flags):
            __members__ = ['f0', 'f1', 'f2']
        self._test_flags_class(MyFlags)

    def test_flag_names_as_set(self):
        class MyFlags(Flags):
            __members__ = {'f0', 'f1', 'f2'}
        self._test_flags_class(MyFlags, unordered_members=True)

    def test_flag_names_as_frozenset(self):
        class MyFlags(Flags):
            __members__ = frozenset(['f0', 'f1', 'f2'])
        self._test_flags_class(MyFlags, unordered_members=True)

    def test_flags_with_data_as_tuple(self):
        class MyFlags(Flags):
            __members__ = (('f0', ['data0']), ['f1', ['data1']], ('f2', ['data2']))
        self._test_flags_class(MyFlags, has_data=True)

    def test_flags_with_data_as_list(self):
        class MyFlags(Flags):
            __members__ = [('f0', ['data0']), ['f1', ['data1']], ('f2', ['data2'])]
        self._test_flags_class(MyFlags, has_data=True)

    def test_flags_with_data_as_set(self):
        class MyFlags(Flags):
            __members__ = {('f0', ('data0',)), ('f1', ('data1',)), ('f2', ('data2',))}
        self._test_flags_class(MyFlags, has_data=True, unordered_members=True)

    def test_flags_with_data_as_frozenset(self):
        class MyFlags(Flags):
            __members__ = frozenset([('f0', ('data0',)), ('f1', ('data1',)), ('f2', ('data2',))])
        self._test_flags_class(MyFlags, has_data=True, unordered_members=True)

    def test_flags_with_data_as_dict(self):
        class MyFlags(Flags):
            __members__ = dict(f0=['data0'], f1=['data1'], f2=['data2'])
        self._test_flags_class(MyFlags, has_data=True, unordered_members=True)

    def test_flags_with_data_as_ordered_dict(self):
        class MyFlags(Flags):
            __members__ = collections.OrderedDict([('f0', ['data0']), ('f1', ['data1']), ('f2', ['data2'])])
        self._test_flags_class(MyFlags, has_data=True)

    def test_flags_with_data_as_iterable(self):
        class MyFlags(Flags):
            __members__ = iter([('f0', ['data0']), ('f1', ['data1']), ('f2', ['data2'])])
        self._test_flags_class(MyFlags, has_data=True)

    def _test_special_flags(self, flags_class, *, no_flags_name='no_flags', all_flags_name='all_flags'):
        self.assertEqual(flags_class.__no_flags_name__, no_flags_name)
        self.assertEqual(flags_class.__all_flags_name__, all_flags_name)
        self.assertEqual(len(flags_class), 2)
        self.assertEqual(int(getattr(flags_class, no_flags_name)), 0)
        self.assertEqual(int(getattr(flags_class, all_flags_name)), 3)
        self.assertEqual(flags_class.__all_bits__, 3)
        self.assertIn(no_flags_name, flags_class.__all_members__)
        self.assertIn(all_flags_name, flags_class.__all_members__)
        self.assertNotIn(no_flags_name, flags_class.__members__)
        self.assertNotIn(all_flags_name, flags_class.__members__)

    def test_special_flags_with_class_declaration(self):
        class MyFlags(Flags):
            f0 = ()
            f1 = ()
        self._test_special_flags(MyFlags)

    def test_special_flags_with_dynamic_class_creation(self):
        flags_class = Flags('MyFlags', 'f0 f1')
        self._test_special_flags(flags_class)

    def test_special_flags_with_class_declaration_and_custom_flag_names(self):
        class MyFlags(Flags):
            __no_flags_name__ = 'custom_no_flags_name'
            __all_flags_name__ = 'custom_all_flags_name'
            f0 = ()
            f1 = ()
        self._test_special_flags(MyFlags, no_flags_name='custom_no_flags_name',
                                 all_flags_name='custom_all_flags_name')

    def test_special_flags_disabled_with_class_declaration(self):
        # First we check the non-disabled version
        class NoDisable(Flags):
            f0 = ()

        self.assertTrue(hasattr(NoDisable, 'no_flags'))
        self.assertTrue(hasattr(NoDisable, 'all_flags'))
        self.assertTrue(hasattr(NoDisable, '__no_flags__'))
        self.assertTrue(hasattr(NoDisable, '__all_flags__'))

        # Now let's check the disabled versions
        class DisabledNoFlags(Flags):
            __no_flags_name__ = None
            f0 = ()

        self.assertFalse(hasattr(DisabledNoFlags, 'no_flags'))
        self.assertTrue(hasattr(DisabledNoFlags, 'all_flags'))
        self.assertTrue(hasattr(DisabledNoFlags, '__no_flags__'))
        self.assertTrue(hasattr(DisabledNoFlags, '__all_flags__'))

        class DisabledAllFlags(Flags):
            __all_flags_name__ = None
            f0 = ()

        self.assertTrue(hasattr(DisabledAllFlags, 'no_flags'))
        self.assertFalse(hasattr(DisabledAllFlags, 'all_flags'))
        self.assertTrue(hasattr(DisabledAllFlags, '__no_flags__'))
        self.assertTrue(hasattr(DisabledAllFlags, '__all_flags__'))

        class BothDisabled(Flags):
            __no_flags_name__ = None
            __all_flags_name__ = None
            f0 = ()

        self.assertFalse(hasattr(BothDisabled, 'no_flags'))
        self.assertFalse(hasattr(BothDisabled, 'all_flags'))
        self.assertTrue(hasattr(BothDisabled, '__no_flags__'))
        self.assertTrue(hasattr(BothDisabled, '__all_flags__'))

    def test_special_flags_with_dynamic_class_creation_and_custom_flag_names(self):
        flags_class = Flags('MyFlags', 'f0 f1', no_flags_name='custom_no_flags_name',
                            all_flags_name='custom_all_flags_name')
        self._test_special_flags(flags_class, no_flags_name='custom_no_flags_name',
                                 all_flags_name='custom_all_flags_name')

    def test_special_flags_with_class_declaration_and_custom_flag_names_inherited_from_base_class(self):
        class MyFlagsBase(Flags):
            __no_flags_name__ = 'custom_no_flags_name'
            __all_flags_name__ = 'custom_all_flags_name'

        class MyFlags(MyFlagsBase):
            f0 = ()
            f1 = ()
        self._test_special_flags(MyFlags, no_flags_name='custom_no_flags_name',
                                 all_flags_name='custom_all_flags_name')

    def test_special_flags_with_dynamic_class_creation_and_custom_flag_names_inherited_from_base_class(self):
        class MyFlagsBase(Flags):
            __no_flags_name__ = 'custom_no_flags_name'
            __all_flags_name__ = 'custom_all_flags_name'

        flags_class = MyFlagsBase('MyFlags', 'f0 f1')
        self._test_special_flags(flags_class, no_flags_name='custom_no_flags_name',
                                 all_flags_name='custom_all_flags_name')

    def test_aliases(self):
        class MyFlags(Flags):
            f1 = 1
            f1_alias = 1
            f2 = 2
            f2_alias = 2

        # all_members includes the aliases and also no_flags and all_flags special members
        self.assertEqual(len(MyFlags.__all_members__), 6)
        self.assertEqual(len(MyFlags.__members__), 4)
        self.assertEqual(len(MyFlags.__members_without_aliases__), 2)
        self.assertSetEqual(set(MyFlags.__member_aliases__.items()), {('f1_alias', 'f1'), ('f2_alias', 'f2')})


class TestFlagsDeclarationErrors(TestCase):
    def test_alias_declares_data(self):
        with self.assertRaisesRegex(ValueError, re.escape(r"You aren't allowed to associate data with alias 'f2'")):
            class MyFlags(Flags):
                f0 = 1
                f2 = 1, None

        with self.assertRaisesRegex(ValueError, re.escape(r"You aren't allowed to associate data with alias 'f2'")):
            class MyFlags(Flags):
                f0 = 1
                f2 = 1, 'data'

    def test_duplicate_flag_name_in_member_names_string(self):
        with self.assertRaisesRegex(ValueError, re.escape(r"Duplicate flag name: 'f1'")):
            Flags('MyFlags', 'f0 f1 f1')

    def test_default_special_flag_name_conflicts_with_a_declared_flag(self):
        with self.assertRaisesRegex(ValueError, re.escape(r"Duplicate flag name: 'no_flags'")):
            class MyFlags(Flags):
                no_flags = ()

    def test_custom_special_flag_name_conflicts_with_a_declared_flag(self):
        with self.assertRaisesRegex(ValueError, re.escape(r"Duplicate flag name: 'f0'")):
            class MyFlags(Flags):
                __no_flags_name__ = 'f0'
                f0 = ()

    def test_custom_special_flag_name_conflicts_with_anoter_custom_special_flag_name(self):
        with self.assertRaisesRegex(ValueError, re.escape(r"Duplicate flag name: 'special_flag'")):
            class MyFlags(Flags):
                __no_flags_name__ = 'special_flag'
                __all_flags_name__ = 'special_flag'
                f0 = ()

    def test_custom_special_flag_name_conflicts_with_anoter_default_special_flag_name(self):
        with self.assertRaisesRegex(ValueError, re.escape(r"Duplicate flag name: 'all_flags'")):
            class MyFlags(Flags):
                __no_flags_name__ = 'all_flags'
                f0 = ()

    def test_flags_class_new_alters_the_value_of_bits(self):
        with self.assertRaisesRegex(RuntimeError,
                                    r"MyFlags has altered the assigned bits of member 'f0' from 1 to 2"):
            class MyFlags(Flags):
                f0 = ()

                def __new__(cls, bits):
                    bits = 2
                    return Flags.__new__(cls, bits)

    def test_slots_usage_isnt_allowed(self):
        with self.assertRaisesRegex(RuntimeError, r"You aren't allowed to use __slots__ in your Flags subclasses"):
            class MyFlags(Flags):
                __slots__ = ('my_slot',)
                f0 = ()

    def test_iterable_longer_than_2(self):
        with self.assertRaisesRegex(
                ValueError,
                re.escape(r"Iterable is expected to have at most 2 items instead of 3 "
                          r"for flag 'f0', iterable: (None, None, None)")):
            class MyFlags(Flags):
                f0 = (None, None, None)

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

    def test_bits_is_bool_in_2_long_iterable(self):
        with self.assertRaisesRegex(
                TypeError,
                re.escape(r"Expected an int value as the bits of flag 'f0', received False")):
            class MyFlags(Flags):
                f0 = (False, 'data0')

    def test_bits_is_str_in_2_long_iterable(self):
        with self.assertRaisesRegex(
                TypeError,
                re.escape(r"Expected an int value as the bits of flag 'f0', received 5.5")):
            class MyFlags(Flags):
                f0 = 5.5, 'data0'

    def test_bits_is_none_in_2_long_iterable(self):
        with self.assertRaisesRegex(
                TypeError,
                re.escape(r"Expected an int value as the bits of flag 'f1', received None")):
            class MyFlags(Flags):
                f0 = 0b0011
                f1 = (None, 'data1')
                f2 = 0b0110


class TestAutoAssignedBits(TestCase):
    def test_auto_assign_with_flag_data(self):
        class MyFlagData(FlagData):
            pass

        my_flag_data = MyFlagData()

        class MyFlags(Flags):
            f0 = 0b001
            f1 = my_flag_data
            f2 = 0b010

        self.assertListEqual([int(MyFlags.f0), int(MyFlags.f1), int(MyFlags.f2)], [0b001, 0b100, 0b010])
        self.assertIs(MyFlags.f0.data, UNDEFINED)
        self.assertIs(MyFlags.f1.data, my_flag_data)
        self.assertIs(MyFlags.f2.data, UNDEFINED)

    def test_auto_assign_with_empty_tuple(self):
        class MyFlags(Flags):
            f0 = 0b0011
            f1 = ()
            f2 = 0b1000

        self.assertListEqual([int(MyFlags.f0), int(MyFlags.f1), int(MyFlags.f2)], [0b0011, 0b0100, 0b1000])
        self.assertIs(MyFlags.f0.data, UNDEFINED)
        self.assertIs(MyFlags.f1.data, UNDEFINED)
        self.assertIs(MyFlags.f2.data, UNDEFINED)

    def test_auto_assign_with_empty_list(self):
        class MyFlags(Flags):
            f0 = 0b0011
            f1 = []
            f2 = 0b0110

        self.assertListEqual([int(MyFlags.f0), int(MyFlags.f1), int(MyFlags.f2)], [0b0011, 0b1000, 0b0110])
        self.assertIs(MyFlags.f0.data, UNDEFINED)
        self.assertIs(MyFlags.f1.data, UNDEFINED)
        self.assertIs(MyFlags.f2.data, UNDEFINED)


class TestFlagsInheritance(TestCase):
    def test_dynamic_flags_class_creation_subclasses_the_called_flags_class(self):
        MyFlags = Flags('MyFlags', '')
        self.assertTrue(issubclass(MyFlags, Flags))

        MyFlags2 = MyFlags('MyFlags2', '')
        self.assertTrue(issubclass(MyFlags2, MyFlags))

    def test_subclassing_more_than_one_abstract_flags_classes_works(self):
        class FlagsBase1(Flags):
            __no_flags_name__ = 'custom_no_flags_name'

        class FlagsBase2(Flags):
            __all_flags_name__ = 'custom_all_flags_name'

        class MyFlags(FlagsBase1, FlagsBase2):
            f0 = ()
            f1 = ()

        self.assertEqual(MyFlags.__no_flags_name__, 'custom_no_flags_name')
        self.assertEqual(MyFlags.__all_flags_name__, 'custom_all_flags_name')

    def test_subclassing_fails_if_at_least_one_flags_base_class_isnt_abstract(self):
        class NonAbstract(Flags):
            f0 = ()

        class Abstract1(Flags):
            pass

        class Abstract2(Flags):
            pass

        with self.assertRaisesRegex(
            RuntimeError, re.escape("You can't subclass 'NonAbstract' because it has already defined flag members")):
            NonAbstract('MyFlags', 'flag1 flag2')

        with self.assertRaisesRegex(
            RuntimeError, re.escape("You can't subclass 'NonAbstract' because it has already defined flag members")):
            NonAbstract('MyFlags', 'flag1 flag2', mixins=[Abstract1])

        with self.assertRaisesRegex(
            RuntimeError, re.escape("You can't subclass 'NonAbstract' because it has already defined flag members")):
            Flags('MyFlags', 'flag1 flag2', mixins=[NonAbstract])

        with self.assertRaisesRegex(
            RuntimeError, re.escape("You can't subclass 'NonAbstract' because it has already defined flag members")):
            Flags('MyFlags', 'flag1 flag2', mixins=[Abstract1, NonAbstract])

        with self.assertRaisesRegex(
            RuntimeError, re.escape("You can't subclass 'NonAbstract' because it has already defined flag members")):
            Flags('MyFlags', 'flag1 flag2', mixins=[Abstract1, NonAbstract, Abstract2])

        with self.assertRaisesRegex(
            RuntimeError, re.escape("You can't subclass 'NonAbstract' because it has already defined flag members")):
            Abstract1('MyFlags', 'flag1 flag2', mixins=[NonAbstract])

        with self.assertRaisesRegex(
            RuntimeError, re.escape("You can't subclass 'NonAbstract' because it has already defined flag members")):
            Abstract1('MyFlags', 'flag1 flag2', mixins=[Abstract2, NonAbstract])


class TestFlagsClassInstantiationFromValue(TestCase):
    def test_instantiation_of_abstract_flags_class_fails(self):
        # A flags class is considered to be "abstract" if it doesn't define any members.
        with self.assertRaisesRegex(RuntimeError, r"Instantiation of abstract flags class '.+\.Flags' isn't allowed."):
            Flags()

        class MyAbstractFlagsClass(Flags):
            pass

        with self.assertRaisesRegex(RuntimeError,
                                    r"Instantiation of abstract flags class "
                                    r"'.+\.MyAbstractFlagsClass' isn't allowed."):
            MyAbstractFlagsClass()

        # Subclassing MyAbstractFlagsClass by calling it:
        MyAbstractFlagsClass_2 = MyAbstractFlagsClass('MyAbstractFlagsClass_2', '')

        with self.assertRaisesRegex(RuntimeError,
                                    r"Instantiation of abstract flags class "
                                    r"'.+\.MyAbstractFlagsClass_2' isn't allowed."):
            MyAbstractFlagsClass_2()

    def test_no_arg_to_create_zero_flag(self):
        MyFlags = Flags('MyFlags', 'f0 f1 f2')
        flag = MyFlags()
        self.assertIsInstance(flag, MyFlags)
        self.assertEqual(flag, MyFlags.no_flags)
        self.assertEqual(int(flag), 0)

    def test_value_is_flags_instance(self):
        MyFlags = Flags('MyFlags', 'f0 f1 f2')
        flag = MyFlags(MyFlags.f1)
        self.assertIsInstance(flag, MyFlags)
        self.assertEqual(flag, MyFlags.f1)

    def test_int_value_zero(self):
        MyFlags = Flags('MyFlags', 'f0 f1 f2')
        flag = MyFlags(0)
        self.assertIsInstance(flag, MyFlags)
        self.assertEqual(flag, MyFlags.no_flags)
        self.assertEqual(int(flag), 0)

    def test_int_value_single_member(self):
        MyFlags = Flags('MyFlags', 'f0 f1 f2')
        flag = MyFlags(int(MyFlags.f1))
        self.assertIsInstance(flag, MyFlags)
        self.assertEqual(flag, MyFlags.f1)

    def test_int_value_multiple_members(self):
        MyFlags = Flags('MyFlags', 'f0 f1 f2')
        flag = MyFlags(int(MyFlags.f1) | int(MyFlags.f2))
        self.assertIsInstance(flag, MyFlags)
        self.assertEqual(flag, MyFlags.f1 | MyFlags.f2)

    def test_str_value_zero(self):
        MyFlags = Flags('MyFlags', 'f0 f1 f2')
        flag = MyFlags(str(MyFlags.no_flags))
        self.assertIsInstance(flag, MyFlags)
        self.assertEqual(flag, MyFlags.no_flags)

    def test_str_value_single_member(self):
        MyFlags = Flags('MyFlags', 'f0 f1 f2')
        flag = MyFlags(str(MyFlags.f1))
        self.assertIsInstance(flag, MyFlags)
        self.assertEqual(flag, MyFlags.f1)

    def test_str_value_multiple_members(self):
        MyFlags = Flags('MyFlags', 'f0 f1 f2')
        flag = MyFlags(str(MyFlags.f1 | MyFlags.f2))
        self.assertIsInstance(flag, MyFlags)
        self.assertEqual(flag, MyFlags.f1 | MyFlags.f2)

    def test_simple_str_value_zero(self):
        MyFlags = Flags('MyFlags', 'f0 f1 f2')
        flag = MyFlags(MyFlags.no_flags.to_simple_str())
        self.assertIsInstance(flag, MyFlags)
        self.assertEqual(flag, MyFlags.no_flags)

    def test_simple_str_value_single_member(self):
        MyFlags = Flags('MyFlags', 'f0 f1 f2')
        flag = MyFlags(MyFlags.f1.to_simple_str())
        self.assertIsInstance(flag, MyFlags)
        self.assertEqual(flag, MyFlags.f1)

    def test_simple_str_value_multiple_members(self):
        MyFlags = Flags('MyFlags', 'f0 f1 f2')
        flag = MyFlags((MyFlags.f1 | MyFlags.f2).to_simple_str())
        self.assertIsInstance(flag, MyFlags)
        self.assertEqual(flag, MyFlags.f1 | MyFlags.f2)

    def test_float_value_fails(self):
        MyFlags = Flags('MyFlags', 'f0 f1 f2')
        with self.assertRaisesRegex(TypeError, re.escape(r"Can't instantiate flags class 'MyFlags' from value 0.5")):
            MyFlags(0.5)

    def test_bool_value_fails(self):
        MyFlags = Flags('MyFlags', 'f0 f1 f2')
        with self.assertRaisesRegex(TypeError, re.escape(r"Can't instantiate flags class 'MyFlags' from value False")):
            MyFlags(False)


class TestProcessMemberDefinitions(TestCase):
    """ Tests the process_member_definitions() method of the flags class. """
    def test_returned_name_isnt_a_string(self):
        with self.assertRaisesRegex(TypeError, r"Flag name should be an str but it is 123"):
            class MyFlags(Flags):
                f0 = ()

                @classmethod
                def process_member_definitions(cls, member_definitions):
                    return [(123, 1, None)]

    def test_returned_bits_isnt_an_int(self):
        with self.assertRaisesRegex(TypeError, r"Bits for flag 'f0' should be an int but it is 'invalid_bits'"):
            class MyFlags(Flags):
                f0 = ()

                @classmethod
                def process_member_definitions(cls, member_defintions):
                    return [['f0', 'invalid_bits', None]]

    def test_returned_bits_is_zero(self):
        with self.assertRaisesRegex(ValueError, r"Flag 'f0' has the invalid value of zero"):
            class MyFlags(Flags):
                f0 = ()

                @classmethod
                def process_member_definitions(cls, member_defintions):
                    yield 'f0', 0, None

    def test_returning_empty_iterable_fails(self):
        with self.assertRaisesRegex(RuntimeError,
                                    re.escape("MyFlags.process_member_definitions returned an empty iterable")):
            class MyFlags(Flags):
                f0 = ()

                @classmethod
                def process_member_definitions(cls, member_definitions):
                    return ()


class TestFlagsClassMethods(TestCase):
    def setUp(self):
        self.MyFlags = Flags('MyFlags', 'f0 f1 f2')

    def test_iter(self):
        self.assertListEqual(list(iter(self.MyFlags)), [self.MyFlags.f0, self.MyFlags.f1, self.MyFlags.f2])

    def test_reversed(self):
        self.assertListEqual(list(reversed(self.MyFlags)), [self.MyFlags.f2, self.MyFlags.f1, self.MyFlags.f0])

    def test_getitem(self):
        self.assertEqual(self.MyFlags['f0'], self.MyFlags.f0)
        self.assertEqual(self.MyFlags['f1'], self.MyFlags.f1)
        self.assertNotEqual(self.MyFlags['f0'], self.MyFlags.f1)

    def test_setitem_fails(self):
        with self.assertRaisesRegex(TypeError, r"does not support item assignment"):
            self.MyFlags['f0'] = 'whatever'

    def test_bool(self):
        self.assertTrue(Flags)
        self.assertTrue(self.MyFlags)

    def test_len(self):
        self.assertEqual(len(Flags), 0)
        self.assertEqual(len(self.MyFlags), 3)

    def test_repr(self):
        self.assertEqual(repr(self.MyFlags), '<flags MyFlags>')

    def test_setattr_fails_with_protected_class_members(self):
        for attribute in PROTECTED_FLAGS_CLASS_ATTRIBUTES | set(self.MyFlags.__all_members__.keys()):
            if attribute in ('no_flags', 'all_flags', '__writable_protected_flags_class_attributes__'):
                regex = re.escape(attribute)
            else:
                regex = re.escape(r"Can't delete protected attribute '%s'" % attribute)

            with self.assertRaisesRegex(AttributeError, regex):
                delattr(self.MyFlags, attribute)

    def test_delattr_fails_with_protected_class_members(self):
        for attribute in PROTECTED_FLAGS_CLASS_ATTRIBUTES | set(self.MyFlags.__all_members__.keys()):
            with self.assertRaisesRegex(
                    AttributeError, re.escape(r"Can't assign protected attribute '%s'" % attribute)):
                setattr(self.MyFlags, attribute, 'new_value')

    def test_setattr_and_delattr_work_with_non_protected_class_members(self):
        self.assertFalse(hasattr(self.MyFlags, 'non_protected_member'))
        self.MyFlags.non_protected_member = 42
        self.assertEqual(self.MyFlags.non_protected_member, 42)
        del self.MyFlags.non_protected_member
        self.assertFalse(hasattr(self.MyFlags, 'non_protected_member'))


class TestFlagsInstanceMethods(TestCase):
    class MyFlags(Flags):
        f0 = ['data0']
        f1 = ['data1']
        f2 = ['data2']

    class NoDottedSingleFlagStr(Flags):
        __dotted_single_flag_str__ = False
        f0 = ()
        f1 = ()

    class SubsetFlag(Flags):
        # f1 is a proper/strict subset of f3
        f1 = 1
        f3 = 3

    def test_is_member(self):
        self.assertFalse(self.MyFlags.no_flags.is_member)
        self.assertFalse(self.MyFlags.all_flags.is_member)
        self.assertTrue(self.MyFlags.f0.is_member)
        self.assertTrue(self.MyFlags.f1.is_member)
        self.assertTrue(self.MyFlags.f2.is_member)
        self.assertFalse((self.MyFlags.f0 | self.MyFlags.f1).is_member)
        self.assertFalse((self.MyFlags.f0 | self.MyFlags.f2).is_member)
        self.assertFalse((self.MyFlags.f1 | self.MyFlags.f2).is_member)

    def test_properties(self):
        self.assertIsNone(self.MyFlags.no_flags.properties)
        self.assertIsNone(self.MyFlags.all_flags.properties)
        self.assertIsNotNone(self.MyFlags.f0.properties)
        self.assertIsNotNone(self.MyFlags.f1.properties)
        self.assertIsNotNone(self.MyFlags.f2.properties)
        self.assertIsNone((self.MyFlags.f0 | self.MyFlags.f1).properties)
        self.assertIsNone((self.MyFlags.f0 | self.MyFlags.f2).properties)
        self.assertIsNone((self.MyFlags.f1 | self.MyFlags.f2).properties)

    def test_name(self):
        self.assertIsNone(self.MyFlags.no_flags.name)
        self.assertIsNone(self.MyFlags.all_flags.name)
        self.assertEqual(self.MyFlags.f0.name, 'f0')
        self.assertEqual(self.MyFlags.f1.name, 'f1')
        self.assertEqual(self.MyFlags.f2.name, 'f2')
        self.assertIsNone((self.MyFlags.f0 | self.MyFlags.f1).name)
        self.assertIsNone((self.MyFlags.f0 | self.MyFlags.f2).name)
        self.assertIsNone((self.MyFlags.f1 | self.MyFlags.f2).name)

    def test_data(self):
        self.assertIs(self.MyFlags.no_flags.data, UNDEFINED)
        self.assertIs(self.MyFlags.all_flags.data, UNDEFINED)
        self.assertEqual(self.MyFlags.f0.data, 'data0')
        self.assertEqual(self.MyFlags.f1.data, 'data1')
        self.assertEqual(self.MyFlags.f2.data, 'data2')
        self.assertIs((self.MyFlags.f0 | self.MyFlags.f1).data, UNDEFINED)
        self.assertIs((self.MyFlags.f0 | self.MyFlags.f2).data, UNDEFINED)
        self.assertIs((self.MyFlags.f1 | self.MyFlags.f2).data, UNDEFINED)

    def test_getattr(self):
        flags = self.MyFlags.f0

        with self.assertRaises(AttributeError):
            _ = flags.no_flags
        with self.assertRaises(AttributeError):
            _ = flags.all_flags

        self.assertTrue(flags.f0)
        self.assertFalse(flags.f1)
        self.assertFalse(flags.f2)

    def test_int(self):
        self.assertEqual(int(self.MyFlags.no_flags), 0)
        self.assertEqual(int(self.MyFlags.all_flags), 7)
        self.assertEqual(int(self.MyFlags.f0), 1)
        self.assertEqual(int(self.MyFlags.f1), 2)
        self.assertEqual(int(self.MyFlags.f2), 4)
        self.assertEqual(int(self.MyFlags.f0 | self.MyFlags.f1), 3)
        self.assertEqual(int(self.MyFlags.f0 | self.MyFlags.f2), 5)
        self.assertEqual(int(self.MyFlags.f1 | self.MyFlags.f2), 6)

    def test_bool(self):
        self.assertFalse(self.MyFlags.no_flags)
        self.assertTrue(self.MyFlags.all_flags)
        self.assertTrue(self.MyFlags.f0)
        self.assertTrue(self.MyFlags.f1)
        self.assertTrue(self.MyFlags.f2)
        self.assertTrue(self.MyFlags.f0 | self.MyFlags.f1)
        self.assertTrue(self.MyFlags.f0 | self.MyFlags.f2)
        self.assertTrue(self.MyFlags.f1 | self.MyFlags.f2)

    def test_len(self):
        self.assertEqual(len(self.MyFlags.no_flags), 0)
        self.assertEqual(len(self.MyFlags.all_flags), 3)
        self.assertEqual(len(self.MyFlags.f0), 1)
        self.assertEqual(len(self.MyFlags.f1), 1)
        self.assertEqual(len(self.MyFlags.f2), 1)
        self.assertEqual(len(self.MyFlags.f0 | self.MyFlags.f1), 2)
        self.assertEqual(len(self.MyFlags.f0 | self.MyFlags.f2), 2)
        self.assertEqual(len(self.MyFlags.f1 | self.MyFlags.f2), 2)

    def test_iter(self):
        self.assertEqual(list(self.MyFlags.no_flags), [])
        self.assertEqual(list(self.MyFlags.all_flags), [self.MyFlags.f0, self.MyFlags.f1, self.MyFlags.f2])
        self.assertEqual(list(self.MyFlags.f0), [self.MyFlags.f0])
        self.assertEqual(list(self.MyFlags.f1), [self.MyFlags.f1])
        self.assertEqual(list(self.MyFlags.f2), [self.MyFlags.f2])
        self.assertEqual(list(self.MyFlags.f0 | self.MyFlags.f1), [self.MyFlags.f0, self.MyFlags.f1])
        self.assertEqual(list(self.MyFlags.f0 | self.MyFlags.f2), [self.MyFlags.f0, self.MyFlags.f2])
        self.assertEqual(list(self.MyFlags.f1 | self.MyFlags.f2), [self.MyFlags.f1, self.MyFlags.f2])

    def test_reversed(self):
        self.assertEqual(list(reversed(self.MyFlags.no_flags)), [])
        self.assertEqual(list(reversed(self.MyFlags.all_flags)), [self.MyFlags.f2, self.MyFlags.f1, self.MyFlags.f0])
        self.assertEqual(list(reversed(self.MyFlags.f0)), [self.MyFlags.f0])
        self.assertEqual(list(reversed(self.MyFlags.f1)), [self.MyFlags.f1])
        self.assertEqual(list(reversed(self.MyFlags.f2)), [self.MyFlags.f2])
        self.assertEqual(list(reversed(self.MyFlags.f0 | self.MyFlags.f1)), [self.MyFlags.f1, self.MyFlags.f0])
        self.assertEqual(list(reversed(self.MyFlags.f0 | self.MyFlags.f2)), [self.MyFlags.f2, self.MyFlags.f0])
        self.assertEqual(list(reversed(self.MyFlags.f1 | self.MyFlags.f2)), [self.MyFlags.f2, self.MyFlags.f1])

    def test_repr(self):
        self.assertEqual(repr(self.MyFlags.no_flags), '<MyFlags() bits=0x0000>')
        self.assertEqual(repr(self.MyFlags.all_flags), '<MyFlags(f0|f1|f2) bits=0x0007>')
        self.assertEqual(repr(self.MyFlags.f0), "<MyFlags.f0 bits=0x0001 data='data0'>")
        self.assertEqual(repr(self.MyFlags.f1), "<MyFlags.f1 bits=0x0002 data='data1'>")
        self.assertEqual(repr(self.MyFlags.f2), "<MyFlags.f2 bits=0x0004 data='data2'>")
        self.assertEqual(repr(self.MyFlags.f0 | self.MyFlags.f1), '<MyFlags(f0|f1) bits=0x0003>')
        self.assertEqual(repr(self.MyFlags.f0 | self.MyFlags.f2), '<MyFlags(f0|f2) bits=0x0005>')
        self.assertEqual(repr(self.MyFlags.f1 | self.MyFlags.f2), '<MyFlags(f1|f2) bits=0x0006>')

        self.assertEqual(repr(self.NoDottedSingleFlagStr.no_flags), '<NoDottedSingleFlagStr() bits=0x0000>')
        self.assertEqual(repr(self.NoDottedSingleFlagStr.all_flags), '<NoDottedSingleFlagStr(f0|f1) bits=0x0003>')
        self.assertEqual(repr(self.NoDottedSingleFlagStr.f0), "<NoDottedSingleFlagStr(f0) bits=0x0001 data=UNDEFINED>")
        self.assertEqual(repr(self.NoDottedSingleFlagStr.f1), "<NoDottedSingleFlagStr(f1) bits=0x0002 data=UNDEFINED>")
        self.assertEqual(repr(self.NoDottedSingleFlagStr.f0 | self.NoDottedSingleFlagStr.f1),
                         '<NoDottedSingleFlagStr(f0|f1) bits=0x0003>')

        self.assertEqual(repr(self.SubsetFlag.f3), '<SubsetFlag(f1|f3) bits=0x0003>')

    def test_str(self):
        self.assertEqual(str(self.MyFlags.no_flags), 'MyFlags()')
        self.assertEqual(str(self.MyFlags.all_flags), 'MyFlags(f0|f1|f2)')
        self.assertEqual(str(self.MyFlags.f0), 'MyFlags.f0')
        self.assertEqual(str(self.MyFlags.f1), 'MyFlags.f1')
        self.assertEqual(str(self.MyFlags.f2), 'MyFlags.f2')
        self.assertEqual(str(self.MyFlags.f0 | self.MyFlags.f1), 'MyFlags(f0|f1)')
        self.assertEqual(str(self.MyFlags.f0 | self.MyFlags.f2), 'MyFlags(f0|f2)')
        self.assertEqual(str(self.MyFlags.f1 | self.MyFlags.f2), 'MyFlags(f1|f2)')

        self.assertEqual(str(self.NoDottedSingleFlagStr.no_flags), 'NoDottedSingleFlagStr()')
        self.assertEqual(str(self.NoDottedSingleFlagStr.all_flags), 'NoDottedSingleFlagStr(f0|f1)')
        self.assertEqual(str(self.NoDottedSingleFlagStr.f0), 'NoDottedSingleFlagStr(f0)')
        self.assertEqual(str(self.NoDottedSingleFlagStr.f1), 'NoDottedSingleFlagStr(f1)')
        self.assertEqual(str(self.NoDottedSingleFlagStr.f0 | self.NoDottedSingleFlagStr.f1),
                         'NoDottedSingleFlagStr(f0|f1)')

        self.assertEqual(str(self.SubsetFlag.f3), 'SubsetFlag(f1|f3)')

    def test_from_str(self):
        self.assertEqual(self.MyFlags.no_flags, self.MyFlags.from_str('MyFlags()'))
        self.assertEqual(self.MyFlags.all_flags, self.MyFlags.from_str('MyFlags(f0|f1|f2)'))
        self.assertEqual(self.MyFlags.f0, self.MyFlags.from_str('MyFlags.f0'))
        self.assertEqual(self.MyFlags.f1, self.MyFlags.from_str('MyFlags.f1'))
        self.assertEqual(self.MyFlags.f2, self.MyFlags.from_str('MyFlags.f2'))
        self.assertEqual(self.MyFlags.f0 | self.MyFlags.f1, self.MyFlags.from_str('MyFlags(f0|f1)'))
        self.assertEqual(self.MyFlags.f0 | self.MyFlags.f2, self.MyFlags.from_str('MyFlags(f0|f2)'))
        self.assertEqual(self.MyFlags.f1 | self.MyFlags.f2, self.MyFlags.from_str('MyFlags(f1|f2)'))

        with self.assertRaisesRegex(TypeError, re.escape(r"Expected an str instance, received 42")):
            self.MyFlags.from_str(42)

    def test_bits_from_str(self):
        self.assertEqual(0, self.MyFlags.bits_from_str('MyFlags()'))
        self.assertEqual(7, self.MyFlags.bits_from_str('MyFlags(f0|f1|f2)'))
        self.assertEqual(1, self.MyFlags.bits_from_str('MyFlags.f0'))
        self.assertEqual(2, self.MyFlags.bits_from_str('MyFlags.f1'))
        self.assertEqual(4, self.MyFlags.bits_from_str('MyFlags.f2'))
        self.assertEqual(3, self.MyFlags.bits_from_str('MyFlags(f0|f1)'))
        self.assertEqual(5, self.MyFlags.bits_from_str('MyFlags(f0|f2)'))
        self.assertEqual(6, self.MyFlags.bits_from_str('MyFlags(f1|f2)'))

        with self.assertRaisesRegex(ValueError, re.escape(r"Invalid flag 'MyFlags.invalid' in string 'f0|invalid|f1'")):
            self.MyFlags.bits_from_str('f0|invalid|f1')

        with self.assertRaisesRegex(ValueError, re.escape("MyFlags.bits_from_str: invalid input: 'MyFlags(f0'")):
            self.MyFlags.bits_from_str('MyFlags(f0')

        with self.assertRaisesRegex(ValueError, re.escape("MyFlags.bits_from_str: invalid input: 'MyFlags<f0'")):
            self.MyFlags.bits_from_str('MyFlags<f0')

        with self.assertRaisesRegex(ValueError, re.escape("MyFlags.bits_from_str: Invalid flag name 'invalid' in "
                                                          "input: 'MyFlags.invalid'")):
            self.MyFlags.bits_from_str('MyFlags.invalid')

    def test_simple_str(self):
        self.assertEqual(self.MyFlags.no_flags.to_simple_str(), '')
        self.assertEqual(self.MyFlags.all_flags.to_simple_str(), 'f0|f1|f2')
        self.assertEqual(self.MyFlags.f0.to_simple_str(), 'f0')
        self.assertEqual(self.MyFlags.f1.to_simple_str(), 'f1')
        self.assertEqual(self.MyFlags.f2.to_simple_str(), 'f2')
        self.assertEqual((self.MyFlags.f0 | self.MyFlags.f1).to_simple_str(), 'f0|f1')
        self.assertEqual((self.MyFlags.f0 | self.MyFlags.f2).to_simple_str(), 'f0|f2')
        self.assertEqual((self.MyFlags.f1 | self.MyFlags.f2).to_simple_str(), 'f1|f2')

    def test_from_simple_str(self):
        self.assertEqual(self.MyFlags.no_flags, self.MyFlags.from_simple_str(''))
        self.assertEqual(self.MyFlags.all_flags, self.MyFlags.from_simple_str('f0|f1|f2'))
        self.assertEqual(self.MyFlags.f0, self.MyFlags.from_simple_str('f0'))
        self.assertEqual(self.MyFlags.f1, self.MyFlags.from_simple_str('f1'))
        self.assertEqual(self.MyFlags.f2, self.MyFlags.from_simple_str('f2'))
        self.assertEqual(self.MyFlags.f0 | self.MyFlags.f1, self.MyFlags.from_simple_str('f0|f1'))
        self.assertEqual(self.MyFlags.f0 | self.MyFlags.f2, self.MyFlags.from_simple_str('f0|f2'))
        self.assertEqual(self.MyFlags.f1 | self.MyFlags.f2, self.MyFlags.from_simple_str('f1|f2'))

        with self.assertRaisesRegex(TypeError, re.escape(r"Expected an str instance, received 42")):
            self.MyFlags.from_simple_str(42)

    def test_bits_from_simple_str(self):
        self.assertEqual(0, self.MyFlags.bits_from_simple_str(''))
        self.assertEqual(7, self.MyFlags.bits_from_simple_str('f0|f1|f2'))
        self.assertEqual(1, self.MyFlags.bits_from_simple_str('f0'))
        self.assertEqual(2, self.MyFlags.bits_from_simple_str('f1'))
        self.assertEqual(4, self.MyFlags.bits_from_simple_str('f2'))
        self.assertEqual(3, self.MyFlags.bits_from_simple_str('f0|f1'))
        self.assertEqual(5, self.MyFlags.bits_from_simple_str('f0|f2'))
        self.assertEqual(6, self.MyFlags.bits_from_simple_str('f1|f2'))

        with self.assertRaisesRegex(ValueError, re.escape(r"Invalid flag 'MyFlags.invalid' in string 'f0|invalid|f1'")):
            self.MyFlags.bits_from_simple_str('f0|invalid|f1')
