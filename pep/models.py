from datetime import datetime
from re import compile

from pyquery import PyQuery
from sqlalchemy import event, DDL, Index
from sqlalchemy.orm import deferred

from app import db
from util.hstore import HSTORE


class PepQuery(db.Query):

    def search(self, term):

        sql = """
        SELECT
            pep.id AS pep_id, pep.number AS pep_number, ts_headline('english', pep.title, query) AS pep_title,
            pep.added AS pep_added, pep.updated AS pep_updated, pep.properties AS
            pep_properties, pep.filename AS pep_filename,
            ts_rank_cd('{0.1, 0.8, 0.9, 1.0}', search_col, query) AS rank
        FROM pep, plainto_tsquery(:term) query
        WHERE query @@ search_col
        ORDER BY rank DESC;
        """

        return Pep.query.session.query(Pep).from_statement(sql).params(term=term).all()


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

    query_class = PepQuery

    __table_args__ = (
        Index('pep_number_idx', 'properties'),
    )

    def keywords(self):

        sql = """
        SELECT word FROM ts_stat('SELECT search_col FROM pep WHERE id = :id')
        ORDER BY nentry DESC, ndoc DESC, word
        LIMIT 30;
        """

        kws = Pep.query.session.execute(sql, {'id': self.id}).fetchall()

        return [k[0] for k in kws]

    def abstract(self):
        """
        This is somewhat gross. Try and find something that looks like an
        abstract and use it for the HTML description. Also does some ghetto
        stripping of HTML to make it look better (not to make it safe - jinja
        does that bit).
        """

        d = PyQuery(self.content)

        p = d("#abstract p").html() or d(".section p").html() or d("pre").html()

        p = ' '.join(l.strip() for l in p.splitlines())
        p = compile(r'<.*?>').sub('', p)

        return p

    def url(self):
        return "/%s/" % self.id

    def sorted_properties(self):
        return sorted(self.properties.items())


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
