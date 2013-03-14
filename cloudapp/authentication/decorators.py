# -*- coding: utf-8 -*-
from functools import wraps
from flask import g, session, Response, json, request, current_app, abort
from flask.ext.couchdb import to_dict
from flask.ext.principal import Identity, identity_changed, UserNeed

from .models import validate_token

def load_user():
    """
     if an identity exists in the session, then on_load_identity will have been
     executed prior to this call.  in this case, we simply need to load g.user
     from g.identity.user

     otherwise, we do not have a validated session.  we need to check for a valid
     api token / user session.  if the client passed a X-Auth-Token, validate it,
     then trigger an identity changed signal if the token was valid.

     we do not check username/passwords here; only api / session tokens.  the client
     applicaiton should request a token by a GET to /auth/token with the basic HTTP
     client authentication header set.
    """
    g.user = None
    if 'user' in vars(g.identity):
       g.user = g.identity.user
       return
    token = dict(request.headers).get("X-Auth-Token", None)
    if token and validate_token(token):
       identity_changed.send(current_app._get_current_object(), identity=Identity(token, auth_type='token'))
       if 'user' in vars(g.identity):
          g.user = g.identity.user
          session.permanent = True
          return

def check_authentication(username, password):
    """ This function is called to check if a username password combination is valid. """
    g.user = g.User.load(username)
    if g.user:
       return g.user.challenge_password(password)
    return False

def _send_authentication_challenge():
    """ Sends a 401 response that enables basic auth """
    return Response( json.dumps({'meta': {'code': 401, 'error_message': 'Invalid User Credentials' }}),
        401, {'WWW-Authenticate': 'Basic realm="Login Required"'}, mimetype='application/json')

def requires_login(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_authentication(auth.username, auth.password):
           return _send_authentication_challenge()
        return f(*args,**kwargs)
    return decorated

