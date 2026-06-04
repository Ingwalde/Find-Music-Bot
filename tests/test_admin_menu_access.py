from types import SimpleNamespace

from app.bot import actions, handlers
from app.bot.keyboard_menus import admin_menu_keyboard, main_menu_keyboard
from app.config import admins
from app.localization.translations import get_menu_action_by_text, t


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


class FakeBot:
    def __init__(self):
        self.messages = []
        self.message_handlers = []

    def send_message(self, *args, **kwargs):
        self.messages.append((args, kwargs))
        chat_id = kwargs.get("chat_id", args[0] if args else 1)
        return SimpleNamespace(chat=SimpleNamespace(id=chat_id), message_id=len(self.messages))

    def message_handler(self, **decorator_kwargs):
        def decorator(func):
            self.message_handlers.append((decorator_kwargs, func))
            return func

        return decorator


def fake_message(text, user_id=123):
    return SimpleNamespace(
        text=text,
        from_user=SimpleNamespace(id=user_id, username="tester", first_name="Test"),
        chat=SimpleNamespace(id=10),
    )


def get_registered_handler(bot, name):
    for _metadata, func in bot.message_handlers:
        if func.__name__ == name:
            return func
    raise AssertionError(f"Handler {name} was not registered")


def test_show_main_menu_uses_admin_visibility(monkeypatch):
    bot = FakeBot()
    monkeypatch.setattr(actions, "get_user_language", lambda user_id: "en")
    monkeypatch.setattr(actions, "is_admin_user", lambda user_id: user_id == 123)

    actions.show_main_menu(bot, chat_id=10, user_id=123)
    actions.show_main_menu(bot, chat_id=10, user_id=999)

    admin_texts = reply_button_texts(bot.messages[0][1]["reply_markup"])
    regular_texts = reply_button_texts(bot.messages[1][1]["reply_markup"])

    assert t("btn_admin", "en") in admin_texts
    assert t("btn_admin", "en") not in regular_texts


def test_admin_button_opens_admin_menu(monkeypatch):
    bot = FakeBot()
    monkeypatch.setattr(handlers, "upsert_user", lambda user: None)
    monkeypatch.setattr(handlers, "get_user_language", lambda user_id: "en")
    monkeypatch.setattr(handlers, "is_admin", lambda user_id: True)

    handlers.register_handlers(bot)
    text_handler = get_registered_handler(bot, "text_handler")
    text_handler(fake_message(t("btn_admin", "en")))

    assert bot.messages[-1][0][1] == t("admin_menu", "en")
    assert t("btn_admin_stats", "en") in reply_button_texts(bot.messages[-1][1]["reply_markup"])


def test_admin_menu_action_runs_report(monkeypatch):
    bot = FakeBot()
    monkeypatch.setattr(handlers, "upsert_user", lambda user: None)
    monkeypatch.setattr(handlers, "get_user_language", lambda user_id: "en")
    monkeypatch.setattr(handlers, "is_admin", lambda user_id: True)
    monkeypatch.setattr(handlers, "format_stats_report", lambda language="en": "stats report")

    handlers.register_handlers(bot)
    text_handler = get_registered_handler(bot, "text_handler")
    text_handler(fake_message(t("btn_admin_stats", "en")))

    assert bot.messages[-1][0][1] == "stats report"


def test_admin_menu_rejects_non_admin(monkeypatch):
    bot = FakeBot()
    monkeypatch.setattr(handlers, "upsert_user", lambda user: None)
    monkeypatch.setattr(handlers, "get_user_language", lambda user_id: "en")
    monkeypatch.setattr(handlers, "is_admin", lambda user_id: False)

    handlers.show_admin_menu(bot, fake_message(t("btn_admin", "en"), user_id=999))

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
