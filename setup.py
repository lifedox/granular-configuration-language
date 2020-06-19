#!/usr/bin/env python
from pipenv.project import Project
from pipenv.utils import convert_deps_to_pip
from setuptools import find_packages, setup
import os

version = "1.8.1" + '.' + os.environ.get('BUILD_NUMBER', '0')

pfile = Project(chdir=False).parsed_pipfile


setup(
    name='granular-configuration',
    version=version,
    description='Granular Configuration library for Runtime-Loaded YAML Configurations',
    author='Granular GLaDOS',
    author_email='team_glados@granular.ag',
    url='https://gitlab.encirca.auto.pioneer.com/shared-services/granular-configuration',
    packages=find_packages(exclude=['tests*']),
    package_data={"granular_configuration": ["py.typed", "*.pyi"]},
    install_requires=convert_deps_to_pip(pfile["packages"], r=False),
    tests_require=convert_deps_to_pip(pfile["dev-packages"], r=False),
    python_requires=">=3.6"
)
