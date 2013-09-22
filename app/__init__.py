from os import environ

from flask import Flask, render_template, request
from flask.ext.sqlalchemy import SQLAlchemy
from logging import ERROR
from logging.handlers import SMTPHandler
from psycopg2.extras import register_hstore
from raven.contrib.flask import Sentry
from werkzeug.contrib.cache import SimpleCache


def create_app():
    return Flask("peps", template_folder='app/templates',
        static_folder='app/static')

app = create_app()
app.config.from_object('config')

try:
    sentry = Sentry(app, dsn=environ['SENTRY_DSN'])
except KeyError:
    sentry = None
    print "MISSING SENTRY_DSN"

db = SQLAlchemy(app)
register_hstore(db.engine.raw_connection(), True)

cache = SimpleCache()

# For DEBUG, enable the debug toolbar and set the cach to be the NullCache.
if app.config['DEBUG']:
    from flask_debugtoolbar import DebugToolbarExtension
    from werkzeug.contrib.cache import NullCache
    toolbar = DebugToolbarExtension(app)
    cache = NullCache()

# Try to setup email logging if details can be found.
try:
    smtp_server = environ['SMTP_HOST']
    credentials = (environ['SMTP_USER'], environ['SMTP_PASSWORD'])

    mail_handler = SMTPHandler(smtp_server, environ['SMTP_USER'],
        app.config['ADMINS'], '[www.peps.io] 500', credentials=credentials)
    mail_handler.setLevel(ERROR)
    app.logger.addHandler(mail_handler)

except KeyError as e:
    pass


@app.errorhandler(404)
def not_found(error):
    if sentry:
        sentry.captureMessage("404: %s" % request.url)
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('500.html'), 404


from util.template import format_datetime_filter, nl2br, rst_to_html, literalnl2br
app.jinja_env.filters['datetime'] = format_datetime_filter
app.jinja_env.filters['nl2br'] = nl2br
app.jinja_env.filters['literalnl2br'] = literalnl2br
app.jinja_env.filters['rst_to_html'] = rst_to_html

from app import views
app.register_blueprint(views.mod)

from pep.models import *
