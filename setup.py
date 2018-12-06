#!/usr/bin/env python3
from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))
version = '1.4.11'

long_des = ""
with open(path.join(here, 'README.md')) as f:
    long_des = f.read()

setup(
    name='MeleeUploader',
    description="A YouTube Uploader with Super Smash Bros. Melee in mind",
    long_description=long_des,
    long_description_content_type="text/markdown",
    url="https://github.com/NikhilNarayana/Melee-YouTube-Uploader",
    author="Nikhil Narayana",
    author_email="nikhil.narayana@live.com",
    license="GNU Public License v3.0",
    keywords='smash melee youtube uploader',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python :: 3.6',
        'Operating System :: OS Independent',
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: English",
    ],
    entry_points=dict(console_scripts=['meleeuploader = meleeuploader.main:main']),
    python_requires='~=3.5',
    version=version,
    packages=["meleeuploader"],
    install_requires=[
        'CacheControl',
        'google-api-python-client',
        'oauth2client',
        'Pyforms-Lite',
    ],
    data_files=[("share/meleeuploader", ['meleeuploader/client_secrets.json'])],
    package_data={'meleeuploader': ['meleeuploader/client_secrets.json']},
)
