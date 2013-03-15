"""
CloudApp
~~~~~~~~

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
    ]
)
