# -*- coding: utf-8 -*-
from cloudapp import Application, BaseUser
from cloudapp.api import Blueprint as APIBlueprint, Envelope
from cloudapp.config import DebugConfig
from cloudapp.permissions import valid_user
from flask import Blueprint, request, redirect, render_template, g, url_for, json

# you need to create a www blueprint
www = Blueprint("www", __name__)
api = APIBlueprint("api")

# you need to create a User calls from BaseUser
class User(BaseUser):
    pass

# inherit cloudapp's debug config
class Config(DebugConfig):
    SERVER_NAME = 'example.dev:5000'
    SECRET_KEY  = 'generate-me'

#
# views
#

@www.route('/')
def index():
    try:
        with valid_user.require():
           return redirect( url_for('.profile') )
    except:
        pass
    return render_template('splash.html')

@www.route('/profile')
@valid_user.require(http_exception=403)
def profile():
    return render_template('profile.html', user=g.identity.user)

@www.route('/settings')
@valid_user.require(http_exception=403)
def settings():
    return render_template('settings/profile.html', user=g.identity.user)

@www.errorhandler(403)
def permission_denied(err_code):
    return redirect( url_for('cloudapp.login') )

@api.route('/echo', methods=['PUT','POST'])
def echo():
    # the api blueprint preprocesses request.data looking for a json.
    # if a valid json is put or posted, the results of json.loads can
    # be found in g.json, otherwise g.json = None
    from flask import g
    env = Envelope()
    if g.json:
       env.add_data(g.json)
    else:
       env.add_meta('code',400)
       env.add_meta('error_message',u'unable to process json')
    return env.send()

#
# application
#

"""
 http://stackoverflow.com/questions/7974771/flask-blueprint-template-folder
"""
import os
template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
def init_example(*args, **kwargs):
    flask_app = Application.flask("Example", Config, template_folder=template_folder)
    flask_app.debug = True
    example = Application(User, flask_app, **kwargs)
    flask_app.config['BOOTSTRAP_JQUERY_STATIC'] = True
    example.couch.setup(flask_app)
    example.couch.sync(flask_app)
    flask_app.register_blueprint(www)
    flask_app.register_blueprint(api)
    return example


if __name__ == '__main__':
   users = [ ('admin@example.com','admin1234',['Admin']),
             ('test1@example.com','test1234',[]) ]
   Example = init_example(users=users)
   Example.app.run(port=5000)
