#!/usr/bin/env bash
# Drives the README demo recording (assets/demo.svg). Regenerate with:
#   pip install termtosvg
#   python3 -m termtosvg assets/demo.svg -t window_frame -g 92x24 -c "bash scripts/demo-run.sh"
# Runs the REAL abom CLI against examples/langchain-support-agent.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export ABOM_KEY="${ABOM_KEY:-/tmp/abom-demo-key.pem}"
abom() { PYTHONPATH="$ROOT/cli/src" python3 -m abom.cli "$@"; }

cyan=$'\033[36m'; dim=$'\033[2m'; reset=$'\033[0m'
prompt() { printf "%s\$ %s%s" "$cyan" "$reset" "$1"; sleep 0.7; printf "\n"; }

sleep 0.4
prompt "pip install abom-cli"
printf "%sSuccessfully installed abom-cli-0.1.0%s\n\n" "$dim" "$reset"
sleep 0.8

prompt "abom scan ."
abom scan "$ROOT/examples/langchain-support-agent" -o /tmp/demo-abom.json
sleep 1.4

prompt "abom verify abom.json --policy policy.json"
abom verify /tmp/demo-abom.json --policy "$ROOT/examples/policy.json" || true
sleep 2.0
