from functools import lru_cache

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from .settings import settings


def generate_keypair() -> tuple[Ed25519PrivateKey, Ed25519PublicKey]:
    """
    Generate an Ed25519 private/public key pair.
    """
    priv = Ed25519PrivateKey.generate()
    pub = priv.public_key()
    return priv, pub


def sign(private_key: Ed25519PrivateKey, message: bytes) -> bytes:
    """
    Sign `message` with `private_key`. Returns signature (64 bytes).
    """
    return private_key.sign(message)


def verify(public_key: Ed25519PublicKey, message: bytes, signature: bytes) -> bool:
    """
    Verify a signature. Returns True if valid, False otherwise.
    """
    try:
        public_key.verify(signature, message)
        return True
    except Exception:
        return False


def private_key_to_pem(
    private_key: Ed25519PrivateKey, password: bytes | None = None
) -> bytes:
    """
    Serialize private key to PEM. If password provided (bytes), the PEM is encrypted.
    """
    if password:
        enc = serialization.BestAvailableEncryption(password)
    else:
        enc = serialization.NoEncryption()

    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=enc,
    )


def public_key_to_pem(public_key: Ed25519PublicKey) -> bytes:
    """
    Serialize public key to PEM (SubjectPublicKeyInfo).
    """
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )


def load_private_key_from_pem(
    pem_data: bytes, password: bytes | None = None
) -> Ed25519PrivateKey:
    """
    Load a private key from PEM. Password should be bytes if the PEM is encrypted.
    """
    return serialization.load_pem_private_key(pem_data, password=password)


def load_public_key_from_pem(pem_data: bytes) -> Ed25519PublicKey:
    """
    Load a public key from PEM.
    """
    return serialization.load_pem_public_key(pem_data)


@lru_cache(1)
def get_private_key() -> Ed25519PrivateKey:
    with settings.PRIVATE_KEY_PEM.open("rb") as f:
        return load_private_key_from_pem(f.read())


@lru_cache(1)
def get_public_key() -> Ed25519PublicKey:
    with settings.PUBLIC_KEY_PEM.open("rb") as f:
        return load_public_key_from_pem(f.read())


if __name__ == "__main__":
    priv, pub = generate_keypair()
    with open("priv.pem", "wb") as f:
        f.write(private_key_to_pem(priv))
    with open("pub.pem", "wb") as f:
        f.write(public_key_to_pem(pub))
