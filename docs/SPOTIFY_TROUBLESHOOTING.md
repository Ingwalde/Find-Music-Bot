# Spotify Troubleshooting

This project uses Spotify Web API only for metadata and track links.
It does not download music and does not access private Spotify user data.

## Required `.env` variables

```env
SPOTIFY_ENABLED=true
SPOTIFY_CLIENT_ID=your_spotify_client_id_here
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here
SPOTIFY_MARKET=NO
SPOTIFY_FORBIDDEN_COOLDOWN_SECONDS=3600
```

## `403 Forbidden`

Example log:

```text
Spotify lookup failed for 884037: 403 Client Error: Forbidden
```

This means Spotify refused access to the Web API endpoint.
The bot now handles this safely:

```text
Spotify lookup temporarily disabled for 3600 seconds
```

During this cooldown, the bot continues working with Deezer and does not repeatedly call Spotify.

## What to check

1. Check that `SPOTIFY_CLIENT_ID` is correct.
2. Check that `SPOTIFY_CLIENT_SECRET` is correct.
3. Check that the Spotify app has Web API access enabled.
4. Check whether your Spotify Developer account/app has the required access level.
5. Restart the bot after changing `.env`.

## Disable Spotify manually

If Spotify access is currently unavailable, set:

```env
SPOTIFY_ENABLED=false
```

The bot will continue working with Deezer only.

## Market

Default market:

```env
SPOTIFY_MARKET=NO
```

You can change it to another country code, for example:

```env
SPOTIFY_MARKET=US
```
