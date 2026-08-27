# Spotify Troubleshooting

This project uses the Spotify Web API only for metadata and track links.
It does not download music and does not access private Spotify user data.

Spotify is optional. Every failure path below degrades to Deezer-only results
rather than breaking search.

## Required `.env` variables

```env
SPOTIFY_ENABLED=true
SPOTIFY_CLIENT_ID=your_spotify_client_id_here
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here
SPOTIFY_MARKET=NO
SPOTIFY_FORBIDDEN_COOLDOWN_SECONDS=3600
```

## `403 Forbidden`

Since v3.7.14 the bot reports **Spotify's own reason** instead of a list of
things to check. Read the reason first — it usually names the cause outright.

Where to find it:

- The admin `/health` command, for the whole cooldown:

  ```text
  ⚠️ Spotify: Temporarily unavailable: Spotify returned 403 Forbidden during
  token request. Active premium subscription required for the owner of the app.
  ```

- The log, once, when the cooldown starts:

  ```text
  Spotify lookup temporarily disabled for 3600 seconds. Reason: Spotify returned
  403 Forbidden during token request. Active premium subscription required for
  the owner of the app.
  ```

During the cooldown the bot keeps working with Deezer and stops calling Spotify
entirely, so the reason is not refreshed until it expires.

### The common causes, by what the reason says

| Reason contains | What it means | What to do |
|---|---|---|
| `Active premium subscription required for the owner of the app` | The Spotify account that owns the Developer app has no active Premium. Nothing about the bot's credentials is wrong. | Restore Premium on the owner account, or set `SPOTIFY_ENABLED=false`. Spotify notes it can take a few hours after the subscription changes before requests are allowed again. |
| `Invalid client secret` (or another `error_description`) | Credentials are wrong or rotated. | Re-copy `SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET` from the Developer dashboard, restart. |
| The generic checklist below | Spotify sent no usable body — rare. | Fall back to checking Web API access, app mode (development apps only serve users added to the app), account access level, and Premium. |

A `401 Unauthorized` is always credentials, and says so:

```text
Spotify returned 401 Unauthorized. Check SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET.
```

### Why the cooldown matters when taking screenshots or testing

The cooldown lives in process memory and lasts `SPOTIFY_FORBIDDEN_COOLDOWN_SECONDS`
(1 hour by default). A single track search is enough to trip it, and `/health`
reports the cooldown state from then on. Restart the bot to clear it.

Note what `/health` does and does not tell you: it reports **configuration and
cooldown state**, not live reachability. A freshly restarted bot reports
`✅ Spotify: Configured` because nothing has failed yet — it has not called
Spotify.

## Disable Spotify manually

If Spotify access is unavailable for a while, set:

```env
SPOTIFY_ENABLED=false
```

The bot continues with Deezer only, and `/health` reports
`✅ Spotify: Disabled by configuration` rather than an error.

## Market

Default market:

```env
SPOTIFY_MARKET=NO
```

Any ISO country code works, for example:

```env
SPOTIFY_MARKET=US
```
