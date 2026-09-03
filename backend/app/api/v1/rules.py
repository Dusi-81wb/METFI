"""
API Router for Microsoft Purview-style Rule Studio.
Enables dynamic user rule configuration, toggling, and testing.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.schemas.rules import (
    CreateRuleRequest,
    CustomRule,
    RuleType,
    ToggleRuleRequest,
)
from app.services.rule_service import RuleService

rules_router = APIRouter(prefix="/rules", tags=["Rule Studio"])


def get_rule_service() -> RuleService:
    """Dependency provider for RuleService."""
    return RuleService.get_instance()


@rules_router.get("", response_model=list[CustomRule])
async def list_rules_endpoint(
    rule_type: RuleType | None = None,
    is_enabled: bool | None = None,
) -> list[CustomRule]:
    """
    List all system-default and user-defined custom rules, sorted by priority.
    """
    service = get_rule_service()
    return service.list_rules(rule_type=rule_type, is_enabled=is_enabled)


@rules_router.post("", response_model=CustomRule, status_code=status.HTTP_201_CREATED)
async def create_rule_endpoint(req: CreateRuleRequest) -> CustomRule:
    """
    Create and activate a new custom classification or policy gating rule.
    """
    service = get_rule_service()
    return service.create_rule(req)


@rules_router.patch("/{rule_id}/toggle", response_model=CustomRule)
async def toggle_rule_endpoint(
    rule_id: str,
    req: ToggleRuleRequest,
) -> CustomRule:
    """
    Enable or disable a specific classification or policy rule.
    """
    service = get_rule_service()
    updated = service.toggle_rule(rule_id=rule_id, is_enabled=req.is_enabled)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule with id '{rule_id}' not found.",
        )
    return updated


@rules_router.delete("/{rule_id}")
async def delete_rule_endpoint(rule_id: str) -> dict[str, Any]:
    """
    Delete a user-defined custom rule. System-default rules cannot be deleted.
    """
    service = get_rule_service()
    rule = service.get_rule(rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule with id '{rule_id}' not found.",
        )
    if rule.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"System rule '{rule_id}' cannot be deleted.",
        )
    service.delete_rule(rule_id)
    return {"status": "DELETED", "rule_id": rule_id}


@rules_router.post("/reset", response_model=list[CustomRule])
async def reset_rules_endpoint() -> list[CustomRule]:
    """
    Reset all rules back to standard corporate system defaults.
    """
    service = get_rule_service()
    service.reset_to_defaults()
    return service.list_rules()
