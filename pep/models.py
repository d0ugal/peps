from app import db

from util.hstore import Hstore


class Pep(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    added = db.Column(db.DateTime, nullable=False)
    pub_date = db.Column(db.DateTime, nullable=True)

    properties = db.Column(Hstore, nullable=False, default={})
