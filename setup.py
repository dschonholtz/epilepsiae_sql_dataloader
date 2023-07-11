#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = ['Click>=7.0', ]

test_requirements = ['pytest>=3', ]

setup(
    author="Douglas Schonholtz",
    author_email='schonholtz.d@northeastern.edu',
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="This leverages the https://epilepsiae.uniklinik-freiburg.de/ epilepsy dataset to allow you to arbitrarily query data for an ML dataloader. You must have the raw binary data to configure a SQL DB or a preconfigured DB that you can reference for the dataloader.",
    entry_points={
        'console_scripts': [
            'epilepsiae_sql_dataloader=epilepsiae_sql_dataloader.cli:main',
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='epilepsiae_sql_dataloader',
    name='epilepsiae_sql_dataloader',
    packages=find_packages(include=['epilepsiae_sql_dataloader', 'epilepsiae_sql_dataloader.*']),
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/dschonholtz/epilepsiae_sql_dataloader',
    version='0.1.0',
    zip_safe=False,
)
