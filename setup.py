#!/usr/bin/env python
from setuptools import setup, find_packages
import os

version = "1.1" + '.' + os.environ.get('BUILD_NUMBER', '0')

def load_requirements(filename):
    with open(filename) as f_obj:
        return list(filter(lambda line: line and not line.startswith('#'), map(lambda line: line.strip(), f_obj)))

install_requires = load_requirements('requirements.txt')
tests_requires = load_requirements('test_requirements.txt')


setup(
    name='granular-configuration',
    version=version,
    description='Granular Configuration library for Runtime-Loaded YAML Configurations',
    author='Granular GLaDOS',
    author_email='team_glados@granular.ag',
    url='https://gitlab.encirca.auto.pioneer.com/granular-lite/granular-configuration',
    packages=find_packages(exclude=['tests*']),
    package_data={},
    install_requires=install_requires#,
    #setup_requires=['pytest-runner'],
    #tests_require=tests_requires
)
