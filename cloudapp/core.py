# -*- coding: utf-8 -*-
"""
 http://stackoverflow.com/questions/7974771/flask-blueprint-template-folder
"""
import os
tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')

from cloudapp import public
from datetime import timedelta

from flask import Flask, Blueprint, g
from flask.ext.bootstrap import Bootstrap

EXTENSION_NAME = 'cloudapp'

@public
class Application(object):

    def __init__(self, user, app=None, documents=[], users=[], **kwargs):
        self.app   = app
        self.user  = user
        self.documents = documents
        self.couch = None
        self.default_users = users
        if app is not None:
           self.init_app(app)

    def init_app(self, app):
        if not hasattr(app, 'extensions'):
           app.extensions = dict()
        cloudapp = app.extensions.get(EXTENSION_NAME, None)
        if cloudapp is not None:
           raise RuntimeError('Multiple Flask-WebApplications loaded')
      

        app.before_request(self._before_request)

        self._init_couch(app)
        self._init_cache(app)
        self._init_principal(app)
        self._init_blueprints(app)
        self._init_users(app)

        app.extensions[EXTENSION_NAME] = self

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
        Bootstrap(app)
        auth = Blueprint('cloudapp',
                          __name__,
                          template_folder='templates',
                          static_folder='static',
                          url_prefix='/cloudapp')
        from .authentication.views import login as alogin, logout as alogout
        @auth.route('/login', methods=['POST','GET'])
        def login():
            return alogin()
        @auth.route('/logout')
        def logout():
            return alogout()
        app.register_blueprint(auth)
        from cloudapp.authentication import authAPI
        app.register_blueprint(authAPI)

    def _init_users(self, app):
        with app.app_context():
           for user in self.default_users:
             if self.user.load(user[0],db=self.couch.db) is None:
                self.user(email=user[0],password=user[1],roles=user[2]).store(self.couch.db)

    def _before_request(self):
        g.User = self.user

