#!/usr/bin/env bash
set -euo pipefail
TARGET=${1:-.}
osv-scanner -r "$TARGET" -o osv.json || true
cat osv.json
