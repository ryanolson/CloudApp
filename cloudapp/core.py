# -*- coding: utf-8 -*-
"""
 http://stackoverflow.com/questions/7974771/flask-blueprint-template-folder
"""
import os
tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')

from cloudapp import public
from datetime import timedelta

from flask import Flask, g

EXTENSION_NAME = 'QCWebApp'

@public
class Application(object):

    def __init__(self, user, app=None, documents=[], **kwargs):
        self.app   = app
        self.user  = user
        self.documents = documents
        self.couch = None
        if app is not None:
           self.init_app(app)

    def init_app(self, app):
        if not hasattr(app, 'extensions'):
           app.extensions = dict()
        webapp = app.extensions.get(EXTENSION_NAME, None)
        if webapp is not None:
           raise RuntimeError('Multiple Flask-WebApplications loaded')
        
        app.before_request(self._before_request)

        self._init_couch(app)
        self._init_cache(app)
        self._init_principal(app)
        self._init_blueprints(app)

        app.extensions[EXTENSION_NAME] = self

        # create default admins
        with app.app_context():
             if self.user.load("rmolson@gmail.com",db=self.couch.db) is None:
                self.user(email="rmolson@gmail.com",password="test1234",roles=['Admin']).store(self.couch.db)

    @classmethod
    def flask(cls, name, config=None, debug=False, **kwargs):
        template_folder = kwargs.pop('template_folder', tmpl_dir)
        app = Flask(name, template_folder=template_folder, **kwargs)
        if config:
           app.config.from_object(config)
        app.permanent_session_lifetime = timedelta(minutes=60)
        app.debug = debug

        if app.config.get('COUCHDB_DATABASE',None) is None:
           app.config['COUCHDB_DATABASE'] = name.lower()

        assert app.secret_key is not None, "flask config does not specify a secret key"
        return app

    def _init_couch(self, app):
        from flask.ext.couchdb import CouchDBManager
        couch = CouchDBManager(app,auto_sync=False)
        couch.add_document(self.user)
        for doc in self.documents:
            couch.add_document(doc)
        self.couch = couch

    def _init_cache(self,app):
        cache = None
        prefix=app.name.lower()

        try:
           from werkzeug.contrib.cache import RedisCache
           cache = RedisCache(key_prefix=prefix)
        except:
           RuntimeWarning("RedisCache not available")

#       try:
#          from werkzeug.contrib.cache import MemcachedCache
#          cache = MemcachedCache(app.config['MEMCACHED_SERVERS'], key_prefix=prefix)
#       except:
#          RuntimeWarning("Memcached not available")

        if cache is not None:
           cache.clear()
        app.cache = cache
        self.cache = cache

    def _init_principal(self, app):
        from cloudapp.identity import on_load_identity
        from flask.ext.principal import Principal, identity_loaded
        principal = Principal(app)
        identity_loaded.connect(on_load_identity)
        self.principal = principal

    def _init_blueprints(self, app):
        from cloudapp.authentication import authAPI
        from cloudapp.authentication import authWWW
        app.register_blueprint(authAPI)
        app.register_blueprint(authWWW)

    def _before_request(self):
        g.User = self.user

#   def setupFlaskAdmin(self):
#       from flask.ext.admin import Admin
#       admin = Admin(self.app, name=self.name)
#       from cloudapp.users.admin.views import Users
#       admin.add_view(Users(name='Users'))
#       if self.app.debug:
#          from cloudapp.views.test import Test
#          admin.add_view(Test())
#       self.admin = admin


#   def register_blueprints(self):
#       if self.app.debug:
#          from cloudapp.api.test_endpoints import api as testAPI
#          self.app.register_blueprint(testAPI)
#          from cloudapp.views.test import www as testWWW
#          self.app.register_blueprint(testWWW)
#       from cloudapp.authentication.t import Authentication
#       self.auth = Authentication(self.user, app=self.app, url_prefix='/oauth')
#       from cloudapp.authentication.endpoints import api as authAPI
#       self.app.register_blueprint(authAPI, url_prefix='/oauth')


@public
def Blueprint(name, **kwargs):
    error_if_exists = kwargs.pop('template_folder', None)
    if error_if_exists:
       raise RuntimeError("[error] QCBlueprint: template_folder is not an allowed keyword")
    from flask import Blueprint
    return Blueprint(name, __name__, template_folder='templates', **kwargs)

