# Release Workflow

`main` is protected. Direct pushes are rejected, so every release reaches
`main` through a pull request that passes the required CI checks. Tags are cut
after the merge, never before.

## Version format

Semantic versioning, `vMAJOR.MINOR.PATCH`. The full history lives in
[`CHANGELOG.md`](../CHANGELOG.md) and [`ROADMAP.md`](ROADMAP.md) — this file
deliberately does not keep its own copy of the list, which is how the previous
version of this document ended up three years of releases out of date.

Versioned release or chore? A change that alters runtime behaviour a user or
admin can observe gets a version, a CHANGELOG entry and a tag. A change to CI,
docs or tooling alone is a chore: PR and merge, no version bump, no tag.

## Before opening the release PR

Work on a feature or chore branch, never on `main`.

1. Update `app/version.py`.
2. Add the `CHANGELOG.md` entry — heading `## [vX.Y.Z] - YYYY-MM-DD`.
3. Add the `ROADMAP.md` line under **Completed**.
4. Update `README.md` if the release changes something it describes.

Then run the local gate. This mirrors the three CI jobs; the `quality-gate`
skill runs the whole sequence in order.

```bash
python -m ruff check .
python -m mypy
python -m pip_audit -r requirements/base.txt
python scripts/check_release_clean.py
python scripts/check_version_sync.py
python scripts/check_env_example.py
python scripts/check_locale_coverage.py
python -m pre_commit run --all-files
docker build -f deploy/Dockerfile -t find-music-bot:test .
```

`mypy` takes no arguments on purpose — the checked file list lives in
`pyproject.toml`, and passing paths narrows the check and hides failures CI
will catch anyway.

Tests need PostgreSQL and Redis. Without `DATABASE_URL` and `REDIS_URL` the
integration fixtures fail at setup, and the coverage number from such a run is
not comparable to the ~94% baseline:

```bash
docker compose up -d --wait test-postgres test-redis
DATABASE_URL=postgresql://testuser:testpass@localhost:5433/testdb \
  REDIS_URL=redis://localhost:6380 \
  alembic upgrade head
DATABASE_URL=postgresql://testuser:testpass@localhost:5433/testdb \
  REDIS_URL=redis://localhost:6380 \
  python -m pytest
docker compose stop test-postgres test-redis
```

Coverage floor is 85% (`pyproject.toml`); below it is a hard stop, not a
warning.

## Merging

1. Push the branch and open a PR: base `main` ← compare the branch.
2. If GitHub reports the branch is behind, use **Merge latest changes from
   main into this branch**. Do not merge `main` locally — branch protection
   rejects the resulting push.
3. Wait for all required checks: Lint & Static Analysis, Pytest Coverage,
   Docker Build.
4. Merge with GitHub's **Merge pull request** button.

Never `git push origin main` and never force-push.

## After the merge

```bash
git checkout main
git pull
git tag vX.Y.Z
git push origin vX.Y.Z
```

Tags are for versioned releases only, not chores.

The tag matters beyond bookkeeping: `scripts/check_version_sync.py` uses it to
detect changes under `app/` that reached `main` with no CHANGELOG entry. Until
the tag exists that check reports "skipped".

Deployment is automatic. The merge triggers Tests; on success the Deploy
workflow fires via `workflow_run`, pulls the new GHCR image, restarts the
stack and polls `/ready`. See [`DEPLOYMENT.md`](DEPLOYMENT.md).

If CI does not fire for a merge — it has happened — re-run Tests manually from
the Actions tab (`workflow_dispatch`). A dispatch on `main` publishes the image
exactly as a push does.

## GitHub Release

Create the release from the tag. Title format:

```text
v3.7.13 - Portfolio Polish
```

Body: reuse the CHANGELOG entry for that version rather than writing a second
description that can drift from it.

## Admin access configuration

Admin menu visibility comes from local admin IDs in `config/admins.json` or the
legacy `ADMIN_ID` environment variable. `config/admins.json` must stay local
and is ignored by Git; `scripts/check_release_clean.py` fails the build if it
is ever tracked.
