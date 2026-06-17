import pytest

from app.bot.language_callbacks import handle_language_callback
from app.localization.translations import get_menu_action_by_text, t
from tests.conftest import AsyncFakeBot, fake_call, to_async


def reply_button_texts(markup):
    texts = []

    for row in markup.keyboard:
        for button in row:
            if isinstance(button, dict):
                texts.append(button.get("text"))
            else:
                texts.append(button.text)

    return texts


@pytest.mark.asyncio
async def test_language_change_keeps_admin_button_for_admin_user(monkeypatch):
    bot = AsyncFakeBot()

    monkeypatch.setattr("app.bot.language_callbacks.upsert_user", to_async(lambda user: None))
    monkeypatch.setattr("app.bot.language_callbacks.set_user_language", to_async(lambda user_id, language: None))
    monkeypatch.setattr("app.bot.language_callbacks.is_admin_user", lambda user_id: user_id == 123)

    await handle_language_callback(bot, fake_call(user_id=123), "uk")

    assert bot.messages[-1][0][1] == t("language_changed", "uk")
    assert t("btn_admin", "uk") in reply_button_texts(bot.messages[-1][1]["reply_markup"])


@pytest.mark.asyncio
async def test_language_change_hides_admin_button_for_regular_user(monkeypatch):
    bot = AsyncFakeBot()

    monkeypatch.setattr("app.bot.language_callbacks.upsert_user", to_async(lambda user: None))
    monkeypatch.setattr("app.bot.language_callbacks.set_user_language", to_async(lambda user_id, language: None))
    monkeypatch.setattr("app.bot.language_callbacks.is_admin_user", lambda user_id: False)

    await handle_language_callback(bot, fake_call(user_id=999), "uk")

    assert t("btn_admin", "uk") not in reply_button_texts(bot.messages[-1][1]["reply_markup"])


def test_admin_menu_buttons_are_localized_and_detected():
    assert t("btn_admin", "uk") == "🛠 Адмін"
    assert t("btn_admin_stats", "uk") == "📊 Статистика"
    assert t("btn_admin_maintenance", "no") == "🛠 Vedlikehold"

    assert get_menu_action_by_text(t("btn_admin", "uk")) == "admin"
    assert get_menu_action_by_text(t("btn_admin_stats", "uk")) == "admin_stats"
    assert get_menu_action_by_text(t("btn_admin_maintenance", "no")) == "admin_maintenance"
