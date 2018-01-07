"""Test fixie JSON utilities."""

from fixie import jsonutils


def test_set():
    s = {1, 2, 3}
    obs = jsonutils.dumps(s)
    assert '__set__' in obs
    t = jsonutils.loads(obs)
    assert s == t


def test_bytes():
    s = b"some bytes"
    obs = jsonutils.dumps(s)
    assert '__bytes__' in obs
    t = jsonutils.loads(obs)
    assert s == t


