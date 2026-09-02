"""
Audit Sanitization, Secret Redaction, and Ground-Truth Isolation.

Strict Non-Negotiable Rules:
1. All API keys, passwords, bearer tokens, and credentials must be masked before audit logging.
2. Synthetic ground-truth metadata, generator corruption labels, and expected answers
   must NEVER enter audit events.
"""

from __future__ import annotations

import re
from typing import Any

# Regex patterns matching common secret formats
SECRET_PATTERNS = [
    re.compile(r"sk-[a-zA-Z0-9]{20,}", re.IGNORECASE),
    re.compile(r"AIza[0-9A-Za-z-_]{20,}", re.IGNORECASE),
    re.compile(r"Bearer\s+[a-zA-Z0-9_\-\.]{15,}", re.IGNORECASE),
    re.compile(r"ghp_[a-zA-Z0-9]{36}", re.IGNORECASE),
    re.compile(r"xox[baprs]-[0-9a-zA-Z]{10,}", re.IGNORECASE),
    re.compile(r"basic\s+[a-zA-Z0-9=+/]{15,}", re.IGNORECASE),
]

# Sensitive dictionary keys whose values must always be redacted
SENSITIVE_KEY_NAMES = {
    "password",
    "secret",
    "api_key",
    "apikey",
    "access_token",
    "auth_token",
    "authorization",
    "private_key",
    "client_secret",
    "card_cvv",
    "pin",
}

# Ground truth and synthetic evaluation keys that must be strictly isolated
GROUND_TRUTH_KEYS = {
    "ground_truth",
    "ground_truth_label",
    "ground_truth_classification",
    "expected_classification",
    "expected_result",
    "expected_policy_outcome",
    "corruption_type",
    "corruption_manifest",
    "injected_fault_type",
    "injected_fault",
    "generator_seed",
    "synthetic_label",
    "is_planted_corruption",
    "planted_anomaly",
    "evaluation_target",
}


class AuditSanitizer:
    """
    Sanitizes arbitrary payloads for safe, leak-free persistence in the immutable audit trail.
    """

    @classmethod
    def mask_string(cls, text: str) -> str:
        """Mask sensitive tokens and secret patterns in raw string text."""
        sanitized = text
        for pattern in SECRET_PATTERNS:
            sanitized = pattern.sub("[REDACTED_SECRET]", sanitized)
        return sanitized

    @classmethod
    def sanitize_payload(cls, data: Any) -> Any:
        """
        Recursively redact secrets and strip ground-truth labels from dictionaries and lists.
        """
        if isinstance(data, dict):
            clean_dict: dict[str, Any] = {}
            for k, v in data.items():
                k_lower = str(k).lower()

                # Rule 1: Strip ground truth keys completely
                if k_lower in GROUND_TRUTH_KEYS:
                    continue

                # Rule 2: Mask sensitive key values
                if any(sens in k_lower for sens in SENSITIVE_KEY_NAMES):
                    clean_dict[k] = "[REDACTED_SECRET]"
                else:
                    clean_dict[k] = cls.sanitize_payload(v)
            return clean_dict

        elif isinstance(data, list):
            return [cls.sanitize_payload(item) for item in data]

        elif isinstance(data, str):
            return cls.mask_string(data)

        return data
