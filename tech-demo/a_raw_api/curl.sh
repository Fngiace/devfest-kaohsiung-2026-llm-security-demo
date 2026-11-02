#!/bin/sh
set -eu
cd "$(dirname "$0")/../.."
setting="${1:-omitted}"
out_dir="${2:-tech-demo/a_raw_api/out}"
case "$setting" in omitted|true|false) ;; *) echo 'usage: curl.sh [omitted|true|false]' >&2; exit 2;; esac
# probe_raw.py saves the exact request used for the measured run.
curl --noproxy '*' --fail-with-body --silent --show-error \
  http://localhost:11434/api/chat -H 'Content-Type: application/json' \
  --data-binary "@$out_dir/$setting.request.json"
