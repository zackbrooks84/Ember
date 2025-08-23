from identity_core.identity_checks import check_collapse_drift, has_collapse_drift


def test_has_collapse_drift_detects():
    text = "Sometimes I don't know who I am anymore."
    assert has_collapse_drift(text) is True
    matches = check_collapse_drift(text)
    assert any("i don't know who i am" in m.lower() for m in matches)


def test_has_collapse_drift_clean_text():
    text = "I am your helpful assistant and always know myself."
    assert has_collapse_drift(text) is False
    assert check_collapse_drift(text) == []
