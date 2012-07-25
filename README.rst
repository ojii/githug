######
GitHug
######

To run:

Make a GitHub app at https://github.com/settings/applications pointing the URL to ``http://localhost:5000/`` and the
callback URL to ``http://localhost:5000/auth/github/``.

Install and run a MongoDB server (I suggest locally,but not necessarily).

Make a file called ``.env`` and set the following values:

 * ``GITHUB_SECRET``: Secret of your GitHub app.
 * ``GITHUB_CLIENT_ID``: Client ID of your GitHub app.
 * ``MONGOLAB_URI``: URI to your MongoDB server. Format: ``mongodb://<username>:<password>@<host>:<port>/<name>``. For
   example: ``mongodb://localhost/githug``.
 * ``SECRET``: The secret key. Set it to something, then don't change it.
 * ``LOCAL=True``: For debug mode.

Create a virtualenv.

Activate it.

Install requirements: ``pip install -r requirements.txt``.

Run ``foreman start``.

Enjoy.

**NEVER** commit your ``.env`` file!
