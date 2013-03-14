# -*- coding: utf-8 -*-
from __future__ import absolute_import
from cloudapp import public

@public
def Blueprint(name, **kwargs):
    from flask import Blueprint
    from werkzeug.exceptions import default_exceptions
    from cloudapp.authentication.decorators import load_user
    error_if_exists = kwargs.pop('subdomain', None)
    if error_if_exists:
       raise RuntimeError("[api] Blueprint: subdomain is not an allowed keyword")
    bp = Blueprint(name, __name__, subdomain="api", **kwargs)
    bp.before_request(load_user)
    for code in default_exceptions.iterkeys():
        if code >= 500: continue
        @bp.errorhandler(code)
        def errorhandler(code):
            return _json_errorhandler(code)
    return bp

def _json_errorhandler(ex):
    from flask import jsonify
    from werkzeug.exceptions import HTTPException
    response = jsonify( meta = { 'error_message': str(ex), 'code': ex.code })
    response.status_code = (ex.code
                            if isinstance(ex, HTTPException)
                            else 500)
    return response


@public
class Envelope:
    def __init__(self, code=200):
        self.payload = { }
        self.payload['meta'] = { 'code': code }
        self.payload['data'] = [ ]
        self.payload['pagination'] = { }

    def add_meta(self,key,value):
        self.payload['meta'][key] = value

    def add_data(self,value):
        self.payload['data'].append(value)

    def send(self):
        from flask import jsonify
        if 'data' in self.payload:
           if len(self.payload['data']) == 0:
              del(self.payload['data'])
        if 'pagination' in self.payload:
           if len(self.payload['pagination'].keys()) == 0:
              del(self.payload['pagination'])
        return jsonify(self.payload)

