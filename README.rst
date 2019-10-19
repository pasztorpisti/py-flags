========
py-flags
========

Type-safe (bit)flags
""""""""""""""""""""


.. image:: https://img.shields.io/travis/pasztorpisti/py-flags.svg?style=flat
    :target: https://travis-ci.org/pasztorpisti/py-flags
    :alt: build

.. image:: https://img.shields.io/codacy/grade/6a7d15a84f524e98943678875d2f0dd8/master.svg?style=flat
    :target: https://www.codacy.com/app/pasztorpisti/py-flags
    :alt: code quality

.. image:: https://img.shields.io/coveralls/pasztorpisti/py-flags/master.svg?style=flat
    :target: https://coveralls.io/r/pasztorpisti/py-flags?branch=master
    :alt: coverage

.. image:: https://img.shields.io/pypi/v/py-flags.svg?style=flat
    :target: https://pypi.python.org/pypi/py-flags
    :alt: pypi

.. image:: https://img.shields.io/github/tag/pasztorpisti/py-flags.svg?style=flat
    :target: https://github.com/pasztorpisti/py-flags
    :alt: github

.. image:: https://img.shields.io/github/license/pasztorpisti/py-flags.svg?style=flat
    :target: https://github.com/pasztorpisti/py-flags/blob/master/LICENSE.txt
    :alt: license: MIT


.. note::

    Python 3.6+ users should consider using the ``Flag`` and ``IntFlag`` classes of the standard ``enum`` module.
    Those are very similar to the ``flags.Flags`` class of this repo.

    It's enough to read only the short Installation_ and `Quick Overview`_ sections to start using this module.
    The rest is about details.


.. contents::


Installation
============

.. code-block:: sh

    pip install py-flags

Alternatively you can download the distribution from the following places:

- https://pypi.python.org/pypi/py-flags#downloads
- https://github.com/pasztorpisti/py-flags/releases


Quick Overview
==============

With this module you can define type-safe (bit)flags. The style of the flag definition is very similar to the enum
definitions you can create using the standard ``enum`` module of python 3.


Defining flags with the ``class`` syntax:

.. code-block:: python

    >>> from flags import Flags
    >>>
    >>> class TextStyle(Flags):
    >>>     bold = 1            # value = 1 << 0
    >>>     italic = 2          # value = 1 << 1
    >>>     underline = 4       # value = 1 << 2


In most cases you just want to use the flags as a set (of ``bool`` variables) and the actual flag values aren't
important. To avoid manually setting unique flag values you can use auto assignment. To auto-assign a unique flag value
use an empty iterable (for example empty tuple or list) as the value of the flag. Auto-assignment picks the first
unused least significant bit for each auto-assignable flag in top-to-bottom order.

.. code-block:: python

    >>> class TextStyle(Flags):
    >>>     bold = ()           # value = 1 << 0
    >>>     italic = ()         # value = 1 << 1
    >>>     underline = ()      # value = 1 << 2


As a shortcut you can call a flags class to create a subclass of it. This pattern has also been stolen from the
standard ``enum`` module. The following flags definition is equivalent to the previous definition that uses the
``class`` syntax:


.. code-block:: python

    >>> TextStyle = Flags('TextStyle', 'bold italic underline')


Flags have human readable string representations and ``repr`` with more info:

.. code-block:: python

    >>> print(TextStyle.bold)
    TextStyle.bold
    >>> print(repr(TextStyle.bold))
    <TextStyle.bold bits=0x0001 data=UNDEFINED>

The type of a flag is the flags class it belongs to:

.. code-block:: python

    >>> type(TextStyle.bold)
    <class '__main__.TextStyle'>
    >>> isinstance(TextStyle.bold, TextStyle)
    True


You can combine flags with bool operators. The result is also an instance of the flags class with the previously
described properties.

.. code-block:: python

    >>> result = TextStyle.bold | TextStyle.italic
    >>>
    >>> print(result)
    TextStyle(bold|italic)
    >>> print(repr(result))
    <TextStyle(bold|italic) bits=0x0003>


