# Release Workflow

This project uses version tags and GitHub Releases.

## Version Format

The project uses semantic-style version names:

```text
v1.0.0
v1.1.0
v1.2.0
v1.3.0
v1.4.0
v1.5.0
v1.6.0
v1.7.0
v1.8.0
```

## Before Creating a Release

1. Update `app/version.py`
2. Update `README.md`
3. Update `CHANGELOG.md`
4. Run tests:

```bash
python -m pytest
```

5. Check that local/private files are not staged:

```text
.env
data/
logs/
__pycache__/
.vscode/
```

## Commit Message Format

Use clear release commits:

```text
Release v1.8.0: improve GitHub documentation
```

## Create Git Tag

If using terminal:

```bash
git tag v1.8.0
git push origin v1.8.0
```

If using GitHub website:

1. Open repository
2. Go to Releases
3. Click Draft a new release
4. Choose or create tag `v1.8.0`
5. Set target branch to `main`
6. Add title and release notes
7. Publish release

## Release Title Format

```text
v1.8.0 - GitHub Polish Update
```

## Release Notes Template

```md
## Overview

Short explanation of this release.

## Added

- New files or features

## Changed

- Updated behavior or structure

## Fixed

- Bug fixes

## Notes

Additional technical notes.
```

## Current Releases

```text
v1.0.0 - Deezer MVP
v1.1.0 - Pagination and History Update
v1.2.0 - UX Improvements
v1.3.0 - Track Metadata Update
v1.4.0 - Logging Update
v1.5.0 - Project Refactoring Update
v1.6.0 - Database Optimization Update
v1.7.0 - Tests Update
v1.8.0 - GitHub Polish Update
```
