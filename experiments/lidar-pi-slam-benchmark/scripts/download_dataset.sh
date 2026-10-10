#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
DEST="$ROOT/data/lidar-pi-slam-benchmark"
mkdir -p "$DEST"
OUT="$DEST/intel.clf"
URL="${DATASET_URL:-http://kaspar.informatik.uni-freiburg.de/~slamEvaluation/datasets/intel.clf}"
echo "Dataset URL: $URL"
echo "Destination: $OUT"
curl --fail --location --retry 2 --output "$OUT.part" "$URL"
test -s "$OUT.part"
grep -m 1 '^FLASER ' "$OUT.part" >/dev/null || { echo "Downloaded file does not look like a CARMEN FLASER log" >&2; rm -f "$OUT.part"; exit 2; }
mv "$OUT.part" "$OUT"
sha256sum "$OUT" | tee "$OUT.sha256"
echo "Downloaded candidate. Verify provenance/licence and inspect output before citing it."