Operators work in a type-safe way: you can combine only flags of the same type. Trying to combine them with instances
of other types results in error:

.. code-block:: python

    >> result = TextStyle.bold | 1
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
    TypeError: unsupported operand type(s) for |: 'TextStyle' and 'int'
    >>>
    >>> class OtherFlags(Flags):
    ...     flag0 = ()
    ...
    >>> result = TextStyle.bold | OtherFlags.flag0
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
    TypeError: unsupported operand type(s) for |: 'TextStyle' and 'OtherFlags'


Flags and their combinations (basically the instances of the flags class) are immutable and hashable so they can be
used as set members and dictionary keys:

.. code-block:: python

    >>> font_files = {}
    >>> font_files[TextStyle.bold] = 'bold.ttf'
    >>> font_files[TextStyle.italic] = 'italic.ttf'
    >>> font_files == {TextStyle.bold: 'bold.ttf', TextStyle.italic: 'italic.ttf'}
    True


The flags you define automatically have two "virtual" flags: ``no_flags`` and ``all_flags``. ``no_flags`` is basically
the zero flag and ``all_flags`` is the combination of all flags you've defined:

.. code-block:: python

    >>> TextStyle.no_flags
    <TextStyle() bits=0x0000>
    >>> TextStyle.all_flags
    <TextStyle(bold|italic|underline) bits=0x0007>


Testing whether specific flags are set:

.. code-block:: python

    >>> result = TextStyle.bold | TextStyle.italic
    >>> bool(result & TextStyle.bold)       # 1. oldschool bit twiddling
    True
    >>> TextStyle.bold in result            # 2. in operator
    True
    >>> result.bold                         # 3. attribute-style access
    True


From the above testing methods the attribute-style access can check only the presence of a single flag. With the
``&`` and ``in`` operators you can check the presence of multiple flags at the same time:

.. code-block:: python

    >>> result = TextStyle.bold | TextStyle.italic
    >>>
    >>> # True if at least one of the bold and underline flags is set
    >>> bool((TextStyle.bold | TextStyle.underline) & result)
    True
    >>> # True only when both the bold and underline flags are set
    >>> (TextStyle.bold | TextStyle.underline) in result
    False


If for some reason you need the actual integer value of the flags then you can cast them to ``int``:

.. code-block:: python

    >>> int(TextStyle.bold)
    1


You can convert the ``int()`` and ``str()`` representations of flags back into flags instances:

.. code-block:: python

    >>> TextStyle(2)
    <TextStyle.italic bits=0x0002 data=UNDEFINED>
    >>> TextStyle('TextStyle.bold')
    <TextStyle.bold bits=0x0001 data=UNDEFINED>


Flags type VS builtin python types
==================================

You can find several discussions online questioning the pythonicity of using flags. The reason for this is that
python provides several builtin types that provide flags-like functionality. Despite this you can still see some
libraries (like the ``re`` module of python) that make use of flags usually in the form of an ``int`` value.

I think that a flags type provides an interesting combination of the properties of the native python solutions
that can make your code better in some cases.


Instead of a flags type you can use the following solutions if you want to work with builtin python types:

+------------------------------+-------------------------------------------------------------------------+
| Builtin type                 | How can we use it as flags?                                             |
+==============================+=========================================================================+
| ``int``                      | Closes sibling of a full-featured flags class. No need for explanation. |
+------------------------------+-------------------------------------------------------------------------+
| ``set``, ``frozenset``       | By giving each flag an id/name we can represent a set of flags by       |
|                              | putting only the name of the active bits/flags into the set.            |
+------------------------------+-------------------------------------------------------------------------+
| Several ``bool`` variables   | We can store bits of a flag in separate ``bool`` variables:             |
|                              |                                                                         |
|                              | - as function args and locals                                           |
|                              | - as named ``bool`` values in dictionaries                              |
|                              | - as attributes of an arbitrary object                                  |
+------------------------------+-------------------------------------------------------------------------+

