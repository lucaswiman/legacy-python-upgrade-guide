#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import csv
import __builtin__
import sys
from operator import itemgetter

from io import BytesIO


output = BytesIO()


REMOVALS_AND_RENAMES = []


with open('./six-moves.tsv', 'r') as f:  # copy/pasted from https://pythonhosted.org/six/#module-six.moves
    rows = list(csv.DictReader(f, delimiter='\t'))

rows.sort(key=lambda x: x[('Python 2 name')].lower())

def uniquify(rows):
    seen = set()
    uniquified = []
    for row in rows:
        if row['Python 2 name'] in seen:
            continue
        else:
            seen.add(row['Python 2 name'])
        uniquified.append(row)
    return uniquified

# For some reason robotparser is included twice.
rows = uniquify(rows)

output.write('''\
[flake8]
banned-modules =
''')

for row in rows:
    py2 = row['Python 2 name'].strip()
    py3 = row['Python 3 name'].strip()
    six_moves_name = row['Name'].strip()
    if py2.startswith('See '):  # Special cases from urllib 🙄
        continue
    elif py2.startswith('ConfigParser'):  # specially noted two options below
        continue
    import_parts = py2.split('.')
    if import_parts[-1].endswith('()'):
        import_parts[-1] = import_parts[-1].rstrip('()')
        if len(import_parts) == 1:
            # These are never imported since they're in builtins.
            assert import_parts[0] in __builtin__.__dict__, import_parts
            continue
    # Check that it can actually be imported.  This raises ImportError for invalid imports.
    if len(import_parts) > 1:
        exec('from %s import %s' % ('.'.join(import_parts[:-1]), import_parts[-1]))
    else:
        try:
            exec('import %s' % '.'.join(import_parts))
        except ImportError:
            if import_parts[0] == 'gdbm':
                # gdbm doesn't seem to be installed on OS X but is a valid import
                # in some distributions of py2.
                pass
            elif import_parts[0] == '_winreg':
                # Windows only, obvs.
                pass
            else:
                raise
    banned_import = '.'.join(import_parts)
    REMOVALS_AND_RENAMES.append(
        [banned_import, 'six.moves.{six_moves_name}'.format(**locals()), True]
    )


# Manually add moves for urllib/urllib2/urlparse, since they're all over the place.

six_moves_urlparse = [
    # https://pythonhosted.org/six/#module-six.moves.urllib.parse
    'urlparse.ParseResult',
    'urlparse.SplitResult',
    'urlparse.urlparse',
    'urlparse.urlunparse',
    'urlparse.parse_qs',
    'urlparse.parse_qsl',
    'urlparse.urljoin',
    'urlparse.urldefrag',
    'urlparse.urlsplit',
    'urlparse.urlunsplit',
    'urlparse.uses_fragment',
    'urlparse.uses_netloc',
    'urlparse.uses_params',
    'urlparse.uses_query',
    'urlparse.uses_relative',
    'urllib.quote',
    'urllib.quote_plus',
    'urllib.splitquery',  # This was incorrectly put in urlparse in the six docs.
    'urllib.splittag',
    'urllib.splituser',
    'urllib.unquote',
    'urllib.unquote_plus',
    'urllib.urlencode',
]

six_moves_urlerror = [
    # https://pythonhosted.org/six/#module-six.moves.urllib.error
    'urllib.ContentTooShortError',
    'urllib2.URLError',
    'urllib2.HTTPError',
]

six_moves_urlrequest = [
    'urllib.pathname2url',
    'urllib.url2pathname',
    'urllib.getproxies',
    'urllib.urlretrieve',
    'urllib.urlcleanup',
    'urllib.URLopener',
    'urllib.FancyURLopener',
    'urllib.proxy_bypass',
    'urllib2.urlopen',
    'urllib2.install_opener',
    'urllib2.build_opener',
    'urllib2.Request',
    'urllib2.OpenerDirector',
    'urllib2.HTTPDefaultErrorHandler',
    'urllib2.HTTPRedirectHandler',
    'urllib2.HTTPCookieProcessor',
    'urllib2.ProxyHandler',
    'urllib2.BaseHandler',
    'urllib2.HTTPPasswordMgr',
    'urllib2.HTTPPasswordMgrWithDefaultRealm',
    'urllib2.AbstractBasicAuthHandler',
    'urllib2.HTTPBasicAuthHandler',
    'urllib2.ProxyBasicAuthHandler',
    'urllib2.AbstractDigestAuthHandler',
    'urllib2.HTTPDigestAuthHandler',
    'urllib2.ProxyDigestAuthHandler',
    'urllib2.HTTPHandler',
    'urllib2.HTTPSHandler',
    'urllib2.FileHandler',
    'urllib2.FTPHandler',
    'urllib2.CacheFTPHandler',
    'urllib2.UnknownHandler',
    'urllib2.HTTPErrorProcessor',
]

