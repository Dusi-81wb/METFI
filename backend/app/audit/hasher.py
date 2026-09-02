"""
Deterministic Canonical Serialization and Cryptographic Hash Chaining for Audit Events.

Strict Non-Negotiable Rules:
1. Serialization must be purely deterministic (sorted keys, compact separators, UTF-8 encoded).
2. The event_hash field is excluded from the serialization payload during its own calculation.
3. Every event hash binds the previous_event_hash, creating an unbroken tamper-evident chain.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from app.domain.audit import AuditEvent


class AuditHasher:
    """
    Computes deterministic SHA-256 hashes and verifies hash chain integrity for audit events.
    """

    @classmethod
    def canonical_serialize(cls, data: dict[str, Any]) -> str:
        """
        Deterministically serialize a dictionary to a canonical JSON string.

        Guarantees:
        - Keys are sorted recursively.
        - Compact formatting with no unnecessary whitespace.
        - Floats and numbers formatted consistently.
        """
        return json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            default=str,
        )

    @classmethod
    def compute_event_hash(
        cls,
        event_dict: dict[str, Any],
        previous_event_hash: str = "GENESIS",
    ) -> str:
        """
        Compute cryptographic SHA-256 hash of an audit event payload bound to previous_event_hash.
        """
        # Create a clean copy excluding any pre-existing event_hash
        data_to_hash = dict(event_dict)
        data_to_hash.pop("event_hash", None)
        data_to_hash["previous_event_hash"] = previous_event_hash

        canonical_json = cls.canonical_serialize(data_to_hash)
        raw_to_hash = f"{previous_event_hash}:{canonical_json}"
        return hashlib.sha256(raw_to_hash.encode("utf-8")).hexdigest()

    @classmethod
    def verify_event_hash(cls, event: AuditEvent) -> bool:
        """
        Verify that an event's event_hash matches the recomputed canonical hash.
        """
        event_dict = event.model_dump(mode="json")
        expected_hash = cls.compute_event_hash(
            event_dict=event_dict,
            previous_event_hash=event.previous_event_hash,
        )
        return event.event_hash == expected_hash
