from datetime import datetime
from docutils import core
from fabric.api import sudo, put, cd, run, get
from fabulaws.ec2 import SmallLucidInstance
from glob import glob
from os import environ
from os.path import dirname, abspath, join
from re import compile, sub, findall, UNICODE
from requests import get as http_get
from tempfile import mkdtemp, NamedTemporaryFile
from zipfile import ZipFile

from app import db
from pep.models import Pep
from util.db import get_or_create

zip_url = "http://hg.python.org/peps/archive/tip.zip"


def pep_numbers(base_dir):
    """
    Given the base directory for an extracted pep repo, yield a 2-tuple of
    pep numbers and full paths to the pep file.
    """

    matcher = compile("(\d+)")

    for full_path in glob("%s/pep-*.txt" % base_dir):

        file_name = full_path.rsplit('/', 1)[-1]
        a = matcher.search(file_name)

        if not a:
            continue

        pep_number = int(a.groups()[0])
        yield (pep_number, full_path)


def get_pep_type(input_lines):
    """
    Return the Content-Type of the input.  "text/plain" is the default.
    Return ``None`` if the input is not a PEP.
    """
    pep_type = None
    for line in input_lines:
        line = line.rstrip().lower()
        if not line:
            # End of the RFC 2822 header (first blank line).
            break
        elif line.startswith('content-type: '):
            pep_type = line.split()[1] or 'text/plain'
            break
        elif line.startswith('pep: '):
            # Default PEP type, used if no explicit content-type specified:
            pep_type = 'text/plain'
    return pep_type


def text2html(input_lines):
    """
    Render a text (non-rst) pep as HTML. This uses all of the original code in
    pep2html.py convertor in the pep repo.
    """

    from pep2html import fixfile
    from StringIO import StringIO

    s = StringIO()

    fixfile("", input_lines, s)

    return s.getvalue().decode("utf-8")


def rst2html(lines):
    """
    Use docutils to render the RST peps.
    """
    input_string = ''.join(lines)

    parts = core.publish_parts(
        source=input_string,
        source_path="inpath",
        destination_path="outfile.name",
        reader_name='pep',
        parser_name='restructuredtext',
        writer_name='pep_html',
        settings_overrides={
            'report_level': 'quiet',
            'traceback': 1,
            'pep_base_url': '/',
            'pep_file_url_template': '%d/'
        })

    # nasty hack in the end here. Sorry, but meh.
    return (parts['body_pre_docinfo'] + parts['fragment']).replace("<hr />", "")

ANGLE_BRACKETS = compile(ur'\<.+\>', UNICODE)
ROUND_BRACKETS = compile(ur'\(([\w\s\-\.]+)\)', UNICODE)


def tidy_author(authors):

    authors = authors.replace(u"(Pfizer, Inc.)", u"")
    cleaned = []

    for author in authors.split(u","):

        author = author.strip()
        author = sub(ANGLE_BRACKETS, u"", author).strip()

        if u"(" in author:
            author = u",".join(findall(ROUND_BRACKETS, author))

        cleaned.append(author.strip())

    return cleaned


def pep_file_to_metadata(path):
    """
    Badly named function that gets all the pep data and returns a tuple with
    its various properties and the rendered HTML.
    """

    pep_file = open(path)
    lines = pep_file.readlines()

    pep_type = get_pep_type(lines)

    iter_lines = iter(lines)

    metadata = []

    for line in iter_lines:

        line = line.decode("utf-8")

        if not line.strip():
            break

        if line[0].strip():
            if ":" not in line:
                break
            key, value = line.split(":", 1)
            key = key.strip().lower()
            value = value.strip()

            if key == "last-modified" or key == "version":
                value = value.replace("$Date: ", "")
                value = value.replace("$Revision: ", "")
                value = value.replace(" $", "")
            metadata.append((key, value))
        else:
            key, value = metadata[-1]
            value = value + line
            metadata[-1] = key, value

    pep_type = get_pep_type(lines)
    metadata = dict(metadata)

    metadata['author'] = u','.join(tidy_author(metadata['author']))

    # If its the plain text, we already have the headers - for rst that
    # doesn't matter and it actually needs the heades.

    if pep_type == 'text/plain':
        contents = text2html(iter_lines)
    elif pep_type == 'text/x-rst':
        contents = rst2html(lines)

    raw = ''.join(lines)

    return path, raw, contents, metadata


