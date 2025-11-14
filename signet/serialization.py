"""
Minimal-size secure pack/unpack for Seal model.

- Uses canonical CBOR for smallest deterministic serialization.
- Signs the serialized Seal with Ed25519.
- Bundles {msg, sig} as a CBOR envelope, zlib-compresses it.
- Encrypts with AES-GCM (random 256-bit key), wraps AES key with RSA-OAEP.
- Final container is CBOR'd and Base85-encoded for safe transport/storage.
"""

import os
import zlib
import base64
from typing import Any

import cbor2
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding

from .crypt import (
    sign_message,
    verify_signature,
    get_ed25519_private_key,
    get_ed25519_public_key,
    get_rsa_public_key,
    get_rsa_private_key,
)
from .models import Seal  # adjust import path as needed


# -----------------------
# Serialization helpers
# -----------------------
def serialize_seal_cbor(seal: Seal) -> bytes:
    """
    Canonical CBOR serialization of Seal (uses aliases).
    Deterministic and compact.
    """
    data = seal.model_dump(by_alias=True)
    # cbor2 canonical=True gives deterministic map ordering and minimal encoding
    return cbor2.dumps(data, canonical=True)


def _cbor_pack(obj: Any) -> bytes:
    """Canonical CBOR dump for arbitrary object (bytes fields preserved)."""
    return cbor2.dumps(obj, canonical=True)


def _cbor_unpack(blob: bytes) -> Any:
    return cbor2.loads(blob)


# -----------------------
# Main pack / unpack
# -----------------------
def pack_seal_minimal(seal: Seal) -> bytes:
    """
    Pack a Seal into a compact, signed, encrypted, encoded blob (bytes).

    Returns Base85-encoded bytes (ASCII).
    """
    # 1. Serialize (CBOR canonical)
    msg = serialize_seal_cbor(seal)  # bytes

    # 2. Sign (Ed25519)
    sig = sign_message(get_ed25519_private_key(), msg)  # 64 bytes

    # 3. Build inner envelope (raw bytes allowed)
    inner_envelope = {"v": 1, "msg": msg, "sig": sig}
    inner_bytes = _cbor_pack(inner_envelope)

    # 4. Compress (zlib) — useful before encryption for size
    compressed = zlib.compress(inner_bytes)

    # 5. Hybrid encrypt: AES-GCM + RSA-OAEP-wrapped key
    aes_key = AESGCM.generate_key(bit_length=256)
    aesgcm = AESGCM(aes_key)
    nonce = os.urandom(12)  # recommended 12 bytes for AES-GCM
    ciphertext = aesgcm.encrypt(nonce, compressed, None)  # auth tag appended inside

    # 6. Wrap AES key with RSA public key
    rsa_pub = get_rsa_public_key()
    wrapped_key = rsa_pub.encrypt(
        aes_key,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )

    # 7. Build outer container and CBOR-encode (canonical)
    outer = {
        "v": 1,
        "wrap": wrapped_key,  # bytes
        "nonce": nonce,  # bytes
        "ct": ciphertext,  # bytes
    }
    outer_bytes = _cbor_pack(outer)

    # 8. Base85 encode (compact ASCII-safe)
    return base64.b85encode(outer_bytes)


def unpack_seal_minimal(encoded_blob: bytes) -> Seal:
    """
    Decode and verify a blob produced by pack_seal_minimal.
    Returns a validated Seal instance or raises on failure.
    """
    # 1. Base85 decode
    outer_bytes = base64.b85decode(encoded_blob)

    # 2. Parse outer CBOR container
    outer = _cbor_unpack(outer_bytes)
    if outer.get("v") != 1:
        raise ValueError("unsupported outer version")

    wrapped_key = outer["wrap"]
    nonce = outer["nonce"]
    ciphertext = outer["ct"]

    # 3. Unwrap AES key with RSA private key
    rsa_priv = get_rsa_private_key()
    aes_key = rsa_priv.decrypt(
        wrapped_key,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )

    # 4. AES-GCM decrypt
    aesgcm = AESGCM(aes_key)
    try:
        compressed = aesgcm.decrypt(nonce, ciphertext, None)
    except Exception as e:
        raise ValueError("decryption/authentication failed") from e

    # 5. Decompress
    inner_bytes = zlib.decompress(compressed)

    # 6. Parse inner envelope
    inner = _cbor_unpack(inner_bytes)
    if inner.get("v") != 1:
        raise ValueError("unsupported inner version")

    msg = inner["msg"]  # serialized Seal CBOR bytes
    sig = inner["sig"]

    # 7. Verify signature
    if not verify_signature(get_ed25519_public_key(), msg, sig):
        raise ValueError("signature verification failed")

    # 8. Deserialize Seal (CBOR -> dict -> model_validate)
    obj = cbor2.loads(
        msg
    )  # gives dict with native types (datetime preserved if present)
    return Seal.model_validate(obj)
