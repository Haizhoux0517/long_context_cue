# Release Cleanup Recommendations

After applying this patch, remove or archive stale root-level files:

```bash
bash scripts/cleanup_release_root.sh
```

This will:

- remove `README_REPRODUCE_updated.md` after its content has been merged into `README_REPRODUCE.md`;
- move `README_PATCH.md` to `docs/archive/README_PATCH.md`;
- move `README_DIAGNOSTIC_REFACTOR.md` to `docs/archive/README_DIAGNOSTIC_REFACTOR.md`.

Recommended final audit:

```bash
python -m pytest -q
python scripts/check_release_artifacts.py --strict-data --strict-clean
```
