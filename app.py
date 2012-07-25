# -*- coding: utf-8 -*-
from auth import GithubAuth
from flaskext.seasurf import SeaSurf
from models import User, Hug
import os
from flask import Flask, g, render_template, request, abort
from flask_heroku import Heroku
from mongoengine import connect
from raven.contrib.flask import Sentry


#
# Setup
#

app = Flask(__name__)
app.secret_key = os.environ['SECRET']
heroku = Heroku(app)
if app.config.get('SENTRY_DSN'):
    sentry = Sentry(app)
connect(app.config['MONGODB_DB'], host=app.config['MONGODB_HOST'], port=app.config['MONGODB_PORT'], username=app.config['MONGODB_USER'], password=app.config['MONGODB_PASSWORD'])
github = GithubAuth(
    client_id=os.environ['GITHUB_CLIENT_ID'],
    client_secret=os.environ['GITHUB_SECRET'],
    session_key='github',
    redirect_url_name='me',
    model=User,
    username_field='name',
    access_token_field='access_token',
    admin_field='is_admin',
)
csrf = SeaSurf(app)

#
# Helpers
#

@app.before_request
def before_request():
    g.user = github.get_user()

@app.teardown_request
def teardown_request(exception):
    try:
        del g.user
    except AttributeError:
        pass

#
# Views
#

# Auth

app.route('/login/github/', endpoint='github_login')(github.login)

app.route('/auth/github/', endpoint='github_auth')(github.auth)


# Home

@app.route('/')
def index():
    stats = {
        'total_hugs': User.objects.total_hugs(),
        'average_hugs_given': User.objects.average_hugs_given(),
        'average_hugs_received': User.objects.average_hugs_received(),
        'hugs_this_week': Hug.objects.hugs_this_week(),
        'hugs_last_week': Hug.objects.hugs_last_week(),
    }
    return render_template('index.html', **stats)

@app.route('/me/')
@github.login_required
def me():
    return render_template('me.html', user=g.user)

@app.route('/me/', methods=['POST'])
@github.login_required
def hug():
    if not g.user.can_hug():
        abort(400)
    try:
        receiver_name = request.form['receiver']
        network = 'github' # todo: make dynamic
    except KeyError:
        abort(400)
    receiver,_ = User.objects.get_or_create(name=receiver_name, network=network)
    g.user.hug(receiver)
    return me()

@app.route('/user/<network>/<username>/')
def user(network, username):
    try:
        user = User.objects.get(network=network, name=username)
    except User.DoesNotExist:
        abort(404)
    return render_template('user.html', user=user)

if __name__ == '__main__':
    port = os.environ.get('PORT', None) or 5000
    app.local = os.environ.get('LOCAL', None) is not None
    if app.local:
        app.run(debug=True)
    else:
        app.run(port=int(port), host='0.0.0.0')
