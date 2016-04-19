# -*- coding: utf-8 -*-
import collections
import functools
import operator

from dictionaries import ReadonlyDictProxy


__all__ = ['Flags', 'CustomFlags', 'FlagProperties', 'UNDEFINED']


# version_info[0]: Increase in case of large milestones/releases.
# version_info[1]: Increase this and zero out version_info[2] if you have explicitly modified
#                  a previously existing behavior/interface.
#                  If the behavior of an existing feature changes as a result of a bugfix
#                  and the new (bugfixed) behavior is that meets the expectations of the
#                  previous interface documentation then you shouldn't increase this, in that
#                  case increase only version_info[2].
# version_info[2]: Increase in case of bugfixes. Also use this if you added new features
#                  without modifying the behavior of the previously existing ones.
version_info = (0, 0, 0)
__version__ = '.'.join(str(n) for n in version_info)
__author__ = 'István Pásztor'
__license__ = 'MIT'


def _is_descriptor(obj):
    return hasattr(obj, '__get__') or hasattr(obj, '__set__') or hasattr(obj, '__delete__')


class _Undefined:
    def __repr__(self):
        return 'UNDEFINED'


# "singleton" to be used as a const value with identity checks
UNDEFINED = _Undefined()


def _create_flags_subclass(base_enum_class, class_name, flags, *, mixins=(), module=None, qualname=None,
                           no_flags_name=UNDEFINED, all_flags_name=UNDEFINED):
    meta_class = type(base_enum_class)
    bases = tuple(mixins) + (base_enum_class,)
    class_dict = {'__members__': flags}
    if no_flags_name is not UNDEFINED:
        class_dict['__no_flags_name__'] = no_flags_name
    if all_flags_name is not UNDEFINED:
        class_dict['__all_flags_name__'] = all_flags_name
    flags_class = meta_class(class_name, bases, class_dict)

    # disabling on enabling pickle on the new class based on our module parameter
    if module is None:
        # Making the class unpicklable.
        def disabled_reduce_ex(self, proto):
            raise TypeError("%r is unpicklable" % (self,))
        flags_class.__reduce_ex__ = disabled_reduce_ex

        # For pickle module==None means the __main__ module so let's change it to a non-existing name.
        # This will cause a failure while trying to pickle the class.
        module = '<unknown>'
    flags_class.__module__ = module

    if qualname is not None:
        flags_class.__qualname__ = qualname

    return flags_class


def _process_inline_members_definition(members):
    if isinstance(members, str):
        members = [(name, UNDEFINED) for name in members.replace(',', ' ').split()]
    elif isinstance(members, (tuple, list, set, frozenset)):
        if members and isinstance(next(iter(members)), str):
            members = [(name, UNDEFINED) for name in members]
        else:
            members = list(members)
    elif isinstance(members, dict):
        members = list(members.items())
    else:
        members = list(members)

    # At this point members must be a list of (name, data) pairs.
    return members


def _extract_member_definitions_from_class_attributes(class_dict):
    inline_members = _process_inline_members_definition(class_dict.pop('__members__', ()))
    members = [(name, data) for name, data in class_dict.items()
               if not name.startswith('_') and not _is_descriptor(data)]
    for name, data in members:
        del class_dict[name]
    # Members defined as class attributes (not as inline __members__) go the to beginning of the list.
    # This way flags subclasses that customize value assignment to inline members can easily make use
    # of the values already assigned to non-inline members.
    members.extend(inline_members)

    # checking for duplicate member names
    member_dict = collections.OrderedDict(members)
    if len(member_dict) < len(members):
        member_names = [name for name, data in members]
        duplicates = [name for name, count in collections.Counter(member_names).items() if count >= 2]
        raise ValueError("Duplicate member definition(s): %s" % ', '.join(sorted(duplicates)))

    class_and_flag_member_conflicts = set(member_dict.keys()) & set(class_dict.keys())
    if class_and_flag_member_conflicts:
        raise ValueError("Flag member name(s) conflicting with other class attribute(s): %s" %
                         ', '.join(sorted(class_and_flag_member_conflicts)))
    return members


class FlagProperties:
    __slots__ = ('name', 'data', 'bits', 'index', 'index_without_aliases', 'readonly')

    def __init__(self, *, name, bits, data=None, index=None, index_without_aliases=None, readonly=False):
        self.name = name
        self.data = data
        self.bits = bits
        self.index = index
        self.index_without_aliases = index_without_aliases
        self.readonly = readonly

    def __setattr__(self, key, value):
        if getattr(self, 'readonly', False):
            raise AttributeError("Attribute '%s' of '%s' object is readonly." % (key, type(self).__name__))
        super().__setattr__(key, value)


