"""
Compatibility facade for translation helpers.

The translation implementation is now split into `translator.py` and `locales/`.
Existing imports from `app.localization.translations` continue to work.
"""

from app.localization.translator import TRANSLATIONS, get_menu_action_by_text, t

__all__ = ["TRANSLATIONS", "t", "get_menu_action_by_text"]