six_moves_urlresponse = [
    'urllib.addbase',
    'urllib.addclosehook',
    'urllib.addinfo',
    'urllib.addinfourl',
]

urllib_moves = [
    ['six.moves.urllib.parse', six_moves_urlparse],
    ['six.moves.urllib.error', six_moves_urlerror],
    ['six.moves.urllib.request', six_moves_urlrequest],
]


for six_module, moves in urllib_moves:
    for moved_from in moves:
        name = moved_from.split('.')[-1]
        exec('from {module} import {name}'.format(module=''.join(moved_from.split('.')[:-1]), name=name))  # Verify the original move actually exists
        exec('from {six_module} import {name}'.format(**locals()))  # Verify the import can be executed.
        moved_to = '{six_module}.{name}'.format(**locals())
        REMOVALS_AND_RENAMES.append([moved_from, moved_to, True])


# Now add the urllib2 and urlparse deprecations
REMOVALS_AND_RENAMES.extend([
    ['urllib2', 'six.moves.urllib'],
    ['urlparse', 'six.moves.parse'],
])

# Modules from PEP 3108: https://www.python.org/dev/peps/pep-3108/

REMOVALS_AND_RENAMES.extend([
    # https://www.python.org/dev/peps/pep-3108/#previously-deprecated-done
    'cfmfile',
        # Documented as deprecated since Python 2.4 without an explicit reason.
    'cl',
        # Documented as obsolete since Python 2.0 or earlier.
        # Interface to SGI hardware.
    ['mimetools', 'email'],
        # Documented as obsolete in a previous version.
        # Supplanted by the email package.
    ['MimeWriter', 'email'],
        # Supplanted by the email package.
    ['mimify', 'email'],
        # Supplanted by the email package.
    ['multifile', 'email'],
        # Supplanted by the email package.
    ['posixfile', 'fcntl.lockf'],
        # Locking is better done by fcntl.lockf() .
    ['rfc822', 'email'],
        # Supplanted by the email package.
    ['sha.new', 'hashlib.sha1', True],
    ['sha.sha', 'hashlib.sha1', True],
    ['sha', 'hashlib'],
        # Supplanted by the hashlib package.
    ['md5', 'hashlib', True],
    ['md5.md5', 'hashlib.md5', True],
    ['md5.new', 'hashlib.md5', True],
        # Supplanted by the hashlib module.
    'sv',
        # Documented as obsolete since Python 2.0 or earlier.
        # Interface to obsolete SGI Indigo hardware.
    ['timing', 'time.clock'],
        # Documented as obsolete since Python 2.0 or earlier.
        # time.clock() gives better time resolution.

    # Skip "platform specific modules". I'm sure NO ONE is using these anymore.

    # https://www.python.org/dev/peps/pep-3108/#hardly-used-done
    'audiodev',
        # Undocumented.
        # Not edited in five years.
    'imputil',
        # Undocumented.
        # Never updated to support absolute imports.
    'mutex',
        # Easy to implement using a semaphore and a queue.
        # Cannot block on a lock attempt.
        # Not uniquely edited since its addition 15 years ago.
        # Only useful with the 'sched' module.
        # Not thread-safe.
    'stringold',
        # Function versions of the methods on string objects.
        # Obsolete since Python 1.6.
        # Any functionality not in the string object or module will be moved to the string module (mostly constants).
    'sunaudio',
        # Undocumented.
        # Not edited in over seven years.
        # The sunau module provides similar abilities.
    'toaiff',
        # Undocumented.
        # Requires sox library to be installed on the system.
    'user',
        # Easily handled by allowing the application specify its own module name, check for existence, and import if found.
    'new',
        # Just a rebinding of names from the 'types' module.
        # Can also call type built-in to get most types easily.
        # Docstring states the module is no longer useful as of revision 27241 (2002-06-15).
    'pure',
        # Written before Pure Atria was bought by Rational which was then bought by IBM (in other words, very old).
    'test.testall',
        # From the days before regrtest.

    # https://www.python.org/dev/peps/pep-3108/#obsolete


    'Bastion',
    'rexec',
        # Restricted execution / security.
        # Turned off in Python 2.3.
        # Modules deemed unsafe.

    ['bsddb185', 'bsddb3'],
        # Superseded by bsddb3
        # Not built by default.
        # Documentation specifies that the "module should never be used directly in new code".
        # Available externally from PyPI [27] .

    'Canvas',
        # Marked as obsolete in a comment by Guido since 2000 (see http://bugs.python.org/issue210677 ).
        # Better to use the Tkinter.Canvas class.

    ['commands', 'subprocess'],
        # subprocess module replaces it [9] .
        # Remove getstatus(), move rest to subprocess.

    ['compiler', 'ast'],
        # Having to maintain both the built-in compiler and the stdlib package is redundant [24] .
        # The AST created by the compiler is available [23] .
        # Mechanism to compile from an AST needs to be added.

    'dircache',
        # Negligible use.
        # Easily replicated.

    ['dl', 'ctypes'],
        # ctypes provides better support for same functionality.

    'fpformat',
        # All functionality is supported by string interpolation.

    ['htmllib', 'six.moves.html_parser'],
        # Superseded by HTMLParser.
        # HTMLParser was moved later on and has a six move, though not an exact replacement.

    'ihooks',
        # Undocumented.
        # For use with rexec which has been turned off since Python 2.3.

    ['imageop', 'PIL/Pillow'],

        # Better support by third-party libraries (Python Imaging Library [17] ).
        #
        # Unit tests relied on rgbimg and imgfile.
        #         rgbimg was removed in Python 2.6.
        #         imgfile slated for removal in this PEP.

    ['linuxaudiodev', 'ossaudiodev'],
        # Replaced by ossaudiodev.

    ['mhlib', 'mailbox'],
        # Should be removed as an individual module; use mailbox instead.

    ['popen2', 'subprocess'],
        # subprocess module replaces it [9] .

    'sgmllib',
        # Does not fully parse SGML.
        # In the stdlib for support to htmllib which is slated for removal.

    ['sre', 're'],
        # Previously deprecated; import re instead.


    ['statvfs', 'os.statvfs'],
        # os.statvfs now returns a tuple with attributes.

    # Handled in six renaming
    # thread [done]
    #     People should use 'threading' instead.
    #         Rename 'thread' to _thread.
    #         Deprecate dummy_thread and rename _dummy_thread.
    #         Move thread.get_ident over to threading.
    #     Guido has previously supported the deprecation [13] .

    # Handled in six renaming
    # urllib [done]
    #     Superseded by urllib2.
    #     Functionality unique to urllib will be kept in the urllib package.
    # ['repr', 'reprlib'],
    # ['cookielib', 'http.cookiejar'],
    # ['httplib', 'http.client'],
    # ['CGIHTTPServer', 'http.server'],
    # ['Cookie', 'http.cookies'],
    # ['Queue', 'queue'],
    # ['copy_reg', 'copyreg'],
    # ['SocketServer', 'socketserver'],
    # ['SimpleHTTPServer', 'http.server'],
    # ['htmlentitydefs', 'html.entities'],
    # ['HTMLParser', 'html.parser'],
    # ['BaseHTTPServer', 'http.server'],

    ['UserDict', 'dict or collections.UserDict/collections.MutableMapping'],
        # Not as useful since types can be a superclass.
        # Useful bits moved to the 'collections' module.
    ['UserDict.UserDictMixin', 'collections.MutableMapping'],

    ['UserList', 'list or collections.UserList/collections.MutableSequence'],

    ['UserString', 'six.text_type, six.binary_type or collections.UserString'],
        # Not useful since types can be a superclass.
        # Moved to the 'collections' module.

    # https://www.python.org/dev/peps/pep-3108/#modules-to-rename
    ['ConfigParser', 'six.moves.configparser', True],

    # These aren't _completely_ compatible, but can be substituted in almost all cases.
    # The only difference is that cStringIO implicitly calls `.encode('ascii')`, while
    # io.BytesIO does not. Both will fail if fed unicode that cannot be directly encoded
    # to ascii.
    ['cStringIO.cStringIO', 'io.BytesIO', True],

    ['cStringIO', 'io', True],
    ['StringIO', 'io.StringIO or io.BytesIO'],

    # These moves are not included in six.moves, though they can be added manually if needed.
    ['cProfile', '_profile (C) or profile (Python)'],
    ['markupbase', '_markupbase'],
    ['test.test_support', 'test.support'],

    ['DocXMLRPCServer', 'six.moves.xmlrpc_server'],  # Missing from six.moves docs
])

