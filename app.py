# -*- coding: utf-8 -*-
import urlparse
from flask_sslify import SSLify
import os
import json

from flask import Flask, g, render_template, request, abort, redirect, url_for, session, jsonify
from flask_heroku import Heroku
from flaskext.seasurf import SeaSurf
from mongoengine import connect
from raven.contrib.flask import Sentry
from redis import from_url

from auth import GithubAuth
from models import User, Hug


#
# Custom GithubAuth, we'll leave auth.py as clean as possible so I can continue to copy/paste it around
#

class GitHugAuth(GithubAuth):
    def build_user(self, data):
        user = super(GitHugAuth, self).build_user(data)
        user.avatar_url = data['user']['avatar_url']
        return user

#
# Setup
#
import requests

app = Flask(__name__)
app.secret_key = os.environ['SECRET']
app.config['WEBSOCKET_URL'] = os.environ['WEBSOCKET_URL']
app.config['REDIS_CHANNEL'] = os.environ['REDIS_CHANNEL']
app.local = os.environ.get('LOCAL', None) is not None
app.debug = bool(app.local)
if not app.debug:
    sslify = SSLify(app)
heroku = Heroku(app)
if app.config.get('SENTRY_DSN'):
    sentry = Sentry(app)
db = connect(app.config['MONGODB_DB'], host=app.config['MONGODB_HOST'], port=app.config['MONGODB_PORT'], username=app.config['MONGODB_USER'], password=app.config['MONGODB_PASSWORD'])
github = GitHugAuth(
    client_id=os.environ['GITHUB_CLIENT_ID'],
    client_secret=os.environ['GITHUB_SECRET'],
    session_key_prefix='github-',
    model=User,
    username_field='name',
    access_token_field='access_token',
    admin_field='is_admin',
    login_view_name='github_login',
)
csrf = SeaSurf(app)
redis = from_url(os.environ['REDISTOGO_URL'])
requests_session = requests.session()

#
# Helpers
#

@app.before_request
def before_request():
    g.user = github.get_user()
    g.websocket_url = app.config['WEBSOCKET_URL']

@app.teardown_request
def teardown_request(exception):
    try:
        del g.user
    except AttributeError:
        pass

@app.context_processor
def reverse_filter():
    return {
        'urljoin': lambda *args: urlparse.urljoin(*args),
        'ANALYTICS_ID': os.environ.get('ANALYTICS_ID', None)
    }

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

# Profile

@app.route('/me/')
@github.login_required
def me():
    return render_template('me.html', user=g.user)


@app.route('/me/', methods=['POST'])
@github.login_required
def prepare_to_hug():
    try:
        return redirect(url_for('confirm_hug', network='github', username=request.form['receiver']))
    except KeyError:
        abort(400)

# Two step hug

@app.route('/hug/<network>/<username>/')
@github.login_required
def confirm_hug(network, username):
    if network != 'github':
        abort(400)
    if not g.user.can_hug():
        return render_template('already_hugged.html')
    response = requests_session.get('https://api.github.com/users/%s' % username)
    if not response.ok:
        return redirect(url_for('me'))
    session['avatar-url'] = response.json['avatar_url']
    return render_template('confirm_hug.html', user=response.json)

@app.route('/hug/<network>/<username>/', methods=['POST'])
@github.login_required
def hug(network, username):
    if network != 'github':
        abort(400)
    if 'avatar-url' not in session:
        abort(400)
    if not g.user.can_hug():
        return render_template('already_hugged.html')
    if request.form.get('confirm', None) != 'confirm':
        abort(400)
    receiver,_ = User.objects.get_or_create(name=username, network=network, avatar_url=session['avatar-url'])
    del session['avatar-url']
    hug = g.user.hug(receiver)
    redis.publish(app.config['REDIS_CHANNEL'], json.dumps(hug.to_dict(True)))
    return redirect(url_for('me'))


# User profile

@app.route('/user/<network>/<username>/')
def user(network, username):
    try:
        user = User.objects.get(network=network, name=username)
    except User.DoesNotExist:
        abort(404)
    best = request.accept_mimetypes.best_match(['application/json', 'application/python', 'text/html'])
    if best == 'application/json' and request.accept_mimetypes[best] > request.accept_mimetypes['text/html']:
        return jsonify(user.to_dict(True))
    return render_template('user.html', user=user)

@app.route('/api/')
def api():
    return render_template('api_docs.html')

# Run this stuff!

if __name__ == '__main__':
    port = os.environ.get('PORT', None) or 5000
    app.run(port=int(port))
