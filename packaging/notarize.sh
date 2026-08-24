#!/usr/bin/env bash
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
APP="$REPO/dist/PCA-100.app"
ZIP="$REPO/dist/PCA-100-notarize.zip"
trap 'rm -f "$ZIP"' EXIT
PROFILE="${NOTARY_PROFILE:-pca100-notary}"
/usr/bin/ditto -c -k --keepParent "$APP" "$ZIP"
xcrun notarytool submit "$ZIP" --keychain-profile "$PROFILE" --wait
xcrun stapler staple "$APP"
xcrun stapler validate "$APP"
echo "notarized and stapled $APP"
