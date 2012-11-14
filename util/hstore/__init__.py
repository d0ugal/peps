# -*- coding: utf-8 -*-

import re

import sqlalchemy.sql.functions as safunc
import sqlalchemy.dialects.postgresql as pgdialect
from sqlalchemy import types
from sqlalchemy.sql.operators import custom_op
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.mutable import Mutable

__all__ = ['HStoreSyntaxError', 'HSTORE', 'hstore']

# My best guess at the parsing rules of hstore literals, since no formal
# grammar is given.  This is mostly reverse engineered from PG's input parser
# behavior.
HSTORE_PAIR_RE = re.compile(r"""
(
  "(?P<key> (\\ . | [^"])* )"       # Quoted key
)
[ ]* => [ ]*    # Pair operator, optional adjoining whitespace
(
    (?P<value_null> NULL )          # NULL value
  | "(?P<value> (\\ . | [^"])* )"   # Quoted value
)
""", re.VERBOSE)

HSTORE_DELIMITER_RE = re.compile(r"""
[ ]* , [ ]*
""", re.VERBOSE)


class HStoreSyntaxError(SQLAlchemyError):
    """Indicates an error unmarshalling an hstore value."""

    def __init__(self, hstore_str, pos):
        self.hstore_str = hstore_str
        self.pos = pos

        ctx = 20
        hslen = len(hstore_str)

        parsed_tail = hstore_str[max(pos - ctx - 1, 0):min(pos, hslen)]
        residual = hstore_str[min(pos, hslen):min(pos + ctx + 1, hslen)]

        if len(parsed_tail) > ctx:
            parsed_tail = '[...]' + parsed_tail[1:]
        if len(residual) > ctx:
            residual = residual[:-1] + '[...]'

        super(HStoreSyntaxError, self).__init__(
            "After %r, could not parse residual at position %d: %r" %
            (parsed_tail, pos, residual)
        )


def _parse_hstore(hstore_str):
    """Parse an hstore from it's literal string representation.

    Attempts to approximate PG's hstore input parsing rules as closely as
    possible. Although currently this is not strictly necessary, since the
    current implementation of hstore's output syntax is stricter than what it
    accepts as input, the documentation makes no guarantees that will always
    be the case.

    Throws HStoreSyntaxError if parsing fails.

    """
    result = {}
    pos = 0
    pair_match = HSTORE_PAIR_RE.match(hstore_str)

    while pair_match is not None:
        key = unicode(pair_match.group('key'), 'utf-8')
        if pair_match.group('value_null'):
            value = None
        else:
            value = pair_match.group('value').replace(r'\"', '"')
        result[key] = unicode(value, 'utf-8')

        pos += pair_match.end()

        delim_match = HSTORE_DELIMITER_RE.match(hstore_str[pos:])
        if delim_match is not None:
            pos += delim_match.end()

        pair_match = HSTORE_PAIR_RE.match(hstore_str[pos:])

    if pos != len(hstore_str):
        raise HStoreSyntaxError(hstore_str, pos)

    return result


def _serialize_hstore(val):
    """Serialize a dictionary into an hstore literal.  Keys and values must
    both be strings (except None for values).

    """
    def esc(s, position):
        if position == 'value' and s is None:
            return 'NULL'
        elif isinstance(s, basestring):
            return '"%s"' % s.replace('"', r'\"')
        else:
            raise ValueError("%r in %s position is not a string." %
                             (s, position))

    return ', '.join('%s=>%s' % (esc(k, 'key'), esc(v, 'value'))
                     for k, v in val.iteritems())


class MutationDict(Mutable, dict):
    def __setitem__(self, key, value):
        """Detect dictionary set events and emit change events."""
        dict.__setitem__(self, key, value)
        self.changed()

    def __delitem__(self, key, value):
        """Detect dictionary del events and emit change events."""
        dict.__delitem__(self, key, value)
        self.changed()

    @classmethod
    def coerce(cls, key, value):
        """Convert plain dictionary to MutationDict."""
        if not isinstance(value, MutationDict):
            if isinstance(value, dict):
                return MutationDict(value)
            return Mutable.coerce(key, value)
        else:
            return value

    def __getstate__(self):
        return dict(self)

    def __setstate__(self, state):
        self.update(state)


