from app.config.admins import clear_admin_ids_cache
from app.database.maintenance import (
    cleanup_old_errors,
    cleanup_search_history,
    get_database_summary,
)
from app.localization.translations import t
from app.platforms.spotify.auth import (
    get_spotify_block_reason,
    is_spotify_configured,
    is_spotify_temporarily_blocked,
)


def get_spotify_status_text(language: str = "en") -> str:
    """
    Returns a localized Spotify runtime status for admin reports.
    """
    if not is_spotify_configured():
        return t("admin_spotify_not_configured", language)

    if is_spotify_temporarily_blocked():
        reason = get_spotify_block_reason() or t("admin_spotify_temporary_cooldown", language)
        return t("admin_spotify_temporarily_disabled", language, reason=reason)

    return t("admin_spotify_available", language)


def format_stats_report(language: str = "en") -> str:
    """
    Formats database statistics for the admin /stats command.
    """
    summary = get_database_summary()
    counts = summary["table_counts"]

    return "\n".join(
        [
            t("admin_stats_title", language),
            t("admin_stats_users", language, count=counts.get("users", 0)),
            t("admin_stats_searches", language, count=counts.get("searches", 0)),
            t("admin_stats_favorites", language, count=counts.get("favorites", 0)),
            t("admin_stats_tracks", language, count=counts.get("tracks", 0)),
            t("admin_stats_errors", language, count=counts.get("errors", 0)),
            t("admin_stats_database_size", language, size=summary["database_size"]),
            t("admin_stats_spotify_status", language, status=get_spotify_status_text(language)),
        ]
    )


def format_maintenance_report(language: str = "en") -> str:
    """
    Formats maintenance diagnostics for the admin /maintenance command.
    """
    summary = get_database_summary()
    counts = summary["table_counts"]

    rows = t(
        "admin_maintenance_rows",
        language,
        users=counts.get("users", 0),
        searches=counts.get("searches", 0),
        tracks=counts.get("tracks", 0),
        favorites=counts.get("favorites", 0),
        errors=counts.get("errors", 0),
    )

    return "\n".join(
        [
            t("admin_maintenance_title", language),
            t("admin_maintenance_version", language, version=summary["app_version"]),
            t("admin_maintenance_schema", language, version=summary["schema_version"]),
            t("admin_maintenance_database", language, size=summary["database_size"]),
            t("admin_maintenance_database_path", language, path=summary["database_path"]),
            rows,
            t("admin_maintenance_spotify", language, status=get_spotify_status_text(language)),
        ]
    )


def format_cleanup_result(title: str, result: dict[str, int], language: str = "en") -> str:
    """
    Formats cleanup results returned by maintenance helpers.
    """
    return "\n".join(
        [
            f"✅ {title}",
            t("admin_cleanup_before", language, count=result["before"]),
            t("admin_cleanup_deleted", language, count=result["deleted"]),
            t("admin_cleanup_after", language, count=result["after"]),
        ]
    )


def cleanup_errors_report(language: str = "en") -> str:
    """
    Runs saved error cleanup and returns a readable admin report.
    """
    return format_cleanup_result(
        t("admin_cleanup_errors_completed", language),
        cleanup_old_errors(),
        language,
    )


def cleanup_history_report(language: str = "en") -> str:
    """
    Runs search history cleanup and returns a readable admin report.
    """
    return format_cleanup_result(
        t("admin_cleanup_history_completed", language),
        cleanup_search_history(),
        language,
    )


def reload_admins_report(language: str = "en") -> str:
    """
    Clears cached admin configuration and returns a localized report.
    """
    clear_admin_ids_cache()
    return t("admin_reload_completed", language)
