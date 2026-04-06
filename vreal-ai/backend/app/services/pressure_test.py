"""
Multi-Model Pressure Testing Service

Sends work through multiple AI models for diverse feedback:
  - Claude (internal, 6-agent review council)
  - ChatGPT (external perspective)
  - Gemini (external perspective)
  - Grok (contrarian perspective)

Each model reviews independently. The best feedback is cherry-picked
and synthesized into a single improvement directive.

This is the "pressure test" — if ALL models agree it's 10/10, it ships.
If any model finds a weakness, it loops back with combined feedback.
"""
from __future__ import annotations

import os
import json
import httpx
from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent.parent / ".env")

# ── API Keys ─────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROK_API_KEY = os.getenv("GROK_API_KEY", "")

# ── Models ───────────────────────────────────────────────────────────────────
CLAUDE_MODEL = "claude-sonnet-4-20250514"
OPENAI_MODEL = "gpt-4o"
GEMINI_MODEL = "gemini-2.0-flash"
GROK_MODEL = "grok-3"


@dataclass
class PressureTestResult:
    """Result from a single model's review."""
    model: str
    score: int
    verdict: str  # "APPROVED" or "REVISION_NEEDED"
    feedback: str
    raw_response: str
    error: Optional[str] = None


@dataclass
class PressureTestSummary:
    """Combined results from all models."""
    passed: bool
    average_score: float
    lowest_score: int
    highest_score: int
    results: list[PressureTestResult]
    synthesized_feedback: str
    unanimous: bool  # All models agreed


PRESSURE_TEST_PROMPT = """You are a world-class quality reviewer for a faceless BBC/Netflix documentary YouTube channel called V-Real AI (@VRealAI).

Channel: AI tools, systems, and transformation. Dark cinematic visuals. Voice: Julian (ElevenLabs). 50% stories, 30% breakdowns, 20% playbooks.

You are reviewing the {stage} output for an episode titled "{title}".

Score on 1-10 scale:
- 10 = Would win an award. Flawless. Would stop you mid-scroll on YouTube.
- 9 = Excellent but one thing prevents perfection.
- 8 = Good but noticeable gaps.
- 7 or below = Not ready.

ONLY 10/10 passes. Be brutally honest.

Respond in EXACTLY this format:
SCORE: [X]/10
VERDICT: [PASS or FAIL]
STRENGTHS: [What works well, 2-3 bullet points]
WEAKNESSES: [What needs improvement, be specific and actionable]
SPECIFIC_FIXES: [Exact changes needed to reach 10/10]

---

{stage} output to review:

{content}
"""

SYNTHESIS_PROMPT = """You are the V-Real AI Quality Synthesis Agent. Multiple AI models just reviewed the same work.

Here are their individual reviews:

{reviews}

Your job:
1. Cherry-pick the BEST feedback from each model (the most specific, actionable insights)
2. Ignore generic or overlapping feedback
3. Combine into ONE clear improvement directive

Respond in this format:
COMBINED SCORE: [average, rounded]/10
UNANIMOUS: [YES if all said PASS, NO if any said FAIL]
CHERRY-PICKED FEEDBACK:
[The best, most specific, most actionable feedback from across all models. No fluff. Just what needs to change.]
"""


async def _call_claude(prompt: str) -> PressureTestResult:
    """Call Claude API for review."""
    if not ANTHROPIC_API_KEY:
        return PressureTestResult(
            model="claude", score=0, verdict="SKIP",
            feedback="", raw_response="", error="ANTHROPIC_API_KEY not set"
        )

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": CLAUDE_MODEL,
                    "max_tokens": 2000,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            data = response.json()
            text = data.get("content", [{}])[0].get("text", "")
            score, verdict, feedback = _parse_review(text)
            return PressureTestResult(
                model="claude", score=score, verdict=verdict,
                feedback=feedback, raw_response=text
            )
    except Exception as e:
        return PressureTestResult(
            model="claude", score=0, verdict="ERROR",
            feedback="", raw_response="", error=str(e)
        )


async def _call_openai(prompt: str) -> PressureTestResult:
    """Call ChatGPT API for review."""
    if not OPENAI_API_KEY:
        return PressureTestResult(
            model="chatgpt", score=0, verdict="SKIP",
            feedback="", raw_response="", error="OPENAI_API_KEY not set — add to .env to enable ChatGPT pressure testing"
        )

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": OPENAI_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 2000,
                },
            )
            data = response.json()
            text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            score, verdict, feedback = _parse_review(text)
            return PressureTestResult(
                model="chatgpt", score=score, verdict=verdict,
                feedback=feedback, raw_response=text
            )
    except Exception as e:
        return PressureTestResult(
            model="chatgpt", score=0, verdict="ERROR",
            feedback="", raw_response="", error=str(e)
        )


async def _call_gemini(prompt: str) -> PressureTestResult:
    """Call Google Gemini API for review."""
    if not GEMINI_API_KEY:
        return PressureTestResult(
            model="gemini", score=0, verdict="SKIP",
            feedback="", raw_response="", error="GEMINI_API_KEY not set — add to .env to enable Gemini pressure testing"
        )

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}",
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"maxOutputTokens": 2000},
                },
            )
            data = response.json()
            text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            score, verdict, feedback = _parse_review(text)
            return PressureTestResult(
                model="gemini", score=score, verdict=verdict,
                feedback=feedback, raw_response=text
            )
    except Exception as e:
        return PressureTestResult(
            model="gemini", score=0, verdict="ERROR",
            feedback="", raw_response="", error=str(e)
        )


