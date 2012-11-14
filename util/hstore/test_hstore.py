import unittest
import re

from sqlalchemy.dialects.postgresql import array
from sqlalchemy.dialects import postgresql
from sqlalchemy import MetaData, Table, Column, Integer, select, cast, Text

from hstore import HSTORE, hstore


class CoreGenerationTest(unittest.TestCase):
    def _assert_sql(self, construct, expected):
        dialect = postgresql.dialect()
        compiled = str(construct.compile(dialect=dialect))
        compiled = re.sub(r'\s+', ' ', compiled)
        expected = re.sub(r'\s+', ' ', expected)
        self.assertEquals(compiled, expected)

    def setUp(self):
        metadata = MetaData()
        self.test_table = Table('test_table', metadata,
            Column('id', Integer, primary_key=True),
            Column('hash', HSTORE)
        )
        self.hashcol = self.test_table.c.hash

    def _test_where(self, whereclause, expected):
        stmt = select([self.test_table]).where(whereclause)
        self._assert_sql(
            stmt,
            "SELECT test_table.id, test_table.hash FROM test_table "
            "WHERE %s" % expected
        )

    def _test_cols(self, colclause, expected, from_=True):
        stmt = select([colclause])
        self._assert_sql(
            stmt,
            (
                "SELECT %s" +
                (" FROM test_table" if from_ else "")
            ) % expected
        )

    def test_where_has_key(self):
        self._test_where(
            self.hashcol.has_key('foo'),
            "test_table.hash ? %(hash_1)s"
        )

    def test_where_has_all(self):
        self._test_where(
            self.hashcol.has_all(array(['1', '2'])),
            "test_table.hash ?& ARRAY[%(param_1)s, %(param_2)s]"
        )

    def test_where_has_any(self):
        self._test_where(
            self.hashcol.has_any(array(['1', '2'])),
            "test_table.hash ?| ARRAY[%(param_1)s, %(param_2)s]"
        )

    def test_where_defined(self):
        self._test_where(
            self.hashcol.defined('foo'),
            "defined(test_table.hash, %(param_1)s)"
        )

    def test_where_contains(self):
        self._test_where(
            self.hashcol.contains({'foo': '1'}),
            "test_table.hash @> %(hash_1)s"
        )

    def test_where_contained_by(self):
        self._test_where(
            self.hashcol.contained_by({'foo': '1', 'bar': None}),
            "test_table.hash <@ %(hash_1)s"
        )

    def test_where_getitem(self):
        self._test_where(
            self.hashcol['bar'] == None,
            "(test_table.hash -> %(hash_1)s) IS NULL"
        )

    def test_cols_get(self):
        self._test_cols(
            self.hashcol['foo'],
            "test_table.hash -> %(hash_1)s AS anon_1",
            True
        )

    def test_cols_delete_single_key(self):
        self._test_cols(
            self.hashcol.delete('foo'),
            "delete(test_table.hash, %(param_1)s) AS delete_1",
            True
        )

    def test_cols_delete_array_of_keys(self):
        self._test_cols(
            self.hashcol.delete(array(['foo', 'bar'])),
            ("delete(test_table.hash, ARRAY[%(param_1)s, %(param_2)s]) "
             "AS delete_1"),
            True
        )

    def test_cols_delete_matching_pairs(self):
        self._test_cols(
            self.hashcol.delete(hstore('1', '2')),
            ("delete(test_table.hash, hstore(%(param_1)s, %(param_2)s)) "
             "AS delete_1"),
            True
        )

    def test_cols_slice(self):
        self._test_cols(
            self.hashcol.slice(array(['1', '2'])),
            ("slice(test_table.hash, ARRAY[%(param_1)s, %(param_2)s]) "
             "AS slice_1"),
            True
        )

    def test_cols_hstore_pair_text(self):
        self._test_cols(
            hstore('foo', '3')['foo'],
            "hstore(%(param_1)s, %(param_2)s) -> %(hstore_1)s AS anon_1",
            False
        )

    def test_cols_hstore_pair_array(self):
        self._test_cols(
            hstore(array(['1', '2']), array(['3', None]))['1'],
            ("hstore(ARRAY[%(param_1)s, %(param_2)s], "
             "ARRAY[%(param_3)s, NULL]) -> %(hstore_1)s AS anon_1"),
            False
        )

    def test_cols_hstore_single_array(self):
        self._test_cols(
            hstore(array(['1', '2', '3', None]))['3'],
            ("hstore(ARRAY[%(param_1)s, %(param_2)s, %(param_3)s, NULL]) "
             "-> %(hstore_1)s AS anon_1"),
            False
        )

    def test_cols_concat(self):
        self._test_cols(
            self.hashcol.concat(hstore(cast(self.test_table.c.id, Text), '3')),
            ("test_table.hash || hstore(CAST(test_table.id AS TEXT), "
             "%(param_1)s) AS anon_1"),
            True
        )

    def test_cols_concat_op(self):
        self._test_cols(
            self.hashcol + self.hashcol,
            "test_table.hash || test_table.hash AS anon_1",
            True
        )

    def test_cols_concat_get(self):
        self._test_cols(
            (self.hashcol + self.hashcol)['foo'],
            "test_table.hash || test_table.hash -> %(param_1)s AS anon_1"
        )

    def test_cols_keys(self):
        self._test_cols(
            self.hashcol.keys(),
            "akeys(test_table.hash) AS akeys_1",
            True
        )

    def test_cols_vals(self):
        self._test_cols(
            self.hashcol.vals(),
            "avals(test_table.hash) AS avals_1",
            True
        )

    def test_cols_array(self):
        self._test_cols(
            self.hashcol.array(),
            "hstore_to_array(test_table.hash) AS hstore_to_array_1",
            True
        )

    def test_cols_matrix(self):
        self._test_cols(
            self.hashcol.matrix(),
            "hstore_to_matrix(test_table.hash) AS hstore_to_matrix_1",
            True
        )


if __name__ == '__main__':
    unittest.main()