REMOVALS_AND_RENAMES.extend([
    # Misc holes not mentioned in the PEP or six docs.
    ['anydbm', 'dbm', True],
    ['string.atof', 'float', True],
    ['string.atoi', 'int', True],
    ['string.atol', 'int', True],
    ['string.letters', 'string.ascii_letters', True],
    ['string.lowercase', 'string.ascii_lowercase', True],
    ['string.uppercase', 'string.ascii_uppercase', True],
    'string.capitalize',
    'string.center',
    'string.count',
    'string.expandtabs',
    'string.find',
    'string.index',
    'string.join',
    'string.joinfields',
    'string.ljust',
    'string.lower',
    'string.lstrip',
    ['string.maketrans', 'bytes.maketrans/bytearray.maketrans or a dict of unicode codepoints to substitutions'],
    'string.replace',
    'string.rfind',
    'string.rindex',
    'string.rjust',
    'string.rsplit',
    'string.rstrip',
    'string.split',
    'string.splitfields',
    'string.strip',
    'string.swapcase',
    'string.translate',
    'string.upper',
    'string.zfill',
    ['contextlib.nested', 'Use the contextlib2.ExitStack backport or the shim in http://stackoverflow.com/a/39158985/303931'],  # Removed in python 3.2
    'time.accept2dyear',  # removed in python 3.3
    ['smtplib.SSLFakeFile', 'socket.socket.makefile'],  # removed in python 3.3

     # Removed in python 3.4
    ['plistlib.readPlist', 'plistlib.load'],
    ['plistlib.writePlist', 'plistlib.dump'],
    ['plistlib.readPlistFromBytes', 'plistlib.loads'],
    ['plistlib.writePlistToBytes', 'plistlib.dumps'],
    'pydoc.Scanner',
    'platform._mac_ver_lookup',
    'platform._mac_ver_gstalt',
    'platform._bcd2str',
    ['tarfile.S_IFDIR', 'stat.S_IFDIR', True],
    ['tarfile.S_IFCHR', 'stat.S_IFCHR', True],
    ['tarfile.S_IFBLK', 'stat.S_IFBLK', True],
    ['tarfile.S_IFLNK', 'stat.S_IFLNK', True],
    ['tarfile.S_IFREG', 'stat.S_IFREG', True],
    ['tarfile.S_IFIFO', 'stat.S_IFIFO', True],

    # removed in python 3.5
    'ftplib.Netrc',

    # Removed in python 3.6
    ['inspect.getmoduleinfo', 'inspect.getmodulename'],
    'asynchat.fifo',

    ['types.IntType', 'six.integer_types', True],
    ['types.TypeType', 'six.class_types', True],
    ['types.BooleanType', 'bool', True],
    'types.UnboundMethodType',
    ['types.StringType', 'six.binary_types or six.text_types depdending on context'],
    ['types.FloatType', 'float', True],
    'types.DictionaryType',
    'types.NotImplementedType',
    'types.DictProxyType',
    ['types.StringTypes', 'six.string_types', True],
    'types.InstanceType',
    'types.SliceType',
    ['types.DictType', 'dict', True],
    'FileType',
    ['EllipsisType', 'type(Ellipsis)', True],
    ['ListType', 'list', True],
    ['TupleType', 'tuple', True],
    'LongType',
    'BufferType',
    'ClassType',
    ['UnicodeType', 'six.text_type', True],
    ['ComplexType', 'complex', True],
    'ObjectType',
    'XRangeType',
    ['NoneType', 'type(None)', True],

])

def sort_key(removal_or_rename):
    return (removal_or_rename[0] if isinstance(removal_or_rename, list) else removal_or_rename).lower()

REMOVALS_AND_RENAMES.sort(key=sort_key)

# Verify we didn't duplicate anything.
assert len(set(map(sort_key, REMOVALS_AND_RENAMES))) == len(REMOVALS_AND_RENAMES)

for removal_or_rename in REMOVALS_AND_RENAMES:
    if isinstance(removal_or_rename, basestring):
        banned_import = removal_or_rename
        output.write('    {banned_import} = {banned_import} is removed in Python 3.\n'.format(**locals()))
    elif len(removal_or_rename) == 2:
        moved_from, moved_to = removal_or_rename
        output.write('    {moved_from} = {moved_from} is moved in Python 3. Use {moved_to} instead\n'.format(**locals()))
    else:
        moved_from, moved_to, exact = removal_or_rename
        assert exact is True
        output.write('    {moved_from} = {moved_from} is moved in Python3. {moved_to} can be used as a drop-in replacement.\n'.format(**locals()))


print output.getvalue()