#!/usr/bin/env bash
set -euo pipefail
TARGET=${1:-.}
syft dir:$TARGET -o json > sbom.json
grype sbom:sbom.json -o json > grype.json || true
cat grype.json
