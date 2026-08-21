"""
Track persistence: the local cache of track metadata.

Owns the bot layer's access to the tracks table. See user_service for why these
are re-exports rather than wrappers.

Distinct from track_platform_service, which is the compatibility facade for
platform enrichment (Spotify links) and does not touch storage.
"""

from app.database.repositories import get_track_by_deezer_id, save_track

__all__ = ["get_track_by_deezer_id", "save_track"]
