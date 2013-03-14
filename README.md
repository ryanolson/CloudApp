
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



