# Code Review Action Plan (historical record — frozen at v2.5.2)

> **This document is closed.** It tracked improvement items from an external
> review of the **v2.5** codebase and was last updated at v2.5.2, in the run-up
> to the aiogram 3 migration. Everything listed below has either shipped or
> been superseded — the "Planned for v3.0.0" section is the aiogram migration
> that landed in v3.0.0.
>
> It is kept because it is the record of how that migration was planned, which
> [`CHANGELOG.md`](../CHANGELOG.md) shows only the outcome of. It is **not** a
> live TODO list: current plans live in [`ROADMAP.md`](ROADMAP.md), and later
> reviews are recorded in the CHANGELOG entry for the release that acted on
> them. Nothing here should be treated as outstanding work — some of it
> describes code that no longer exists, such as SQLite table discovery, removed
> when the project moved to PostgreSQL in v3.1.0.

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
