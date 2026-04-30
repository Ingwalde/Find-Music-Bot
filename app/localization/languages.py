"""
Supported languages for the bot interface.
"""

DEFAULT_LANGUAGE = "en"

SUPPORTED_LANGUAGES = {
    "en": {"name": "English", "flag": "🇬🇧"},
    "uk": {"name": "Українська", "flag": "🇺🇦"},
    "no": {"name": "Norsk", "flag": "🇳🇴"},
    "de": {"name": "Deutsch", "flag": "🇩🇪"},
    "fr": {"name": "Français", "flag": "🇫🇷"},
    "es": {"name": "Español", "flag": "🇪🇸"},
    "it": {"name": "Italiano", "flag": "🇮🇹"},
    "pl": {"name": "Polski", "flag": "🇵🇱"},
}


def is_supported_language(language_code: str) -> bool:
    """
    Checks if language code is supported.
    """
    return language_code in SUPPORTED_LANGUAGES


def get_language_label(language_code: str) -> str:
    """
    Returns visible language label for keyboard buttons.
    """
    language = SUPPORTED_LANGUAGES.get(language_code, SUPPORTED_LANGUAGES[DEFAULT_LANGUAGE])
    return f"{language['flag']} {language['name']}"
