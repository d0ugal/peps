#!/usr/bin/env python
"""
This is a tweaked version of the copy found in http://hg.python.org/peps.

Some of the HTML output is changed but the logic remains mostly the same. It
proved easier to update this file than replicate the logic without error.

- Dougal

"""


"""Convert PEPs to (X)HTML - courtesy of /F

Usage: %(PROGRAM)s [options] [<peps> ...]

Options:

-u, --user
    python.org username

-b, --browse
    After generating the HTML, direct your web browser to view it
    (using the Python webbrowser module).  If both -i and -b are
    given, this will browse the on-line HTML; otherwise it will
    browse the local HTML.  If no pep arguments are given, this
    will browse PEP 0.

-i, --install
    After generating the HTML, install it and the plaintext source file
    (.txt) on python.org.  In that case the user's name is used in the scp
    and ssh commands, unless "-u username" is given (in which case, it is
    used instead).  Without -i, -u is ignored.

-l, --local
    Same as -i/--install, except install on the local machine.  Use this
    when logged in to the python.org machine (dinsdale).

-q, --quiet
    Turn off verbose messages.

-h, --help
    Print this help message and exit.

The optional arguments ``peps`` are either pep numbers or .txt files.
"""

import sys
import os
import re
import cgi
import glob
import getopt
import errno
import random
import time

REQUIRES = {'python': '2.2',
            'docutils': '0.2.7'}
PROGRAM = sys.argv[0]
RFCURL = 'http://www.faqs.org/rfcs/rfc%d.html'
PEPURL = '/%d/'
PEPCVSURL = ('http://hg.python.org/peps/file/tip/pep-%04d.txt')
PEPDIRRUL = 'http://www.python.org/peps/'


HOST = "dinsdale.python.org"                    # host for update
HDIR = "/data/ftp.python.org/pub/www.python.org/peps" # target host directory
LOCALVARS = "Local Variables:"

COMMENT = """<!--
This HTML is auto-generated.  DO NOT EDIT THIS FILE!  If you are writing a new
PEP, see http://www.python.org/peps/pep-0001.html for instructions and links
to templates.  DO NOT USE THIS HTML FILE AS YOUR TEMPLATE!
-->"""

# The generated HTML doesn't validate -- you cannot use <hr> and <h3> inside
# <pre> tags.  But if I change that, the result doesn't look very nice...
DTD = ('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN"\n'
       '                      "http://www.w3.org/TR/REC-html40/loose.dtd">')

fixpat = re.compile("((https?|ftp):[-_a-zA-Z0-9/.+~:?#$=&,]+)|(pep-\d+(.txt)?)|"
                    "(RFC[- ]?(?P<rfcnum>\d+))|"
                    "(PEP\s+(?P<pepnum>\d+))|"
                    ".")

EMPTYSTRING = ''
SPACE = ' '
COMMASPACE = ', '



def usage(code, msg=''):
    """Print usage message and exit.  Uses stderr if code != 0."""
    if code == 0:
        out = sys.stdout
    else:
        out = sys.stderr
    print >> out, __doc__ % globals()
    if msg:
        print >> out, msg
    sys.exit(code)



def fixanchor(current, match):
    text = match.group(0)
    link = None
    if (text.startswith('http:') or text.startswith('https:')
        or text.startswith('ftp:')):
        # Strip off trailing punctuation.  Pattern taken from faqwiz.
        ltext = list(text)
        while ltext:
            c = ltext.pop()
            if c not in '();:,.?\'"<>':
                ltext.append(c)
                break
        link = EMPTYSTRING.join(ltext)
    elif text.startswith('pep-') and text <> current:
        link = os.path.splitext(text)[0] + ".html"
    elif text.startswith('PEP'):
        pepnum = int(match.group('pepnum'))
        link = PEPURL % pepnum
    elif text.startswith('RFC'):
        rfcnum = int(match.group('rfcnum'))
        link = RFCURL % rfcnum
    if link:
        return '<a href="%s">%s</a>' % (cgi.escape(link), cgi.escape(text))
    return cgi.escape(match.group(0)) # really slow, but it works...



NON_MASKED_EMAILS = [
    'peps@python.org',
    'python-list@python.org',
    'python-dev@python.org',
    ]

def fixemail(address, pepno):
    if address.lower() in NON_MASKED_EMAILS:
        # return hyperlinked version of email address
        return linkemail(address, pepno)
    else:
        # return masked version of email address
        parts = address.split('@', 1)
        return '%s&#32;&#97;t&#32;%s' % (parts[0], parts[1])


