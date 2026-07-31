from app.localization.translator import t


def test_t_returns_formatted_text_when_placeholders_match():
    assert t("search_found", "en", count=3, query="test") == "Found 3 tracks for: test"


def test_t_falls_back_to_unformatted_text_on_missing_placeholder(monkeypatch):
    import app.localization.translator as translator_module

    monkeypatch.setitem(
        translator_module.TRANSLATIONS["en"], "broken_key", "Hello {name}, you have {count} items"
    )

    result = t("broken_key", "en", name="Alice")

    assert result == "Hello {name}, you have {count} items"
