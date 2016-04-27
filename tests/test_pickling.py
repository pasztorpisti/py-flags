""" This module tests the compatibility of the standard pickle module with our flags classes and instances. """
import pickle
import sys
from unittest import TestCase, skipIf

from flags import Flags
# Don't import classes from test_base directly to the namespace of this
# module in order to avoid discovering those base classes as tests.
from . import test_base


class ModuleScopeFlags(Flags):
    f0 = ['data0']
    f1 = ['data1']
    f2 = ['data2']
    f3 = ['data3']


class PicklingFlagsDeclaredAsClassAtModuleScope(test_base.PicklingSuccessTestBase):
    FlagsClass = ModuleScopeFlags


@skipIf(sys.version_info < (3, 4), 'Pickling inner classes with __qualname__ is supported only by python3.4+')
class PicklingFlagsDeclaredAsClassInsideAnotherClass(test_base.PicklingSuccessTestBase):
    # InnerFlags isn't at module scope
    class InnerFlags(Flags):
        f0 = ['data0']
        f1 = ['data1']
        f2 = ['data2']
        f3 = ['data3']

    FlagsClass = InnerFlags


DynamicModuleScopeFlags = Flags('DynamicModuleScopeFlags', 'f0 f1 f2 f3', module=__name__)


class PicklingFlagsCreatedAndStoredAtModuleScope(test_base.PicklingSuccessTestBase):
    FlagsClass = DynamicModuleScopeFlags


@skipIf(sys.version_info < (3, 4), 'Pickling inner classes with __qualname__ is supported only by python3.4+')
class PicklingFlagsCreatedAndStoredAtClassScope(test_base.PicklingSuccessTestBase):
    DynamicallyCreatedInnerFlags = Flags(
        'DynamicallyCreatedInnerFlags', 'f0 f1 f2 f3', module=__name__,
        qualname='PicklingFlagsCreatedAndStoredAtClassScope.DynamicallyCreatedInnerFlags',
    )

    FlagsClass = DynamicallyCreatedInnerFlags


DynamicModuleScopeFlagsWithoutModuleName = Flags('DynamicModuleScopeFlagsWithoutModuleName', 'f0 f1 f2 f3')


# Pickling HAS TO FAIL in some cases. If pickle can't the fully qualified name of the class then it should
# fail. This can be a problem in case of flags classes that has been created "dynamically" with a function call.
class PicklingFailure(TestCase):
    DynamicInnerFlags = Flags('DynamicInnerFlags', 'f0 f1 f2 f3', module=__name__)

    def test_pickling_fails_with_dynamically_created_class_without_module_name(self):
        self.assertRaises(pickle.PicklingError, pickle.dumps, DynamicModuleScopeFlagsWithoutModuleName.f0)

    def test_pickling_fails_with_dynamically_created_inner_class_without_qualname(self):
        self.assertRaises(pickle.PicklingError, pickle.dumps, self.DynamicInnerFlags.f0)


class FlagsWithPickleIntFlags(Flags):
    __pickle_int_flags__ = True
    f0 = ['data0']
    f1 = ['data1']
    f2 = ['data2']
    f3 = ['data3']


class PicklingFlagsWtihPickleIntFlagsSetToTrue(test_base.PicklingSuccessTestBase):
    FlagsClass = FlagsWithPickleIntFlags


class TestPickleIntFlags(TestCase):
    def test_pickle_int_flags_is_false_by_default(self):
        self.assertFalse(ModuleScopeFlags.__pickle_int_flags__)

    def test_picle_int_flags_can_be_set_to_true(self):
        self.assertTrue(FlagsWithPickleIntFlags.__pickle_int_flags__)

    def test_reduce_ex_returns_string_when_pickle_int_flags_is_false(self):
        cls, args = ModuleScopeFlags.f0.__reduce_ex__(4)
        self.assertIs(cls, ModuleScopeFlags)
        self.assertEqual(len(args), 1)
        self.assertEqual(args[0], ModuleScopeFlags.f0.to_simple_str())

    def test_reduce_ex_returns_int_when_pickle_int_flags_is_true(self):
        cls, args = FlagsWithPickleIntFlags.f0.__reduce_ex__(4)
        self.assertIs(cls, FlagsWithPickleIntFlags)
        self.assertEqual(len(args), 1)
        self.assertIs(type(args[0]), int)
        self.assertEqual(args[0], int(FlagsWithPickleIntFlags.f0))
