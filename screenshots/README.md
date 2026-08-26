# Screenshots

Three shots, linked from the root `README.md`:

```text
search-results.jpg   paginated search — the page indicator and Next control must be visible
track-card.jpg       cover art plus the full metadata block
health-admin.jpg     /health, admin-only, every dependency reporting
```

Three rather than a longer set on purpose: favourites and history render the
same list-of-buttons layout that `search-results.jpg` already shows, so extra
shots dilute rather than add.

## Retaking them

Order matters. `/health` reports Spotify's cooldown state, and a track search
trips that cooldown for an hour when Spotify returns 403 — which it does when
the app owner has no active Premium subscription. So:

1. Restart the bot (the cooldown lives in process memory), wait for `/ready`
2. `/health` — before searching anything
3. Search, then open a track

Doing it the other way round is why an earlier attempt caught Spotify with a
warning icon.

## Rules

- Test chat only — no personal username, avatar or other chats in frame
- Crop to the message; no Telegram chrome, no compose box
- One theme across all three, and the same width, or the README table skews
- Never capture `.env` values or a bot token
