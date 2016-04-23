# -*- coding: utf-8 -*-
import collections
import functools
import pickle

from dictionaries import ReadonlyDictProxy

__all__ = ['Flags', 'FlagProperties', 'FlagData', 'UNDEFINED']


# version_info[0]: Increase in case of large milestones/releases.
# version_info[1]: Increase this and zero out version_info[2] if you have explicitly modified
#                  a previously existing behavior/interface.
#                  If the behavior of an existing feature changes as a result of a bugfix
#                  and the new (bugfixed) behavior is that meets the expectations of the
#                  previous interface documentation then you shouldn't increase this, in that
#                  case increase only version_info[2].
# version_info[2]: Increase in case of bugfixes. Also use this if you added new features
#                  without modifying the behavior of the previously existing ones.
version_info = (1, 0, 0)
__version__ = '.'.join(str(n) for n in version_info)
__author__ = 'István Pásztor'
__license__ = 'MIT'


def _is_descriptor(obj):
    return hasattr(obj, '__get__') or hasattr(obj, '__set__') or hasattr(obj, '__delete__')


class _Const:
    def __init__(self, name):
        self.__name = name

    def __repr__(self):
        return self.__name


# "singleton" to be used as a const value with identity checks
UNDEFINED = _Const('UNDEFINED')


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
            raise pickle.PicklingError("'%s' is unpicklable" % (type(self).__name__,))
        flags_class.__reduce_ex__ = disabled_reduce_ex

        # For pickle module==None means the __main__ module so let's change it to a non-existing name.
        # This will cause a failure while trying to pickle the class.
        module = '<unknown>'
    flags_class.__module__ = module

    if qualname is not None:
        flags_class.__qualname__ = qualname

    return flags_class


def _process_inline_members_definition(members):
    """
    :param members: this can be any of the following:
    - a string containing a space and/or comma separated list of names: e.g.:
      "item1 item2 item3" OR "item1,item2,item3" OR "item1, item2, item3"
    - tuple/list/Set of strings (names)
    - Mapping of (name, data) pairs
    - any kind of iterable that yields (name, data) pairs
    :return: An iterable of (name, data) pairs.
    """
    if isinstance(members, str):
        members = ((name, UNDEFINED) for name in members.replace(',', ' ').split())
    elif isinstance(members, (tuple, list, collections.Set)):
        if members and isinstance(next(iter(members)), str):
            members = ((name, UNDEFINED) for name in members)
    elif isinstance(members, collections.Mapping):
        members = members.items()
    return members


def _extract_member_definitions_from_class_attributes(class_dict):
    members = [(name, data) for name, data in class_dict.items()
               if not name.startswith('_') and not _is_descriptor(data)]
    for name, _ in members:
        del class_dict[name]

    members.extend(_process_inline_members_definition(class_dict.pop('__members__', ())))
    return members


class ReadonlyzerMixin:
    """ Makes instance attributes readonly after setting readonly=True. """
    __slots__ = ('__readonly',)

    def __init__(self, *args, readonly=False, **kwargs):
        # Calling super() before setting readonly.
        # This way super().__init__ can set attributes even if readonly==True
        super().__init__(*args, **kwargs)
        self.__readonly = readonly

    @property
    def readonly(self):
        try:
            return self.__readonly
        except AttributeError:
            return False

    @readonly.setter
    def readonly(self, value):
        self.__readonly = value

    def __setattr__(self, key, value):
        if self.readonly:
            raise AttributeError("Can't set attribute '%s' of readonly '%s' object" % (key, type(self).__name__))
        super().__setattr__(key, value)

    def __delattr__(self, key):
        if self.readonly:
            raise AttributeError("Can't delete attribute '%s' of readonly '%s' object" % (key, type(self).__name__))
        super().__delattr__(key)


class FlagProperties(ReadonlyzerMixin):
    __slots__ = ('name', 'data', 'bits', 'index', 'index_without_aliases')

    def __init__(self, *, name, bits, data=None, index=None, index_without_aliases=None):
        self.name = name
        self.data = data
        self.bits = bits
        self.index = index
        self.index_without_aliases = index_without_aliases
        super().__init__()


_READONLY_PROTECTED_FLAGS_CLASS_ATTRIBUTES = frozenset([
    '__writable_protected_flags_class_attributes__', '__all_members__', '__members__', '__members_without_aliases__',
    '__member_aliases__', '__bits_to_properties__', '__bits_to_instance__',
])

