# -*- coding: utf-8 -*-
from copy import copy
from pprint import pprint
from flask import current_app, session, g
from flask.ext.principal import UserNeed, RoleNeed, AnonymousIdentity
from flask.ext.couchdb import to_dict

from cloudapp.permissions import valid_user
from cloudapp.authentication.models import Session

def _load_user(user_id, identity):
    user = g.User.load(user_id)
    if user:
       identity.user = user
       identity.provides.add(UserNeed('Valid'))
       identity.provides.add(UserNeed(user.id))
       for role in user.roles:
         identity.provides.add(RoleNeed(role))
    else:
       raise RuntimeError("user is None; user_id not found")

def _cache_identity(identity):
    if current_app.cache is None: return
    cached_identity = copy(identity)
    cached_identity.user = to_dict(identity.user)
    current_app.cache.set(identity.name, cached_identity, timeout=600)


def on_load_identity(sender, identity):
    """
     This function is called to load the user's identity from either
     data saved in the client's session or from a identity_changed.send
     signal/notificaiton. 

     This function should never be triggered unless we have passed
     a valid identity; however, we should do a quick double check here
     before loading the identity's allowed permissions / needs.

     In the future, we may want to avoid the user lookup and utilize
     memcache for the storage of the user's base information.
    """
    if current_app.cache is not None:
       stored_identity = current_app.cache.get(identity.name)
       if stored_identity is not None:
          identity.user = g.User.wrap(stored_identity.user)
          identity.provides = stored_identity.provides
          if current_app.testing: session['loaded_from']='memcached'
          return
    try:
       if identity.auth_type == 'web-token':
          _load_user(identity.name, identity)
          _cache_identity(identity)
       elif identity.auth_type == 'token':
          auth_session = Session.load(identity.name)
          if auth_session:
             _load_user(auth_session.user_id, identity)
             _cache_identity(identity)
             if not session.permanent: session.permanent=True
             if current_app.testing: session['loaded_from']='couchdb'
    except:
       g.identity = AnonymousIdentity()
       session.pop('identity.name',None)
       session.pop('identity.auth_type', None)
       session.modified = True
