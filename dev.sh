#!/usr/bin/env bash
set -euo pipefail

# In WSL, binding the inspector to all interfaces allows the Windows host to
# reach the UI and proxy via localhost forwarding or the WSL IP.
HOST="${MCP_INSPECTOR_HOST:-0.0.0.0}" \
CLIENT_PORT="${MCP_INSPECTOR_CLIENT_PORT:-6274}" \
SERVER_PORT="${MCP_INSPECTOR_SERVER_PORT:-6277}" \
MCP_AUTO_OPEN_ENABLED="${MCP_INSPECTOR_AUTO_OPEN:-false}" \
npx @modelcontextprotocol/inspector@latest "$@"
