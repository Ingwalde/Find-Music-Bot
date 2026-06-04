"""
Checks how many English translation keys are overridden by non-English locales.

The bot intentionally supports English fallback, so incomplete locales are not an
error by default. Use --strict to fail when a locale has no custom keys.
"""

from __future__ import annotations

import argparse
import sys
from importlib import import_module
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def get_language_config() -> tuple[str, tuple[str, ...]]:
    """
    Loads supported language metadata after the project root is on sys.path.
    """
    languages = import_module("app.localization.languages")
    return languages.DEFAULT_LANGUAGE, tuple(languages.SUPPORTED_LANGUAGES)


def get_english_translations() -> dict[str, str]:
    """
    Loads the English baseline translations after the project root is on sys.path.
    """
    en_locale = import_module("app.localization.locales.en")
    return getattr(en_locale, "TRANSLATIONS", {})


def get_locale_overrides(language_code: str) -> dict[str, str]:
    """
    Imports one locale module and returns its explicit translations.
    """
    default_language, _ = get_language_config()
    if language_code == default_language:
        return get_english_translations()

    module = import_module(f"app.localization.locales.{language_code}")
    return getattr(module, "TRANSLATIONS", {})


def build_locale_report() -> list[str]:
    """
    Builds readable locale coverage lines.
    """
    default_language, supported_languages = get_language_config()
    en_translations = get_english_translations()
    total_keys = len(en_translations)
    lines = [f"English baseline keys: {total_keys}"]

    for language_code in supported_languages:
        overrides = get_locale_overrides(language_code)

        if language_code == default_language:
            lines.append(f"{language_code}: {total_keys}/{total_keys} baseline")
            continue

        overridden_keys = set(overrides) & set(en_translations)
        missing_keys = set(en_translations) - set(overrides)
        percentage = (len(overridden_keys) / total_keys * 100) if total_keys else 100
        lines.append(
            f"{language_code}: {len(overridden_keys)}/{total_keys} overridden "
            f"({percentage:.1f}%), fallback keys: {len(missing_keys)}"
        )

    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Check locale override coverage.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail if any supported non-English locale has zero overridden keys.",
    )
    args = parser.parse_args()

    lines = build_locale_report()
    print("\n".join(lines))

    if args.strict:
        default_language, supported_languages = get_language_config()
        for language_code in supported_languages:
            if language_code == default_language:
                continue

            if not get_locale_overrides(language_code):
                print(f"Locale {language_code} has no overrides.")
                return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
