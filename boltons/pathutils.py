"""
Functions for working with filesystem paths.

The ``expandpath`` function expands the tilde to $HOME and environment variables
to their values.

The ``augpath`` function creates variants of an existing path without having to
spend multiple lines of code spliting it up and stitching it back together.

The ``shrinkuser`` function replaces your home directory with a tilde.

The ``userhome`` function reports the home directory of the current user of the
operating system.
"""
from __future__ import print_function

from os.path import dirname
from os.path import exists
from os.path import expanduser
from os.path import expandvars
from os.path import join
from os.path import normpath
from os.path import split
from os.path import splitext
import os
import sys


__all__ = [
    'augpath', 'shrinkuser', 'userhome', 'expandpath',
]


def augpath(path, suffix='', prefix='', ext=None, base=None, dpath=None,
            multidot=False):
    """
    Create a new path with a different extension, basename, directory, prefix,
    and/or suffix.

    A prefix is inserted before the basename. A suffix is inserted
    between the basename and the extension. The basename and extension can be
    replaced with a new one. Essentially a path is broken down into components
    (dpath, base, ext), and then recombined as (dpath, prefix, base, suffix,
    ext) after replacing any specified component.

    Args:
        path (PathLike): a path to augment
        suffix (str, default=''): placed between the basename and extension
        prefix (str, default=''): placed in front of the basename
        ext (str, optional): if specified, replaces the extension
        base (str, optional): if specified, replaces the basename without extension
        dpath (PathLike, optional): if specified, replaces the directory
        multidot (bool, default=False): if False, everything after the last dot
            in the basename is the extension. If True, everything after the first
            dot in the basename is the extension.

    Returns:
        PathLike: augmented path

    Example:
        >>> path = 'foo.bar'
        >>> suffix = '_suff'
        >>> prefix = 'pref_'
        >>> ext = '.baz'
        >>> newpath = augpath(path, suffix, prefix, ext=ext, base='bar')
        >>> print('newpath = %s' % (newpath,))
        newpath = pref_bar_suff.baz

    Example:
        >>> augpath('foo.bar')
        'foo.bar'
        >>> augpath('foo.bar', ext='.BAZ')
        'foo.BAZ'
        >>> augpath('foo.bar', suffix='_')
        'foo_.bar'
        >>> augpath('foo.bar', prefix='_')
        '_foo.bar'
        >>> augpath('foo.bar', base='baz')
        'baz.bar'
        >>> augpath('foo.tar.gz', ext='.zip', multidot=True)
        foo.zip
        >>> augpath('foo.tar.gz', ext='.zip', multidot=False)
        foo.tar.zip
        >>> augpath('foo.tar.gz', suffix='_new', multidot=True)
        foo_new.tar.gz
    """
    # Breakup path
    orig_dpath, fname = split(path)
    if multidot:
        # The first dot defines the extension
        parts = fname.split('.', 1)
        orig_base = parts[0]
        orig_ext = '' if len(parts) == 1 else '.' + parts[1]
    else:
        # The last dot defines the extension
        orig_base, orig_ext = splitext(fname)
    # Replace parts with specified augmentations
    if dpath is None:
        dpath = orig_dpath
    if ext is None:
        ext = orig_ext
    if base is None:
        base = orig_base
    # Recombine into new path
    new_fname = ''.join((prefix, base, suffix, ext))
    newpath = join(dpath, new_fname)
    return newpath


def shrinkuser(path, home='~'):
    """
    Inverse of ````os.path.expanduser````

    Args:
        path (PathLike): path in system file structure
        home (str): symbol used to replace the home path. Defaults to '~', but
            you might want to use '$HOME' or '%USERPROFILE%' instead.

    Returns:
        PathLike: path: shortened path replacing the home directory with a tilde

    Example:
        >>> path = expanduser('~')
        >>> assert path != '~'
        >>> assert shrinkuser(path) == '~'
        >>> assert shrinkuser(path + '1') == path + '1'
        >>> assert shrinkuser(path + '/1') == join('~', '1')
        >>> assert shrinkuser(path + '/1', '$HOME') == join('$HOME', '1')
    """
    path = normpath(path)
    userhome_dpath = userhome()
    if path.startswith(userhome_dpath):
        if len(path) == len(userhome_dpath):
            path = home
        elif path[len(userhome_dpath)] == os.path.sep:
            path = home + path[len(userhome_dpath):]
    return path


def expandpath(path):
    """
    Wrapper around expanduser and expandvars.

    Less aggressive than truepath. Only expands environs and tilde. Does not
    change relative paths to absolute paths.

    Args:
        path (PathLike): string representation of a path

    Returns:
        PathLike : expanded path

    Example:
        >>> assert normpath(expandpath('~/foo')) == join(userhome(), 'foo')
        >>> assert expandpath('foo') == 'foo'
    """
    path = expanduser(path)
    path = expandvars(path)
    return path


def userhome(username=None):
    """
    Returns the user's home directory.

    Args:
        username (str, default=None): name of a user on the system. If not
            specified, the current user is inferred.

    Returns:
        PathLike: userhome_dpath: path to the home directory

    Example:
        >>> import getpass
        >>> username = getpass.getuser()
        >>> assert userhome() == expanduser('~')
        >>> assert userhome(username) == expanduser('~')
    """
    if username is None:
        # get home directory for the current user
        if 'HOME' in os.environ:
            userhome_dpath = os.environ['HOME']
        else:  # nocover
            if sys.platform.startswith('win32'):
                # win32 fallback when HOME is not defined
                if 'USERPROFILE' in os.environ:
                    userhome_dpath = os.environ['USERPROFILE']
                elif 'HOMEPATH' in os.environ:
                    drive = os.environ.get('HOMEDRIVE', '')
                    userhome_dpath = join(drive, os.environ['HOMEPATH'])
                else:
                    raise OSError("Cannot determine the user's home directory")
            else:
                # posix fallback when HOME is not defined
                import pwd
                userhome_dpath = pwd.getpwuid(os.getuid()).pw_dir
    else:
        # A specific user directory was requested
        if sys.platform.startswith('win32'):  # nocover
            # get the directory name for the current user
            c_users = dirname(userhome())
            userhome_dpath = join(c_users, username)
            if not exists(userhome_dpath):
                raise KeyError('Unknown user: {}'.format(username))
        else:
            import pwd
            try:
                pwent = pwd.getpwnam(username)
            except KeyError:  # nocover
                raise KeyError('Unknown user: {}'.format(username))
            userhome_dpath = pwent.pw_dir
    return userhome_dpath
