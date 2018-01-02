"""Various helper tools for fixie services."""
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
