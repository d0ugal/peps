from flask import Blueprint, render_template, redirect
from flask import request, Response
from sqlalchemy.orm import undefer

from pep.models import Pep
from pep.tasks import sort_peps
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
    results = Pep.query.search(q)

    return render_template('base/search.html',
        term=q,
        peps=results,
    )


@mod.route('/<int:pep_number>/')
@cached(timeout=60 * 60)
def pep_view(pep_number):

    pep = Pep.query.options(undefer('content')
        ).filter_by(number=pep_number).first_or_404()

    return render_template('base/pep_view.html',
        pep=pep,
    )


@mod.route('/<int:pep_number>/<file>')
@cached(timeout=60 * 60)
def pep_view_file_redirect(pep_number, file):

    url = "http://www.python.org/dev/peps/pep-%04d/%s" % (pep_number, file)
    return redirect(url)


@mod.route('/<int:pep_number>.txt')
@cached(timeout=60 * 60)
def pep_view_raw(pep_number):

    pep = Pep.query.options(undefer('raw_content')
            ).filter_by(number=pep_number).first_or_404()

    return Response(pep.raw_content, mimetype='text/plain')


@mod.route('/pep-<int:pep_number>/')
@cached(timeout=60 * 60)
def pep_redirect(pep_number):

    return redirect("/%s/" % pep_number, code=301)


@mod.route('/sitemap.xml')
@cached(timeout=60 * 60)
def sitemap():
    url_root = request.url_root[:-1]
    pep_ids = [p.number for p in Pep.query.order_by(Pep.number.asc())]
    xml = render_template('sitemap.xml', url_root=url_root, pep_ids=pep_ids)
    return Response(xml, mimetype='text/xml')


@mod.route('/stats/')
@cached(timeout=60 * 60)
def stats():

    top_authors = """
    SELECT
        unnest(regexp_split_to_array(properties->'author', ',')) as author,
        count(*) as count
    FROM pep
    GROUP BY author
    ORDER BY count desc, author
    LIMIT 10;
    """

    top_words = """
        SELECT word, nentry
        FROM ts_stat('SELECT search_col FROM pep')
        ORDER BY nentry DESC, ndoc DESC, word
        LIMIT 10;
    """

    return render_template('base/stats.html',
        top_authors=Pep.query.session.execute(top_authors).fetchall(),
        top_words=Pep.query.session.execute(top_words).fetchall(),
    )
