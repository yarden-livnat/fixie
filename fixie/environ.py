"""Custom environment handling tools for fixie."""
import os
import builtins
from contextlib import contextmanager
from collections.abc import MutableMapping

from xonsh.environ import Ensurer, VarDocs
from xonsh.tools import (is_string, ensure_string, always_false, always_true, is_bool,
                         is_string_set, csv_to_set, set_to_csv, is_nonstring_seq_of_strings,
                         to_bool, bool_to_str, expand_path)


ENV = builtins.__xonsh_env__

def csv_to_list(x):
    """Converts a comma separated string to a list of strings."""
    return x.split(',')


def list_to_csv(x):
    """Converts a list of str to a comma-separated string."""
    return ','.join(x)


def is_dict_str_str_or_none(x):
    """Checks if x is a mutable mapping from strings to strings or None"""
    if x is None:
        return True
    elif not isinstance(x, MutableMapping):
        return False
    # now we know we have a mapping, check items.
    for key, value in x.items():
        if not isinstance(key, str) or not isinstance(value, str):
            return False
    return True


def expand_file_and_mkdirs(x):
    """Expands a variable that represents a file, and ensures that the
    directory it lives in actually exists.
    """
    x = os.path.abspath(expand_path(x))
    d = os.path.dirname(x)
    os.makedirs(d, exist_ok=True)
    return x


def expand_and_make_dir(x):
    """Expands a variable that represents a directory, and ensures that the
    directory actually exists.
    """
    x = os.path.abspath(expand_path(x))
    os.makedirs(x, exist_ok=True)
    return x


def fixie_config_dir():
    """Ensures and returns the $FIXIE_CONFIG_DIR"""
    fcd = os.path.expanduser(os.path.join(ENV.get('XDG_CONFIG_HOME'), 'fixie'))
    os.makedirs(fcd, exist_ok=True)
    return fcd


def fixie_data_dir():
    """Ensures and returns the $FIXIE_DATA_DIR"""
    fdd = os.path.expanduser(os.path.join(ENV.get('XDG_DATA_HOME'), 'fixie'))
    os.makedirs(fdd, exist_ok=True)
    return fdd


def fixie_logfile():
    flf = os.path.join(ENV.get('XDG_DATA_HOME'), 'fixie', 'log.json')
    flf = expand_file_and_mkdirs(flf)
    return flf


# key = name
# value = (default, validate, convert, detype, docstr)
ENVVARS = {
    'FIXIE_CONFIG_DIR': (fixie_config_dir, is_string, str, ensure_string,
                         'Path to fixie configuration directory'),
    'FIXIE_DATA_DIR': (fixie_config_dir, is_string, str, ensure_string,
                       'Path to fixie data directory'),
    'FIXIE_LOGFILE': (fixie_logfile, always_false, expand_file_and_mkdirs, ensure_string,
                      'Path to the fixie logfile.')
    }


def setup():
    for key, (default, validate, convert, detype, docstr) in ENVVARS.items():
        if key in ENV:
            del ENV[key]
        ENV._defaults[key] = default() if callable(default) else default
        ENV._ensurers[key] = Ensurer(validate=validate, convert=convert,
                                     detype=detype)
        ENV._docs[key] = VarDocs(docstr=docstr)


def teardown():
    for key in ENVVARS:
        ENV._defaults.pop(key)
        ENV._ensurers.pop(key)
        ENV._docs.pop(key)
        if key in ENV:
            del ENV[key]


@contextmanager
def context():
    """A context manager for entering and leaving the fixie environment
    safely.
    """
    setup()
    yield
    teardown()


def fixie_envvar_names():
    """Returns the fixie environment variable names as a set of str."""
    names = set(ENVVARS.keys())
    return names


def fixie_detype_env():
    """Returns a detyped version of the environment containing only the fixie
    environment variables.
    """
    keep = fixie_envvar_names()
    denv = {k: v for k, v in ENV.detype().items() if k in keep}
    return denv