# these attributes are writable when __writable_protected_flags_class_attributes__ is set to True on the class.
_TEMPORARILY_WRITABLE_PROTECTED_FLAGS_CLASS_ATTRIBUTES = frozenset([
    '__all_bits__', '__no_flags__', '__all_flags__', '__no_flags_name__', '__all_flags_name__',
])

_PROTECTED_FLAGS_CLASS_ATTRIBUTES = _READONLY_PROTECTED_FLAGS_CLASS_ATTRIBUTES | \
                                    _TEMPORARILY_WRITABLE_PROTECTED_FLAGS_CLASS_ATTRIBUTES


def _is_valid_bits_value(bits):
    return isinstance(bits, int) and not isinstance(bits, bool)


def _initialize_class_dict_and_create_flags_class(class_dict, class_name, create_flags_class):
    # all_members is used by __getattribute__ and __setattr__. It contains all items
    # from members and also the no_flags and all_flags special members if they are defined.
    all_members = collections.OrderedDict()
    members = collections.OrderedDict()
    members_without_aliases = collections.OrderedDict()
    bits_to_properties = collections.OrderedDict()
    bits_to_instance = collections.OrderedDict()
    member_aliases = {}
    class_dict['__all_members__'] = ReadonlyDictProxy(all_members)
    class_dict['__members__'] = ReadonlyDictProxy(members)
    class_dict['__members_without_aliases__'] = ReadonlyDictProxy(members_without_aliases)
    class_dict['__bits_to_properties__'] = ReadonlyDictProxy(bits_to_properties)
    class_dict['__bits_to_instance__'] = ReadonlyDictProxy(bits_to_instance)
    class_dict['__member_aliases__'] = ReadonlyDictProxy(member_aliases)

    flags_class = create_flags_class(class_dict)

    def instantiate_member(properties, special):
        if not isinstance(properties.name, str):
            raise TypeError('Flag name should be an str but it is %r' % (properties.name,))
        if not _is_valid_bits_value(properties.bits):
            raise TypeError("Bits for flag '%s' should be an int but it is %r" % (properties.name, properties.bits))
        if not special and properties.bits == 0:
            raise ValueError("Flag '%s' has the invalid value of zero" % properties.name)
        member = flags_class(properties.bits)
        if int(member) != properties.bits:
            raise RuntimeError("%s has altered the assigned bits of member '%s' from %r to %r" % (
                class_name, properties.name, properties.bits, int(member)))
        return member

    def register_member(member, properties, special):
        # special members (like no_flags, and all_flags) have no index
        # and they appear only in the __all_members__ collection.
        if all_members.setdefault(properties.name, member) is not member:
            raise ValueError('Duplicate flag name: %r' % properties.name)

        # It isn't a problem if an instance with the same bits already exists in bits_to_instance because
        # a member contains only the bits so our new member is equivalent with the replaced one.
        bits_to_instance[properties.bits] = member

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

    def instantiate_and_register_member(properties, special_member=False):
        member = instantiate_member(properties, special_member)
        register_member(member, properties, special_member)
        return member

    return flags_class, instantiate_and_register_member


def _create_flags_class_with_members(class_name, class_dict, member_definitions, create_flags_class):
    class_dict['__writable_protected_flags_class_attributes__'] = True

    flags_class, instantiate_and_register_member = _initialize_class_dict_and_create_flags_class(
        class_dict, class_name, create_flags_class)

    flag_properties_list = [FlagProperties(name=name, data=data, bits=None) for name, data in member_definitions]
    flag_properties_list = flags_class.process_flag_properties_before_flag_creation(flag_properties_list)
    # flag_properties_list isn't anymore guaranteed to be a list, treat it as an iterable

    all_bits = 0
    for properties in flag_properties_list:
        if not isinstance(properties, FlagProperties):
            raise TypeError("%s.%s returned an object that isn't an instance of %s: %r" %
                            (flags_class.__name__, flags_class.process_flag_properties_before_flag_creation.__name__,
                             FlagProperties.__name__, properties))
        instantiate_and_register_member(properties)
        all_bits |= properties.bits

    if len(flags_class) == 0:
        # In this case process_flag_properties_before_flag_creation() returned an empty iterable which isn't allowed.
        raise RuntimeError("%s.%s returned an iterable with zero %s instances" %
                           (flags_class.__name__, flags_class.process_flag_properties_before_flag_creation.__name__,
                            FlagProperties.__name__))

    def instantiate_special_member(name, default_name, bits):
        name = default_name if name is None else name
        return instantiate_and_register_member(FlagProperties(name=name, bits=bits), special_member=True)

    flags_class.__no_flags__ = instantiate_special_member(flags_class.__no_flags_name__, '__no_flags__', 0)
    flags_class.__all_flags__ = instantiate_special_member(flags_class.__all_flags_name__, '__all_flags__', all_bits)

    flags_class.__all_bits__ = all_bits

    del flags_class.__writable_protected_flags_class_attributes__
    return flags_class


