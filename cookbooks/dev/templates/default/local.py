from os import environ, path
_basedir = path.abspath(path.dirname(__file__))

CSRF_SESSION_KEY = environ.get('CSRF_SESSION_KEY', 'Dev placeholder.')
DATABASE_CONNECT_OPTIONS = {}
DEBUG = True
SECRET_KEY = environ.get('SECRET_KEY', "Dev placeholder.")
SQLALCHEMY_DATABASE_URI = "postgresql://pep:pep@localhost/pep"
SQLALCHEMY_ECHO = True
