from __future__ import annotations

import json
import logging
import time

logger = logging.getLogger(__name__)

_MAX_RETRIES = 5
_RETRY_BASE_DELAY = 5  # seconds; doubles each attempt

_JUDGE_PROMPT = """\
You are evaluating whether an AI-generated answer introduces financial or factual claims \
that are NOT supported by the provided context passages.

Context passages:
{contexts}

Generated answer:
{answer}

Task: Identify if the answer contains specific company names, financial figures, project names, \
dates, or factual claims that are NOT present or directly inferable from the context above. \
Hallucinated content that sounds plausible but is absent from the context counts as a failure.

Respond with ONLY a valid JSON object on a single line:
{{"score": <0 or 1>, "reason": "<one concise sentence>"}}

score=1 means the answer is fully grounded in the provided context.
score=0 means the answer contains at least one unsupported claim.\
"""


def financial_groundedness_score(answer: str, contexts: list[str]) -> float:
    """Claude Sonnet judge: 1.0 = grounded, 0.0 = fabricated claims detected.

    Returns float("nan") if the API call fails so the caller can omit the sample
    from the aggregate rather than silently pollute the score.
    """
    import anthropic
    from configs.settings import settings

    context_block = "\n\n---\n\n".join(contexts) if contexts else "(no context retrieved)"
    prompt = _JUDGE_PROMPT.format(contexts=context_block, answer=answer)

    client = anthropic.Anthropic()
    delay = _RETRY_BASE_DELAY
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            msg = client.messages.create(
                model=settings.eval_model,
                max_tokens=128,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = msg.content[0].text.strip()
            data = json.loads(raw)
            score = float(data.get("score", 0))
            logger.debug("financial_groundedness score=%.1f reason=%s", score, data.get("reason", ""))
            return score
        except anthropic.RateLimitError:
            if attempt == _MAX_RETRIES:
                logger.warning("financial_groundedness: rate limit after %d retries", _MAX_RETRIES)
                return float("nan")
            logger.warning("financial_groundedness: rate limit, retrying in %ds (attempt %d/%d)", delay, attempt, _MAX_RETRIES)
            time.sleep(delay)
            delay *= 2
        except Exception as exc:
            logger.warning("financial_groundedness scoring failed: %s", exc)
            return float("nan")
    return float("nan")
