from datetime import datetime

from sqlalchemy import event, DDL, Index

from app import db
from util.hstore import HSTORE


class Pep(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, unique=True)
    added = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated = db.Column(db.DateTime, nullable=False, default=datetime.now)

    properties = db.Column(HSTORE, nullable=False, default={})
    content = db.Column(db.Text)
    raw_content = db.Column(db.Text)
    filename = db.Column(db.String(200))

    __table_args__ = (
        Index('pep_number_idx', 'properties'),
    )

trig_ddl = DDL("CREATE INDEX content_gin_idx ON pep USING gin(to_tsvector('english', content))")
event.listen(Pep.__table__, 'after_create', trig_ddl.execute_if(dialect='postgresql'))
