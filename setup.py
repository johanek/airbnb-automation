# -*- coding: utf-8 -*-
#pylint: skip-file

from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='airbnb-automation',
    version='0.0.3',
    description='airbnb automation',
    long_description=readme,
    author='Johan van den Dorpe',
    author_email='johan@johan.org.uk',
    url='https://github.com/johanek/airbnb-automation.git',
    license=license,
    packages=find_packages(exclude=('tests', 'docs')),
    scripts=[
        'bin/calendar_sync',
        'bin/daily_reminders',
        'bin/nuki_status',
        'bin/nuki_entry_logs',
    ],
    install_requires=[
        'voluptuous',
        'icalevents',
        'pyyaml',
        'google-api-python-client',
        'google-auth-httplib2',
        'google-auth-oauthlib',
        'babel',
        'icalendar',
        'flask',
        'airbnb @ git+https://github.com/johanek/airbnb-python@master#egg=airbnb',
        'pynuki',
    ],
    setup_requires=[
        'pytest-runner',
        'pytest-flakes',
    ],
    tests_require=[
        'pytest',
        'pyflakes',
        'pytest-mock'
    ],
)