A purpose-built flags type can provide all of the following features while all builtin python types lack at least some:

- Easy to store and pass around as a single object (e.g.: as a function arg).
- Easy way to combine "a set of ``bool`` variables"/flags with a single bitwise bool operation.
- Flag with integer representation possibly with several bits set (sometimes comes in handy for FFI code).
- Human readable ``str()`` and ``repr()`` for debugging and error messages.
- Type safety: we should be able to combine only instances of the same flags type.
- Immutability.

Based on the above info it's easier to decide when it makes sense to use flags. In some cases the ``flags`` module
absolutely rocks:

- FFI code.
- Having a lot of related ``bool`` variables that you often pass around in function calls. In this case using flags
  can simplify your function declarations (and other parts of the code) while adding/removing flags requires no change
  in function signatures.


Flags class declaration
=======================


Class attributes: flags VS your helper methods, properties and attributes
-------------------------------------------------------------------------

A flags class attribute is treated as a flag if it isn't a descriptor and its name doesn't start with ``_``.
For those who don't know what python descriptors are: methods and properties are descriptors so you
can safely define helper methods and properties without being afraid that they are treated as flags.

.. code-block:: python

    >>> from flags import Flags
    >>>
    >>> class TextStyle(Flags):
    >>>     bold = 1            # value = 1 << 0
    >>>     italic = 2          # value = 1 << 1
    >>>     underline = 4       # value = 1 << 2
    >>>
    >>>     # this isn't treated as a flag because of the '_' prefix
    >>>     _extra_data = 42
    >>>
    >>>     @property
    >>>     def helper_property(self):
    >>>         ...
    >>>
    >>>     def helper_method(self):
    >>>         ...


Possible ways to define flag values
-----------------------------------

Each flag in your flags class has an integer value (bitmask) and also an optional user defined app-specific data object.
Class attributes that define your flags can have the following values:

1. An integer value: bits=integer_value, data=\ ``flags.UNDEFINED``
2. An iterable of ...
    1. 0 items: bits=<auto-assigned>, data=\ ``flags.UNDEFINED``
    2. 1 item: bits=<auto-assigned>, data=iterable[0]
    3. 2 items: bits=iterable[0], data=iterable[1]

.. code-block:: python

    >>> from flags import Flags
    >>>
    >>> class FlagValueAssignmentExample(Flags):
    >>>     # 1. bits=42, data=flags.UNDEFINED
    >>>     flag1 = 42
    >>>
    >>>     # 2.1. bits=<auto-assigned>, data=flags.UNDEFINED
    >>>     flag21_1 = ()
    >>>     flag21_2 = []
    >>>
    >>>     # 2.2. bits=<auto-assigned>, data='my_data'
    >>>     flag22_1 = 'my_data',       # a tuple with 1 item
    >>>     flag22_2 = ('my_data',)
    >>>     flag22_3 = ['my_data']
    >>>
    >>>     # 2.3. bits=42, data='my_data'
    >>>     flag23_1 = 42, 'my_data'    # a tuple with 2 items
    >>>     flag23_2 = (42, 'my_data')
    >>>     flag23_3 = [42, 'my_data']


Auto-assignment processes auto-assignable flag definitions in top-to-bottom order and picks the first unused least
significant bit for each. We treat a bit as used if it has been used by any flags that aren't auto-assignable
including those that are defined below the currently auto-assigned flag.

See the `Instance methods and properties`_ section to find out how to access the bits and the user defined
data of flag members.


Aliases
-------

If you define more than one flags with the same bits then these flags are aliases to the first flag that has
been defined with the given bits. In this case only the first flag member is allowed to define user data.
Trying to define data in aliases results in error.

.. code-block:: python

    >>> class AliasExample(Flags):
    >>>     flag1 = 1, 'user_data1'
    >>>     flag2 = 2, 'user_data2'
    >>>
    >>>     # Alias for flag1 because it has the same bit value (1)
    >>>     flag1_alias1 = 1
    >>>
    >>>     # The flag definition below would cause an error because
    >>>     # aliases aren't allowed to define user data.
    >>>     # flag1_alias2 = 1, 'alias_user_data'


