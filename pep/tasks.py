from glob import glob
from re import compile
from requests import get
from tempfile import mkdtemp, NamedTemporaryFile
from zipfile import ZipFile
from docutils.utils import SystemMessage
from docutils import core
from sys import stderr
from cgi import escape

from app import db
from pep.models import Pep
from util.db import get_or_create

zip_url = "http://hg.python.org/peps/archive/tip.zip"


def pep_numbers(base_dir):

    matcher = compile("(\d+)")

    for full_path in glob("%s/peps-*/pep-*.txt" % base_dir):

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

    from pep2html import fixfile
    from StringIO import StringIO

    s = StringIO()

    fixfile("", input_lines, s)

    return s.getvalue().decode("utf-8")


def rst2html(lines):
    input_string = ''.join(lines)
    try:
        parts = core.publish_parts(
            source=input_string,
            source_path="inpath",
            destination_path="outfile.name",
            reader_name='pep',
            parser_name='restructuredtext',
            writer_name='pep_html',
            settings_overrides={'report_level': 'quiet', 'traceback': 1})
    except SystemMessage:
        raise
        return input_string

    # nasty hack in the end here. Sorry, but meh.
    return (parts['body_pre_docinfo'] + parts['fragment']).replace("<hr />", "")


def pep_file_to_metadata(path):

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
                print "BREAK", line
                break
            key, value = line.split(":", 1)
            key = key.strip().lower()
            value = value.strip()

            metadata.append((key, value))
        else:
            key, value = metadata[-1]
            value = value + line
            metadata[-1] = key, value

    pep_type = get_pep_type(lines)

    # If its the plain text, we already have the headers - for rst that
    # doesn't matter and it actually needs the heades.

    if pep_type == 'text/plain':
        contents = text2html(iter_lines)
    elif pep_type == 'text/x-rst':
        contents = rst2html(lines)

    return path, contents, dict(metadata)


def fetch_peps():

    tmp_file = NamedTemporaryFile(delete=False)
    tmp_dir = mkdtemp()

    # Get the remote file and save it. I had some issues loading an in memory
    # zip file for some reason...
    f = get(zip_url)
    tmp_file.write(f.content)

    # Extract the tmp file to a tmp directory.
    z = ZipFile(tmp_file)
    # We trust this zip file, otherwise shouldn't use extractall.
    z.extractall(tmp_dir)

    results = ((number,) + pep_file_to_metadata(filename)
        for number, filename in pep_numbers(tmp_dir))

    for number, path, contents, properties in results:

        pep, created = get_or_create(Pep, commit=False, number=number, defaults={
            'properties': properties,
            'filename': path.rsplit("/")[-1],
            'content': contents
        })

        if not created:
            pep.content = contents
            pep.properties = properties
            db.session.add(pep)

    db.session.commit()
