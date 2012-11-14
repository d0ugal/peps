from sqlalchemy.orm.exc import NoResultFound
from app import db


def get_or_create(model, **kwargs):

    defaults = kwargs.pop('defaults', {})
    lookup = kwargs.copy()

    created = False
    try:
        model_instance = model.query.filter_by(**lookup).one()
    except NoResultFound:
        lookup.update(defaults)
        model_instance = model(**lookup)
        db.session.add(model_instance)
        db.session.commit()
        created = True

    return model_instance, created
