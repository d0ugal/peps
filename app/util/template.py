from babel.dates import format_datetime
from jinja2 import evalcontextfilter, Markup, escape
import re


def format_datetime_filter(value, format='medium'):
    if format == 'full':
        format = "EEEE, d. MMMM y 'at' HH:mm"
    elif format == 'medium':
        format = "dd.MM.y"
    return format_datetime(value, format)


_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')


@evalcontextfilter
def nl2br(eval_ctx, value):
    result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', '<br>\n')
                          for p in _paragraph_re.split(escape(value)))
    if eval_ctx.autoescape:
        result = Markup(result)
    return result


def rst_to_html(rst_text):
    from docutils.core import publish_string
    return Markup(publish_string(rst_text, writer_name='html'))