class HSTORE(types.Concatenable, types.UserDefinedType):
    """The column type for representing PostgreSQL's contrib/hstore type.  This
    type is a miniature key-value store in a column.  It supports query
    operators for all the usual operations on a map-like data structure.

    """
    class comparator_factory(types.UserDefinedType.Comparator):
        def has_key(self, other):
            """Boolean expression.  Test for presence of a key.  Note that the
            key may be a SQLA expression.
            """
            return self.expr.op('?')(other)

        def has_all(self, other):
            """Boolean expression.  Test for presence of all keys in the PG
            array.
            """
            return self.expr.op('?&')(other)

        def has_any(self, other):
            """Boolean expression.  Test for presence of any key in the PG
            array.
            """
            return self.expr.op('?|')(other)

        def defined(self, key):
            """Boolean expression.  Test for presence of a non-NULL value for
            the key.  Note that the key may be a SQLA expression.
            """
            return _HStoreDefinedFunction(self.expr, key)

        def contains(self, other, **kwargs):
            """Boolean expression.  Test if keys are a superset of the keys of
            the argument hstore expression.
            """
            return self.expr.op('@>')(other)

        def contained_by(self, other):
            """Boolean expression.  Test if keys are a proper subset of the
            keys of the argument hstore expression.
            """
            return self.expr.op('<@')(other)

        def __getitem__(self, other):
            """Text expression.  Get the value at a given key.  Note that the
            key may be a SQLA expression.
            """
            return self.expr.op('->', precedence=5)(other)

        def __add__(self, other):
            """HStore expression.  Merge the left and right hstore expressions,
            with duplicate keys taking the value from the right expression.
            """
            return self.expr.concat(other)

        def delete(self, key):
            """HStore expression.  Returns the contents of this hstore with the
            given key deleted.  Note that the key may be a SQLA expression.
            """
            if isinstance(key, dict):
                key = _serialize_hstore(key)
            return _HStoreDeleteFunction(self.expr, key)

        def slice(self, array):
            """HStore expression.  Returns a subset of an hstore defined by
            array of keys.
            """
            return _HStoreSliceFunction(self.expr, array)

        def keys(self):
            """Text array expression.  Returns array of keys."""
            return _HStoreKeysFunction(self.expr)

        def vals(self):
            """Text array expression.  Returns array of values."""
            return _HStoreValsFunction(self.expr)

        def array(self):
            """Text array expression.  Returns array of alternating keys and
            values.
            """
            return _HStoreArrayFunction(self.expr)

        def matrix(self):
            """Text array expression.  Returns array of [key, value] pairs."""
            return _HStoreMatrixFunction(self.expr)

        def _adapt_expression(self, op, other_comparator):
            if isinstance(op, custom_op):
                if op.opstring in ['?', '?&', '?|', '@>', '<@']:
                    return op, types.Boolean
                elif op.opstring == '->':
                    return op, types.Text
            return op, other_comparator.type

    def bind_processor(self, dialect):
        def process(value):
            if isinstance(value, dict):
                return _serialize_hstore(value)
            else:
                return value
        return process

    def get_col_spec(self):
        return 'HSTORE'

    def result_processor(self, dialect, coltype):
        def process(value):
            if value is not None and not isinstance(value, dict):
                return _parse_hstore(value)
            else:
                return {unicode(k, 'utf-8'): unicode(v, 'utf-8') for k, v in value.items()}
        return process

MutationDict.associate_with(HSTORE)


class hstore(safunc.GenericFunction):
    """Construct an hstore on the server side using the hstore function.

    The single argument or a pair of arguments are evaluated as SQLAlchemy
    expressions, so both may contain columns, function calls, or any other
    valid SQL expressions which evaluate to text or array.

    """
    type = HSTORE

    def __init__(self, *args, **kwargs):
        safunc.GenericFunction.__init__(self, *args, **kwargs)
        self.name = 'hstore'


class _HStoreDefinedFunction(safunc.GenericFunction):
    type = types.Boolean

    def __init__(self, store, key, **kwargs):
        safunc.GenericFunction.__init__(self, store, key, **kwargs)
        self.name = 'defined'


class _HStoreDeleteFunction(safunc.GenericFunction):
    type = HSTORE

    def __init__(self, store, key, **kwargs):
        safunc.GenericFunction.__init__(self, store, key, **kwargs)
        self.name = 'delete'


class _HStoreSliceFunction(safunc.GenericFunction):
    type = HSTORE

    def __init__(self, store, array, **kwargs):
        safunc.GenericFunction.__init__(self, store, array, **kwargs)
        self.name = 'slice'


class _HStoreKeysFunction(safunc.GenericFunction):
    type = pgdialect.ARRAY(types.Text)

    def __init__(self, store, **kwargs):
        safunc.GenericFunction.__init__(self, store, **kwargs)
        self.name = 'akeys'


class _HStoreValsFunction(safunc.GenericFunction):
    type = pgdialect.ARRAY(types.Text)

    def __init__(self, store, **kwargs):
        safunc.GenericFunction.__init__(self, store, **kwargs)
        self.name = 'avals'


class _HStoreArrayFunction(safunc.GenericFunction):
    type = pgdialect.ARRAY(types.Text)

    def __init__(self, store, **kwargs):
        safunc.GenericFunction.__init__(self, store, **kwargs)
        self.name = 'hstore_to_array'


class _HStoreMatrixFunction(safunc.GenericFunction):
    type = pgdialect.ARRAY(types.Text)

    def __init__(self, store, **kwargs):
        safunc.GenericFunction.__init__(self, store, **kwargs)
        self.name = 'hstore_to_matrix'
