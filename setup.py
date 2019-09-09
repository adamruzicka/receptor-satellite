#!/usr/bin/env python

# Copyright (c) 2018 Red Hat, Inc.
# All Rights Reserved.

from setuptools import setup, find_packages

with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name="receptor-http",
    version="1.0.0",
    author='Red Hat Ansible',
    url="https://github.com/project-receptor/receptor-http",
    license='Apache',
    packages=find_packages(),
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=[
        'requests',
    ],
    zip_safe=False,
    entry_points={
        'receptor.worker': 'receptor_http = receptor_http.worker',
    },
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
)