def sort_peps(peps):
    """
    Sort PEPs into meta, informational, accepted, open, finished,
    and essentially dead.
    This logic is taken from pep2html.py
    """
    meta = []
    info = []
    accepted = []
    open_ = []
    finished = []
    historical = []
    deferred = []
    dead = []
    for pep in peps:

        status = pep.properties['status']
        type_ = pep.properties['type']
        title = pep.title
        # Order of 'if' statement important.  Key Status values take precedence
        # over Type value, and vice-versa.
        if status == 'Draft':
            open_.append(pep)
        elif status == 'Deferred':
            deferred.append(pep)
        elif type_ == 'Process':
            if status == "Active":
                meta.append(pep)
            elif status in ("Withdrawn", "Rejected"):
                dead.append(pep)
            else:
                historical.append(pep)
        elif status in ('Rejected', 'Withdrawn',
                            'Incomplete', 'Superseded'):
            dead.append(pep)
        elif type_ == 'Informational':
            # Hack until the conflict between the use of "Final"
            # for both API definition PEPs and other (actually
            # obsolete) PEPs is addressed
            if (status == "Active" or
                "Release Schedule" not in title):
                info.append(pep)
            else:
                historical.append(pep)
        elif status in ('Accepted', 'Active'):
            accepted.append(pep)
        elif status == 'Final':
            finished.append(pep)
        else:
            raise Exception("unsorted (%s/%s)" %
                           (type_, status),
                           pep.filename, pep.number)

    return (
        ('Meta-PEPs (PEPs about PEPs or Processes)', meta,),
        ('Other Informational PEPs', info,),
        ('Accepted PEPs (accepted; may not be implemented yet)', accepted,),
        ('Open PEPs (under consideration)', open_,),
        ('Finished PEPs (done, implemented in code repository)', finished,),
        ('Historical Meta-PEPs and Informational PEPs', historical,),
        ('Deferred PEPs', deferred,),
        ('Abandoned, Withdrawn, and Rejected PEPs', dead,),
    )


class OldSmallLucidInstance(SmallLucidInstance):
    run_upgrade = False


def fetch_peps():

    tmp_file = NamedTemporaryFile(delete=False)
    tmp_dir = mkdtemp()

    # Get the remote file and save it. I had some issues loading an in memory
    # zip file for some reason...

    try:

        environ['AWS_ACCESS_KEY_ID'], environ['AWS_SECRET_ACCESS_KEY']

        with OldSmallLucidInstance(terminate=True):

            sudo('apt-get -y -q install mercurial zip')
            run('hg clone http://hg.python.org/peps ~/peps/')
            put(join(dirname(abspath(__file__)), 'hg_config'), '~/.hgrc')
            with cd('~/peps/'):
                # So, Mercurial is annoying me. Half of the time after doing
                # a clean checkout its showin that there are file changes.
                # However, a diff shows nothing - I think its a file
                # permission thing... but anyway, I don't care what it is -
                # so doin a commit fixes it.
                run('hg commit -m "Hackety Hackety Hack!"')
                run('hg update --clean')
                run('hg kwexpand')
            run('zip -q -r ~/peps.zip ./peps/')
            get('~/peps.zip', tmp_file)
            pep_base = join(tmp_dir, 'peps')

    except KeyError:
        print '*' * 80
        print "AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environ vars need to be set."
        print "DEFAULTING TO THE non-mercurial pull method (Revisions and dates will be missing)"
        print '*' * 80
        f = http_get(zip_url)
        tmp_file.write(f.content)
        pep_base = join(tmp_dir, 'peps-*')

    # Extract the tmp file to a tmp directory.
    z = ZipFile(tmp_file)
    # We trust this zip file, otherwise shouldn't use extractall.
    z.extractall(tmp_dir)

    results = ((number,) + pep_file_to_metadata(filename)
        for number, filename in pep_numbers(pep_base))

    for number, path, raw, contents, properties in results:

        print number

        contents = contents.replace("http://www.python.org/dev/peps/pep-", "http://www.peps.io/")
        title = properties.pop('title')
        patterns = ["%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"]

        if properties.get('last-modified'):
            for pattern in patterns:
                try:
                    dt = datetime.strptime(properties.get('last-modified'),  pattern)
                    break
                except ValueError:
                    dt = None

        filename = path.rsplit("/")[-1]

        pep, created = get_or_create(Pep, commit=False, number=number, title=title, defaults={
            'properties': properties,
            'filename': filename,
            'content': contents,
            'raw_content': raw,
        })

        if not created:
            pep.properties = properties
            pep.filename = filename
            pep.content = contents
            pep.raw_content = raw
            if dt:
                pep.updated = dt
            db.session.add(pep)

    db.session.commit()
