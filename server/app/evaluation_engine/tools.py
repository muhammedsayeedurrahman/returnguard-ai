"""Tool definitions for the AI Evaluation Engine.

Three tools — kept narrow to prevent prompt injection / unbounded action.
"""
from __future__ import annotations
import json
from typing import Any


POLICY_KB = {
    "damaged": {
        "window_days": 14,
        "evidence_required": ["clear damage photo", "original packaging photo"],
        "denial_reasons": ["photo predates delivery", "damage type contradicts claim text"],
    },
    "wrong_item": {
        "window_days": 14,
        "evidence_required": ["photo of received item with order label"],
        "denial_reasons": ["received product matches order"],
    },
    "not_received": {
        "window_days": 7,
        "evidence_required": ["non-receipt confirmation"],
        "denial_reasons": ["carrier POD shows successful delivery + signature"],
    },
    "receipt_tampered": {
        "window_days": 14,
        "evidence_required": ["original receipt PDF"],
        "denial_reasons": ["receipt amount doesn't match order"],
    },
}


TOOL_SCHEMAS = [
    {
        "name": "request_live_photo",
        "description": "Ask the customer to take a fresh photo right now showing today's date or a newspaper. Use when EXIF or image-text signals fired and you need a verified-time image.",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Polite request message to show the customer."
                }
            },
            "required": ["prompt"],
        },
    },
    {
        "name": "lookup_policy",
        "description": "Look up the retailer's return policy for a given reason code.",
        "parameters": {
            "type": "object",
            "properties": {
                "reason_code": {
                    "type": "string",
                    "enum": ["damaged", "wrong_item", "not_received", "receipt_tampered"],
                }
            },
            "required": ["reason_code"],
        },
    },
    {
        "name": "issue_decision",
        "description": "Final decision on the claim. Always call this at the end of the conversation.",
        "parameters": {
            "type": "object",
            "properties": {
                "verdict": {
                    "type": "string",
                    "enum": ["APPROVE", "REJECT", "ESCALATE"],
                },
                "rationale": {
                    "type": "string",
                    "description": "Plain-language reasoning citing specific evidence.",
                },
            },
            "required": ["verdict", "rationale"],
        },
    },
]


def execute_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    if name == "request_live_photo":
        return {"asked": True, "prompt": args.get("prompt", "Please take a fresh photo.")}
    if name == "lookup_policy":
        code = args.get("reason_code", "")
        return {"policy": POLICY_KB.get(code, {"error": "unknown reason code"})}
    if name == "issue_decision":
        return {
            "decision": args.get("verdict"),
            "rationale": args.get("rationale", ""),
            "terminal": True,
        }
    return {"error": f"unknown tool: {name}"}
