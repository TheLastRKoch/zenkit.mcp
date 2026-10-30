#!/usr/bin/env bash
# Launch the Zenkit MCP server over stdio for MCP clients that use this repo's
# project-scoped configuration (.mcp.json, registered with `agy mcp add ...`).
#
# The API key is never stored in the repository. Resolution order:
#   1. ZENKIT_API_KEY already exported in the environment;
#   2. otherwise the key configured for this server in ~/.copilot/mcp-config.json.
# The value only enters this process's environment and is never printed.
set -euo pipefail

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -z "${ZENKIT_API_KEY:-}" ]]; then
  current_key="$(python3 - "$HOME/.copilot/mcp-config.json" <<'PY'
import json
import sys

try:
    with open(sys.argv[1], encoding="utf-8") as handle:
        servers = json.load(handle).get("mcpServers", {})
except (OSError, ValueError):
    raise SystemExit(0)

for config in servers.values():
    value = (config.get("env") or {}).get("ZENKIT_API_KEY") or ""
    if value and "${" not in value:
        print(value)
        break
PY
)"
  if [[ -n "$current_key" ]]; then
    export ZENKIT_API_KEY="$current_key"
  fi
fi

exec uv run --directory "$repo_root" zenkit-mcp
