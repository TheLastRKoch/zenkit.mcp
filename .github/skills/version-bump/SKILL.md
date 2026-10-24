---
name: version-bump
description: Bump the project version in VERSION before opening a pull request. Use when preparing a branch for a PR, when asked to bump or update the project version, or when a release version must be recorded.
license: MIT
---

# Bump the project version before creating a PR

`VERSION` at the repository root is the single source of truth for the project version. `pyproject.toml` reads it dynamically through hatchling (`[tool.hatch.version]`), and the server reports it through `importlib.metadata`. Never edit a version field in `pyproject.toml`; only edit `VERSION`.

This skill updates and commits the version. It does **not** create the pull request; the caller opens it after this skill finishes.

## Preconditions

Run from the repository root, and stop with a clear report if any check fails.

1. `git rev-parse --show-toplevel` succeeds.
2. Current branch is not the default branch:

   ```bash
   git rev-parse --abbrev-ref HEAD
   ```

   The result must not be `main` or `master` (or whatever the repository's default branch is).
3. `VERSION` exists and matches `^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[-+][0-9A-Za-z.-]+)?$`. Read the working-tree file with `tr -d '[:space:]' < VERSION`.
4. A base ref exists for comparison.

Resolve the default branch and base ref:

```bash
default_branch="$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##')"
if [ -z "$default_branch" ]; then
  for candidate in main master; do
    if git rev-parse --verify --quiet "$candidate" >/dev/null; then default_branch="$candidate"; break; fi
  done
fi
[ -n "$default_branch" ] || { echo "Cannot determine the default branch"; exit 1; }

base_ref="origin/${default_branch}"
git rev-parse --verify --quiet "$base_ref" >/dev/null || base_ref="$default_branch"
```

If neither ref resolves, stop and ask the user to fetch the base branch.

## Detect an existing bump

```bash
current="$(tr -d '[:space:]' < VERSION)"
base="$(git show "${base_ref}:VERSION" 2>/dev/null | tr -d '[:space:]')"
```

- If `base` is non-empty and `current != base`, the branch already bumps the version. Do not bump again. Report `base -> current` and stop.
- If `base` is empty, the base branch does not contain `VERSION` yet. Treat the baseline as `0.0.0` when `current` is `0.0.0`; otherwise report that the baseline is unavailable and stop.
- If `current == base`, continue.

## Classify the change

Inspect the branch, not only the working tree:

```bash
git log --oneline "${base_ref}..HEAD"
git diff --stat "${base_ref}...HEAD"
git diff "${base_ref}...HEAD"
```

Choose the highest bump that applies:

| Bump | Use when the PR... |
| --- | --- |
| MAJOR | removes or renames a public MCP tool, changes a tool's required inputs incompatibly, removes or renames a CLI flag or environment variable, drops a supported Python version, or otherwise breaks existing clients |
| MINOR | adds a backward-compatible capability such as a new MCP tool, a new optional CLI flag or environment variable, or a new public module, or changes behavior compatibly |
| PATCH | fixes behavior, refactors, or changes only docs, tests, CI, or dependencies |

Rules:

- Mixed changes take the highest level.
- If a change might break existing clients, classify it as MAJOR; only classify lower when the existing contract is preserved.
- If `git diff --stat` shows no changes, report that there is nothing to release and stop.
- Changes confined to `openspec/`, documentation, tests, or CI are PATCH.
- Never infer the bump from the version number alone.

**0.x convention:** while the current major version is `0`, breaking changes bump MINOR (for example `0.2.1 -> 0.3.0`). Reserve `1.0.0` for an explicit stable release.

## Compute and write the version

Parse `MAJOR.MINOR.PATCH` and increment exactly one component, resetting lower components to zero:

- major: `(MAJOR+1).0.0`
- minor: `MAJOR.(MINOR+1).0`
- patch: `MAJOR.MINOR.(PATCH+1)`

For example:

```bash
# patch: 0.0.0 -> 0.0.1
printf '%s\n' "0.0.1" > VERSION
```

Verify the new version is greater than `current` and still matches the semver pattern. Do not change `pyproject.toml`, `uv.lock`, or dependencies.

## Verify and commit

1. Confirm `VERSION` contains exactly the new version with no stray whitespace.
2. Refresh the installed metadata and prove the package reports the new version. Plain `uv sync` can reuse the cached project build when only `VERSION` changed, so force a reinstall of the project:

   ```bash
   uv sync --reinstall-package zenkit-mcp
   uv run python -c "from importlib.metadata import version; print(version('zenkit-mcp'))"
   ```

   The printed value must equal the new version. If it does not, stop and fix the mismatch before committing.

3. Run the version-sensitive test:

   ```bash
   uv run pytest tests/test_server.py -q
   ```

4. Commit only the version file, leaving unrelated changes alone:

   ```bash
   git add VERSION
   git commit -m "chore(release): bump version to <new_version>"
   ```

   If the repository's commit policy requires a trailer such as `Co-authored-by`, add it to the commit message.

## Report

Summarize:

- old version -> new version
- bump type and the one or two changes that justified it
- commit hash
- reminder that this skill does not create the PR and that the PR should be opened next

## Do not

- Do not create or modify a pull request.
- Do not bump when the branch already changed `VERSION` relative to the base branch.
- Do not bump on the default branch or from a detached HEAD.
- Do not edit any version field in `pyproject.toml`.
- Do not include unrelated working-tree changes in the version commit; ask the user how to proceed if the working tree is mixed.