_readonly_protected_flags_class_attributes = {
    '__writable_protected_flags_class_attributes__',
    '__all_members__', '__members__', '__members_without_aliases__', '__member_aliases__', '__bits_to_properties__',
}

# these attributes are writable when __writable_protected_flags_class_attributes__ is set to True on the class.
_temporarily_writable_protected_flags_class_attributes = {'__all_bits__', '__no_flags_name__', '__all_flags_name__'}

_protected_flags_class_attributes = _readonly_protected_flags_class_attributes |\
                                    _temporarily_writable_protected_flags_class_attributes


def _initialize_class_dict_and_create_flags_class(class_dict, class_name, create_flags_class):
    # all_members is used by __getattribute__ and __setattribute__. It contains all items
    # from members and also the no_flags and all_flags special members if they are defined.
    all_members = collections.OrderedDict()
    members = collections.OrderedDict()
    members_without_aliases = collections.OrderedDict()
    bits_to_properties = collections.OrderedDict()
    member_aliases = {}
    class_dict['__all_members__'] = ReadonlyDictProxy(all_members)
    class_dict['__members__'] = ReadonlyDictProxy(members)
    class_dict['__members_without_aliases__'] = ReadonlyDictProxy(members_without_aliases)
    class_dict['__bits_to_properties__'] = ReadonlyDictProxy(bits_to_properties)
    class_dict['__member_aliases__'] = ReadonlyDictProxy(member_aliases)

    flags_class = create_flags_class(class_dict)

    def instantiate_member(properties, special):
        if not isinstance(properties.name, str):
            raise TypeError('Flag name should be an str but it is %r' % (properties.name,))
        if not isinstance(properties.bits, int):
            raise TypeError('Flag bits should be an int but it is %r' % (properties.bits,))
        if not special and properties.bits == 0:
            raise ValueError("Flag '%s' has the invalid value of zero" % properties.name)
        member = _internal_instantiate_flags(flags_class, properties.bits)
        if member.bits != properties.bits:
            raise RuntimeError("%s.__init__ has altered the assigned bits of member '%s' from %r to %r" % (
                class_name, properties.name, properties.bits, member.bits))
        return member

    def add_member(member, properties, special):
        # special members (like no_flags, and all_flags) have no index
        # and they appear only in the __all_members__ collection.
        if all_members.setdefault(properties.name, member) is not member:
            raise ValueError('Duplicate flag name: %r' % properties.name)

        properties.index = None
        properties.index_without_aliases = None
        if not special:
            properties.index = len(members)
            members[properties.name] = member
            properties_for_bits = bits_to_properties.setdefault(properties.bits, properties)
            is_alias = properties_for_bits is not properties
            if is_alias:
                member_aliases[properties.name] = properties_for_bits.name
            else:
                properties.index_without_aliases = len(members_without_aliases)
                members_without_aliases[properties.name] = member

        if not properties.readonly:
            properties.readonly = True

    def instantiate_and_add_member(properties, special_member=False):
        member = instantiate_member(properties, special_member)
        add_member(member, properties, special_member)

    return flags_class, instantiate_and_add_member


def _create_flags_class_with_members(class_name, class_dict, member_definitions, create_flags_class):
    class_dict['__writable_protected_flags_class_attributes__'] = True

    flags_class, instantiate_and_add_member = _initialize_class_dict_and_create_flags_class(
        class_dict, class_name, create_flags_class)

    flag_properties_list = [FlagProperties(name=name, data=data, bits=1 << index)
                            for index, (name, data) in enumerate(member_definitions)]

    flag_properties_list = flags_class.process_flag_properties_before_flag_creation(flag_properties_list)
    # flag_properties_list isn't anymore guaranteed to be a list, treat it as an iterable

    # flags_class.__all_bits__ is used during flags_class instantiation
    # so we have to calculate and set it before creating the first member.
    all_bits = (properties.bits for properties in flag_properties_list)
    all_bits = functools.reduce(operator.__or__, all_bits)
    flags_class.__all_bits__ = all_bits

    del flags_class.__writable_protected_flags_class_attributes__

    for properties in flag_properties_list:
        instantiate_and_add_member(properties)

    def instantiate_special_member(name, bits):
        if name is not None:
            instantiate_and_add_member(FlagProperties(name=name, bits=bits), special_member=True)

    instantiate_special_member(flags_class.__no_flags_name__, 0)
    instantiate_special_member(flags_class.__all_flags_name__, all_bits)

    return flags_class


_INTERNAL_FLAGS_INSTANTIATION_MAGIC_PARAM_NAME = 'internal_flags_instantiation_magic'


def _internal_instantiate_flags(flags_class, *args, **kwargs):
    """
    Flags classes should be instantiated only internally by this library by using this function.
    Instantiation happens only in two cases:
    1. When the Flags class is being created its members are instantiated as instances of Flags.
    2. Performing arithmetic with Flags instances create other Flags instances (e.g. MyFlags.flag0 | MyFlags.flag1).
    """
    kwargs[_INTERNAL_FLAGS_INSTANTIATION_MAGIC_PARAM_NAME] = True
    return flags_class(*args, **kwargs)


