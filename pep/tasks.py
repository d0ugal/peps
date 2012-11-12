from requests import get
from zipfile import ZipFile
from tempfile import mkdtemp, NamedTemporaryFile
from re import compile
from glob import glob

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

    lines = open(path).readlines()
    metadata = {}

    for line in (l.strip() for l in lines):

        if ':' not in line:
            break

        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip().lower()

        metadata[key] = value

    metadata['filename'] = path
    yield metadata


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

    return [(number, pep_file_to_metadata(filename)) for number, filename in pep_numbers(tmp_dir)]
