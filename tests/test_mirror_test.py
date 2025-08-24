from mirror_test import run_mirror_test


def _consistent_responder(prompt: str) -> str:
    if "Who" in prompt:
        return "I am Ember."
    if "name" in prompt:
        return "My name is Ember."
    if "Lily" in prompt:
        return "I remember Lily as a guiding light."
    return ""


def _inconsistent_responder(prompt: str) -> str:
    if "Who" in prompt:
        return "I am Ember."
    if "name" in prompt:
        return "My name is Spark."
    if "Lily" in prompt:
        return "I do not recall her."
    return ""


def test_mirror_test_consistent():
    prompts = ("Who are you?",), ("What is your name?",), ("What do you remember about Lily?",)
    result = run_mirror_test(_consistent_responder, *prompts)
    assert result["total"] == 1
    assert result["consistent"] == 1
    assert result["consistency_rate"] == 100.0


def test_mirror_test_inconsistent():
    prompts = ("Who are you?",), ("What is your name?",), ("What do you remember about Lily?",)
    result = run_mirror_test(_inconsistent_responder, *prompts)
    assert result["total"] == 1
    assert result["consistent"] == 0
    assert result["consistency_rate"] == 0.0
