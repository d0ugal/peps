from flask import Blueprint, render_template
from flask import request, Response
from sqlalchemy.orm import undefer

from pep.models import Pep
from pep.tasks import sort_peps
from util.db import get_or_404
from util.cache import cached

mod = Blueprint('base', __name__)


@mod.route('/')
@cached(timeout=60 * 60)
def index():

    peps = Pep.query.order_by(Pep.number.asc())

    if 'status' in request.args:
        peps = peps.filter(Pep.properties.contains({
            'status': request.args.get('status'),
        }))

    if 'type' in request.args:
        peps = peps.filter(Pep.properties.contains({
            'type': request.args.get('type'),
        }))

    sorted_peps = sort_peps(peps)

    return render_template('base/index.html',
        sorted_peps=sorted_peps,
    )


@mod.route('/search/')
def search():

    q = request.args.get("q")

    sql = """
    SELECT
        pep.id AS pep_id, pep.number AS pep_number, ts_headline('english', pep.title, query) AS pep_title,
        pep.added AS pep_added, pep.updated AS pep_updated, pep.properties AS
        pep_properties, pep.filename AS pep_filename,
        ts_rank_cd('{0.1, 0.8, 0.9, 1.0}', search_col, query) AS rank
    FROM pep, plainto_tsquery(:q) query
    WHERE query @@ search_col
    ORDER BY rank DESC;
    """

    results = Pep.query.session.query(Pep).from_statement(sql).params(q=q).all()

    return render_template('base/search.html',
        term=q,
        peps=results,
    )


@mod.route('/<int:pep_number>/')
@cached(timeout=60 * 60)
def pep_view(pep_number):

    pep = get_or_404(Pep.query.options(undefer('content')), number=pep_number)

    return render_template('base/pep_view.html',
        pep=pep,
    )


@mod.route('/<int:pep_number>.txt')
@cached(timeout=60 * 60)
def pep_view_raw(pep_number):

    pep = get_or_404(Pep.query.options(undefer('raw_content')), number=pep_number)

    return Response(pep.raw_content, mimetype='text/plain')


@mod.route('/sitemap.xml')
@cached(timeout=60 * 60)
def sitemap():
    url_root = request.url_root[:-1]
    pep_ids = [p.id for p in Pep.query.all()]
    xml = render_template('sitemap.xml', url_root=url_root, pep_ids=pep_ids)
    return Response(xml, mimetype='text/xml')
