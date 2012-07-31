######
GitHug
######

Run the web server
==================

Make a GitHub app at https://github.com/settings/applications pointing the URL to ``http://localhost:5000/`` and the
callback URL to ``http://localhost:5000/auth/github/``.

Install and run a MongoDB server (I suggest locally,but not necessarily).
Install and run a Redis server (again, local server is best).

Make a file called ``.env`` and set the following values:

 * ``GITHUB_SECRET``: Secret of your GitHub app.
 * ``GITHUB_CLIENT_ID``: Client ID of your GitHub app.
 * ``MONGOLAB_URI``: URI to your MongoDB server. Format: ``mongodb://<username>:<password>@<host>:<port>/<name>``. For
   example: ``mongodb://localhost/githug``.
 * ``REDISTOGO_URL``: Set it to something like ``redis://localhost:6379/5``.
 * ``REDIS_CHANNEL``: Set it to ``hug``.
 * ``WEBSOCKET_URL``: Set it to ``ws://localhost:9000/``.
 * ``SECRET``: The secret key. Set it to something, then don't change it.
 * ``LOCAL=True``: For debug mode.

Create a virtualenv.

Activate it.

Install requirements: ``pip install -r requirements.txt``.

Run ``foreman start``.

Open the page at ``http://localhost:5000``.

Enjoy.

**NEVER** commit your ``.env`` file!


Run the websocket
=================

Check out https://github.com/ojii/githug-websocket

Make a file called ``.env`` and set the following values:

* ``REDISTOGO_URL``: Same as above.
* ``REDIS_CHANNEL``: Same as above.

Create a virtualenv

Activate it.

Install requirements: ``pip install -r requirements.txt``.

Run ``foreman start -p 9000``.

Enjoy.

**NEVER** commit your ``.env`` file!
