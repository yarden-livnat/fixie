"""Various helper tools for fixie services."""
import os
import time
import errno
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
    """Obtains the next jobid from the $FIXIE_JOBFILE and increments the
    value in $FIXIE_JOBFILE. A None value means that the jobid could not
    be obtained in time.
    """
    f = ENV['FIXIE_JOBFILE']
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
