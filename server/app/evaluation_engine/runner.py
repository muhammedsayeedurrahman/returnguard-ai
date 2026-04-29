"""AI Evaluation Engine runner — Gemini function-calling loop.

Replaces the customer-care rep for borderline (35-64) claims.
Hard cap: 4 turns. Always terminates with issue_decision.
"""
from __future__ import annotations
import json
import sqlite3
import uuid
from typing import Any
from ..config import GEMINI_API_KEY, USE_MOCK_GEMINI
from .prompts import SYSTEM_PROMPT, CONTEXT_TEMPLATE
from .tools import TOOL_SCHEMAS, execute_tool, POLICY_KB

MAX_TURNS = 4


def _format_signal_summary(evidence: list[dict]) -> str:
    out = []
    for ev in evidence:
        if ev.get("verdict") in ("FAIL", "WARN"):
            out.append(f"- {ev['signal']}: {ev['verdict']} — {ev['detail']}")
    if not out:
        return "(no high-signal verdicts; behaviour-only borderline)"
    return "\n".join(out)


def open_session(claim_id: str, score: int, conn: sqlite3.Connection) -> str:
    session_id = f"sess_{uuid.uuid4().hex[:8]}"
    conn.execute(
        "INSERT INTO evaluation_sessions (id, claim_id, initial_score) VALUES (?, ?, ?)",
        (session_id, claim_id, score),
    )
    conn.commit()
    return session_id


def _build_initial_context(session_id: str, conn: sqlite3.Connection) -> str:
    sess = conn.execute("SELECT * FROM evaluation_sessions WHERE id = ?", (session_id,)).fetchone()
    if not sess:
        return ""
    claim = conn.execute("SELECT * FROM claims WHERE id = ?", (sess["claim_id"],)).fetchone()
    order = conn.execute("SELECT * FROM orders WHERE id = ?", (claim["order_id"],)).fetchone()
    evidence = conn.execute(
        "SELECT signal_name, verdict, detail FROM claim_evidence WHERE claim_id = ?",
        (sess["claim_id"],),
    ).fetchall()
    ev_list = [{"signal": e["signal_name"], "verdict": e["verdict"], "detail": e["detail"]}
               for e in evidence]
    return CONTEXT_TEMPLATE.format(
        order_id=order["id"],
        product_name=order["product_name"],
        value_inr=order["value_inr"],
        reason_code=claim["reason_code"],
        claim_text=claim["claim_text"] or "(no text provided)",
        signal_summary=_format_signal_summary(ev_list),
        score=sess["initial_score"],
    )


def _mock_turn(session_id: str, customer_message: str, turn_number: int,
               conn: sqlite3.Connection) -> dict[str, Any]:
    """Deterministic mock for the demo when USE_MOCK_GEMINI=true or no API key."""
    sess = conn.execute("SELECT * FROM evaluation_sessions WHERE id = ?", (session_id,)).fetchone()
    claim = conn.execute("SELECT * FROM claims WHERE id = ?", (sess["claim_id"],)).fetchone()
    evidence = conn.execute(
        "SELECT signal_name, verdict, detail FROM claim_evidence WHERE claim_id = ?",
        (sess["claim_id"],),
    ).fetchall()
    has_exif_fail = any(e["signal_name"] == "exif" and e["verdict"] == "FAIL" for e in evidence)

    if turn_number == 1:
        if has_exif_fail:
            msg = ("Hi! Thanks for reaching out about order " + claim["order_id"] +
                   ". To process your refund quickly, could you take a fresh photo right now "
                   "showing the item next to today's date on your phone or a newspaper? "
                   "It helps me approve without needing a 24-hour human review.")
        else:
            msg = ("Hi! Thanks for reaching out about order " + claim["order_id"] +
                   ". Could you tell me a bit more about when you noticed the issue?")
        return {"agent_message": msg, "tool_called": "request_live_photo", "terminal": False}

    if turn_number >= 2:
        if has_exif_fail:
            rationale = ("Photo metadata shows the image was captured before the order "
                         "delivery date, which contradicts the damage claim. Refund denied "
                         "with an option to appeal with a fresh photo.")
            return {
                "agent_message": "Thanks for the response. I'll have a teammate review this within 24 hours.",
                "tool_called": "issue_decision",
                "tool_result": {"decision": "REJECT", "rationale": rationale, "terminal": True},
                "terminal": True,
            }
        return {
            "agent_message": "Thanks! Your refund is approved and will be processed within 24 hours.",
            "tool_called": "issue_decision",
            "tool_result": {"decision": "APPROVE", "rationale": "Customer response consistent with evidence", "terminal": True},
            "terminal": True,
        }
    return {"agent_message": "Let me check.", "tool_called": None, "terminal": False}


def _build_history(session_id: str, conn: sqlite3.Connection) -> list[dict]:
    """Reconstruct chat history from evaluation_turns for Gemini context."""
    rows = conn.execute(
        "SELECT agent_message, customer_response FROM evaluation_turns "
        "WHERE session_id = ? ORDER BY turn_number",
        (session_id,),
    ).fetchall()
    history = []
    for r in rows:
        if r["agent_message"]:
            history.append({"role": "model", "parts": [{"text": r["agent_message"]}]})
        if r["customer_response"]:
            history.append({"role": "user", "parts": [{"text": r["customer_response"]}]})
    return history


