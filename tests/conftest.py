import os
import shutil
import random
import tempfile

import pytest

from fixie import environ

try:
    from fixie_creds.cache import CACHE
except ImportError:
    CACHE = None


@pytest.fixture
def seed42(request):
    """A fixture that sets the random seed to 42, for consistency"""
    random.seed(42)
    return request


@pytest.fixture
def credsdir(seed42):
    """A fixure that creates a temporary credsdir and assigns it to the cache.
    """
    request = seed42
    name = request.node.name
    credsdir = os.path.join(tempfile.gettempdir(), name)
    if os.path.exists(credsdir):
        shutil.rmtree(credsdir)
    with environ.context():
        orig, CACHE.credsdir = CACHE.credsdir, credsdir
        yield credsdir
        CACHE.credsdir = orig
    shutil.rmtree(credsdir)
