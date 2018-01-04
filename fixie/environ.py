"""Custom environment handling tools for fixie."""
import os
import builtins
import multiprocessing
from contextlib import contextmanager
from collections import OrderedDict
from collections.abc import MutableMapping

from xonsh.environ import Ensurer, VarDocs
from xonsh.tools import (is_string, ensure_string, always_false, always_true, is_bool,
                         is_string_set, csv_to_set, set_to_csv, is_nonstring_seq_of_strings,
                         to_bool, bool_to_str, expand_path, is_int)


ENV = builtins.__xonsh_env__
SERVICES = frozenset(['creds', 'batch'])


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
    """Ensures and returns the $FIXIE_LOGFILE"""
    flf = os.path.join(ENV.get('FIXIE_DATA_DIR'), 'log.json')
    flf = expand_file_and_mkdirs(flf)
    return flf


def fixie_jobs_dir():
    """Ensures and returns the $FIXIE_JOBS_DIR"""
    fjd = os.path.join(ENV.get('FIXIE_DATA_DIR'), 'jobs')
    os.makedirs(fjd, exist_ok=True)
    return fjd


def fixie_jobid_file():
    """Ensures and returns the $FIXIE_JOBID_FILE"""
    fjf = os.path.join(ENV.get('FIXIE_JOBS_DIR'), 'id')
    fjf = expand_file_and_mkdirs(fjf)
    return fjf


def fixie_job_aliases_file():
    """Ensures and returns the $FIXIE_JOB_ALIASES_FILE"""
    fjf = os.path.join(ENV.get('FIXIE_JOBS_DIR'), 'aliases.json')
    fjf = expand_file_and_mkdirs(fjf)
    return fjf


def fixie_sims_dir():
    """Ensures and returns the $FIXIE_SIMS_DIR"""
    fsd = os.path.join(ENV.get('FIXIE_DATA_DIR'), 'sims')
    os.makedirs(fsd, exist_ok=True)
    return fsd


# key = name
# value = (default, validate, convert, detype, docstr)
# this needs to be ordered so that the default are applied in the correct order
ENVVARS = OrderedDict([
    ('FIXIE_CONFIG_DIR', (fixie_config_dir, is_string, str, ensure_string,
                          'Path to fixie configuration directory')),
    ('FIXIE_DATA_DIR', (fixie_data_dir, is_string, str, ensure_string,
                       'Path to fixie data directory')),
    ('FIXIE_JOBS_DIR', (fixie_jobs_dir, is_string, str, ensure_string,
                        'Path to fixie jobs directory')),
    ('FIXIE_JOBID_FILE', (fixie_jobid_file, always_false, expand_file_and_mkdirs, ensure_string,
                          'Path to the fixie job file, which contains the next jobid.')),
    ('FIXIE_JOB_ALIASES_FILE', (fixie_job_aliases_file, always_false,
                                expand_file_and_mkdirs, ensure_string,
                                'Path to the fixie job names file, which contains '
                                'aliases associated with users, projects, and jobids.')),
    ('FIXIE_NJOBS', (multiprocessing.cpu_count(), is_int, int, ensure_string,
                     'Number of jobs allowed in parallel on this server.')),
    ('FIXIE_LOGFILE', (fixie_logfile, always_false, expand_file_and_mkdirs, ensure_string,
                       'Path to the fixie logfile.')),
    ('FIXIE_SIMS_DIR', (fixie_sims_dir, is_string, str, ensure_string,
                        'Path to fixie simulations directory')),
    ])
for service in SERVICES:
    key = 'FIXIE_' + service.upper() + '_URL'
    ENVVARS[key] = ('', is_string, str, ensure_string,
                    'Base URL for ' + service + ' service, default is an empty '
                    'string indicating service is provided locally (if available).')
del service, key


_ENV_SETUP = False


def setup():
    global _ENV_SETUP
    if _ENV_SETUP:
        return
    for key, (default, validate, convert, detype, docstr) in ENVVARS.items():
        if key in ENV:
            del ENV[key]
        ENV._defaults[key] = default() if callable(default) else default
        ENV._ensurers[key] = Ensurer(validate=validate, convert=convert,
                                     detype=detype)
        ENV._docs[key] = VarDocs(docstr=docstr)
    _ENV_SETUP = True


def teardown():
    global _ENV_SETUP
    if not _ENV_SETUP:
        return
    for key in ENVVARS:
        ENV._defaults.pop(key)
        ENV._ensurers.pop(key)
        ENV._docs.pop(key)
        if key in ENV:
            del ENV[key]
    _ENV_SETUP = False


@contextmanager
def context():
    """A context manager for entering and leaving the fixie environment
    safely. This context manager is reentrant and will only be executed
    if it hasn't already been entered.
    """
    global _ENV_SETUP
    if _ENV_SETUP:
        yield
        return
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
