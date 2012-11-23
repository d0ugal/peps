from flask import Blueprint, render_template
from flask import request, Response

from pep.models import Pep
from pep.tasks import sort_peps
from util.db import get_or_404, find
from util.cache import cached

mod = Blueprint('base', __name__)


@mod.route('/')
@cached(timeout=60 * 60)
def index():

    peps = Pep.query.order_by(Pep.number.asc())

    if 'status' in request.args:
        peps = peps.filter(Pep.properties.contains({'status': request.args.get('status')}))

    if 'type' in request.args:
        peps = peps.filter(Pep.properties.contains({'type': request.args.get('type')}))

    sorted_peps = sort_peps(peps)

    return render_template('base/index.html',
        sorted_peps=sorted_peps,
    )


@mod.route('/search/')
def search():

    q = request.args.get("q")
    find
    results = Pep.query.filter("to_tsvector('english', pep.content) @@ plainto_tsquery(:q)").params(q=q).limit(10)

    return render_template('base/search.html',
        term=q,
        peps=results,
    )


@mod.route('/<int:pep_number>/')
@cached(timeout=60 * 60)
def pep_view(pep_number):

    pep = get_or_404(Pep, number=pep_number)

    return render_template('base/pep_view.html',
        pep=pep,
    )


@mod.route('/<int:pep_number>.txt')
@cached(timeout=60 * 60)
def pep_view_raw(pep_number):

    pep = get_or_404(Pep, number=pep_number)

    return Response(pep.raw_content, mimetype='text/plain')