Inheritance
-----------

If a flags class has already defined at least one flag then it is considered to be final. Trying to subclass it
results in error. Extending an existing flags class with additional flag members and behavior through subclassing
is semantically undesired (just like in case of enums).

You can however define and subclass your own customized flags base class given that it doesn't define any flags.
This is useful if you want to share utility functions/properties between your flags classes or if you want to
customize some special class attributes (like `__no_flags_name__`_ and `__all_flags_name__`_) for multiple flags
classes in one base class.

.. code-block:: python

    >>> # defining a project-wide customized flags base class
    >>> class BaseFlags(Flags):
    >>>     # setting the project-wide pickle serialization mode
    >>>     __pickle_int_flags__ = True
    >>>
    >>>     # changing the default 'no_flags' to 'none'
    >>>     __no_flags_name__ = 'none'
    >>>
    >>>     # changing the default 'all_flags' to 'all'
    >>>     __all_flags_name__ = 'all'
    >>>
    >>>     @property
    >>>     def helper_property_shared_by_subclasses(self):
    >>>         ...


Subclassing with the function call syntax
-----------------------------------------

To create a subclass of an existing (non-final) flags class you can also call it. In this case the flags class
provides the following signature:

**FlagsClass**\ *(class_name, flags, \*, mixins=(), module=None, qualname=None, no_flags_name=flags.UNDEFINED, all_flags_name=flags.UNDEFINED)*

The return value of this function call is the newly created subclass.

The format of the ``flags`` parameter can be one of the following:

- A space and/or comma separated list of flag names. E.g.: ``'flag0 flag1 flag2'`` or ``'flag0, flag1, flag2'``
- An iterable of flag names. E.g.: ``['flag0', 'flag1']``
- An iterable of ``(name, value)`` pairs where value defines the bits and/or the data for this flag as described in
  the `Possible ways to define flag values`_ section.
- A mapping (e.g.: ``dict``) where the keys are flag names and the values define the bits and/or data for the flags
  as described in the `Possible ways to define flag values`_ section.

The ``module`` and ``qualname`` parameters have to be specified only if you want to use the the created flags class
with pickle. In this case ``module`` and ``qualname`` should point to a place from where pickle can import the
created flags class. For flags classes that reside at module level it's enough to define only ``module`` and
``class_name`` for pickle support. ``qualname`` is optional and works only with python 3.4+ with pickle protocol 4.


.. code-block::

    >>> class MyBaseFlags(Flags):
    ...     __no_flags_name__ = 'none'
    ...     __all_flags_name__ = 'all'
    ...
    >>> FlagsClass1 = Flags('FlagsClass1', 'flag0 flag1')
    >>> FlagsClass2 = MyBaseFlags('FlagsClass2', ['flag0', 'flag1'])
    >>> FlagsClass3 = Flags('FlagsClass3', '', no_flags_name='zero', all_flags_name='all')
    >>> FlagsClass4 = FlagsClass3('FlagsClass4', dict(flag4=4, flag8=8))


Supported operations
====================

Instance methods and properties
-------------------------------

*property* Flags.\ **properties**

    If this instance has the same bits as one of the flags you have defined in the flags class then this property
    is an object with some extra info for that flag member definition otherwise ``None``. Note that if you are using
    flag aliases then all aliases share the same properties object.

    The returned object has the following readonly attributes:

    ``name``

        The name of the flag.

    ``bits``

        The integer value associated with this flag.

    ``data``

        The user defined application-specific data for this flag. The value of this is ``flags.UNDEFINED`` if you
        haven't defined any user-data for this flag.

    ``index``

        The zero based index of this flag in the flags class.

    ``index_without_aliases``

        The zero based index of this flag in the flags class excluding the aliases.

*property* Flags.\ **name**

    Returns ``None`` if the ``properties`` property is ``None`` otherwise returns ``properties.name``.

