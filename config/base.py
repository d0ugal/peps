import os
_basedir = os.path.abspath(os.path.dirname(__file__))

DEBUG = True

ADMINS = frozenset(['dougal85@gmail.com'])
SECRET_KEY = os.environ.get('SECRET_KEY', "Yikes.")

SQLALCHEMY_DATABASE_URI = "postgresql://pep:pep@localhost/pep"
DATABASE_CONNECT_OPTIONS = {}

THREADS_PER_PAGE = 8

CSRF_ENABLED = True
CSRF_SESSION_KEY = os.environ.get('CSRF_SESSION_KEY')

SQLALCHEMY_ECHO = True


try:
    from local_config import *
except ImportError:
    pass
