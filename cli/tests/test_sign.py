"""Tests for ed25519 signing."""
from abom import sign


def test_sign_verify_roundtrip(tmp_path):
    key = sign.load_or_create_key(tmp_path / "k.pem")
    signed = sign.sign_obj({"hello": "world", "n": 1}, key)
    assert signed["signature"]["alg"] == "ed25519"
    assert signed["signature"]["public_key"]
    assert sign.verify_obj(signed) is True


def test_tamper_breaks_signature(tmp_path):
    key = sign.load_or_create_key(tmp_path / "k.pem")
    signed = sign.sign_obj({"x": 1}, key)
    signed["x"] = 2  # tamper
    assert sign.verify_obj(signed) is False


def test_key_persists(tmp_path):
    p = tmp_path / "k.pem"
    k1 = sign.load_or_create_key(p)
    k2 = sign.load_or_create_key(p)
    assert sign._pub_b64(k1.public_key()) == sign._pub_b64(k2.public_key())


def test_trusted_keys_enforced(tmp_path):
    key = sign.load_or_create_key(tmp_path / "k.pem")
    signed = sign.sign_obj({"x": 1}, key)
    kid = signed["signature"]["key_id"]
    assert sign.verify_obj(signed, trusted_keys={kid}) is True
    assert sign.verify_obj(signed, trusted_keys={"0000000000000000"}) is False