*property* Flags.\ **data**

    Returns ``flags.UNDEFINED`` if the ``properties`` property is ``None`` otherwise returns ``properties.data``.

.. _`Flags.to_simple_str()`:

Flags.\ **to_simple_str**\ *()*

    While ``Flags.__str__()`` returns a long string representation that always contains the flags class name
    (e.g.: ``'TextStyle()'``, ``'TextStyle.bold'`` or ``'TextStyle(bold|italic)'``) this method returns a simplified
    string without the classname. This simple string is an empty string for the zero flag or the ``'|'`` concatenated
    list of flag names otherwise. Examples: ``''``,  ``'bold'``, ``'bold|italic'``

Flags.\ **__iter__**\ *()* and Flags.\ **__len__**\ *()*

    Iterating over a flags class instance yields all flags class members that are part of this flag instance.
    Flag aliases are excluded from the yielded items.
    A flags class member is part of this flag instance if the ``flags_class_member in flags_instance`` expression is
    ``True``. ``len(flags_instance)`` returns the number of items returned by iteration.

    .. code-block:: python

        >>> from flags import Flags
        >>>
        >>> class Example(Flags):
        ...     flag_1 = 1
        ...     flag_2 = 2
        ...     # Note: flag_3 is the combination of flag_1 and flag_2
        ...     flag_3 = 3
        ...     flag_4 = 4
        ...     # Alias for flag_4
        ...     flag_4_alias = 4
        ...
        >>> list(iter(Example.no_flags))
        []
        >>> len(Example.no_flags)
        0

        >>> list(Example.all_flags)
        [<Example.flag_1 bits=0x0001 data=UNDEFINED>, <Example.flag_2 bits=0x0002 data=UNDEFINED>,
         <Example.flag_3 bits=0x0003 data=UNDEFINED>, <Example.flag_4 bits=0x0004 data=UNDEFINED>]
        >>> len(Example.all_flags)
        4

        >>> list(Example.flag_1)
        [<Example.flag_1 bits=0x0001 data=UNDEFINED>]
        >>> len(Example.flag_1)
        1

        >>> list(Example.flag_2)
        [<Example.flag_2 bits=0x0002 data=UNDEFINED>]
        >>> len(Example.flag_2)
        1

        >>> list(Example.flag_3)
        [<Example.flag_1 bits=0x0001 data=UNDEFINED>, <Example.flag_2 bits=0x0002 data=UNDEFINED>,
         <Example.flag_3 bits=0x0003 data=UNDEFINED>]
        >>> len(Example.flag_3)
        3

        >>> list(Example.flag_4)
        [<Example.flag_4 bits=0x0004 data=UNDEFINED>]
        >>> len(Example.flag_4)
        1

        >>> list(Example.flag_4_alias)
        [<Example.flag_4 bits=0x0004 data=UNDEFINED>]
        >>> len(Example.flag_4_alias)
        1

        >>> list(Example.flag_1 | Example.flag_4)
        [<Example.flag_1 bits=0x0001 data=UNDEFINED>, <Example.flag_4 bits=0x0004 data=UNDEFINED>]
        >>> len(Example.flag_1 | Example.flag_4)
        2


    .. note::

        Under the hood ``__len__()`` uses iteration to count the number of contained flag members.


Flags.\ **__hash__**\ *()*

    Flags class instances are immutable and hashable. You can use the builtin ``hash()`` function to hash them and
    you can use them as set members and mapping keys.


Flags.\ **__eq__**\ *()*, Flags.\ **__ne__**\ *()*, Flags.\ **__ge__**\ *()*, Flags.\ **__gt__**\ *()*,
Flags.\ **__le__**\ *()*, Flags.\ **__lt__**\ *()*

    Comparison operators on flag instances work similarly as in case of native python ``set``\ s.
    Two flag instances are equal only if their bits are the same. A flags instance is less than or equal to another
    flags instance only if its bits are a subset of the bits of the other one. The first flags instance is less than
    the second one if its bits are a **proper/strict** subset (is subset, but not equal) of the bits of the other one.

