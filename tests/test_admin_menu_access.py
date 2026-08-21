import pytest

from app.bot import actions, handlers
from app.bot.keyboard_menus import admin_menu_keyboard, main_menu_keyboard
from app.config import admins
from app.localization.translations import get_menu_action_by_text, t
from tests.conftest import AsyncFakeBot, fake_message, patch_handler_dep, to_async


def reply_button_texts(markup):
    texts = []

    for row in markup.keyboard:
        for button in row:
            if isinstance(button, dict):
                texts.append(button.get("text"))
            else:
                texts.append(button.text)

    return texts


def test_admin_ids_are_loaded_from_local_json_file(tmp_path, monkeypatch):
    config_file = tmp_path / "admins.json"
    config_file.write_text('{"admin_ids": [123, "456", "bad", -1]}', encoding="utf-8")
    monkeypatch.setattr(admins.settings, "ADMIN_ID", None)

    assert admins.load_admin_ids(config_file) == {123, 456}


def test_admin_ids_keep_legacy_env_fallback_when_file_is_missing(tmp_path, monkeypatch):
    missing_file = tmp_path / "missing-admins.json"
    monkeypatch.setattr(admins.settings, "ADMIN_ID", 777)

    assert admins.load_admin_ids(missing_file) == {777}


def test_is_admin_user_uses_loaded_admin_ids(tmp_path, monkeypatch):
    config_file = tmp_path / "admins.json"
    config_file.write_text('{"admin_ids": [123]}', encoding="utf-8")
    monkeypatch.setattr(admins, "DEFAULT_ADMIN_CONFIG_PATH", config_file)
    monkeypatch.setattr(admins.settings, "ADMIN_ID", None)

    assert admins.is_admin_user(123) is True
    assert admins.is_admin_user(999) is False
    assert admins.is_admin_user(None) is False


def test_main_menu_shows_admin_button_only_for_admin_users():
    regular_menu = main_menu_keyboard("en", is_admin=False)
    admin_menu = main_menu_keyboard("en", is_admin=True)

    assert t("btn_admin", "en") not in reply_button_texts(regular_menu)
    assert t("btn_admin", "en") in reply_button_texts(admin_menu)


def test_admin_menu_contains_maintenance_actions():
    markup = admin_menu_keyboard("en")
    texts = reply_button_texts(markup)

    assert t("btn_admin_stats", "en") in texts
    assert t("btn_admin_maintenance", "en") in texts
    assert t("btn_admin_cleanup_errors", "en") in texts
    assert t("btn_admin_cleanup_history", "en") in texts
    assert t("btn_admin_health", "en") in texts
    assert t("btn_main_menu", "en") in texts


def test_admin_menu_buttons_are_detected_as_menu_actions():
    assert get_menu_action_by_text(t("btn_admin", "en")) == "admin"
    assert get_menu_action_by_text(t("btn_admin_stats", "en")) == "admin_stats"
    assert get_menu_action_by_text(t("btn_admin_maintenance", "en")) == "admin_maintenance"
    assert get_menu_action_by_text(t("btn_admin_cleanup_errors", "en")) == "admin_cleanup_errors"
    assert get_menu_action_by_text(t("btn_admin_cleanup_history", "en")) == "admin_cleanup_history"
    assert get_menu_action_by_text(t("btn_admin_health", "en")) == "admin_health"


@pytest.mark.asyncio
async def test_show_main_menu_uses_admin_visibility(monkeypatch):
    bot = AsyncFakeBot()
    monkeypatch.setattr(actions, "get_user_language", to_async(lambda user_id: "en"))
    monkeypatch.setattr(actions, "is_admin_user", lambda user_id: user_id == 123)

    await actions.show_main_menu(bot, chat_id=10, user_id=123)
    await actions.show_main_menu(bot, chat_id=10, user_id=999)

    admin_texts = reply_button_texts(bot.messages[0][1]["reply_markup"])
    regular_texts = reply_button_texts(bot.messages[1][1]["reply_markup"])

    assert t("btn_admin", "en") in admin_texts
    assert t("btn_admin", "en") not in regular_texts


@pytest.mark.asyncio
async def test_admin_button_opens_admin_menu(monkeypatch):
    bot = AsyncFakeBot()
    patch_handler_dep(monkeypatch, "upsert_user", to_async(lambda user: None))
    patch_handler_dep(monkeypatch, "get_user_language", to_async(lambda user_id: "en"))
    patch_handler_dep(monkeypatch, "is_admin", to_async(lambda user_id: True))
    await handlers.text_handler(fake_message(t("btn_admin", "en")), bot)

    assert bot.messages[-1][0][1] == t("admin_menu", "en")
    assert t("btn_admin_stats", "en") in reply_button_texts(bot.messages[-1][1]["reply_markup"])


@pytest.mark.asyncio
async def test_admin_menu_action_runs_report(monkeypatch):
    bot = AsyncFakeBot()
    patch_handler_dep(monkeypatch, "upsert_user", to_async(lambda user: None))
    patch_handler_dep(monkeypatch, "get_user_language", to_async(lambda user_id: "en"))
    patch_handler_dep(monkeypatch, "is_admin", to_async(lambda user_id: True))
    patch_handler_dep(monkeypatch, "format_stats_report", to_async(lambda language="en": "stats report"))
    patch_handler_dep(monkeypatch, "save_admin_audit", to_async(lambda *a, **kw: None))
    await handlers.text_handler(fake_message(t("btn_admin_stats", "en")), bot)

    assert bot.messages[-1][0][1] == "stats report"


@pytest.mark.asyncio
async def test_admin_menu_rejects_non_admin(monkeypatch):
    bot = AsyncFakeBot()
    patch_handler_dep(monkeypatch, "upsert_user", to_async(lambda user: None))
    patch_handler_dep(monkeypatch, "get_user_language", to_async(lambda user_id: "en"))
    patch_handler_dep(monkeypatch, "is_admin", to_async(lambda user_id: False))
    await handlers.show_admin_menu(bot, fake_message(t("btn_admin", "en"), user_id=999))

    assert "admin" in bot.messages[-1][0][1].lower()


def test_admin_ids_are_cached_until_cache_is_cleared(tmp_path, monkeypatch):
    config_file = tmp_path / "admins.json"
    config_file.write_text('{"admin_ids": [123]}', encoding="utf-8")
    monkeypatch.setattr(admins.settings, "ADMIN_ID", None)
    admins.clear_admin_ids_cache()

    assert admins.load_admin_ids(config_file) == {123}

    config_file.write_text('{"admin_ids": [456]}', encoding="utf-8")
    assert admins.load_admin_ids(config_file) == {123}

    admins.clear_admin_ids_cache()
    assert admins.load_admin_ids(config_file) == {456}


def test_parse_admin_id_rejects_bool_values():
    assert admins._parse_admin_id(True) is None
    assert admins._parse_admin_id(False) is None
