#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

requirements = ["pyfrc", "wpilib"]

setup(
    author="Noskcaj19",
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    description="Utilities for",
    install_requires=requirements,
    license="License :: OSI Approved :: MIT License",
    include_package_data=True,
    name='marsutils',
    packages=find_packages(include=['marsutils']),
    url='https://github.com/Mars1523/Mars-Utils',
    version='0.1.0',
)