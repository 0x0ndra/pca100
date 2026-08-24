#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
WORK="pca100.iconset"
PNG="base_1024.png"
rm -rf "$WORK" && mkdir "$WORK"
if command -v rsvg-convert >/dev/null; then
  rsvg-convert -w 1024 -h 1024 ../../frontend/public/favicon.svg -o "$PNG"
else
  sips -s format png -Z 1024 ../../frontend/dist/xctech-logo-white.png --out "$PNG"
fi
for size in 16 32 64 128 256 512 1024; do
  sips -z "$size" "$size" "$PNG" --out "$WORK/icon_${size}x${size}.png" >/dev/null
  half=$((size/2))
  [ "$half" -ge 16 ] && cp "$WORK/icon_${size}x${size}.png" "$WORK/icon_${half}x${half}@2x.png"
done
iconutil -c icns "$WORK" -o pca100.icns
rm -rf "$WORK" "$PNG"
echo "wrote pca100.icns"
