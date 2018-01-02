"""Tests request handler object."""
import pytest
import tornado.web
from tornado.httpclient import HTTPError

import fixie.jsonutils as json
from fixie.request_handler import RequestHandler
from fixie.tools import fetch, verify_user_remote, verify_user_local
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
