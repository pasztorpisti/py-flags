========
py-flags
========

Type-safe (bit)flags
""""""""""""""""""""


.. image:: https://img.shields.io/travis/pasztorpisti/py-flags.svg?style=flat
    :target: https://travis-ci.org/pasztorpisti/py-flags
    :alt: build

.. image:: https://img.shields.io/codacy/0c56231fea3a49b48bc39d0803ec3c21/master.svg?style=flat
    :target: https://www.codacy.com/app/pasztorpisti/py-flags
    :alt: code quality

.. image:: https://landscape.io/github/pasztorpisti/py-flags/master/landscape.svg?style=flat
    :target: https://landscape.io/github/pasztorpisti/py-flags/master
    :alt: code health

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


.. contents::


Quick Intro
===========

With this module you can define type-safe (bit)flags. The style of the flag definition is very similar to the enum
definitions you can create using the standard ``enum`` module of python 3.


Defining flags with the ``class`` syntax:

.. code-block:: python

    >>> from flags import Flags

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
    <TextStyle.bold bits=0x0001 data=None>

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


From the above testing methods the attribute-style access can only check the presence of a single flag. With the
``&`` and ``in`` operators you can check the presence of multiple flags at the same time:

.. code-block:: python

    >>> bool((TextStyle.bold | TextStyle.italic) & TextStyle.all_flags)
    True
    >>> (TextStyle.bold | TextStyle.italic) in TextStyle.all_flags
    True


If for some reason you need the actual integer value of the flags then you can cast them to ``int``:

.. code-block:: python

    >>> int(TextStyle.bold)
    1


You can convert the ``int()`` and ``str()`` representations of flags back into flags instances:

.. code-block:: python

    >>> TextStyle(2)
    <TextStyle.italic bits=0x0002 data=None>
    >>> TextStyle('TextStyle.bold')
    <TextStyle.bold bits=0x0001 data=None>


Installation
============

.. code-block:: sh

    pip install py-flags

Alternatively you can download the distribution from the following places:

- https://pypi.python.org/pypi/py-flags#downloads
- https://github.com/pasztorpisti/py-flags/releases
