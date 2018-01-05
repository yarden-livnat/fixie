"""Tests request handler object."""
import os
import time
import tempfile

import pytest
import tornado.web
from tornado.httpclient import HTTPError

import fixie.jsonutils as json
from fixie.environ import ENV
from fixie.request_handler import RequestHandler
from fixie.tools import (fetch, verify_user_remote, verify_user_local, flock,
    next_jobid, detached_call, waitpid, register_job_alias, jobids_from_alias,
    jobids_with_name, default_path)
try:
    from fixie_creds.cache import CACHE
    HAVE_CREDS = True
except ImportError:
    HAVE_CREDS = False


skipif_no_creds = pytest.mark.skipif(not HAVE_CREDS,
                                     reason="fixie-creds is not installed.")


class NameObjectRequest(RequestHandler):

    schema = {'name': {'type': 'string'}}

    def post(self):
        name = self.request.arguments['name']
        self.write({'nomen': 'My name is '+ name})


class MockVerifyRequest(RequestHandler):
    """Only will verify if user == token"""

    schema = {'user': {'type': 'string'}, 'token': {'type': 'string'}}

    def post(self):
        if self.request.arguments['user'] == self.request.arguments['token']:
            rtn = {'verified': True, 'message': '', 'status': True}
        else:
            rtn = {'verified': False, 'message': '', 'status': True}
        self.write(rtn)


APP = tornado.web.Application([
    (r"/", NameObjectRequest),
    (r"/verify", MockVerifyRequest),
])


@pytest.fixture
def app():
    return APP


@pytest.mark.gen_test
def test_fetch(http_client, base_url):
    body = {"name": "Inigo Montoya"}
    response = yield fetch(base_url, body)
    assert response == {"nomen": 'My name is Inigo Montoya'}


@pytest.mark.gen_test
def test_verify_user_remote_valid(http_client, base_url):
    valid, msg, status = verify_user_remote("me", "me", base_url)
    assert valid
    assert status


@pytest.mark.gen_test
def test_verify_user_remote_invalid(http_client, base_url):
    valid, msg, status = verify_user_remote("me", "you", base_url)
    assert not valid
    assert status


@skipif_no_creds
def test_verify_user_local(credsdir):
    # some set up
    user = 'grammaticus'
    email = 'john@notaspy.com'
    assert not CACHE.user_exists(user)
    token, flag = CACHE.register(user, email)

    # test valid
    valid, message, status = verify_user_local(user, token)
    assert valid
    assert status

    # test invalid
    valid, message, status = verify_user_local(user, '101010')
    assert not valid
    assert status


def test_flock():
    fname = 'flock-test'
    lock = fname + '.lock'
    if os.path.exists(fname):
        os.remove(fname)
    if os.path.exists(lock):
        os.remove(lock)
    with flock(fname, timeout=10.0) as fd:
        # basic checks
        assert fd != 0
        assert os.path.exists(lock)
        # check that the lock is actually working
        with flock(fname, timeout=0.01, sleepfor=0.001, raise_errors=False) as fe:
            assert fe == 0
            assert os.path.exists(lock)
    assert not os.path.exists(lock)


def test_next_jobid(jobfile):
    assert 0 == next_jobid()
    assert 1 == next_jobid()
    assert 2 == next_jobid()
    with open(jobfile) as f:
        n = f.read()
    n = int(n.strip())
    assert 3 == n


def test_job_aliases(jobaliases):
    register_job_alias(1, 'me', name='some-sim', project='myproj')
    register_job_alias(42, 'me', name='some-sim', project='myproj')
    jids = jobids_from_alias('me', name='some-sim', project='myproj')
    assert jids == {1, 42}
    jids = jobids_from_alias('me', name='bad', project='nope')
    assert jids == set()
    # test from name
    register_job_alias(43, 'you', name='some-sim', project='other')
    jids = jobids_with_name('some-sim')
    assert jids == {1, 42, 43}
    jids = jobids_with_name('bad-name')
    assert jids == set()


def test_detached_call():
    with ENV.swap(FIXIE_DETACHED_CALL='test'), tempfile.NamedTemporaryFile('w+t') as f:
        child_pid = detached_call(['env'], stdout=f)
        status = waitpid(child_pid, timeout=10.0)
        f.seek(0)
        s = f.read()
    assert status
    assert os.getpid() != child_pid
    assert 'FIXIE_DETACHED_CALL=test' in s


@pytest.mark.parametrize('path, name, project, jobid, exp', [
    ('x', '', '', -1, '/x'),
    ('/y', '', '', -1, '/y'),
    ('x/y', '', '', -1, '/x/y'),
    ('/x/y/z', '', '', -1, '/x/y/z'),
    ('', 'sim', '', -1, '/sim.h5'),
    ('', 'sim', 'proj', -1, '/proj/sim.h5'),
    ('', '', 'proj', 42, '/proj/42.h5'),
])
def test_default_path(path, name, project, jobid, exp):
    obs = default_path(path, name=name, project=project, jobid=jobid)
    assert exp == obs
