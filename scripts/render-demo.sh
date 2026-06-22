#!/usr/bin/env bash
# Renders the social demo: assets/demo.gif + assets/demo.mp4 from the real abom CLI.
# (VHS's ttyd bridge is flaky on macOS, so we use asciinema + agg + ffmpeg instead.)
#
# One-time:  brew install asciinema agg ffmpeg
# Run:       bash scripts/render-demo.sh        (from anywhere)
set -euo pipefail
cd "$(dirname "$0")/.."
export ABOM_KEY="${ABOM_KEY:-/tmp/abom-demo-key.pem}"

asciinema rec --overwrite -c "bash scripts/demo-run.sh" /tmp/abom-demo.cast
agg --font-size 24 --theme monokai --speed 1.3 /tmp/abom-demo.cast assets/demo.gif
ffmpeg -y -i assets/demo.gif -movflags +faststart -pix_fmt yuv420p \
       -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" assets/demo.mp4

echo "→ assets/demo.gif and assets/demo.mp4 ready (upload the .mp4 to LinkedIn)"
