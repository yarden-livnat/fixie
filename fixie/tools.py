"""Various helper tools for fixie services."""
import os
import time
import errno
import subprocess
import multiprocessing
from contextlib import contextmanager

import tornado.gen
import tornado.ioloop
from tornado.httpclient import AsyncHTTPClient
from lazyasd import lazyobject

from fixie.environ import ENV
from fixie.logger import LOGGER
import fixie.jsonutils as json


@tornado.gen.coroutine
def fetch(url, obj):
    """Asynrochously fetches a fixie URL, using the standard fixie interface
    (POST method, fixie JSON utilties). This fetch functions accepts a Python
    object, rather than a string for its body.
    """
    body = json.encode(obj)
    http_client = AsyncHTTPClient()
    response = yield http_client.fetch(url, method='POST', body=body)
    assert response.code == 200
    rtn = json.decode(response.body)
    return rtn


@lazyobject
def CREDS_CACHE():
    from fixie_creds.cache import CACHE
    return CACHE


def verify_user_local(user, token):
    """Verifies a user via the local (in process) credetialling service."""
    return CREDS_CACHE.verify(user, token)


def verify_user_remote(user, token, base_url):
    """Verifies a user via a remote credentialling service. This runs syncronously."""
    url = base_url + '/verify'
    body = {'user': user, 'token': token}
    rtn = tornado.ioloop.IOLoop.current().run_sync(lambda: fetch(url, body))
    return rtn['verified'], rtn['message'], rtn['status']


def verify_user(user, token, url=None):
    """verifies a user/token pair. This happens either locally (if creds is available)
    or remotely (if $FIXIE_CREDS_URL was provided).
    """
    url = ENV.get('FIXIE_CREDS_URL', '') if url is None else url
    if url:
        return verify_user(user, token, url)
    else:
        return verify_user_local(user, token)


@contextmanager
def flock(filename, timeout=None, sleepfor=0.1, raise_errors=True):
    """A context manager for locking a file via the filesystem.
    This yeilds the file descriptor of the lockfile.
    If raise_errors is False and an exception would have been raised,
    a file descriptor of zero is yielded instead.
    """
    fd = 0
    lockfile = filename + '.lock'
    t0 = time.time()
    while True:
        try:
            fd = os.open(lockfile, os.O_CREAT|os.O_EXCL|os.O_RDWR)
            break
        except OSError as e:
            if e.errno != errno.EEXIST:
                if raise_errors:
                    raise
                else:
                    break
            elif (time.time() - t0) >= timeout:
                if raise_errors:
                    raise TimeoutError(lockfile + " could not be obtained in time.")
                else:
                    break
            time.sleep(sleepfor)
    yield fd
    if fd == 0:
        return
    os.close(fd)
    os.unlink(lockfile)


def next_jobid(timeout=None, sleepfor=0.1, raise_errors=True):
    """Obtains the next jobid from the $FIXIE_JOBID_FILE and increments the
    value in $FIXIE_JOBID_FILE. A None value means that the jobid could not
    be obtained in time.
    """
    f = ENV['FIXIE_JOBID_FILE']
    with flock(f, timeout=timeout, sleepfor=sleepfor, raise_errors=raise_errors) as lockfd:
        if lockfd == 0:
            return
        if os.path.isfile(f):
            with open(f) as fh:
                curr = fh.read()
            curr = int(curr.strip() or 0)
        else:
            curr = 0
        inc = str(curr + 1)
        with open(f, 'w') as fh:
            fh.write(inc)
    return curr


def register_job_alias(jobid, user, name='', project='', timeout=None, sleepfor=0.1,
                      raise_errors=True):
    """Registers a job id, user, name, and project in the global jobs alias cache.
    Returns whether the registration was successful or not.
    """
    f = ENV['FIXIE_JOB_ALIASES_FILE']
    with flock(f, timeout=timeout, sleepfor=sleepfor, raise_errors=raise_errors) as lockfd:
        if lockfd == 0:
            return False
        # obtain the current contents
        if os.path.isfile(f):
            with open(f) as fh:
                s = fh.read()
            if s.strip():
                cache = json.loads(s)
            else:
                cache = {}
        else:
            cache = {}
        # add the entry as approriate
        if user not in cache:
            cache[user] = {}
        u = cache[user]
        if project not in u:
            u[project] = {}
        p = u[project]
        if name not in p:
            p[name] = set()
        p[name].add(jobid)
        # write the file back out
        with open(f, 'w') as fh:
            json.dump(cache, fh)
    return True


