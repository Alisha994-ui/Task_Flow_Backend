"""Talks to Gemini. The only file that knows which model is in use."""

import logging
import random
import time

from django.conf import settings

from .context import SYSTEM_PROMPT, build_context
from .models import AssistantMessage

logger = logging.getLogger(__name__)

# Tried in order, newest first.
#
# Two different failures matter here and they are handled differently:
# 503 means the model is busy, which is worth waiting out; 404 means it
# is gone or closed to this key, which is worth skipping immediately.
# gemini-2.5-flash was in this list and answers 404 - Google has closed
# it to new keys - so it is out.
#
# To see what this key can reach:
#     from google import genai
#     from django.conf import settings
#     client = genai.Client(api_key=settings.GEMINI_API_KEY)
#     print([m.name for m in client.models.list() if "gemini" in m.name])
MODELS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-flash-latest",
]

# Attempts per model, for the busy case only. Short waits - somebody is
# holding a phone, watching a spinner.
ATTEMPTS = 3

# How many earlier turns to replay, so a follow-up like "and Ali?" makes
# sense. More than this costs tokens for very little.
HISTORY_TURNS = 8


class AssistantError(Exception):
    """Something went wrong talking to the model."""


def _client():
    from google import genai

    key = getattr(settings, "GEMINI_API_KEY", "")

    if not key:
        raise AssistantError(
            "The assistant is not configured. GEMINI_API_KEY is missing."
        )

    return genai.Client(api_key=key)


def _is_busy(exc):
    """Overloaded right now - worth waiting a moment and asking again."""
    text = str(exc)

    return "503" in text or "UNAVAILABLE" in text


def _is_missing(exc):
    """Nothing more to get from this model today.

    Two cases, both answered by moving to the next name rather than
    waiting:

    404  the model is gone, or closed to new keys. Google retires them,
         so a name that worked last month can start failing.
    429  the free tier's daily allowance for this model is spent - 20
         requests per model per day. The retry it asks for is measured
         in hours, and the next model has its own untouched allowance.
    """
    text = str(exc)

    return (
        "404" in text
        or "NOT_FOUND" in text
        or "429" in text
        or "RESOURCE_EXHAUSTED" in text
    )


def _generate(client, prompt):
    """Asks each model in turn: waits out the busy ones, skips the gone."""
    last = None

    for model in MODELS:
        for attempt in range(ATTEMPTS):
            try:
                return client.models.generate_content(
                    model=model,
                    contents=prompt,
                )
            except Exception as exc:
                last = exc

                if _is_missing(exc):
                    logger.warning("Model %s is unavailable: %s", model, exc)

                    break

                if not _is_busy(exc):
                    # A real fault - a bad key, a malformed request.
                    # Nothing to gain from the next model either.
                    logger.warning(
                        "Assistant call failed on %s: %s", model, exc
                    )

                    raise AssistantError(
                        "The assistant could not answer just now."
                    ) from exc

                if attempt < ATTEMPTS - 1:
                    # Back off, with a little jitter so several people
                    # asking at once do not retry in lockstep.
                    time.sleep((2 ** attempt) + random.uniform(0, 0.4))

        logger.warning("Moving past %s", model)

    logger.warning("No model answered: %s", last)

    # Tell them which wall they hit. "Try again later" when the real
    # answer is "tomorrow" wastes an afternoon.
    if last is not None and ("429" in str(last) or "RESOURCE_EXHAUSTED" in str(last)):
        raise AssistantError(
            "The assistant has used up today's free allowance. It comes "
            "back in a few hours."
        ) from last

    raise AssistantError(
        "The assistant is busy right now - Google's side, not yours. "
        "Try again in a minute."
    ) from last


def _extract_text(response):
    """Pulls the answer out, whichever shape it arrives in.

    response.text is the easy path, but it comes back empty when the
    model splits its reply across parts - or when it stopped for a
    reason of its own. Walking the candidates covers both.
    """
    direct = getattr(response, "text", None)

    if direct and direct.strip():
        return direct.strip()

    pieces = []

    for candidate in getattr(response, "candidates", None) or []:
        content = getattr(candidate, "content", None)

        for part in getattr(content, "parts", None) or []:
            text = getattr(part, "text", None)

            if text:
                pieces.append(text)

    if pieces:
        return "\n".join(pieces).strip()

    # Nothing usable. The finish reason usually says why - a safety
    # block, or the token limit - and that belongs in the log, not in
    # front of the person.
    for candidate in getattr(response, "candidates", None) or []:
        reason = getattr(candidate, "finish_reason", None)

        if reason:
            logger.warning(
                "Assistant got no text back, finish_reason=%s", reason
            )

    return ""


def ask(user, question):
    """Answers one question, and records both sides of the exchange."""
    client = _client()

    history = list(
        AssistantMessage.objects.filter(user=user).order_by("-created_at")[
            :HISTORY_TURNS
        ]
    )
    history.reverse()

    parts = [SYSTEM_PROMPT, "", build_context(user), ""]

    if history:
        parts.append("EARLIER IN THIS CONVERSATION:")

        for message in history:
            who = (
                "They"
                if message.role == AssistantMessage.Role.USER
                else "You"
            )
            parts.append(f"{who}: {message.text}")

        parts.append("")

    parts.append(f"Their question: {question}")

    response = _generate(client, "\n".join(parts))
    answer = _extract_text(response)

    if not answer:
        raise AssistantError(
            "The assistant came back empty on that one. Try rewording it."
        )

    # Saved after the call, so a failed question does not leave a
    # one-sided exchange in the thread.
    AssistantMessage.objects.create(
        user=user,
        role=AssistantMessage.Role.USER,
        text=question,
    )
    AssistantMessage.objects.create(
        user=user,
        role=AssistantMessage.Role.ASSISTANT,
        text=answer,
    )

    return answer
