from datetime import date, datetime
from urlparse import urljoin

from dateutil import rrule
from flask import abort, request, Response
from flask import Blueprint, render_template
from sqlalchemy.orm import undefer
from werkzeug.contrib.atom import AtomFeed

from pep.models import Pep
from pep.tasks import sort_peps
from util.cache import cached

mod = Blueprint('base', __name__)


def make_external(url):
    return urljoin(request.url_root, url)


@mod.route('/')
@cached(timeout=60 * 60)  # 1 hour
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
@cached(timeout=60 * 60)  # 1 hour
def pep_view(pep_number):

    pep = Pep.query.options(undefer('content')
        ).filter_by(number=pep_number).first_or_404()

    return render_template('base/pep_view.html',
        pep=pep,
    )


@mod.route('/<int:pep_number>.txt')
@cached(timeout=60 * 60)  # 1 hour
def pep_view_raw(pep_number):

    pep = Pep.query.options(undefer('raw_content')
            ).filter_by(number=pep_number).first_or_404()

    return Response(pep.raw_content, mimetype='text/plain')


@mod.route('/sitemap.xml')
@cached(timeout=60 * 60)  # 1 hour
def sitemap():
    url_root = request.url_root[:-1]
    pep_ids = [p.id for p in Pep.query.all()]
    xml = render_template('sitemap.xml', url_root=url_root, pep_ids=pep_ids)
    return Response(xml, mimetype='text/xml')


# Totally arbitrary date. We just need a starting point to count the number
# of passed days from. Also THE BEGINNING OF TIME sounds cool - just make sure
# you say it in a booming voice.
THE_BEGINNING_OF_TIME = date(2012, 11, 29)


@mod.route('/pep-a-<interval>.<format>')
@cached(timeout=60 * 60 * 24)  # 1 day
def pep_a_(interval, format):

    today = date.today()
    passed_days = (today - THE_BEGINNING_OF_TIME).days
    passed_weeks = passed_days / 7

    # Use dateutils ruleset to count the number of working days (we are
    # definging that as mon-fri) between two dates.
    dates = rrule.rruleset()
    dates.rrule(rrule.rrule(rrule.DAILY, dtstart=THE_BEGINNING_OF_TIME, until=today))
    dates.exrule(rrule.rrule(rrule.DAILY, byweekday=(rrule.SA, rrule.SU), dtstart=THE_BEGINNING_OF_TIME))
    #This is includive of start and end dates - so to normalise and make it
    # the same as the daily calcs, remove one.
    passed_weekdays = dates.count() - 1

    intervals = {
        'day': passed_days,
        'week': passed_weeks,
        'weekday': passed_weekdays,
    }

    try:
        metric = intervals[interval]
    except KeyError:
        abort(404)

    if format != "rss" and format != "atom":
        abort(404)

    total = Pep.query.count()

    # If the metric is bigger than the number of peps, we want the remainder
    # and we can go back to the start with that.
    metric = metric % total

    all_peps = Pep.query.order_by(Pep.number.asc()).all()
    peps = all_peps[max(metric - 10, 0): metric]

    if metric < 10 and THE_BEGINNING_OF_TIME.year != today.year:
        peps = peps + list(reversed(all_peps[total - (10 - metric): total]))

    title = "Read a PEP a %s" % interval

    if format == "rss":
        return render_template('rss.xml',
            now=datetime.now(),
            title=title,
            posts=peps,
        )

    feed = AtomFeed(title, feed_url=request.url, url=request.url_root)

    for article in peps:
        feed.add(article.title, article.content,
                 content_type='html',
                 author=article.properties['author'],
                 url=make_external(article.url()),
                 updated=article.added,
                 published=article.added)

    return feed.get_response()
