from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

from app.repositories.rule_repository import (
    create_rule,
    get_all_rules,
    get_rule_by_id,
    update_rule,
    delete_rule
)
from app.core.security import verify_api_key


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/rules",
    tags=["Rules"],
    dependencies=[Depends(verify_api_key)]
)


# ============================================================
# REQUEST MODEL
# ============================================================

class RuleCreate(BaseModel):

    id: str = Field(
        ...,
        min_length=1
    )

    name: str

    enabled: bool = True

    mode: str = "CONDITIONAL"

    priority: int = 0

    conditions: Dict[str, Any] = {}

    actions: Dict[str, Any] = {}


# ============================================================
# UPDATE MODEL
# ============================================================

class RuleUpdate(BaseModel):

    name: Optional[str] = None

    enabled: Optional[bool] = None

    mode: Optional[str] = None

    priority: Optional[int] = None

    conditions: Optional[Dict[str, Any]] = None

    actions: Optional[Dict[str, Any]] = None


# ============================================================
# CREATE RULE
# ============================================================

@router.post("")
def create_new_rule(rule: RuleCreate):

    existing_rule = get_rule_by_id(
        rule.id
    )

    if existing_rule:

        raise HTTPException(
            status_code=409,
            detail="Rule already exists"
        )

    try:

        created_rule = create_rule(
            rule.model_dump()
        )

        return {
            "success": True,
            "rule": created_rule
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# GET ALL RULES
# ============================================================

@router.get("")
def get_rules():

    try:

        rules = get_all_rules()

        return {
            "success": True,
            "count": len(rules),
            "rules": rules
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# GET RULE BY ID
# ============================================================

@router.get("/{rule_id}")
def get_rule(rule_id: str):

    rule = get_rule_by_id(
        rule_id
    )

    if rule is None:

        raise HTTPException(
            status_code=404,
            detail="Rule not found"
        )

    return {
        "success": True,
        "rule": rule
    }


# ============================================================
# UPDATE RULE
# ============================================================

@router.put("/{rule_id}")
def update_existing_rule(
    rule_id: str,
    rule: RuleUpdate
):

    existing_rule = get_rule_by_id(
        rule_id
    )

    if existing_rule is None:

        raise HTTPException(
            status_code=404,
            detail="Rule not found"
        )

    updated_rule = {
        "name": (
            rule.name
            if rule.name is not None
            else existing_rule["name"]
        ),

        "enabled": (
            rule.enabled
            if rule.enabled is not None
            else existing_rule["enabled"]
        ),

        "mode": (
            rule.mode
            if rule.mode is not None
            else existing_rule["mode"]
        ),

        "priority": (
            rule.priority
            if rule.priority is not None
            else existing_rule["priority"]
        ),

        "conditions": (
            rule.conditions
            if rule.conditions is not None
            else existing_rule["conditions"]
        ),

        "actions": (
            rule.actions
            if rule.actions is not None
            else existing_rule["actions"]
        )
    }

    try:

        result = update_rule(
            rule_id,
            updated_rule
        )

        return {
            "success": True,
            "rule": result
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# DELETE RULE
# ============================================================

@router.delete("/{rule_id}")
def remove_rule(rule_id: str):

    existing_rule = get_rule_by_id(
        rule_id
    )

    if existing_rule is None:

        raise HTTPException(
            status_code=404,
            detail="Rule not found"
        )

    try:

        deleted = delete_rule(
            rule_id
        )

        return {
            "success": deleted,
            "message": "Rule deleted successfully"
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
