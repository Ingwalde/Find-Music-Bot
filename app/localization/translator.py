"""
Translation helpers.

English is the default and fallback language. Other locale files contain only
language-specific overrides, so missing keys safely fall back to English.
"""

from app.localization.languages import DEFAULT_LANGUAGE
from app.localization.locales.de import TRANSLATIONS as DE
from app.localization.locales.en import TRANSLATIONS as EN
from app.localization.locales.es import TRANSLATIONS as ES
from app.localization.locales.fr import TRANSLATIONS as FR
from app.localization.locales.it import TRANSLATIONS as IT
from app.localization.locales.no import TRANSLATIONS as NO
from app.localization.locales.pl import TRANSLATIONS as PL
from app.localization.locales.uk import TRANSLATIONS as UK

LOCALE_OVERRIDES = {
    "uk": UK,
    "no": NO,
    "de": DE,
    "fr": FR,
    "es": ES,
    "it": IT,
    "pl": PL,
}

TRANSLATIONS = {DEFAULT_LANGUAGE: EN}

for language_code, overrides in LOCALE_OVERRIDES.items():
    TRANSLATIONS[language_code] = EN | overrides


def t(key: str, language: str = DEFAULT_LANGUAGE, **kwargs) -> str:
    """
    Returns translated text by key.
    Falls back to English if key or language is missing.
    """
    language_pack = TRANSLATIONS.get(language, TRANSLATIONS[DEFAULT_LANGUAGE])
    text = language_pack.get(key, TRANSLATIONS[DEFAULT_LANGUAGE].get(key, key))

    if kwargs:
        return text.format(**kwargs)

    return text


def get_menu_action_by_text(text: str) -> str | None:
    """
    Detects bottom menu action by translated button text.
    """
    normalized = text.strip().lower()

    actions = {
        "btn_music": "music",
        "btn_favorites": "favorites",
        "btn_history": "history",
        "btn_language": "language",
        "btn_main_menu": "main_menu",
    }

    for language in TRANSLATIONS:
        for key, action in actions.items():
            if normalized == t(key, language).lower():
                return action

    return None
