"""Generate gold question candidates for each company PDF using Claude Haiku.

Usage:
    python scripts/generate_gold_questions.py [--companies AMZN GOOGL MSFT NVDA] [--per-company 15]

Outputs one staging file per company:
    tests/evaluation/gold_candidates_AMZN.json
    tests/evaluation/gold_candidates_GOOGL.json
    ...

Review each file and promote the best 10 per company into:
    tests/evaluation/gold_questions.json
"""
from __future__ import annotations

import argparse
import json
import random
import re
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

import anthropic

from configs.settings import settings
from ingestion.chunker import chunk_documents
from ingestion.loader import load_pdf

ZIP_PATH = Path(__file__).parent.parent / "Companies-AI-Initiatives(1).zip"
GOLD_DIR = Path(__file__).parent.parent / "tests" / "evaluation"
ALL_COMPANIES = ["AMZN", "GOOGL", "MSFT", "NVDA"]

_PROMPT = """\
You are creating evaluation questions for a financial intelligence RAG system.

Below are excerpts from {company}'s AI initiatives report. Generate exactly {n} question-answer pairs that:
- Are specific and factual (not vague or generic)
- Can be answered solely from the provided text
- Cover different topics (strategy, products, governance, partnerships, etc.)
- Would be good test cases for a retrieval system

Return ONLY a valid JSON array, no other text:
[
  {{"question": "...", "reference": "..."}},
  ...
]

Document excerpts:
{context}"""


def generate_for_company(company: str, n: int, tmpdir: str) -> list[dict]:
    pdf_name = f"Companies-AI-Initiatives/{company}.pdf"
    pdf_path = Path(tmpdir) / f"{company}.pdf"

    with zipfile.ZipFile(ZIP_PATH) as zf:
        with zf.open(pdf_name) as src, open(pdf_path, "wb") as dst:
            dst.write(src.read())

    docs = load_pdf(pdf_path)
    chunks = chunk_documents(docs, chunk_size=512, chunk_overlap=100, company=company)

    # Sample 8 chunks spread across the document — enough coverage, short enough context
    step = max(1, len(chunks) // 8)
    sampled = chunks[::step][:8]
    random.shuffle(sampled)
    context = "\n\n---\n\n".join(c.text for c in sampled)

    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=settings.rag_model,  # Haiku — fast and cheap for candidate generation
        max_tokens=2048,
        messages=[{
            "role": "user",
            "content": _PROMPT.format(company=company, n=n, context=context),
        }],
    )

    raw = msg.content[0].text.strip()
    # Extract JSON array even if Claude adds surrounding explanation text
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON array found in response. Raw output:\n{raw[:500]}")
    pairs = json.loads(match.group())
    return [{"company": company, "question": p["question"], "reference": p["reference"]} for p in pairs]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate RAGAS gold question candidates per company")
    parser.add_argument(
        "--companies", nargs="+", default=ALL_COMPANIES,
        help="Company tickers to generate questions for (default: all 4 non-IBM companies)",
    )
    parser.add_argument(
        "--per-company", type=int, default=15,
        help="Number of candidate questions to generate per company (default: 15)",
    )
    args = parser.parse_args()

    GOLD_DIR.mkdir(parents=True, exist_ok=True)

    with TemporaryDirectory() as tmpdir:
        for company in args.companies:
            print(f"\nGenerating {args.per_company} candidates for {company} …")
            try:
                candidates = generate_for_company(company, args.per_company, tmpdir)
                out_path = GOLD_DIR / f"gold_candidates_{company}.json"
                out_path.write_text(json.dumps(candidates, indent=2))
                print(f"  Saved {len(candidates)} candidates → {out_path}")
                print(f"  Review and promote best 10 into tests/evaluation/gold_questions.json")
            except Exception as exc:
                print(f"  ERROR for {company}: {exc}")


if __name__ == "__main__":
    main()
