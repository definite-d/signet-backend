from functools import lru_cache

import json
import zlib
import base64
from cryptography.hazmat.primitives.asymmetric import ed25519, rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from pydantic import BaseModel, validate_call

from .settings import settings


# =========================
# Keypair Generation
# =========================


def generate_rsa_keypair(
    key_size: int = 2048,
) -> tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
    """
    Generate an RSA private/public key pair for encryption/decryption.
    """
    priv = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
    )
    return priv, priv.public_key()


def generate_ed25519_keypair() -> tuple[
    ed25519.Ed25519PrivateKey, ed25519.Ed25519PublicKey
]:
    """
    Generate an Ed25519 private/public key pair for signing/verification.
    """
    priv = ed25519.Ed25519PrivateKey.generate()
    return priv, priv.public_key()


# =========================
# RSA Encryption / Decryption
# =========================


def rsa_encrypt(public_key: rsa.RSAPublicKey, data: bytes) -> bytes:
    """
    Encrypt `data` using an RSA public key (OAEP + SHA-256).
    """
    return public_key.encrypt(
        data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )


def rsa_decrypt(private_key: rsa.RSAPrivateKey, ciphertext: bytes) -> bytes:
    """
    Decrypt `ciphertext` using an RSA private key (OAEP + SHA-256).
    """
    return private_key.decrypt(
        ciphertext,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )


# =========================
# Ed25519 Signing / Verification
# =========================


def sign_message(private_key: ed25519.Ed25519PrivateKey, message: bytes) -> bytes:
    """
    Sign `message` with an Ed25519 private key. Returns a 64-byte signature.
    """
    return private_key.sign(message)


def verify_signature(
    public_key: ed25519.Ed25519PublicKey, message: bytes, signature: bytes
) -> bool:
    """
    Verify a signature with an Ed25519 public key.
    Returns True if valid, False otherwise.
    """
    try:
        public_key.verify(signature, message)
        return True
    except Exception:
        return False


# =========================
# Serialization Helpers
# =========================


def private_key_to_pem(private_key, password: bytes | None = None) -> bytes:
    """
    Serialize a private key (RSA or Ed25519) to PEM.
    Encrypts the PEM if `password` is provided.
    """
    enc = (
        serialization.BestAvailableEncryption(password)
        if password
        else serialization.NoEncryption()
    )
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=enc,
    )


def public_key_to_pem(public_key) -> bytes:
    """
    Serialize a public key (RSA or Ed25519) to PEM.
    """
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )


def load_private_key_from_pem(pem_data: bytes, password: bytes | None = None):
    """
    Load a private key (RSA or Ed25519) from PEM.
    """
    return serialization.load_pem_private_key(pem_data, password=password)


def load_public_key_from_pem(pem_data: bytes):
    """
    Load a public key (RSA or Ed25519) from PEM.
    """
    return serialization.load_pem_public_key(pem_data)


# =========================
# Cached Default Keys
# =========================


@lru_cache(1)
def get_rsa_private_key() -> rsa.RSAPrivateKey:
    with settings.RSA_PRIVATE_KEY_PEM.open("rb") as f:
        return load_private_key_from_pem(f.read())


@lru_cache(1)
def get_rsa_public_key() -> rsa.RSAPublicKey:
    """
    Return the cached RSA public key.

    The public key is loaded from the PEM file specified in the settings.

    :return: The cached RSA public key.
    :rtype: rsa.RSAPublicKey
    """
    with settings.RSA_PUBLIC_KEY_PEM.open("rb") as f:
        return load_public_key_from_pem(f.read())


@lru_cache(1)
def get_ed25519_private_key() -> ed25519.Ed25519PrivateKey:
    with settings.ED25519_PRIVATE_KEY_PEM.open("rb") as f:
        return load_private_key_from_pem(f.read())


@lru_cache(1)
def get_ed25519_public_key() -> ed25519.Ed25519PublicKey:
    with settings.ED25519_PUBLIC_KEY_PEM.open("rb") as f:
        return load_public_key_from_pem(f.read())


# =========================
# Secure Serialization
# =========================


@validate_call
def secure_pack(data: dict | BaseModel) -> bytes:
    """
    Sign, encrypt, and encode a dictionary payload.
    """
    # 1. Serialize
    if isinstance(data, dict):
        message = json.dumps(data, separators=(",", ":")).encode()
    else:
        message = data.model_dump_json(by_alias=True).encode()

    # 2. Sign
    sig = sign_message(get_ed25519_private_key(), message)

    # 3. Bundle message + signature
    envelope = json.dumps(
        {
            "msg": base64.b85encode(message).decode(),
            "sig": base64.b85encode(sig).decode(),
        },
        separators=(",", ":"),
    ).encode()

    # 4. Encrypt
    ciphertext = rsa_encrypt(get_rsa_public_key(), envelope)

    # 5. Compress + encode
    return base64.b85encode(zlib.compress(ciphertext))


def secure_unpack(encoded: bytes) -> dict:
    """
    Decode, decrypt, and verify a dictionary payload.
    """
    # 1. Decode + decompress
    ciphertext = zlib.decompress(base64.b85decode(encoded))

    # 2. Decrypt
    envelope = rsa_decrypt(get_rsa_private_key(), ciphertext)

    # 3. Parse envelope
    obj = json.loads(envelope)
    message = base64.b85decode(obj["msg"])
    sig = base64.b85decode(obj["sig"])

    # 4. Verify signature
    if not verify_signature(get_ed25519_public_key(), message, sig):
        raise ValueError("Signature verification failed")

    # 5. Deserialize original dict
    return json.loads(message)


# =========================
# CLI Entrypoint for Key Generation
# =========================

if __name__ == "__main__":
    if any(
        [
            settings.RSA_PRIVATE_KEY_PEM.exists(),
            settings.RSA_PUBLIC_KEY_PEM.exists(),
            settings.ED25519_PRIVATE_KEY_PEM.exists(),
            settings.ED25519_PUBLIC_KEY_PEM.exists(),
        ]
    ):
        print(
            "This operation will overwrite the existing keys.",
            "Are you sure to continue?",
        )
        if input("Type 'yes' to continue: ") != "yes":
            print("Aborted.")
            exit(0)

    rsa_priv, rsa_pub = generate_rsa_keypair()
    ed_priv, ed_pub = generate_ed25519_keypair()

    settings.RSA_PRIVATE_KEY_PEM.write_bytes(private_key_to_pem(rsa_priv))
    settings.RSA_PUBLIC_KEY_PEM.write_bytes(public_key_to_pem(rsa_pub))

    settings.ED25519_PRIVATE_KEY_PEM.write_bytes(private_key_to_pem(ed_priv))
    settings.ED25519_PUBLIC_KEY_PEM.write_bytes(public_key_to_pem(ed_pub))
    print("Generated RSA + Ed25519 keypairs.")
