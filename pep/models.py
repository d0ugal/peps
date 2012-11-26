from datetime import datetime

from sqlalchemy import event, DDL, Index
from sqlalchemy.orm import deferred

from app import db
from util.hstore import HSTORE


class Pep(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, unique=True)
    title = db.Column(db.String(120))
    added = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated = db.Column(db.DateTime, nullable=False, default=datetime.now)

    properties = db.Column(HSTORE, nullable=False, default={})
    content = deferred(db.Column(db.Text))
    raw_content = deferred(db.Column(db.Text))
    filename = db.Column(db.String(200))

    __table_args__ = (
        Index('pep_number_idx', 'properties'),
    )

trig_ddl = DDL("""
ALTER TABLE pep ADD COLUMN search_col tsvector;
CREATE INDEX search_col_gin_idx ON pep USING gin(search_col);

CREATE OR REPLACE FUNCTION search_col_update_trigger() RETURNS trigger AS $$
begin
  new.search_col :=
    setweight(to_tsvector('english', new.number || ''), 'A') ||
    setweight(to_tsvector('english', coalesce(new.title,'')), 'B') ||
    setweight(to_tsvector('english', coalesce(new.properties->'author','')), 'C') ||
    setweight(to_tsvector('english', coalesce(new.content,'')), 'D');
  return new;
end
$$ LANGUAGE plpgsql;


CREATE TRIGGER search_col_update BEFORE INSERT OR UPDATE
ON pep FOR EACH ROW EXECUTE PROCEDURE
search_col_update_trigger();
""")

event.listen(Pep.__table__, 'after_create', trig_ddl.execute_if(dialect='postgresql'))
event.listen(Pep.__table__, 'before_create', DDL("CREATE EXTENSION IF NOT EXISTS hstore").execute_if(dialect='postgresql'))
