import xonsh.main


if hasattr(xonsh.tools, 'setup'):
    xonsh.tools.setup()
    del xonsh
else:
    import builtins
    # setup xonsh ctx and execer
    builtins.__xonsh_ctx__ = {}
    from xonsh.execer import Execer
    builtins.__xonsh_execer__ = Execer(xonsh_ctx=builtins.__xonsh_ctx__)
    from xonsh.shell import Shell
    builtins.__xonsh_shell__ = Shell(builtins.__xonsh_execer__,
                                     ctx=builtins.__xonsh_ctx__,
                                     shell_type='none')
    builtins.__xonsh_env__['RAISE_SUBPROC_ERROR'] = True
    # setup import hooks
    import xonsh.imphooks
    xonsh.imphooks.install_import_hooks()
    del xonsh, builtins, Execer, Shell


__version__ = '0.0.3'


import fixie.jsonutils as json
from fixie.logger import LOGGER
from fixie.environ import ENV, ENVVARS
from fixie.request_handler import RequestHandler
from fixie.tools import (fetch, verify_user, flock, next_jobid, detached_call,
    waitpid, register_job_alias, jobids_from_alias, jobids_with_name)
