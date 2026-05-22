from app.database.maintenance import (
    cleanup_old_errors,
    cleanup_search_history,
    get_database_summary,
)
from app.platforms.spotify.auth import (
    get_spotify_block_reason,
    is_spotify_configured,
    is_spotify_temporarily_blocked,
)


def get_spotify_status_text() -> str:
    """
    Returns a human-readable Spotify runtime status for admin reports.
    """
    if not is_spotify_configured():
        return "not configured or disabled"

    if is_spotify_temporarily_blocked():
        reason = get_spotify_block_reason() or "temporary cooldown"
        return f"temporarily disabled ({reason})"

    return "available"


def format_stats_report() -> str:
    """
    Formats database statistics for the admin /stats command.
    """
    summary = get_database_summary()
    counts = summary["table_counts"]

    return "\n".join(
        [
            "📊 Bot Statistics",
            f"Users: {counts.get('users', 0)}",
            f"Searches: {counts.get('searches', 0)}",
            f"Favorites: {counts.get('favorites', 0)}",
            f"Tracks cached: {counts.get('tracks', 0)}",
            f"Errors stored: {counts.get('errors', 0)}",
            f"Database size: {summary['database_size']}",
            f"Spotify status: {get_spotify_status_text()}",
        ]
    )


def format_maintenance_report() -> str:
    """
    Formats maintenance diagnostics for the admin /maintenance command.
    """
    summary = get_database_summary()
    counts = summary["table_counts"]

    return "\n".join(
        [
            "🛠 Maintenance Report",
            f"Version: v{summary['app_version']}",
            f"Schema version: v{summary['schema_version']}",
            f"Database: OK ({summary['database_size']})",
            f"Database path: {summary['database_path']}",
            f"Rows: users={counts.get('users', 0)}, searches={counts.get('searches', 0)}, tracks={counts.get('tracks', 0)}, favorites={counts.get('favorites', 0)}, errors={counts.get('errors', 0)}",
            f"Spotify: {get_spotify_status_text()}",
        ]
    )


def format_cleanup_result(title: str, result: dict[str, int]) -> str:
    """
    Formats cleanup results returned by maintenance helpers.
    """
    return "\n".join(
        [
            f"✅ {title}",
            f"Before: {result['before']}",
            f"Deleted: {result['deleted']}",
            f"After: {result['after']}",
        ]
    )


def cleanup_errors_report() -> str:
    """
    Runs saved error cleanup and returns a readable admin report.
    """
    return format_cleanup_result("Error cleanup completed", cleanup_old_errors())


def cleanup_history_report() -> str:
    """
    Runs search history cleanup and returns a readable admin report.
    """
    return format_cleanup_result("Search history cleanup completed", cleanup_search_history())