Flags.\ **__int__**\ *()*

    A flags instance can be converted to an ``int`` using the ``int(flags_instance)`` expression. This conversion
    returns the bits of the flags instance.

Flags.\ **__bool__**\ *()*

    A flags instance can be converted to a ``bool`` value using the ``bool(flags_instance)`` expression. The result
    is ``False`` only if the instance is the zero flag.

Flags.\ **__contains__**\ *()*

    A flags instance is contained by another instance if the bits of the first one is a subset of the second one.
    The ``flags_instance1 in flags_instance2`` expression has the same value as the
    ``flags_instance1 <= flags_instance2`` expression.

Flags.\ **is_disjoint**\ *(\*flags_instances)*

    The return value is ``True`` only if the flags instance on which we called ``is_dijoint()`` has no common bit
    with any of the flags instances passed as a parameters.

Flags.\ **__or__**\ *()*, Flags.\ **__xor__**\ *()*, Flags.\ **__and__**\ *()*

    Bitwise bool operators (``|``, ``^``, ``&``) combine the bits of two flags instances and return a new immutable
    flags instance that wraps the combined bits.

Flags.\ **__invert__**\ *()*

    Applying the unary ``~`` operator returns a new immutable flags instance that contains the inverted bits of the
    original flags instance. Note that inversion affects only those bits that are included in the ``__all_flags__``
    of this flag type.

Flags.\ **__sub__**\ *()*

    Subtracting flags instances is similar to subtracting native python ``set`` instances. The result of
    ``flags1 - flags2`` is a new flags instance that contains all bits that are set in ``flags1`` but aren't set
    in ``flags2``. We could also say that ``flags1 - flags2`` is the same as ``flags1 & ~flags2``.


Class methods
-------------

*classmethod* Flags.\ **__iter__**\ *()* and Flags.\ **__len__**\ *()*

    Iterating a flags class yields all non-alias flags you've declared for the class.
    ``len(flags_class)`` returns the number of non-alias flags declared for the class.

*classmethod* Flags.\ **__getitem__**\ *()*

    You can access the members of a flags class not only as class attributes (``FlagsClass.flag``) but also
    with the subscript notation (``FlagsClass['flag']``).

*classmethod* Flags.\ **from_simple_str**\ *(s)*

    Converts the output of `Flags.to_simple_str()`_ into a flags instance.

*classmethod* Flags.\ **from_str**\ *(s)*

    Converts the output of `Flags.to_simple_str()`_ or ``Flags.__str__()`` into a flags instance.

*classmethod* Flags.\ **bits_from_simple_str**\ *(s)*

    Converts the output of `Flags.to_simple_str()`_ into an integer (bits).

*classmethod* Flags.\ **bits_from_str**\ *(s)*

    Converts the output of `Flags.to_simple_str()`_ or ``Flags.__str__()`` into an integer (bits).


The ``@unique`` and ``@unique_bits`` decorators
===============================================

You can apply the ``@unique`` and ``@unique_bits`` operators only to "final" flags classes that have flag members
defined. Trying to apply them onto base classes without any flag members results in error.

``@unique`` forbids the declaration of aliases. In fact, originally I wanted to call this decorator ``@no_aliases``
but decided to use ``@unique`` to follow the conventions used by the standard ``enum`` module.
A flags class with this decorator can not have two flags defined with the exact same bits (but a few overlapping
bits are still allowed).

``@unique_bits`` ensures that there isn't a single bit that is shared by any two members of the flags class.
Note that ``@unique_bits`` is a much stricter requirement than ``@unique`` and applying ``@unique`` along with this
decorator is unnecessary and redundant (but not harmful or forbidden).


Serialization
=============


Pickle
------

Flags class instances are pickle serializable. In case of python 3.3 and lower the picklable flags class has to
be declared at module level in order to make it importable for pickle. From python 3.4 pickle protocol 4 can
deal with ``__qualname__`` so can declare serializable flags classes at a deeper scope.

