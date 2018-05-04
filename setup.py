# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='sniffer',
    version='0.0.1',
    description="",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'sniffer = sniffer.__main__:main',
        ],
    }
)