def _format_user_message(verdict: str, agent_text: str = "") -> str:
    """Map issue_decision verdict to a customer-facing message that never reveals fraud scoring."""
    if agent_text:
        return agent_text
    if verdict == "APPROVE":
        return "Thanks! Your refund is approved and will be processed within 24 hours."
    if verdict == "REJECT":
        return "Thanks for the information — a teammate will follow up within 24 hours."
    return "I'll escalate this to a human teammate. You'll hear back within 24 hours."


def _gemini_turn(session_id: str, customer_message: str, turn_number: int,
                 conn: sqlite3.Connection) -> dict[str, Any]:
    """Real Gemini function-calling path. Falls back to mock on any error."""
    if not GEMINI_API_KEY or USE_MOCK_GEMINI:
        return _mock_turn(session_id, customer_message, turn_number, conn)

    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)

        # Build system prompt + initial claim context (turn 1 only)
        sys_prompt = SYSTEM_PROMPT
        if turn_number == 1:
            sys_prompt = SYSTEM_PROMPT + "\n\n" + _build_initial_context(session_id, conn)

        history = _build_history(session_id, conn)

        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=sys_prompt,
            tools=[{"function_declarations": TOOL_SCHEMAS}],
        )

        chat = model.start_chat(history=history)
        first_msg = customer_message.strip() if customer_message.strip() else "(begin session)"
        response = chat.send_message(first_msg)

        agent_message = ""
        tool_called: str | None = None
        tool_result: dict | None = None
        terminal = False

        # Up to 2 tool rounds — e.g. lookup_policy first, then issue_decision
        for _ in range(2):
            try:
                parts = response.candidates[0].content.parts
            except (AttributeError, IndexError):
                break

            text_chunks: list[str] = []
            fc = None
            for p in parts:
                if hasattr(p, "function_call") and getattr(p.function_call, "name", ""):
                    fc = p.function_call
                if hasattr(p, "text") and p.text:
                    text_chunks.append(p.text)

            joined_text = "".join(text_chunks).strip()
            if joined_text and not agent_message:
                agent_message = joined_text

            if not fc:
                break

            tool_called = fc.name
            args = {k: v for k, v in fc.args.items()}
            tool_result = execute_tool(tool_called, args)
            terminal = bool(tool_result.get("terminal"))

            if tool_called == "issue_decision":
                agent_message = _format_user_message(
                    tool_result.get("decision", "ESCALATE"), agent_message
                )
                break

            if tool_called == "request_live_photo":
                # Prompt arg becomes the customer-facing message; wait for response.
                agent_message = args.get("prompt") or agent_message or \
                    "Could you take a fresh photo right now showing today's date?"
                break

            # Non-terminal tool (lookup_policy) — feed result back to the model.
            try:
                response = chat.send_message([{
                    "function_response": {
                        "name": tool_called,
                        "response": {"result": json.dumps(tool_result)},
                    }
                }])
            except Exception:
                break

        return {
            "agent_message": agent_message or "Let me look into that for you.",
            "tool_called": tool_called,
            "tool_result": tool_result,
            "terminal": terminal,
        }

    except Exception as e:
        # Any failure → mock fallback. Demo never breaks.
        print(f"[gemini] real path failed: {type(e).__name__}: {e}; falling back to mock")
        return _mock_turn(session_id, customer_message, turn_number, conn)


def take_turn(session_id: str, customer_message: str, photo_path: str | None,
              conn: sqlite3.Connection) -> dict[str, Any]:
    sess = conn.execute("SELECT * FROM evaluation_sessions WHERE id = ?",
                        (session_id,)).fetchone()
    if not sess:
        return {"error": "session not found"}
    if sess["outcome"]:
        return {"error": "session already closed", "outcome": sess["outcome"]}

    turn_number = (sess["turn_count"] or 0) + 1
    if turn_number > MAX_TURNS:
        conn.execute(
            "UPDATE evaluation_sessions SET outcome = 'ESCALATE', ended_at = datetime('now'), "
            "final_score = initial_score WHERE id = ?",
            (session_id,),
        )
        conn.commit()
        return {"agent_message": "I'll escalate this to a human teammate. You'll hear back in 24 hours.",
                "terminal": True, "outcome": "ESCALATE"}

    result = _gemini_turn(session_id, customer_message, turn_number, conn)

    conn.execute(
        "INSERT INTO evaluation_turns (session_id, turn_number, agent_message, customer_response, tool_called, tool_result) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (session_id, turn_number, result.get("agent_message", ""), customer_message,
         result.get("tool_called"), json.dumps(result.get("tool_result", {}))),
    )
    conn.execute(
        "UPDATE evaluation_sessions SET turn_count = ? WHERE id = ?",
        (turn_number, session_id),
    )

    if result.get("terminal") and result.get("tool_called") == "issue_decision":
        decision = result["tool_result"]["decision"]
        rationale = result["tool_result"]["rationale"]
        conn.execute(
            "UPDATE evaluation_sessions SET outcome = ?, ended_at = datetime('now'), "
            "final_score = initial_score WHERE id = ?",
            (decision, session_id),
        )
        conn.execute(
            "UPDATE claims SET decision = ? WHERE id = ?",
            (decision, sess["claim_id"]),
        )
        result["outcome"] = decision
        result["rationale"] = rationale

    conn.commit()
    return result
