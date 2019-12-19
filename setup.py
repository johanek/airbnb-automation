# -*- coding: utf-8 -*-
#pylint: skip-file

from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='airbnb-automation',
    version='0.0.1',
    description='airbnb automation',
    long_description=readme,
    author='Johan van den Dorpe',
    author_email='johan@johan.org.uk',
    url='https://github.com/johanek/airbnb-automation.git',
    license=license,
    packages=find_packages(exclude=('tests', 'docs')),
    scripts=[
        'bin/airbnb_automation',
        'bin/nello_webhook',
        'bin/nello_webhook_listener',
    ],
    install_requires=[
        'voluptuous',
        'icalevents',
        'pyyaml',
        'google-api-python-client',
        'google-auth-httplib2',
        'google-auth-oauthlib',
        'twilio',
        'babel',
        'pynello @ git+https://github.com/johanek/pynello@master#egg=pynello',
        'icalendar',
        'flask',
        'airbnb @ git+https://github.com/johanel/airbnb-python@master#egg=airbnb',
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
