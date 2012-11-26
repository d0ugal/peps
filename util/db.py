from flask import abort
from sqlalchemy.orm import Query
from sqlalchemy.orm.exc import NoResultFound

from app import db


def get_or_create(model, commit=True, **kwargs):

    defaults = kwargs.pop('defaults', {})
    lookup = kwargs.copy()

    created = False
    try:
        model_instance = model.query.filter_by(**lookup).one()
    except NoResultFound:
        lookup.update(defaults)
        model_instance = model(**lookup)
        # TODO: If commt = False is passed in should it be adde to the
        # session? I'm not sure really.
        db.session.add(model_instance)
        if commit:
            db.session.commit()
        created = True

    return model_instance, created


def get_or_404(model_or_query, **kwargs):

    lookup = kwargs.copy()

    try:

        if not isinstance(model_or_query, Query):
            query = model_or_query.query
        else:
            query = model_or_query

        model_instance = query.filter_by(**lookup).one()
    except NoResultFound:
        abort(404)

    return model_instance
