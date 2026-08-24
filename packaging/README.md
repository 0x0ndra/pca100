# Packaging PCA-100 for macOS

Builds a signed, notarized `.app` and a distributable `.dmg` for PCA-100
(bundle id `cz.xctech.pca100`), arm64 only.

## Prerequisites

- Xcode Command Line Tools (`xcode-select --install`), which provide `codesign`,
  `xcrun`, `hdiutil`, `ditto`.
- A Developer ID Application signing identity in your login keychain, team
  `63L676LTMM`.
- Node.js (for the frontend build).
- `uv` (for the backend / PyInstaller build).
- Optional: `rsvg-convert` (used by `packaging/icon/make_icon.sh` to
  regenerate `pca100.icns` from an SVG source; not needed if the `.icns`
  is already committed).

## One-time setup: notarization credentials

Notarization needs an app-specific password (not your normal Apple ID
password), generated at https://appleid.apple.com under Sign-In and
Security > App-Specific Passwords. Store it once in the keychain:

```bash
xcrun notarytool store-credentials pca100-notary \
  --apple-id "<your Apple ID email>" --team-id 63L676LTMM \
  --password "<app-specific password>"
```

This creates the `pca100-notary` keychain profile that `packaging/notarize.sh`
uses by default (override with the `NOTARY_PROFILE` env var).

## Build

```bash
bash packaging/build_all.sh
```

This runs, in order:

1. `packaging/build_app.sh`: frontend build, PyInstaller bundle, codesign
   with hardened runtime and entitlements.
2. `packaging/notarize.sh`: zips the app, submits it to Apple notary
   service, staples the ticket, validates it.
3. `packaging/make_dmg.sh`: stages the app plus an `Applications` symlink
   into a `.dmg`, signs the `.dmg` itself.

Output: `dist/PCA-100-<version>.dmg`.

Both `build_app.sh` and `make_dmg.sh` require `CODESIGN_IDENTITY` (your
Developer ID hash) to be set in the environment before running.

Each script can also be run standalone (they all resolve paths relative to
the repo root, not the caller's working directory).

## Verify

```bash
spctl -a -vvv -t install dist/PCA-100.app
```

Expected once notarization has succeeded: `accepted`, `source=Notarized
Developer ID`.

## arm64 only

The app is built and signed for `arm64` only (`target_arch="arm64"` in
`packaging/PCA-100.spec`). It will not run on Intel Macs. Building a
universal2 binary would need a matching universal2 Python/dependency stack
(notably `seabreeze`), which is out of scope for this project.

## Troubleshooting

**Notarization rejected (`Invalid`)**

`notarytool submit --wait` prints a submission id. Fetch the detailed log:

```bash
xcrun notarytool log <submission-id> --keychain-profile pca100-notary
```

Fix whatever it flags (usually a missing entitlement or an unsigned nested
binary) and rerun `packaging/build_all.sh` from the top so the app is
rebuilt and re-signed before resubmitting.

**PyInstaller: missing module at runtime**

If the built app fails to start with an import error (typically from the
`seabreeze` USB backend or a `pyobjc`/`webview` submodule PyInstaller didn't
detect), add it to `hiddenimports` (or wrap it with
`collect_submodules(...)`) in `packaging/PCA-100.spec`, then rerun the build.

**USB device not detected in the packaged app**

The app needs `com.apple.security.device.usb` in `packaging/entitlements.plist`
to access the PCA-100 colorimeter through the hardened runtime. If USB access
works when run from source but not from the packaged `.app`, verify that
entitlement is present and that `build_app.sh` signed with
`--entitlements packaging/entitlements.plist`.

**`codesign` fails with `errSecInternalComponent`**

Seen once during a `--deep` sign of the full bundle; looks like a transient
hiccup against Apple's timestamp authority, not a real signing problem. A
plain retry of the same `codesign` command (no config change) resolved it.
