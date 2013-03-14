
CloudApp is a Flask-based package for creating cloud-based webapps which serve
traditional HTML5-based frontend pages and a set of JSON-based API endpoints 
useful for developing native iOS, Android, etc. apps.

CloudApp provides an extendable user authentication and management (in-progress)
system.  Users will be able to login via an app specific cloud account or via
Facebook Authentication (in-progress), or eventually via Open-ID (in-planning).

CloudApp leverages the html5-boilerplate with Twitter's bootstrap for its
default layout.  Also included are bootstrap-based date and time pickers.

Requirements:

- Python
  * Flask
  * Flask-CouchDB (ryanolson/Flask-CouchDB)
  * Flask-Principal
  * Flask-WTForms
  * python-couchdb (ryanolson/python-couchdb)
  * schematics
- CouchDB
- Redis [optional - used for caching - preferred]
  * w/ Python redis package
- Memcached [optional - used for caching]
  * w/ python-memcached package


Quickstart

Install the System Level Packages
Example below is for development on an OS X system with Homebrew installed

virtualenv
sudo easy_install virtualenv

CouchDB
brew install couchdb

Redis
brew install redis

virtualenv CloudAppEnv
[tcsh] source CloudAppEnv/bin/activate.csh
[bash] . CloudAppEnv/bin/activate

git clone git@github.com:ryanolson/CloudApp.git
cd CloudApp
python setup.py develop 
-or-
python setup.py install [if you are not going to make changes]

Run tests
python tests/__init__.py