def linkemail(address, pepno):
    parts = address.split('@', 1)
    return ('<a href="mailto:%s&#64;%s?subject=PEP%%20%s">'
            '%s&#32;&#97;t&#32;%s</a>'
            % (parts[0], parts[1], pepno, parts[0], parts[1]))


def fixfile(inpath, input_lines, outfile):
    basename = os.path.basename(inpath)
    infile = iter(input_lines)
    # convert plaintext pep to minimal XHTML markup
    pep = ""

    print >> outfile, '<div class="content">'
    need_pre = 1
    for line in infile:
        if line[0] == '\f':
            continue
        if line.strip() == LOCALVARS:
            break
        if line[0].strip():
            if not need_pre:
                print >> outfile, '</pre>'
            print >> outfile, '<h3>%s</h3>' % line.strip()
            need_pre = 1
        elif not line.strip() and need_pre:
            continue
        else:
            # PEP 0 has some special treatment
            if basename == 'pep-0000.txt':
                parts = line.split()
                if len(parts) > 1 and re.match(r'\s*\d{1,4}', parts[1]):
                    # This is a PEP summary line, which we need to hyperlink
                    url = PEPURL % int(parts[1])
                    if need_pre:
                        print >> outfile, '<pre>'
                        need_pre = 0
                    print >> outfile, re.sub(
                        parts[1],
                        '<a href="%s">%s</a>' % (url, parts[1]),
                        line, 1),
                    continue
                elif parts and '@' in parts[-1]:
                    # This is a pep email address line, so filter it.
                    url = fixemail(parts[-1], pep)
                    if need_pre:
                        print >> outfile, '<pre>'
                        need_pre = 0
                    print >> outfile, re.sub(
                        parts[-1], url, line, 1),
                    continue
            line = fixpat.sub(lambda x, c=inpath: fixanchor(c, x), line)
            if need_pre:
                print >> outfile, '<pre>'
                need_pre = 0
            outfile.write(line)
    if not need_pre:
        print >> outfile, '</pre>'


docutils_settings = None
"""Runtime settings object used by Docutils.  Can be set by the client
application when this module is imported."""

def fix_rst_pep(inpath, input_lines, outfile):
    from docutils import core
    output = core.publish_string(
        source=''.join(input_lines),
        source_path=inpath,
        destination_path=outfile.name,
        reader_name='pep',
        parser_name='restructuredtext',
        writer_name='pep_html',
        settings=docutils_settings,
        # Allow Docutils traceback if there's an exception:
        settings_overrides={'traceback': 1})
    outfile.write(output)


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


def get_input_lines(inpath):
    try:
        infile = open(inpath)
    except IOError, e:
        if e.errno <> errno.ENOENT: raise
        print >> sys.stderr, 'Error: Skipping missing PEP file:', e.filename
        sys.stderr.flush()
        return None
    lines = infile.read().splitlines(1) # handles x-platform line endings
    infile.close()
    return lines


def find_pep(pep_str):
    """Find the .txt file indicated by a cmd line argument"""
    if os.path.exists(pep_str):
        return pep_str
    num = int(pep_str)
    return "pep-%04d.txt" % num

def make_html(inpath, verbose=0):
    input_lines = get_input_lines(inpath)
    if input_lines is None:
        return None
    pep_type = get_pep_type(input_lines)
    if pep_type is None:
        print >> sys.stderr, 'Error: Input file %s is not a PEP.' % inpath
        sys.stdout.flush()
        return None
    elif not PEP_TYPE_DISPATCH.has_key(pep_type):
        print >> sys.stderr, ('Error: Unknown PEP type for input file %s: %s'
                              % (inpath, pep_type))
        sys.stdout.flush()
        return None
    elif PEP_TYPE_DISPATCH[pep_type] == None:
        pep_type_error(inpath, pep_type)
        return None
    outpath = os.path.splitext(inpath)[0] + ".html"
    if verbose:
        print inpath, "(%s)" % pep_type, "->", outpath
        sys.stdout.flush()
    outfile = open(outpath, "w")
    PEP_TYPE_DISPATCH[pep_type](inpath, input_lines, outfile)
    outfile.close()
    os.chmod(outfile.name, 0664)
    return outpath

