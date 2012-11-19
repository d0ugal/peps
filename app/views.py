from flask import Blueprint, render_template
from flask import request

from pep.models import Pep
from util.db import get_or_404, find

mod = Blueprint('base', __name__)


@mod.route('/')
def index():

    latest = Pep.query.order_by(Pep.number.asc())

    if 'status' in request.args:
        latest = latest.filter(Pep.properties.contains({'status': request.args.get('status')}))

    if 'type' in request.args:
        latest = latest.filter(Pep.properties.contains({'type': request.args.get('type')}))

    return render_template('base/index.html',
        peps=latest,
    )


@mod.route('/search/')
def search():

    q = request.args.get("q")
    find
    results = Pep.query.filter("to_tsvector('english', pep.content) @@ plainto_tsquery(:q)").params(q=q).limit(10)

    return render_template('base/index.html',
        peps=results,
    )


@mod.route('/<int:pep_number>/')
def pep_view(pep_number):

    pep = get_or_404(Pep, number=pep_number)

    return render_template('base/pep_view.html',
        pep=pep,
    )
