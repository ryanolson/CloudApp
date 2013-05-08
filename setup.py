"""
CloudApp
~~~~~~~~

Copyright 2013 Ryan Olson

This file is part of CloudApp.

CloudApp is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

CloudApp is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with CloudApp.  If not, see <http://www.gnu.org/licenses/>.

"""
from setuptools import setup, find_packages

setup(
    name='CloudApp',
    version='0.1dev',
    author='QuantumCoding',
    author_email='quantumcoding+cloudapp@gmail.com',
    packages=find_packages(exclude=["dependencies"]),
    zip_safe=False,
    platforms='any',
    install_requires=[
        'Flask',
        'Flask-Principal',
        'Flask-WTF',
        'Flask-Bootstrap>=2.0.0dev',
        'Flask-CouchDB>=2.0.0dev',
        'couchdb-python>=2.0.0dev',
        'schematics>=2.0.0dev',
        'python-memcached',
        'redis'
    ],
    dependency_links = [
        'http://github.com/ryanolson/schematics/tarball/master#egg=schematics-2.0.0dev',
        'http://github.com/ryanolson/couchdb-python/tarball/master#egg=couchdb-python-2.0.0dev',
        'http://github.com/ryanolson/flask-couchdb/tarball/master#egg=Flask-CouchDB-2.0.0dev'
        'http://github.com/ryanolson/flask-bootstrap/tarball/master#egg=Flask-Bootstrap-2.0.0dev'
    ]
)
