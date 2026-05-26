#!/usr/bin/env bash
set -euo pipefail

# Cleanup helper for the reviewer-facing SCI release.
# Run from repository root.

mkdir -p docs/archive

if [ -f README_REPRODUCE_updated.md ]; then
  rm README_REPRODUCE_updated.md
fi

if [ -f README_PATCH.md ]; then
  git mv README_PATCH.md docs/archive/README_PATCH.md 2>/dev/null || mv README_PATCH.md docs/archive/README_PATCH.md
fi

if [ -f README_DIAGNOSTIC_REFACTOR.md ]; then
  git mv README_DIAGNOSTIC_REFACTOR.md docs/archive/README_DIAGNOSTIC_REFACTOR.md 2>/dev/null || mv README_DIAGNOSTIC_REFACTOR.md docs/archive/README_DIAGNOSTIC_REFACTOR.md
fi

echo "Cleanup complete."
echo "Now run:"
echo "  python scripts/check_release_artifacts.py --strict-data --strict-clean"
