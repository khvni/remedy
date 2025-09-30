#!/usr/bin/env bash
set -euo pipefail
CFG=${1:-scanners/semgrep/profiles.yml}
semgrep --config "$CFG" --json --timeout 180 --quiet
