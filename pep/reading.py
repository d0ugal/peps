from datetime import date

from dateutil import rrule

from pep.models import Pep

# Totally arbitrary date. We just need a starting point to count the number
# of passed days from. Also THE BEGINNING OF TIME sounds cool - just make sure
# you say it in a booming voice.
THE_BEGINNING_OF_TIME = date(2013, 1, 1)


def passed_days():
    today = date.today()
    return (today - THE_BEGINNING_OF_TIME).days


def passed_weeks():
    return passed_days() / 7


def passed_weekdays():

    today = date.today()

    # Use dateutils ruleset to count the number of working days (we are
    # definging that as mon-fri) between two dates.
    dates = rrule.rruleset()
    dates.rrule(rrule.rrule(rrule.DAILY, dtstart=THE_BEGINNING_OF_TIME, until=today))
    dates.exrule(rrule.rrule(rrule.DAILY, byweekday=(rrule.SA, rrule.SU), dtstart=THE_BEGINNING_OF_TIME))
    #This is includive of start and end dates - so to normalise and make it
    # the same as the daily calcs, remove one.
    passed_weekdays = dates.count() - 1

    return passed_weekdays


def get_reading_list(metric, count):

    total = Pep.query.count()

    # If the metric is bigger than the number of peps, we want the remainder
    # and we can go back to the start with that.
    metric = metric % total

    all_peps = Pep.query.order_by(Pep.number.asc()).all()
    peps = all_peps[max(metric - count, 0): metric]

    if metric < count and THE_BEGINNING_OF_TIME.year != date.today().year:
        peps = peps + list(reversed(all_peps[total - (count - metric): total]))

    return peps
