# -*- coding: utf-8 -*-
import codecs
import os
import re

from setuptools import setup


script_dir = os.path.dirname(os.path.abspath(__file__))


def read_text_file(path):
    with codecs.open(path, 'r', 'utf-8') as f:
        return f.read()


def find_version(*path):
    contents = read_text_file(os.path.join(script_dir, *path))

    # The version line must have the form
    # version_info = (X, Y, Z)
    m = re.search(
        r'^version_info\s*=\s*\(\s*(?P<v0>\d+)\s*,\s*(?P<v1>\d+)\s*,\s*(?P<v2>\d+)\s*\)\s*$',
        contents,
        re.MULTILINE,
    )
    if m:
        return '%s.%s.%s' % (m.group('v0'), m.group('v1'), m.group('v2'))
    raise RuntimeError('Unable to determine package version.')


setup(
    name='py-flags',
    version=find_version('src', 'flags.py'),
    description='Type-safe (bit)flags for python 3',
    long_description=read_text_file(os.path.join(script_dir, 'README.rst')),
    keywords='flags bit flag set bitfield bool arithmetic',

    url='https://github.com/pasztorpisti/py-flags',

    author='István Pásztor',
    author_email='pasztorpisti@gmail.com',

    license='MIT',

    classifiers=[
        'License :: OSI Approved :: MIT License',

        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],

    install_requires=['dictionaries==0.0.1'],
    py_modules=['flags'],
    package_dir={'': 'src'},

    test_suite='tests',
)
