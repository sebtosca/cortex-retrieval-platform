from llm.prompts import RAG_SYSTEM_PROMPT, build_rag_messages


def test_build_rag_messages_returns_two_messages():
    messages = build_rag_messages("What is IBM doing?", ["IBM is building quantum computers."])
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"


def test_system_message_is_rag_prompt():
    messages = build_rag_messages("Q?", ["context"])
    assert messages[0]["content"] == RAG_SYSTEM_PROMPT


def test_query_appears_in_user_message():
    query = "What are NVDA's AI projects?"
    messages = build_rag_messages(query, ["some context"])
    assert query in messages[1]["content"]


def test_all_passages_appear_in_user_message():
    passages = ["Passage one about IBM.", "Passage two about MSFT.", "Passage three about GOOGL."]
    messages = build_rag_messages("Tell me everything.", passages)
    user_content = messages[1]["content"]
    for passage in passages:
        assert passage in user_content


def test_passages_are_separated_by_delimiter():
    passages = ["First.", "Second."]
    messages = build_rag_messages("Q?", passages)
    assert "---" in messages[1]["content"]


def test_empty_passages_list_produces_valid_messages():
    messages = build_rag_messages("Empty?", [])
    assert len(messages) == 2
    assert "Empty?" in messages[1]["content"]
