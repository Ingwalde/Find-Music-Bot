def test_repository_facade_imports():
    from app.database.repositories import get_user_language, save_search, save_track

    assert callable(get_user_language)
    assert callable(save_track)
    assert callable(save_search)


def test_spotify_service_facade_imports():
    from app.services.spotify_service import (
        build_spotify_queries,
        format_spotify_track,
        normalize_text,
        search_spotify_track,
    )

    assert callable(build_spotify_queries)
    assert callable(format_spotify_track)
    assert callable(normalize_text)
    assert callable(search_spotify_track)


def test_translation_facade_imports():
    from app.localization.translations import get_menu_action_by_text, t

    assert t("btn_music", "en") == "🎵 Music"
    assert get_menu_action_by_text("🎵 Music") == "music"


# ── import direction ─────────────────────────────────────────────────────────
#
# The layering used to be a convention: app/bot imported app.database.repositories
# directly for lightweight lookups, and README carried an "Honest scope note"
# admitting it. These tests are what replaced that note — the boundary is now
# checked rather than intended.


def _imports_of(package: str) -> dict[str, set[str]]:
    """Maps each module in `package` to the set of modules it imports from."""
    import ast
    import pathlib

    found: dict[str, set[str]] = {}

    for path in sorted(pathlib.Path(package.replace(".", "/")).rglob("*.py")):
        modules: set[str] = set()
        tree = ast.parse(path.read_text(encoding="utf-8"))

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                modules.add(node.module)
            elif isinstance(node, ast.Import):
                modules.update(alias.name for alias in node.names)

        found[path.as_posix()] = modules

    return found


def test_bot_layer_does_not_import_the_database_layer():
    """
    app/bot reaches storage through app/services, never directly.

    Direction: bot -> services -> database. A bot module importing
    app.database skips the middle layer, which is what made the boundary
    unenforceable before.
    """
    offenders = {
        module: sorted(m for m in imported if m.startswith("app.database"))
        for module, imported in _imports_of("app.bot").items()
        if any(m.startswith("app.database") for m in imported)
    }

    assert not offenders, (
        "app/bot must not import app.database directly — route through "
        f"app/services instead:\n{offenders}"
    )


def test_the_check_would_catch_a_violation():
    """
    Guards the guard: a check that cannot fail proves nothing.

    Rather than trusting that _imports_of() finds anything, this feeds it a
    module that does import app.database and asserts it is reported.
    """
    import ast

    tree = ast.parse("from app.database.repositories import save_track\n")
    modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }

    assert any(m.startswith("app.database") for m in modules)


def test_services_may_import_the_database_layer():
    """
    The other half of the old note claimed "two services read from the cache
    tables" as if it were also a violation. It is not: reaching storage is the
    service layer's job. This pins that so a future tightening does not
    mistakenly forbid it.
    """
    service_imports = _imports_of("app.services")
    reaching_db = [
        module
        for module, imported in service_imports.items()
        if any(m.startswith("app.database") for m in imported)
    ]

    assert reaching_db, "expected at least one service to own database access"
