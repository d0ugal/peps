from flask import Blueprint, render_template
from flask import request

from sqlalchemy import func

from pep.models import Pep

mod = Blueprint('base', __name__)


@mod.route('/')
def index():

    latest = Pep.query.order_by(Pep.number.desc()).limit(10)

    return render_template('base/index.html',
        peps=latest,
    )


@mod.route('/search/')
def search():

    q = request.args.get("q")
    results = Pep.query.filter(func.to_tsvector('english', Pep.content)\
        .match(func.plainto_tsquery(q)))

    return render_template('base/index.html',
        peps=results,
    )
