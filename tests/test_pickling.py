import pickle
from unittest import TestCase

from flags import Flags


# Don't import classes from base directly to the namespace of this
# module in order to avoid discovering those base classes as tests.
from . import test_base


class ModuleScopeFlags(Flags):
    f0 = 'data0'
    f1 = 'data1'
    f2 = 'data2'
    f3 = 'data3'


class PicklingFlagsDeclaredAsClassAtModuleScope(test_base.PicklingSuccessTestBase):
    FlagsClass = ModuleScopeFlags


class PicklingFlagsDeclaredAsClassInsideAnotherClass(test_base.PicklingSuccessTestBase):
    # InnerFlags isn't at module scope
    class InnerFlags(Flags):
        f0 = 'data0'
        f1 = 'data1'
        f2 = 'data2'
        f3 = 'data3'

    FlagsClass = InnerFlags


DynamicModuleScopeFlags = Flags('DynamicModuleScopeFlags', 'f0 f1 f2 f3', module=__name__)


class PicklingFlagsCreatedAndStoredAtModuleScope(test_base.PicklingSuccessTestBase):
    FlagsClass = DynamicModuleScopeFlags


class PicklingFlagsCreatedAndStoredAtClassScope(test_base.PicklingSuccessTestBase):
    DynamicallyCreatedInnerFlags = Flags(
        'DynamicallyCreatedInnerFlags', 'f0 f1 f2 f3', module=__name__,
        qualname='PicklingFlagsCreatedAndStoredAtClassScope.DynamicallyCreatedInnerFlags',
    )

    FlagsClass = DynamicallyCreatedInnerFlags


DynamicModuleScopeFlagsWithoutModuleName = Flags('DynamicModuleScopeFlagsWithoutModuleName', 'f0 f1 f2 f3')


class PicklingFailure(TestCase):
    DynamicInnerFlags = Flags('DynamicInnerFlags', 'f0 f1 f2 f3', module=__name__)

    def test_pickling_fails_with_dynamically_created_class_without_module_name(self):
        self.assertRaises(pickle.PicklingError, pickle.dumps, DynamicModuleScopeFlagsWithoutModuleName.f0)

    def test_pickling_fails_with_dynamically_created_inner_class_without_qualname(self):
        self.assertRaises(pickle.PicklingError, pickle.dumps, self.DynamicInnerFlags.f0)
