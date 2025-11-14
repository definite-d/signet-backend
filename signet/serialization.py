"""
Compact serialization + Ed25519 signature + zlib compression.
No encryption. Returns raw binary bytes.
Optimized for minimum payload size (QR code compatibility).

Changes:
1. 'amount' (float) is replaced by 'x' (integer kobos/smallest unit).
2. All field keys are minimized (a, t, r, s, n, k, d, o, l).
3. The inner envelope is a CBOR array [msg, sig] instead of a map {"m": msg, "s": sig}.
"""

import math
import zlib
from datetime import datetime, timezone
from typing import Any

import cbor2
from pydantic import BaseModel, Field

from .crypt import (
    get_ed25519_private_key,
    get_ed25519_public_key,
    sign_message,
    verify_signature,
)
from .models import Seal


# ----------------------------
# Compact model (MAXIMAL minimal keys & type optimization)
# ----------------------------
class CSeal(BaseModel):
    # 'x' (amount): Use kobo/smallest unit as integer instead of float. Saves ~4-6 bytes.
    x: int = Field(gt=0)
    t: int  # timestamp (unix seconds)
    r: str  # transaction_reference
    s: str = Field(min_length=10, max_length=10)  # sender_account_number
    n: str  # sender_name
    k: str = Field(min_length=6)  # sender_bank_code
    d: str = Field(min_length=10, max_length=10)  # receiver_account_number
    o: str  # receiver_name
    l: str = Field(min_length=6)  # receiver_bank_code


# ----------------------------
# Helpers
# ----------------------------
def _cbor(obj: Any) -> bytes:
    """Canonical CBOR serialization."""
    return cbor2.dumps(obj, canonical=True)


def _uncbor(b: bytes) -> Any:
    """CBOR deserialization."""
    return cbor2.loads(b)


def seal_to_cseal(seal: Seal) -> CSeal:
    """Converts the verbose Seal model to the compact CSeal model."""
    # Amount conversion: float -> int (multiplied by 100).
    # Using math.floor for predictable conversion or round if desired.
    # round() is generally safer for money:
    amount_in_smallest_unit = int(round(seal.amount * 100))

    return CSeal(
        x=amount_in_smallest_unit,
        t=int(seal.timestamp.timestamp()),
        r=seal.transaction_reference,
        s=seal.sender_account_number,
        n=seal.sender_name,
        k=seal.sender_bank_code,
        d=seal.receiver_account_number,
        o=seal.receiver_name,
        l=seal.receiver_bank_code,
    )


def cseal_to_seal(c: CSeal) -> Seal:
    """Converts the compact CSeal back to the verbose Seal model."""
    # Amount conversion: int -> float (divided by 100)
    amount = c.x / 100.0

    return Seal(
        amount=amount,
        timestamp=datetime.fromtimestamp(c.t, tz=timezone.utc),  # Add timezone back
        transaction_reference=c.r,
        sender_account_number=c.s,
        sender_name=c.n,
        sender_bank_code=c.k,
        receiver_account_number=c.d,
        receiver_name=c.o,
        receiver_bank_code=c.l,
    )


# ----------------------------
# Pack (optimized) -> bytes
# ----------------------------
def pack_seal(seal: Seal) -> bytes:
    """
    Serialize Seal -> CBOR (compact keys/types) -> sign -> envelope CBOR array -> zlib.compress(level=9)
    Returns raw bytes optimized for size.
    """
    # 1. Compact representation -> CBOR (msg)
    cseal = seal_to_cseal(seal)
    # Ensure canonical CBOR for consistent signing
    msg = _cbor(cseal.model_dump())

    # 2. Sign message
    sig = sign_message(get_ed25519_private_key(), msg)  # 64 bytes

    # 3. Minimal inner envelope: CBOR array [msg, sig]. Saves space over a map.
    inner = [msg, sig]
    inner_bytes = _cbor(inner)

    # 4. Compress aggressively
    return zlib.compress(inner_bytes, level=9)


# ----------------------------
# Unpack (optimized) <- bytes
# ----------------------------
def unpack_seal(blob: bytes) -> Seal:
    """
    Accepts raw bytes produced by pack_seal, verifies signature,
    and returns a validated Seal instance.
    """
    # 1. Decompress
    try:
        inner_bytes = zlib.decompress(blob)
    except Exception as e:
        raise ValueError("decompression failed") from e

    # 2. Parse envelope (expects array [msg, sig])
    inner = _uncbor(inner_bytes)
    if not (isinstance(inner, list) and len(inner) == 2):
        raise ValueError("malformed envelope")

    msg, sig = inner

    # 3. Verify signature
    if not verify_signature(get_ed25519_public_key(), msg, sig):
        raise ValueError("signature verification failed")

    # 4. Decode message -> CSeal
    cseal_dict = _uncbor(msg)
    # The keys will be the short keys (x, t, r, s, n, k, d, o, l)
    cseal = CSeal.model_validate(cseal_dict)

    # 5. Convert back to Seal and return
    return cseal_to_seal(cseal)


# ----------------------------
# Example usage
# ----------------------------
if __name__ == "__main__":
    from datetime import datetime as dt

    s = Seal(
        amount=10.51,  # Changed to 2 decimal places to test int conversion
        timestamp=dt.now(timezone.utc),
        transaction_reference="ref1234567890",
        sender_account_number="0123456789",
        sender_name="Alice B. Johnson",
        sender_bank_code="123456",
        receiver_account_number="9876543210",
        receiver_name="Bob A. Smith",
        receiver_bank_code="654321",
    )

    packed = pack_seal(s)
    restored = unpack_seal(packed)

    # Asserting restored amount works with float precision issues (should be close)
    assert math.isclose(restored.amount, s.amount, rel_tol=1e-9)
    assert restored.transaction_reference == s.transaction_reference

    # Check conversion to int kobo was correct
    expected_kobos = int(round(s.amount * 100))
    print(f"Original amount: {s.amount}, Stored as kobos: {expected_kobos}")
    print(f"Restored amount: {restored.amount}")

    print("\n--- Payload Size ---")
    print("Round-trip OK.")
    print(f"Optimized Bytes (zlib L9): {len(packed)} bytes")
