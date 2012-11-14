from flask import Blueprint, render_template
from flask import request

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

    # blog_entries.search_vector @@ plainto_tsquery(:terms)
    q = request.args.get("q")
    results = Pep.query.filter("to_tsvector('english', pep.content) @@ plainto_tsquery(:q)").params(q=q).limit(10)

    return render_template('base/index.html',
        peps=results,
    )
