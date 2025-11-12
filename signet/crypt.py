from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives import serialization
from typing import Tuple, Optional


def generate_keypair() -> Tuple[Ed25519PrivateKey, Ed25519PublicKey]:
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
    private_key: Ed25519PrivateKey, password: Optional[bytes] = None
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
    pem_data: bytes, password: Optional[bytes] = None
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


# Example usage (run as script or import functions)
if __name__ == "__main__":
    msg = b"bootstrap asymmetric signature test"

    # generate
    priv, pub = generate_keypair()

    # sign
    sig = sign(priv, msg)
    print("Signature length:", len(sig))

    # verify
    ok = verify(pub, msg, sig)
    print("Verification passed:", ok)

    # serialize
    priv_pem = private_key_to_pem(priv, password=b"strong-password")  # or None
    pub_pem = public_key_to_pem(pub)

    # write to disk
    with open("ed25519_priv.pem", "wb") as f:
        f.write(priv_pem)
    with open("ed25519_pub.pem", "wb") as f:
        f.write(pub_pem)

    # load back
    loaded_priv = load_private_key_from_pem(priv_pem, password=b"strong-password")
    loaded_pub = load_public_key_from_pem(pub_pem)

    # sanity verify loaded keys
    assert verify(loaded_pub, msg, sign(loaded_priv, msg))
    print("Round-trip PEM load OK")