def push_pep(htmlfiles, txtfiles, username, verbose, local=0):
    quiet = ""
    if local:
        if verbose:
            quiet = "-v"
        target = HDIR
        copy_cmd = "cp"
        chmod_cmd = "chmod"
    else:
        if not verbose:
            quiet = "-q"
        if username:
            username = username + "@"
        target = username + HOST + ":" + HDIR
        copy_cmd = "scp"
        chmod_cmd = "ssh %s%s chmod" % (username, HOST)
    files = htmlfiles[:]
    files.extend(txtfiles)
    files.append("style.css")
    files.append("pep.css")
    filelist = SPACE.join(files)
    rc = os.system("%s %s %s %s" % (copy_cmd, quiet, filelist, target))
    if rc:
        sys.exit(rc)
##    rc = os.system("%s 664 %s/*" % (chmod_cmd, HDIR))
##    if rc:
##        sys.exit(rc)


PEP_TYPE_DISPATCH = {'text/plain': fixfile,
                     'text/x-rst': fix_rst_pep}
PEP_TYPE_MESSAGES = {}

def check_requirements():
    # Check Python:
    try:
        from email.Utils import parseaddr
    except ImportError:
        PEP_TYPE_DISPATCH['text/plain'] = None
        PEP_TYPE_MESSAGES['text/plain'] = (
            'Python %s or better required for "%%(pep_type)s" PEP '
            'processing; %s present (%%(inpath)s).'
            % (REQUIRES['python'], sys.version.split()[0]))
    # Check Docutils:
    try:
        import docutils
    except ImportError:
        PEP_TYPE_DISPATCH['text/x-rst'] = None
        PEP_TYPE_MESSAGES['text/x-rst'] = (
            'Docutils not present for "%(pep_type)s" PEP file %(inpath)s.  '
            'See README.txt for installation.')
    else:
        installed = [int(part) for part in docutils.__version__.split('.')]
        required = [int(part) for part in REQUIRES['docutils'].split('.')]
        if installed < required:
            PEP_TYPE_DISPATCH['text/x-rst'] = None
            PEP_TYPE_MESSAGES['text/x-rst'] = (
                'Docutils must be reinstalled for "%%(pep_type)s" PEP '
                'processing (%%(inpath)s).  Version %s or better required; '
                '%s present.  See README.txt for installation.'
                % (REQUIRES['docutils'], docutils.__version__))

def pep_type_error(inpath, pep_type):
    print >> sys.stderr, 'Error: ' + PEP_TYPE_MESSAGES[pep_type] % locals()
    sys.stdout.flush()


def browse_file(pep):
    import webbrowser
    file = find_pep(pep)
    if file.endswith(".txt"):
        file = file[:-3] + "html"
    file = os.path.abspath(file)
    url = "file:" + file
    webbrowser.open(url)

def browse_remote(pep):
    import webbrowser
    file = find_pep(pep)
    if file.endswith(".txt"):
        file = file[:-3] + "html"
    url = PEPDIRRUL + file
    webbrowser.open(url)


def main(argv=None):
    # defaults
    update = 0
    local = 0
    username = ''
    verbose = 1
    browse = 0

    check_requirements()

    if argv is None:
        argv = sys.argv[1:]

    try:
        opts, args = getopt.getopt(
            argv, 'bilhqu:',
            ['browse', 'install', 'local', 'help', 'quiet', 'user='])
    except getopt.error, msg:
        usage(1, msg)

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage(0)
        elif opt in ('-i', '--install'):
            update = 1
        elif opt in ('-l', '--local'):
            update = 1
            local = 1
        elif opt in ('-u', '--user'):
            username = arg
        elif opt in ('-q', '--quiet'):
            verbose = 0
        elif opt in ('-b', '--browse'):
            browse = 1

    if args:
        peptxt = []
        html = []
        for pep in args:
            file = find_pep(pep)
            peptxt.append(file)
            newfile = make_html(file, verbose=verbose)
            if newfile:
                html.append(newfile)
                if browse and not update:
                    browse_file(pep)
    else:
        # do them all
        peptxt = []
        html = []
        files = glob.glob("pep-*.txt")
        files.sort()
        for file in files:
            peptxt.append(file)
            newfile = make_html(file, verbose=verbose)
            if newfile:
                html.append(newfile)
        if browse and not update:
            browse_file("0")

    if update:
        push_pep(html, peptxt, username, verbose, local=local)
        if browse:
            if args:
                for pep in args:
                    browse_remote(pep)
            else:
                browse_remote("0")



if __name__ == "__main__":
    main()
