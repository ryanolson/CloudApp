# -*- coding: utf-8 -*-
"""
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
from functools import wraps
from flask import g, session, Response, json, request, current_app, abort
from flask.ext.principal import Identity, identity_changed, UserNeed

from .models import validate_token

def load_user():
    """
     if an identity exists in the session, then on_load_identity will have been
     executed prior to this call.  

     otherwise, we do not have a validated session.  we need to check for a valid
     api key.  if the client passed a X-Auth-Token, validate it, then trigger an 
     identity changed signal if the token was valid.

     we do not check username/passwords here; only api key.  the client applicaiton 
     should request a token by a GET to /auth/token with the basic HTTP client 
     authentication header set.
    """
    if hasattr(g.identity, 'user') and g.identity.user is not None:
       return
    token = dict(request.headers).get("X-Auth-Token", None)
    if token and validate_token(token):
       identity_changed.send(current_app._get_current_object(), identity=Identity(token, auth_type='api-key'))
       if hasattr(g.identity, 'user') and g.identity.user is not None:
          session.permanent = True
          return

def _check_authentication(username, password):
    """ This function is called to check if a username password combination is valid. """
    user = g.User.load(username)
    if user:
       return user.challenge_password(password)
    return False

def _send_authentication_challenge():
    """ Sends a 401 response that enables basic auth """
    return Response( json.dumps({'meta': {'code': 401, 'error_message': 'Invalid User Credentials' }}),
        401, {'WWW-Authenticate': 'Basic realm="Login Required"'}, mimetype='application/json')

def requires_login(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not _check_authentication(auth.username, auth.password):
           return _send_authentication_challenge()
        return f(*args,**kwargs)
    return decorated