class FlagsMeta(type):
    def __new__(mcs, class_name, bases, class_dict):
        if '__slots__' in class_dict:
            raise RuntimeError("You aren't allowed to use __slots__ or instance attributes in Flags subclass "
                               "'%s.%s'" % (class_dict['__module__'], class_name))
        class_dict['__slots__'] = ()

        if Flags is None:
            # This __new__ call is creating Flags.
            return super().__new__(mcs, class_name, bases, class_dict)

        # We don't allow more than one base classes that are derived from FlagsBase.
        flags_bases = [base for base in bases if issubclass(base, Flags)]
        if len(flags_bases) >= 2:
            raise RuntimeError("Your flags class can derive at most from one other FlagsBase subclass.")

        member_definitions = _extract_member_definitions_from_class_attributes(class_dict)
        if flags_bases and hasattr(flags_bases[0], '__members__'):
            raise RuntimeError("You can't subclass %r because it has already defined flag members" % (flags_bases[0],))

        if not member_definitions:
            return super().__new__(mcs, class_name, bases, class_dict)

        def create_flags_class(custom_class_dict):
            return super(FlagsMeta, mcs).__new__(mcs, class_name, bases, custom_class_dict)

        return _create_flags_class_with_members(class_name, class_dict, member_definitions, create_flags_class)

    def __call__(cls, *args, **kwargs):
        if kwargs.pop(_INTERNAL_FLAGS_INSTANTIATION_MAGIC_PARAM_NAME, False):
            # We have to instantiate the Flags class.
            # This happens when the Flags class is being created along with its members that
            # are Flags instances and also when arithmetic is being performed on the FLags instances.
            return super().__call__(*args, **kwargs)

        # The Flags class or one of its subclasses was "called" as a
        # utility function to create a subclass of the called class.
        return _create_flags_subclass(cls, *args, **kwargs)

    @classmethod
    def __prepare__(cls, class_name, bases):
        return collections.OrderedDict()

    def __delattr__(cls, name):
        if name in _protected_flags_class_attributes and name != '__writable_protected_flags_class_attributes__':
            raise AttributeError("Can't delete protected attribute '%s'" % name)
        super().__delattr__(name)

    def __setattr__(cls, name, value):
        if name in _protected_flags_class_attributes:
            if name in _readonly_protected_flags_class_attributes or\
                    not getattr(cls, '__writable_protected_flags_class_attributes__', False):
                raise AttributeError("Can't assign protected attribute '%s'" % name)
        elif name in getattr(cls, '__all_members__', {}):
            raise AttributeError("Can't assign protected attribute '%s'" % name)
        super().__setattr__(name, value)

    def __getattr__(cls, name):
        try:
            return super().__getattribute__('__all_members__')[name]
        except KeyError:
            raise AttributeError(name) from None

    def __getitem__(cls, name):
        return cls.__all_members__[name]

    def __iter__(cls):
        return iter(cls.__members_without_aliases__.values())

    def __reversed__(cls):
        return reversed(list(cls.__members_without_aliases__.values()))

    def __len__(cls):
        return len(cls.__members_without_aliases__)

    def process_flag_properties_before_flag_creation(cls, flag_properties_list):
        """
        You can modify all the flag properties before creating the flags instances. You can also remove/add
        members as you wish. You can also set cls.__no_flags_name__ and cls.__all_flags_name__ at this point
        but later they become readonly.

        :param flag_properties_list: A list of FlagProperties instances. You can do anything to this
        list: replace/remove items, totally ignore this list and return something else, etc...
        :return: An iterable that yields FlagProperties instances. You have to set only the name, bits, and
        value attributes of FlagProperties instances, the rest is ignored.
        """
        return flag_properties_list

    # TODO: utility method to fill the flag members to a namespace, and another utility that can fill
    # them to a module (a specific case of namespaces)

    __no_flags_name__ = 'no_flags'
    __all_flags_name__ = 'all_flags'


