from glob import glob
from re import compile
from requests import get
from tempfile import mkdtemp, NamedTemporaryFile
from zipfile import ZipFile

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


def pep_file_to_metadata(path):

    pep_file = open(path)
    contents = line = pep_file.read().decode('utf-8')
    pep_file.seek(0)
    lines = pep_file.readlines()
    metadata = {}

    for line in (l.strip() for l in lines):

        line = line.decode('utf-8')

        if ':' not in line:
            break

        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip()

        metadata[key] = value

    return path, contents, metadata


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

    results = ((number,) + pep_file_to_metadata(filename) for number, filename in pep_numbers(tmp_dir))

    for number, path, contents, properties in results:

        get_or_create(Pep, number=number, defaults={
            'properties': properties,
            'filename': path.rsplit("/")[-1],
            'content': contents
        })
