# -*- coding: utf-8 -*-
from gevent import monkey; monkey.patch_all() # ugh
from geventwebsocket.handler import WebSocketHandler
from gevent.pywsgi import WSGIServer

import os

from flask import Flask, render_template, request, redirect
from flask_heroku import Heroku
from raven.contrib.flask import Sentry
from redis import from_url


app = Flask(__name__)
app.secret_key = os.environ['SECRET']
heroku = Heroku(app)
if app.config.get('SENTRY_DSN'):
    sentry = Sentry(app)
redis = from_url(os.environ['REDISTOGO_URL'])


@app.route('/')
def index():
    if request.environ.get('wsgi.websocket'):
        web_socket = request.environ['wsgi.websocket']
        pubsub = redis.pubsub()
        pubsub.subscribe('hug')
        try:
            for obj in pubsub.listen():
                if obj['type'] == 'message':
                    web_socket.send(obj['data'])
        except Exception:
            web_socket.close()
            raise
    else:
        return render_template('api_docs.html')

if __name__ == '__main__':
    port = os.environ.get('PORT', None) or 5000
    app.local = os.environ.get('LOCAL', None) is not None
    if app.local:
        app.debug = True
    http_server = WSGIServer(('0.0.0.0', int(port)), app, handler_class=WebSocketHandler)
    http_server.serve_forever()
