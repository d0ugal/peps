# -*- coding: utf-8 -*-

import os

import sqlalchemy.sql as sql
from sqlalchemy import create_engine, MetaData
from sqlalchemy.schema import Column, Table
from sqlalchemy.types import Integer, Text
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import array

from hstore import HSTORE, hstore

meta = MetaData()
test_table = Table('test_table', meta,
    Column('id', Integer, primary_key=True),
    Column('hash', HSTORE)
)


if __name__ == '__main__':
    user = os.getenv('USER')
    engine = create_engine('postgresql://%s@localhost/%s' % (user, user))
    meta.create_all(engine)

    conn = engine.connect()

    ins = test_table.insert().values(hash={'foo': '1', 'bar': None})
    conn.execute(ins)

    hashcol = test_table.c.hash
    where_tests = [
        hashcol.has_key('foo'),
        hashcol.has_all(array(['foo', 'bar'])),
        hashcol.has_any(array(['baz', 'foo'])),
        hashcol.defined('bar'),
        hashcol.contains({'foo': '1'}),
        hashcol.contained_by({'foo': '1', 'bar': None}),
        hashcol['bar'] == None,
    ]
    select_tests = [
        hashcol['foo'],
        hashcol.delete('foo'),
        hashcol.delete(array(['foo', 'bar'])),
        hashcol.delete(hstore('bar', None)),
        hashcol.delete({'bar': None}),
        hashcol.slice(array(['foo', 'bar'])),
        hstore('foo', '3')['foo'],
        hstore('foo', None)['foo'],
        hstore('bar', 'baz')['foo'],
        hstore(array(['1', '2']), array(['3', '4']))['1'],
        hstore(array(['1', '2', '3', '4']))['3'],
        hashcol + hstore(sql.cast(test_table.c.id, Text), '3'),
        hashcol + hashcol,
        (hashcol + hashcol)['foo'],
        hashcol.keys(),
        hashcol.vals(),
        hashcol.array(),
        hashcol.matrix(),
        sql.func.sum(sql.cast(hashcol['foo'], Integer)),
    ]

    for wt in where_tests:
        a = sql.select([test_table], whereclause=wt)
        print a.compile(dialect=postgresql.dialect())
        print str(list(conn.execute(a)))
        print

    for st in select_tests:
        a = sql.select([st])
        print a.compile(dialect=postgresql.dialect())
        print str(list(conn.execute(a)))
        print

    conn.close()
