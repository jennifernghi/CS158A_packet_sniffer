# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from setuptools.command.build_py import build_py


class BuildPyCommand(build_py):
    @staticmethod
    def build_frontend():
        from subprocess import call
        call(["./build_frontend.sh"])

    def run(self):
        self.execute(BuildPyCommand.build_frontend, (), msg="Building Frontend...")
        print("ayyyyyyyyyyyyyyyyyyyyyyyy")
        super(BuildPyCommand, self).run()


setup(
    name='sniffer',
    version='0.0.1',
    description="",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'sniffer = sniffer.__main__:main',
        ],
    },
    cmdclass={
        'build_py': BuildPyCommand
    },
    include_package_data=True
)
