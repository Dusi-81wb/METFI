"""
Unit tests for secret redaction and ground-truth isolation in audit payloads.
"""

from app.audit.sanitizer import AuditSanitizer


def test_secret_string_masking() -> None:
    raw_text = (
        "Calling model with API Key sk-abcdef1234567890abcdef123456 "
        "and token Bearer my_jwt_token_123456789."
    )
    masked = AuditSanitizer.mask_string(raw_text)

    assert "sk-abcdef" not in masked
    assert "Bearer my_jwt" not in masked
    assert "[REDACTED_SECRET]" in masked


def test_sensitive_dictionary_keys_redacted() -> None:
    payload = {
        "user": "finance_controller",
        "api_key": "some_actual_secret_key_12345",
        "nested": {
            "password": "my_super_secure_password",
            "auth_token": "token_xyz987654321",
            "safe_field": "public_data_value",
        },
    }
    sanitized = AuditSanitizer.sanitize_payload(payload)

    assert sanitized["user"] == "finance_controller"
    assert sanitized["api_key"] == "[REDACTED_SECRET]"
    assert sanitized["nested"]["password"] == "[REDACTED_SECRET]"
    assert sanitized["nested"]["auth_token"] == "[REDACTED_SECRET]"
    assert sanitized["nested"]["safe_field"] == "public_data_value"


def test_ground_truth_isolation_strips_synthetic_labels() -> None:
    payload = {
        "case_id": "case_101",
        "ground_truth": {"expected_exception": "AMOUNT_MISMATCH"},
        "expected_classification": "AMOUNT_MISMATCH",
        "corruption_manifest": {"type": "FEE_DISCREPANCY", "amount": 10.0},
        "generator_seed": 42,
        "legitimate_order_id": "ORD-1234",
    }
    sanitized = AuditSanitizer.sanitize_payload(payload)

    assert "ground_truth" not in sanitized
    assert "expected_classification" not in sanitized
    assert "corruption_manifest" not in sanitized
    assert "generator_seed" not in sanitized
    assert sanitized["case_id"] == "case_101"
    assert sanitized["legitimate_order_id"] == "ORD-1234"