def jobids_from_alias(user, name='', project='', timeout=None, sleepfor=0.1,
                    raise_errors=True):
    """Obtains a set of job ids from user, name, and project informnation.
    This looks up information in the the global jobs alias cache.
    Returns a set of jobids.
    """
    f = ENV['FIXIE_JOB_ALIASES_FILE']
    with flock(f, timeout=timeout, sleepfor=sleepfor, raise_errors=raise_errors) as lockfd:
        if lockfd == 0:
            return set()
        # obtain the current contents
        if os.path.isfile(f):
            with open(f) as fh:
                cache = json.load(fh)
        else:
            return set()
        # add the entry as approriate
        if user not in cache:
            return set()
        u = cache[user]
        if project not in u:
            return set()
        p = u[project]
        if name not in p:
            return set()
        return p[name]


def jobids_with_name(name, project='', timeout=None, sleepfor=0.1,
                    raise_errors=True):
    """Obtains a set of job ids across all users and projects
    that has a given name.
    This looks up information in the the global jobs alias cache.
    Returns a set of jobids.
    """
    f = ENV['FIXIE_JOB_ALIASES_FILE']
    with flock(f, timeout=timeout, sleepfor=sleepfor, raise_errors=raise_errors) as lockfd:
        if lockfd == 0:
            return set()
        # obtain the current contents
        if os.path.isfile(f):
            with open(f) as fh:
                cache = json.load(fh)
        else:
            return set()
        # add the entry as approriate
        jobids = set()
        for user in cache.values():
            for project in user.values():
                j = project.get(name, None)
                if j is not None:
                    jobids |= j
    return jobids


def detached_call(args, stdout=None, stderr=None, stdin=None, env=None, **kwargs):
    """Runs a process and detaches it from its parent (i.e. the current process).
    In the parent process, this will return the PID of the child. By default,
    this will return redirect all streams to os.devnull. Additionally, if an
    environment is not provided, the current fixie environment is passed in.
    If close_fds is provided, it must be True.
    All other kwargs are passed through to Popen.

    Inspired by detach.call(), Copyright (c) 2014 Ryan Bourgeois.
    """
    env = ENV.detype() if env is None else env
    stdin = os.open(os.devnull, os.O_RDONLY) if stdin is None else stdin
    stdout = os.open(os.devnull, os.O_WRONLY) if stdout is None else stdout
    stderr = os.open(os.devnull, os.O_WRONLY) if stderr is None else stderr
    if not kwargs.get('close_fds', True):
        raise RuntimeError('close_fds must be True.')
    shared_pid = multiprocessing.Value('i', 0)
    pid = os.fork()
    if pid == 0:
        # in child
        os.setsid()
        proc = subprocess.Popen(args, stdout=stdout, stderr=stderr, stdin=stdin,
                                close_fds=True, env=env)
        shared_pid.value = proc.pid
        os._exit(0)
    else:
        # in parent
        os.waitpid(pid, 0)
        child_pid = shared_pid.value
        del shared_pid
        return child_pid


def waitpid(pid, timeout=None, sleepfor=0.001, raise_errors=True):
    """Waits for a PID, even if if it isn't a child of the current process.
    Returns a boolean flag for whether the waiting was successfull or not.
    """
    rtn = False
    t0 = time.time()
    while True:
        try:
            os.kill(pid, 0)
        except OSError as e:
            if e.errno != errno.EPERM:
                rtn = True
                break
        if timeout is not None and (time.time() - t0) >= timeout:
            if raise_errors:
                raise TimeoutError('wait time for PID exceeded')
            else:
                rtn = False
                break
        time.sleep(sleepfor)
    return rtn
