"""
Integration tests for Rule Studio API endpoints.
Validates endpoints: GET, POST, PATCH /toggle, DELETE, and POST /reset.
"""

from fastapi.testclient import TestClient

from app.main import app
from app.services.rule_service import RuleService

client = TestClient(app)


def setup_function():
    """Reset rule repository to defaults before each test."""
    RuleService.get_instance().reset_to_defaults()


def test_api_list_rules():
    """GET /api/v1/rules returns standard system rules."""
    resp = client.get("/api/v1/rules")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 3
    assert any(r["rule_id"] == "SYS_RULE_ZERO_TOLERANCE" for r in data)


def test_api_create_custom_rule():
    """POST /api/v1/rules creates custom user rule."""
    payload = {
        "name": "Custom Interchange Ceiling",
        "description": "Custom threshold for card interchange fees.",
        "rule_type": "CLASSIFICATION",
        "condition": {
            "field": "monetary.fee_variance",
            "operator": "<=",
            "value": 45.0,
        },
        "target_classification": "EXACT_MATCH",
        "target_policy_outcome": "AUTO_RECONCILE",
        "priority": 15,
        "is_enabled": True,
    }
    resp = client.post("/api/v1/rules", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Custom Interchange Ceiling"
    assert data["is_system"] is False
    assert "RULE_USER_" in data["rule_id"]


def test_api_toggle_rule():
    """PATCH /api/v1/rules/{id}/toggle toggles enabled state."""
    # Create rule first
    create_resp = client.post(
        "/api/v1/rules",
        json={
            "name": "Toggle Test Rule",
            "description": "Rule to test toggling.",
            "rule_type": "CLASSIFICATION",
            "condition": {
                "field": "timing.hours_to_settlement",
                "operator": "<=",
                "value": 48.0,
            },
        },
    )
    assert create_resp.status_code == 201
    rule_id = create_resp.json()["rule_id"]

    # Toggle off
    toggle_resp = client.patch(
        f"/api/v1/rules/{rule_id}/toggle",
        json={"is_enabled": False},
    )
    assert toggle_resp.status_code == 200
    assert toggle_resp.json()["is_enabled"] is False

    # Toggle on
    toggle_on = client.patch(
        f"/api/v1/rules/{rule_id}/toggle",
        json={"is_enabled": True},
    )
    assert toggle_on.status_code == 200
    assert toggle_on.json()["is_enabled"] is True


def test_api_delete_custom_rule_and_system_protection():
    """DELETE /api/v1/rules/{id} prevents deleting system rules, allows deleting custom rules."""
    # 1. Attempt delete system rule -> 400 Bad Request
    sys_del = client.delete("/api/v1/rules/SYS_RULE_ZERO_TOLERANCE")
    assert sys_del.status_code == 400

    # 2. Create and delete custom rule -> 200 OK
    create_resp = client.post(
        "/api/v1/rules",
        json={
            "name": "Deletable Rule",
            "description": "Rule destined for deletion.",
            "rule_type": "CLASSIFICATION",
            "condition": {
                "field": "monetary.fee_variance",
                "operator": "<=",
                "value": 10.0,
            },
        },
    )
    rule_id = create_resp.json()["rule_id"]

    del_resp = client.delete(f"/api/v1/rules/{rule_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "DELETED"