Note that the pickle support by default saves the flags class (name) along with the output of `Flags.to_simple_str()`_
to the pickled stream. To save the bits of instances (an integer) instead of the `Flags.to_simple_str()`_ output
set the `__pickle_int_flags__`_ class attribute to ``True``.


Custom serialization
--------------------

If you want to roll your own serializer instead of using pickle then it is recommended to use the same
strategy as pickle - your serializer should remember:

1. the flags class
2. the ``int`` or ``string`` representation of the flags class instances

You can retrieve the ``int`` representation of a flags instance with ``int(flags_instance)`` while the recommended
string representation for serialization can be acquired using `Flags.to_simple_str()`_. ``str(flags_instance)``
would also work but it is unnecessarily verbose compared to the ``to_simple_str()`` output.

You can convert the integer and string representations back to flags instances by calling the flags class itself
with the given integer or string as a single argument. E.g.: ``flags_instance = flags_class(int_representation)``


Implementation details
======================


Introspection
-------------


Flags classes have some special attributes that may come in handy for introspection.

``__all_members__``

    This is a readonly ordered dictionary that contains all members including the aliases and also the special
    ``no_flags`` and ``all_flags`` members. The dictionary keys store member names and the values are flags class
    instances.

    .. note::

        If you customize the names of special members through the ``__no_flag_name__`` and ``__all_flag_name__``
        class attributes then this dictionary contains the customized names.

``__members__``

    Same as ``__all_members__`` but this doesn't contain the special ``no_flags`` and ``all_flags`` members.
    This dictionary contains only the members including the aliases.

``__members_without_aliases__``

    Same as ``__members__`` but without the aliases. This doesn't contain the special ``no_flags`` and ``all_flags``
    or any aliases.

``__member_aliases__``

    An ordered dictionary in which each key is the name of an alias and the associated value is the name of the
    aliased member.

``__no_flags__``

    An instance of the flags class: the zero flag.

``__all_flags__``

    The bitwise or combination of all members that have been declared in this class.

.. _`__no_flags_name__`:

``__no_flags_name__``

    A string that specifies the name of an alias for the ``__no_flags__`` class attribute.
    By default the value of ``__no_flags_name__`` is ``'no_flags'`` which means that the zero flag can be accessed
    not only through the ``__no_flags__`` class attribute but also as ``no_flags``.

    The interesting thing about ``__no_flags_name__`` is that it can be customized during flags class declaration
    so the name of this alias can be used to give the zero flag a name that is
    specific to a flags class (e.g.: ``'Unknown'``). A project can also use this name to customize the name of the
    zero flag in a project specific flags base class to match the flags class member naming convention of the project
    (if the default ``'no_flags'`` isn't good). By setting ``__no_flags_name__`` to ``None`` we can prevent the
    creation of an alias for ``__no_flags__``.

.. _`__all_flags_name__`:

``__all_flags_name__``

    A string that specifies the name of an alias for ``__all_flags__``. Works in a similar way as ``__no_flags_name__``.

.. _`__pickle_int_flags__`:

``__pickle_int_flags__``

    By default the pickle serializer support saves the names of flags. By setting ``__pickle_int_flags__`` to ``True``
    you can ask the pickle support to save the ``int`` value of serialized flags instead of the names.

``__dotted_single_flag_str__``

    By default ``__str__()`` handles flag instances with only a single flag set specially. For the zero flag it
    outputs ``'FlagsClass()'``, for a single flag it outputs ``'FlagsClass.flag1'`` and for multiple flags it's
    ``'FlagsClass(flag1|flag2)'``. If you set ``__dotted_single_flag_str__`` to ``False`` then the output for
    a single flag changes to ``'FlagsClass(flag1)'``. This matches the format of the output for zero and
    multiple flags.


Efficiency
----------

A flag object has only a single instance attribute that stores an integer (flags).
The storage of this instance attribute is optimized using ``__slots__``. Your flags classes aren't allowed to add
or use instance variables and you can not define ``__slots__``. Trying to do so results in error.
