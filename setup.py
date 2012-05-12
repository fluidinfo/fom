# -*- coding: utf-8 -*-
#!/usr/bin/env python

from setuptools import setup
from fom.version import version

setup(
    name='Fom',
    version=version,
    description='FluidDB API and Object Mapper',
    author='Ali Afshar',
    author_email='aafshar@gmail.com',
    url='http://packages.python.org/Fom/',
    packages=['fom'],
    scripts=['bin/fdbc'],
    install_requires=['requests', 'blinker'],
)

