#!/usr/bin/env python

# Copyright (c) 2018 Red Hat, Inc.
# All Rights Reserved.

from setuptools import setup, find_packages

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="receptor-satellite",
    version="1.0.1",
    author="Red Hat Ansible",
    url="https://github.com/adamruzicka/receptor-satellite",
    license="Apache",
    packages=find_packages(),
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=["aiohttp"],
    zip_safe=False,
    entry_points={"receptor.worker": "receptor_satellite = receptor_satellite.worker"},
    classifiers=["Programming Language :: Python :: 3"],
    extras_require={"dev": ["pytest", "flake8", "pylint", "black"]},
)