async def _call_grok(prompt: str) -> PressureTestResult:
    """Call Grok API for review (xAI)."""
    if not GROK_API_KEY:
        return PressureTestResult(
            model="grok", score=0, verdict="SKIP",
            feedback="", raw_response="", error="GROK_API_KEY not set — add to .env to enable Grok pressure testing"
        )

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                "https://api.x.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROK_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": GROK_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 2000,
                },
            )
            data = response.json()
            text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            score, verdict, feedback = _parse_review(text)
            return PressureTestResult(
                model="grok", score=score, verdict=verdict,
                feedback=feedback, raw_response=text
            )
    except Exception as e:
        return PressureTestResult(
            model="grok", score=0, verdict="ERROR",
            feedback="", raw_response="", error=str(e)
        )


def _parse_review(text: str) -> tuple[int, str, str]:
    """Parse score, verdict, and feedback from any model's review response."""
    import re

    score = 0
    verdict = "FAIL"
    feedback = ""

    # Extract score (handles "SCORE: X/10" and "QUALITY SCORE: X/10")
    score_match = re.search(r"SCORE:\s*(\d+)\s*/\s*10", text)
    if score_match:
        score = int(score_match.group(1))

    # Extract verdict
    if re.search(r"VERDICT:\s*(PASS|APPROVED)", text, re.IGNORECASE):
        verdict = "PASS"
    else:
        verdict = "FAIL"

    # Override: score < 10 always fails
    if score < 10:
        verdict = "FAIL"

    # Extract weaknesses and specific fixes
    parts = []
    if "WEAKNESSES:" in text:
        weak = text.split("WEAKNESSES:")[1]
        if "SPECIFIC_FIXES:" in weak:
            weak = weak.split("SPECIFIC_FIXES:")[0]
        parts.append(weak.strip())

    if "SPECIFIC_FIXES:" in text:
        fixes = text.split("SPECIFIC_FIXES:")[1]
        parts.append(fixes.strip())

    feedback = "\n".join(parts) if parts else text

    return score, verdict, feedback


async def _synthesize_feedback(results: list[PressureTestResult]) -> str:
    """Use Claude to cherry-pick the best feedback from all models."""
    active_results = [r for r in results if r.verdict not in ("SKIP", "ERROR")]

    if not active_results:
        return "No models available for pressure testing."

    if len(active_results) == 1:
        return f"[{active_results[0].model}] {active_results[0].feedback}"

    reviews_text = ""
    for r in active_results:
        reviews_text += f"\n--- {r.model.upper()} (Score: {r.score}/10) ---\n{r.raw_response}\n"

    # Use Claude to synthesize
    if ANTHROPIC_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": ANTHROPIC_API_KEY,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": CLAUDE_MODEL,
                        "max_tokens": 1500,
                        "messages": [{"role": "user", "content": SYNTHESIS_PROMPT.format(reviews=reviews_text)}],
                    },
                )
                data = response.json()
                return data.get("content", [{}])[0].get("text", reviews_text)
        except Exception:
            pass

    # Fallback: concatenate all feedback
    return reviews_text


async def pressure_test(
    stage: str,
    title: str,
    content: str,
    models: Optional[list[str]] = None,
) -> PressureTestSummary:
    """
    Run multi-model pressure test on content.

    Args:
        stage: Pipeline stage being tested (research, scripted, etc.)
        title: Episode title
        content: The work output to review
        models: Which models to use. Default: all available.

    Returns:
        PressureTestSummary with combined results and synthesized feedback.
    """
    import asyncio

    prompt = PRESSURE_TEST_PROMPT.format(
        stage=stage,
        title=title,
        content=content[:6000],  # Limit content to avoid token overflow
    )

    # Determine which models to use
    if models is None:
        models = ["claude", "chatgpt", "gemini", "grok"]

    # Run all models in parallel
    tasks = []
    if "claude" in models:
        tasks.append(_call_claude(prompt))
    if "chatgpt" in models:
        tasks.append(_call_openai(prompt))
    if "gemini" in models:
        tasks.append(_call_gemini(prompt))
    if "grok" in models:
        tasks.append(_call_grok(prompt))

    results = await asyncio.gather(*tasks)

    # Filter active results (skip errors and missing keys)
    active = [r for r in results if r.verdict not in ("SKIP", "ERROR")]

    if not active:
        return PressureTestSummary(
            passed=False, average_score=0, lowest_score=0, highest_score=0,
            results=list(results), synthesized_feedback="No models available.",
            unanimous=False,
        )

    scores = [r.score for r in active]
    avg_score = sum(scores) / len(scores)
    all_pass = all(r.verdict == "PASS" for r in active)

    # Synthesize the best feedback from all models
    synthesized = await _synthesize_feedback(list(results))

    return PressureTestSummary(
        passed=all_pass and min(scores) >= 10,
        average_score=round(avg_score, 1),
        lowest_score=min(scores),
        highest_score=max(scores),
        results=list(results),
        synthesized_feedback=synthesized,
        unanimous=all_pass,
    )
