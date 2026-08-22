from persona_extractor.archive.adapters.chatgpt import normalize_chatgpt_conversation


def test_chatgpt_normalization_preserves_messages():
    raw = {"id": "c1", "title": "Fixture", "mapping": {"n1": {"message": {"id": "m1", "author": {"role": "user"}, "content": {"parts": ["hello"]}}}}}
    normalized = normalize_chatgpt_conversation(raw, "fixture.json").to_dict()
    assert normalized["schema_version"] == "0.1.0"
    assert normalized["conversation_id"] == "c1"
    assert normalized["messages"][0]["content"] == "hello"
