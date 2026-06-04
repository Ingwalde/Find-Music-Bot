# Code Review Action Plan

This document tracks improvement items identified during the external review of the v2.5 codebase.

## Addressed in v2.5.1

- Removed repeated JSON file reads from admin access checks by caching loaded admin IDs.
- Localized the Genius lyrics URL button instead of using a hardcoded English label.
- Added thread-safe locking around Spotify runtime token/cache/cooldown state.
- Added TTL cleanup for in-memory search contexts to reduce memory-growth risk.
- Removed the lazy `actions.py` to `handlers.py` import workaround by registering the music search handler explicitly.
- Replaced the hardcoded maintenance table list with SQLite table discovery.

## Planned for v2.5.2

- Small cleanup of compatibility facades and documentation wording.
- Review locale fallback behavior and decide which languages should be fully supported in v2.x.
- Review import side effects in Deezer and Genius services and decide whether to move client creation to lazy factories.

## Planned for v2.6.0

- Split `app/bot` into handler, callback and keyboard packages.
- Organize tests by domain folders.
- Keep compatibility facades during the transition.

## Planned for v3.0.0

- Migrate Telegram runtime from pyTelegramBotAPI to aiogram 3.x.
- Move handler execution to async architecture.
- Rework routing, state handling and middleware around aiogram patterns.

## Addressed in v2.5.2

- Moved Deezer client creation from import time to lazy runtime initialization.
- Moved Genius client creation from import time to lazy runtime initialization.
- Added locking around in-memory search context access.
- Added localized admin reports and admin cache reload support.
- Added locale coverage checker for visibility into incomplete locale overrides.
- Grouped deployment and dependency files into `deploy/` and `requirements/`.