class FlagData:
    pass


class FlagsMeta(type):
    def __new__(mcs, class_name, bases, class_dict):
        if '__slots__' in class_dict:
            raise RuntimeError("You aren't allowed to use __slots__ in your Flags subclasses")
        class_dict['__slots__'] = ()

        def create_flags_class(custom_class_dict=None):
            return super(FlagsMeta, mcs).__new__(mcs, class_name, bases, custom_class_dict or class_dict)

        if Flags is None:
            # This __new__ call is creating the Flags class of this module.
            return create_flags_class()

        flags_bases = [base for base in bases if issubclass(base, Flags)]
        for base in flags_bases:
            # pylint: disable=protected-access
            if not base.__is_abstract:
                raise RuntimeError("You can't subclass '%s' because it has already defined flag members" %
                                   (base.__name__,))

        member_definitions = _extract_member_definitions_from_class_attributes(class_dict)
        if not member_definitions:
            return create_flags_class()
        return _create_flags_class_with_members(class_name, class_dict, member_definitions, create_flags_class)

    @property
    def __is_abstract(cls):
        return not hasattr(cls, '__members__')

    def __call__(cls, *args, **kwargs):
        if kwargs or len(args) >= 2:
            # The Flags class or one of its subclasses was "called" as a
            # utility function to create a subclass of the called class.
            return _create_flags_subclass(cls, *args, **kwargs)

        # We have zero or one positional argument and we have to create and/or return an exact instance of cls.
        # 1. Zero argument means we have to return a zero flag.
        # 2. A single positional argument can be one of the following cases:
        #    1. An object whose class is exactly cls.
        #    2. An str object that comes from Flags.__str__() or Flags.to_simple_str()
        #    3. An int object that specifies the bits of the Flags instance to be created.

        if cls.__is_abstract:
            raise RuntimeError("Instantiation of abstract flags class '%s.%s' isn't allowed." % (
                cls.__module__, cls.__name__))

        if not args:
            # case 1 - zero positional arguments, we have to return a zero flag
            return cls.__no_flags__

        value = args[0]

        if type(value) is cls:
            # case 2.1
            return value

        if isinstance(value, str):
            # case 2.2
            bits = cls.bits_from_str(value)
        elif _is_valid_bits_value(value):
            # case 2.3
            bits = cls.__all_bits__ & value
        else:
            raise TypeError("Can't instantiate flags class '%s' from value %r" % (cls.__name__, value))

        instance = cls.__bits_to_instance__.get(bits)
        if instance:
            return instance
        return super().__call__(bits)

    @classmethod
    def __prepare__(cls, class_name, bases):
        return collections.OrderedDict()

    def __delattr__(cls, name):
        if (name in _PROTECTED_FLAGS_CLASS_ATTRIBUTES and name != '__writable_protected_flags_class_attributes__') or\
                (name in getattr(cls, '__all_members__', {})):
            raise AttributeError("Can't delete protected attribute '%s'" % name)
        super().__delattr__(name)

    def __setattr__(cls, name, value):
        if name in _PROTECTED_FLAGS_CLASS_ATTRIBUTES:
            if name in _READONLY_PROTECTED_FLAGS_CLASS_ATTRIBUTES or\
                    not getattr(cls, '__writable_protected_flags_class_attributes__', False):
                raise AttributeError("Can't assign protected attribute '%s'" % name)
        elif name in getattr(cls, '__all_members__', {}):
            raise AttributeError("Can't assign protected attribute '%s'" % name)
        super().__setattr__(name, value)

    def __getattr__(cls, name):
        try:
            return super().__getattribute__('__all_members__')[name]
        except KeyError:
            raise AttributeError(name)

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
        You can modify all of the flag properties before creation of flags instances. You can also remove/add
        members as you wish. You can also set cls.__no_flags_name__ and cls.__all_flags_name__ at this point
        but later they become readonly.

        :param flag_properties_list: A list of FlagProperties instances. You can do anything to this
        list: replace/remove items, totally ignore this list and return something else, etc...
        :return: An iterable that yields FlagProperties instances. You have to set only the name, bits, and
        optionally the value attribute of FlagProperties instances, the rest is ignored.
        """

        def normalize_data(properties):
            data = properties.data
            if data is UNDEFINED:
                return UNDEFINED, None
            elif isinstance(data, FlagData):
                return UNDEFINED, data
            elif _is_valid_bits_value(data):
                return data, None
            elif isinstance(data, collections.Iterable):
                data = tuple(data)
                if len(data) == 0:
                    return UNDEFINED, None
                if len(data) == 1:
                    return UNDEFINED, data[0]
                if len(data) == 2:
                    return data
                raise ValueError("Iterable is expected to have at most 2 items instead of %s "
                                 "for flag '%s', iterable: %r" %
                                 (len(data), properties.name, properties.data))
            raise TypeError("Expected an int or an iterable of at most 2 items "
                            "for flag '%s', received %r" % (properties.name, properties.data))

        auto_flags = []
        all_bits = 0
        for item in flag_properties_list:
            item.bits, item.data = normalize_data(item)
            if item.bits is UNDEFINED:
                auto_flags.append(item)
            elif _is_valid_bits_value(item.bits):
                all_bits |= item.bits
            else:
                raise TypeError("Expected an int value as the bits of flag '%s', received %r" % (item.name, item.bits))

        # auto-assigning unused bits to members without custom defined bits
        bit = 1
        for item in auto_flags:
            while bit & all_bits:
                bit <<= 1
            item.bits = bit
            bit <<= 1

        return flag_properties_list

    __no_flags_name__ = 'no_flags'
    __all_flags_name__ = 'all_flags'
    __all_bits__ = -1

    # TODO: utility method to fill the flag members to a namespace, and another utility that can fill
    # them to a module (a specific case of namespaces)


def operator_requires_type_identity(wrapped):
    @functools.wraps(wrapped)
    def wrapper(self, other):
        if type(other) is not type(self):
            return NotImplemented
        return wrapped(self, other)
    return wrapper


class FlagsArithmeticMixin:
    __slots__ = ('__bits',)

    def __new__(cls, bits):
        instance = super().__new__(cls)
        # pylint: disable=protected-access
        instance.__bits = bits & cls.__all_bits__
        return instance

    def __int__(self):
        return self.__bits

    def __bool__(self):
        return self.__bits != 0

    def __contains__(self, item):
        if type(item) is not type(self):
            return False
        # this logic is equivalent to that of __ge__(self, item) and __le__(item, self)
        # pylint: disable=protected-access
        return item.__bits == (self.__bits & item.__bits)

    def is_disjoint(self, *flags_instances):
        for flags in flags_instances:
            if self & flags:
                return False
        return True

    def __create_flags_instance(self, bits):
        # optimization, exploiting immutability
        if bits == self.__bits:
            return self
        return type(self)(bits)

    @operator_requires_type_identity
    def __or__(self, other):
        # pylint: disable=protected-access
        return self.__create_flags_instance(self.__bits | other.__bits)

    @operator_requires_type_identity
    def __xor__(self, other):
        # pylint: disable=protected-access
        return self.__create_flags_instance(self.__bits ^ other.__bits)

    @operator_requires_type_identity
    def __and__(self, other):
        # pylint: disable=protected-access
        return self.__create_flags_instance(self.__bits & other.__bits)

    @operator_requires_type_identity
    def __sub__(self, other):
        # pylint: disable=protected-access
        bits = self.__bits ^ (self.__bits & other.__bits)
        return self.__create_flags_instance(bits)

    @operator_requires_type_identity
    def __eq__(self, other):
        # pylint: disable=protected-access
        return self.__bits == other.__bits

    @operator_requires_type_identity
    def __ne__(self, other):
        # pylint: disable=protected-access
        return self.__bits != other.__bits

    @operator_requires_type_identity
    def __ge__(self, other):
        # pylint: disable=protected-access
        return other.__bits == (self.__bits & other.__bits)

    @operator_requires_type_identity
    def __gt__(self, other):
        # pylint: disable=protected-access
        return (self.__bits != other.__bits) and (other.__bits == (self.__bits & other.__bits))

    @operator_requires_type_identity
    def __le__(self, other):
        # pylint: disable=protected-access
        return self.__bits == (self.__bits & other.__bits)

    @operator_requires_type_identity
    def __lt__(self, other):
        # pylint: disable=protected-access
        return (self.__bits != other.__bits) and (self.__bits == (self.__bits & other.__bits))

    def __invert__(self):
        return self.__create_flags_instance(self.__bits ^ type(self).__all_bits__)


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
        return type(self).__bits_to_properties__.get(int(self)) is not None

    @property
    def properties(self):
        """
        :return: Returns None if this flag isn't an exact member of a flags class but a combination of flags,
        returns an object holding the properties (e.g.: name, data, index, ...) of the flag otherwise.
        We don't store flag properties directly in Flags instances because this way Flags instances that are
        the (temporary) result of flags arithmetic don't have to maintain these fields and it also has some
        benefits regarding memory usage. """
        return type(self).__bits_to_properties__.get(int(self))

    @property
    def name(self):
        properties = self.properties
        return self.properties.name if properties else None

    @property
    def data(self):
        properties = self.properties
        return self.properties.data if properties else None

    def __getattr__(self, name):
        try:
            member = type(self).__members__[name]
        except KeyError:
            raise AttributeError(name)
        return member in self

    def __iter__(self):
        members = type(self).__members_without_aliases__.values()
        return (member for member in members if member in self)

    def __reversed__(self):
        members = reversed(list(type(self).__members_without_aliases__.values()))
        return (member for member in members if member in self)

    def __len__(self):
        return sum(1 for _ in self)

    def __hash__(self):
        return int(self) ^ hash(type(self))

    def __reduce_ex__(self, proto):
        return type(self), (self.to_simple_str(),)

    def __str__(self):
        # Warning: The output of this method has to be a string that can be processed by bits_from_str
        properties = self.properties
        if properties is None:
            # this is a set of flags as a result of arithmetic
            return '%s(%s)' % (type(self).__name__, self.to_simple_str())
        return '%s.%s' % (type(self).__name__, properties.name)

    def __repr__(self):
        properties = self.properties
        if properties is None:
            # this is a set of flags as a result of arithmetic
            return '<%s(%s) bits=0x%04X>' % (type(self).__name__, self.to_simple_str(), int(self))
        return '<%s.%s bits=0x%04X data=%r>' % (type(self).__name__, properties.name, properties.bits, properties.data)

    def to_simple_str(self):
        return '|'.join(member.name for member in self)

    @classmethod
    def from_simple_str(cls, s):
        return cls(cls.bits_from_simple_str(s))

    @classmethod
    def from_str(cls, s):
        if not isinstance(s, str):
            raise TypeError("Expected an str instance, received %r" % (s,))
        return cls(s)

    @classmethod
    def bits_from_simple_str(cls, s):
        member_names = (name.strip() for name in s.split('|'))
        member_names = filter(None, member_names)
        bits = 0
        for member_name in filter(None, member_names):
            member = cls.__all_members__.get(member_name)
            if member is None:
                raise ValueError("Invalid flag '%s.%s' in string %r" % (cls.__name__, member_name, s))
            bits |= int(member)
        return bits

    @classmethod
    def bits_from_str(cls, s):
        """ Converts the output of __str__ into an integer. """
        try:
            if len(s) <= len(cls.__name__) or not s.startswith(cls.__name__):
                return cls.bits_from_simple_str(s)
            c = s[len(cls.__name__)]
            if c == '(':
                if not s.endswith(')'):
                    raise ValueError
                return cls.bits_from_simple_str(s[len(cls.__name__)+1:-1])
            elif c == '.':
                member_name = s[len(cls.__name__)+1:]
                return int(cls.__all_members__[member_name])
            else:
                raise ValueError
        except ValueError as ex:
            if ex.args:
                raise
            raise ValueError("%s.%s: invalid input: %r" % (cls.__name__, cls.bits_from_str.__name__, s))
        except KeyError as ex:
            raise ValueError("%s.%s: Invalid flag name '%s' in input: %r" % (cls.__name__, cls.bits_from_str.__name__,
                                                                             ex.args[0], s))
