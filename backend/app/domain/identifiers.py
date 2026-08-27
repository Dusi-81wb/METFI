"""Deterministic opaque identifier generator for synthetic financial data."""

import hashlib


def generate_opaque_id(prefix: str, seed: int, entity_type: str, idx: int) -> str:
    """
    Generate a deterministic, cryptographically hashed opaque identifier.

    Guarantees:
    - Bitwise reproducible for identical (seed, entity_type, idx).
    - Semantically opaque: does not leak sequential index, corruption class, or seed.
    - Uniform length and format: {prefix}_{12-hex-chars}.

    Example outputs:
    - pay_8f3a9b2c01d4
    - ord_7e21a4f098c3
    - set_9c41d8e25b7a
    - led_1b5a6c3f8e02
    - cust_3e8f190a42bd
    - case_a0f72c1d9b3e
    """
    key = f"metfi:{seed}:{entity_type}:{idx}".encode()
    digest = hashlib.sha256(key).hexdigest()[:12]
    return f"{prefix}_{digest}"
