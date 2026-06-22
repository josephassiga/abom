"""ed25519 signing for ABOM — real detached signatures over canonical JSON.

A signing key lives at ``~/.abom/signing_key.pem`` (override with ``ABOM_KEY``).
The public key and a short key id are embedded in the signature, so verification
is self-contained. In production a Notary / key registry pins the set of trusted
key ids; ``verify_obj(obj, trusted_keys=...)`` enforces that.
"""
from __future__ import annotations

import base64
import hashlib
import logging
import os
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from .audit import canonical_json

log = logging.getLogger("abom.sign")


def default_key_path() -> Path:
    return Path(os.environ.get("ABOM_KEY", str(Path.home() / ".abom" / "signing_key.pem")))


def load_or_create_key(path: Path | None = None) -> Ed25519PrivateKey:
    path = Path(path or default_key_path())
    if path.exists():
        log.debug("loaded signing key from %s", path)
        return serialization.load_pem_private_key(path.read_bytes(), password=None)
    key = Ed25519PrivateKey.generate()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    log.info("generated new ed25519 signing key at %s", path)
    return key


def _pub_b64(pub: Ed25519PublicKey) -> str:
    raw = pub.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return base64.b64encode(raw).decode()


def key_id(pub_b64: str) -> str:
    return hashlib.sha256(base64.b64decode(pub_b64)).hexdigest()[:16]


def sign_obj(obj: dict, key: Ed25519PrivateKey | None = None) -> dict:
    """Return ``obj`` with a detached ed25519 ``signature`` over its canonical form."""
    key = key or load_or_create_key()
    body = {k: v for k, v in obj.items() if k != "signature"}
    sig = key.sign(canonical_json(body).encode("utf-8"))
    pub_b64 = _pub_b64(key.public_key())
    log.debug("signed with key_id=%s", key_id(pub_b64))
    return {
        **obj,
        "signature": {
            "alg": "ed25519",
            "public_key": pub_b64,
            "key_id": key_id(pub_b64),
            "value": base64.b64encode(sig).decode(),
        },
    }


def verify_obj(obj: dict, trusted_keys: set[str] | None = None) -> bool:
    """Verify the embedded ed25519 signature. If ``trusted_keys`` is given, the
    signer's key id must be in it."""
    sig = obj.get("signature") or {}
    if sig.get("alg") != "ed25519":
        log.debug("verify: unsupported or missing signature alg %r", sig.get("alg"))
        return False
    pub_b64, value = sig.get("public_key"), sig.get("value")
    if not pub_b64 or not value:
        log.debug("verify: signature missing public_key or value")
        return False
    if trusted_keys is not None and key_id(pub_b64) not in trusted_keys:
        log.debug("verify: signer key_id %s not in trusted set", key_id(pub_b64))
        return False
    try:
        pub = Ed25519PublicKey.from_public_bytes(base64.b64decode(pub_b64))
        body = {k: v for k, v in obj.items() if k != "signature"}
        pub.verify(base64.b64decode(value), canonical_json(body).encode("utf-8"))
        log.debug("verify: signature OK (key_id=%s)", key_id(pub_b64))
        return True
    except Exception:
        log.debug("verify: signature INVALID (key_id=%s)", key_id(pub_b64))
        return False
