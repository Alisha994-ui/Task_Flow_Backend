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
    # Lite first: in testing they answered in ~2s while the full Flash
    # models sat at 503/504 under free-tier load. Answers here are short
    # and come from a briefing, which Lite handles fine.
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-flash-latest",
]

# Passes over the model list when every model is busy (503). A busy
# model is skipped at once, not waited on - another model is usually
# free, and waiting cost 8s a time.
PASSES = 2

# One model call may take this long before we give up on it and move to
# the next model (seconds). A healthy answer takes 2-5s; a model that
# has not answered in 12 is hanging (one sat 25s, then sent a 504).
CALL_TIMEOUT = 12

# How long a model sits out after failing, so the next question does
# not walk into the same wall (seconds).
BUSY_COOLDOWN = 60      # 503: overloaded right now
SLOW_COOLDOWN = 300     # 504 / timeout: hanging

# The whole question - every model, every retry - must finish inside
# this. The app waits 90s; answering "busy, try again" at 45s beats the
# app giving up on its own with no reason.
TOTAL_BUDGET = 45

# Answers are meant to be short (it is a phone); a cap also stops the
# occasional runaway reply from eating the time budget.
MAX_OUTPUT_TOKENS = 800

# How many earlier turns to replay, so a follow-up like "and Ali?" makes
# sense. More than this costs tokens for very little.
HISTORY_TURNS = 8


class AssistantError(Exception):
    """Something went wrong talking to the model."""


_CLIENT = None


def _client():
    """One client for the whole process.

    Building a new one per question meant a fresh TLS handshake to
    Google every time. The SDK's own retries are switched off: _generate
    already retries, and the two stacked turned one busy model into a
    minute of silence.
    """
    global _CLIENT

    if _CLIENT is not None:
        return _CLIENT

    from google import genai
    from google.genai import types

    key = getattr(settings, "GEMINI_API_KEY", "")

    if not key:
        raise AssistantError(
            "The assistant is not configured. GEMINI_API_KEY is missing."
        )

    _CLIENT = genai.Client(
        api_key=key,
        http_options=types.HttpOptions(
            timeout=CALL_TIMEOUT * 1000,  # milliseconds
            retry_options=types.HttpRetryOptions(attempts=1),
        ),
    )

    return _CLIENT


def _fast_config():
    """Thinking off (or as low as the model allows), answer capped.

    Current Flash models think before they answer, by default. For
    "what is overdue?" over a short briefing that thinking is most of
    the wait - often 10-30 seconds of it - and buys nothing.
    """
    from google.genai import types

    # MINIMAL is refused by the current Flash models ("not supported for
    # this model"); LOW is the lowest they take.
    for thinking in ({"thinking_level": "LOW"}, {"thinking_budget": 0}):
        try:
            return types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(**thinking),
                max_output_tokens=MAX_OUTPUT_TOKENS,
                temperature=0.3,
            )
        except Exception:
            continue

    return None


def _is_bad_config(exc):
    """The model refused the speed settings (some cannot drop thinking)."""
    text = str(exc)

    return ("400" in text or "INVALID_ARGUMENT" in text) and any(
        word in text.lower() for word in ("thinking", "budget", "level", "config")
    )


def _is_timeout(exc):
    name = type(exc).__name__.lower()
    text = str(exc).lower()

    return (
        "timeout" in name
        or "timed out" in text
        or "deadline" in text
        or "504" in text
    )


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


# What the process has learnt about each model, so the next question
# does not pay for the same lesson again. Lost on restart, which is fine.
_PREFERRED = None        # the model that answered last - tried first
_NO_FAST = set()         # refused the speed settings - send defaults
_SKIP_UNTIL = {}         # model -> monotonic time it is worth trying again


def _ordered_models():
    now = time.monotonic()
    usable = [m for m in MODELS if _SKIP_UNTIL.get(m, 0) <= now]

    if _PREFERRED in usable:
        usable.remove(_PREFERRED)
        usable.insert(0, _PREFERRED)

    # Everything skipped (all out of allowance): try anyway rather than
    # refuse without asking - the allowance may have come back.
    return usable or list(MODELS)


def _call(client, model, prompt, fast):
    """One model, one question. Retries once without the speed settings
    if the model refuses them, and remembers that it did."""
    config = None if model in _NO_FAST else fast
    call_started = time.monotonic()

    try:
        return client.models.generate_content(
            model=model, contents=prompt, config=config
        )
    except Exception as exc:
        if config is None or not _is_bad_config(exc):
            raise

        logger.warning(
            "Assistant: %s refused the speed settings, using defaults",
            model,
        )
        _NO_FAST.add(model)

        return client.models.generate_content(
            model=model, contents=prompt, config=None
        )
    finally:
        logger.warning(
            "Assistant: %s call took %.1fs",
            model,
            time.monotonic() - call_started,
        )


def _generate(client, prompt):
    """Asks the models in turn until one answers.

    The last model that answered goes first; a busy, hanging or missing
    model is passed over at once. Bounded by TOTAL_BUDGET, so the person
    always gets an answer or a reason before the app stops waiting.
    """
    global _PREFERRED

    last = None
    started = time.monotonic()
    fast = _fast_config()

    for attempt in range(PASSES):
        busy = False

        for model in _ordered_models():
            if time.monotonic() - started > TOTAL_BUDGET:
                logger.warning(
                    "Assistant gave up after %.1fs", time.monotonic() - started
                )
                raise AssistantError(
                    "The assistant is slow right now - Google's side, not "
                    "yours. Try again in a minute."
                ) from last

            try:
                response = _call(client, model, prompt, fast)
            except Exception as exc:
                last = exc
                logger.warning("Assistant: %s failed: %s", model, exc)
                text = str(exc)

                if "404" in text or "NOT_FOUND" in text:
                    _SKIP_UNTIL[model] = time.monotonic() + 24 * 3600

                    continue

                if "429" in text or "RESOURCE_EXHAUSTED" in text:
                    _SKIP_UNTIL[model] = time.monotonic() + 3600

                    continue

                if _is_timeout(exc):
                    _SKIP_UNTIL[model] = time.monotonic() + SLOW_COOLDOWN
                    busy = True

                    continue

                if _is_busy(exc):
                    _SKIP_UNTIL[model] = time.monotonic() + BUSY_COOLDOWN
                    busy = True

                    continue

                # A real fault - a bad key, a malformed request.
                # Nothing to gain from the next model either.
                raise AssistantError(
                    "The assistant could not answer just now."
                ) from exc

            _PREFERRED = model
            logger.warning(
                "Assistant: answered by %s, total %.1fs",
                model,
                time.monotonic() - started,
            )

            return response

        if not busy:
            break

        if attempt < PASSES - 1:
            time.sleep(1 + random.uniform(0, 0.4))

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