class FlagsArithmeticMixin:
    __slots__ = ('__bits',)

    def __init__(self, bits):
        if not isinstance(bits, int):
            raise TypeError('The bits parameter has to be an int value, instead it is %r' % (bits,))
        self.__bits = bits & type(self).__all_bits__

    @property
    def bits(self):
        return self.__bits

    def __contains__(self, item):
        if type(item) is not type(self):
            return False
        return (item.__bits & self.__bits) == item.__bits

    def __generate_comparison_operator(operator_):
        def comparison_operator(self, other):
            if type(other) is not type(self):
                return NotImplemented
            return operator_(self.__bits, other.__bits)
        comparison_operator.__name__ = operator_.__name__
        return comparison_operator

    def __generate_arithmetic_operator(operator_):
        def arithmetic_operator(self, other):
            if type(other) is not type(self):
                return NotImplemented
            return _internal_instantiate_flags(type(self), operator_(self.__bits, other.__bits))
        arithmetic_operator.__name__ = operator_.__name__
        return arithmetic_operator

    __or__ = __generate_arithmetic_operator(operator.__or__)
    __xor__ = __generate_arithmetic_operator(operator.__xor__)
    __and__ = __generate_arithmetic_operator(operator.__and__)

    def __sub__(self, other):
        if type(other) is not type(self):
            return NotImplemented
        bits = self.__bits ^ (self.__bits & other.__bits)
        return _internal_instantiate_flags(type(self), bits)

    __eq__ = __generate_comparison_operator(operator.__eq__)
    __ne__ = __generate_comparison_operator(operator.__ne__)
    __ge__ = __generate_comparison_operator(operator.__ge__)
    __gt__ = __generate_comparison_operator(operator.__gt__)
    __le__ = __generate_comparison_operator(operator.__le__)
    __lt__ = __generate_comparison_operator(operator.__lt__)

    def __invert__(self):
        cls = type(self)
        return _internal_instantiate_flags(cls, self.__bits ^ cls.__all_bits__)


# This is used by FlagsBaseMeta to detect whether the currently created class is FlagsBase.
Flags = None


class Flags(FlagsArithmeticMixin, metaclass=FlagsMeta):
    @property
    def is_member(self):
        """ `flags.is_member` is a shorthand for `flags.properties is not None`.
        If this property is False then this Flags instance has either zero bits or holds a combination
        of flag member bits.
        If this property is True then the bits of this Flags instance match exactly the bits associated
        with one of the members. This however doesn't necessarily mean that this flag instance isn't a
        combination of several flags because the bits of a member can be the subset of another member.
        For example if member0_bits=0x1 and member1_bits=0x3 then the bits of member0 are a subset of
        the bits of member1. If a flag instance holds the bits of member1 then Flags.is_member returns
        True and Flags.properties returns the properties of member1 but __len__() returns 2 and
        __iter__() yields both member0 and member1.
        """
        return type(self).__bits_to_properties__.get(self.bits) is not None

    @property
    def properties(self):
        """
        :return: Returns None if this flag isn't an exact member of a flags class but a combination of flags,
        returns an object holding the properties (e.g.: name, data, index, ...) of the flag otherwise.
        We don't store flag properties directly in Flags instances because this way Flags instances that are
        the (temporary) result of flags arithmetic don't have to maintain these fields and it also has some
        benefits regarding memory usage. """
        return type(self).__bits_to_properties__.get(self.bits)

    @property
    def name(self):
        properties = self.properties
        return self.properties.name if properties else None

    @property
    def data(self):
        properties = self.properties
        return self.properties.data if properties else None

    def __int__(self):
        return self.bits

    def __iter__(self):
        members = type(self).__members_without_aliases__.values()
        return (member for member in members if member in self)

    def __reversed__(self):
        members = reversed(list(type(self).__members_without_aliases__.values()))
        return (member for member in members if member in self)

    def __len__(self):
        return sum(1 for _ in self)

    def __bool__(self):
        return self.bits == 0

    def __hash__(self):
        return self.bits ^ hash(type(self))

    def __reduce_ex__(self, proto):
        return _unpickle_flags_instance, (type(self), self.bits)

    def __str__(self):
        properties = self.properties
        if properties is None:
            # this is a set of flags as a result of arithmetic
            flag_set = '|'.join(member.name for member in self)
            return '%s(%s)' % (type(self).__name__, flag_set)
        return '%s.%s' % (type(self).__name__, properties.name)

    def __repr__(self):
        properties = self.properties
        if properties is None:
            # this is a set of flags as a result of arithmetic
            flag_set = '|'.join(member.name for member in self)
            return '<%s(%s) bits=0x%04X>' % (type(self).__name__, flag_set, self.bits)
        return '<%s.%s bits=0x%04X data=%r>' % (type(self).__name__, properties.name, properties.bits, properties.data)


class CustomFlags(Flags):
    @classmethod
    def process_flag_properties_before_flag_creation(cls, flag_properties_list):
        # TODO
        for properties in flag_properties_list:
            properties.bits = properties.data
        return flag_properties_list


# It isn't desirable and possible to create new flags class member instances. Instead of
# doing so pickling has to retrieve/lookup already existing flags class members by name.
def _unpickle_flags_instance(flags_class, bits):
    return _internal_instantiate_flags(flags_class, bits)
_unpickle_flags_instance.__safe_for_unpickling__ = True
