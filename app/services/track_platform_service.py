"""
Compatibility facade for track platform enrichment.

The implementation now lives in `app.platforms.aggregator`.
"""

from app.platforms.aggregator import (
    enrich_track_with_platform_links,
    enrich_track_with_spotify_link,
)

__all__ = ["enrich_track_with_platform_links", "enrich_track_with_spotify_link"]
