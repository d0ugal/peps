# -*- coding: utf-8 -*-

import os

import sqlalchemy.sql as sql
import sqlalchemy.orm as orm
from sqlalchemy import create_engine
from sqlalchemy.schema import Column
from sqlalchemy.types import Integer, Text
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import array
from sqlalchemy.ext.declarative import declarative_base

from hstore import HSTORE, hstore


Base = declarative_base()


class Test(Base):
    __tablename__ = 'test_table'
    id = Column(Integer, primary_key=True)
    hash = Column(HSTORE)

    def __repr__(self):
        return "%s(%r, %r)" % (self.__class__.__name__, self.id, self.hash)


if __name__ == '__main__':
    user = os.getenv('USER')
    engine = create_engine('postgresql://%s@localhost/%s' % (user, user))
    Base.metadata.create_all(engine)

    Session = orm.sessionmaker(bind=engine)
    s = Session()

    test = Test()
    test.hash = {'foo': '1', 'bar': None}
    s.add(test)
    s.commit()

    print 's.dirty:', s.dirty
    test.hash['baz'] = '"baz"'
    print 's.dirty:', s.dirty
    print
    s.commit()

    queries = [
        s.query(Test).filter(Test.hash.has_key('foo')),
        s.query(Test).filter(Test.hash.has_all(array(['foo', 'bar']))),
        s.query(Test).filter(Test.hash.has_any(array(['baz', 'foo']))),
        s.query(Test).filter(Test.hash.defined('bar')),
        s.query(Test).filter(Test.hash.contains({'foo': '1'})),
        s.query(Test).filter(Test.hash.contained_by({'foo': '1', 'bar': None})),
        s.query(Test).filter(Test.hash['bar'] == None),
        s.query(Test.hash['foo']),
        s.query(Test.hash.delete('foo')),
        s.query(Test.hash.delete(array(['foo', 'bar']))),
        s.query(Test.hash.delete(hstore('bar', None))),
        s.query(Test.hash.delete({'bar': None})),
        s.query(Test.hash.slice(array(['foo', 'bar']))),
        s.query(hstore('foo', '3')['foo']),
        s.query(hstore('foo', None)['foo']),
        s.query(hstore('bar', 'baz')['foo']),
        s.query(hstore(array(['1', '2']), array(['3', '4']))['1']),
        s.query(hstore(array(['1', '2', '3', '4']))['3']),
        s.query(Test.hash + hstore(sql.cast(Test.id, Text), '3')),
        s.query(Test.hash + Test.hash),
        s.query((Test.hash + Test.hash)['foo']),
        s.query(Test.hash.keys()),
        s.query(Test.hash.vals()),
        s.query(Test.hash.array()),
        s.query(Test.hash.matrix()),
        s.query(sql.func.sum(sql.cast(Test.hash['foo'], Integer))),
    ]

    for q in queries:
        print q.statement.compile(dialect=postgresql.dialect())
        print q.all()
        print

    s.close()
