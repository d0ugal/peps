from os import environ, path
_basedir = path.abspath(path.dirname(__file__))

ADMINS = frozenset(['dougal85@gmail.com'])
CSRF_ENABLED = True
CSRF_SESSION_KEY = environ.get('CSRF_SESSION_KEY')
DATABASE_CONNECT_OPTIONS = {}
DEBUG = False
SECRET_KEY = environ.get('SECRET_KEY')
SQLALCHEMY_DATABASE_URI = environ.get('HEROKU_POSTGRESQL_BLACK_URL')
THREADS_PER_PAGE = 8
