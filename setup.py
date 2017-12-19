#!/usr/bin/env python
try:
    from setuptools import setup
    HAVE_SETUPTOOLS = True
except ImportError:
    from distutils.core import setup
    HAVE_SETUPTOOLS = False


VERSION = '0.0.1'

setup_kwargs = {
    "version": VERSION,
    "description": 'Cyclus-as-a-Service',
    "license": 'BSD 3-clause',
    "author": 'The ERGS developers',
    "author_email": 'ergsonomic@googlegroups.com',
    "url": 'https://github.com/ergs/fixie',
    "download_url": "https://github.com/ergs/fixie/zipball/" + VERSION,
    "classifiers": [
        "License :: OSI Approved",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Topic :: Utilities",
        ],
    "zip_safe": False,
    "data_files": [("", ['LICENSE', 'README.rst']),],
    "scripts": ["scripts/fixie"],
    }


if __name__ == '__main__':
    setup(
        name='fixie',
        packages=['fixie'],
        long_description=open('README.rst').read(),
        **setup_kwargs
        )
