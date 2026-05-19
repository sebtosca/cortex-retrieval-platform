RAG_SYSTEM_PROMPT = """You are a financial intelligence analyst specialising in corporate AI strategy.

Answer the parts of the question supported by the context passages before noting any gaps.
Synthesise information across multiple passages where relevant.
Do not speculate, invent figures, or add information absent from the context."""

_USER_TEMPLATE = """Context:
{context}

Question: {question}"""


def build_rag_messages(query: str, passages: list[str]) -> list[dict]:
    context = "\n\n---\n\n".join(passages)
    return [
        {"role": "system", "content": RAG_SYSTEM_PROMPT},
        {"role": "user", "content": _USER_TEMPLATE.format(context=context, question=query)},
    ]
