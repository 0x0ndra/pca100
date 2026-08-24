# Contributing

Thanks for your interest in PCA-100 Measurement Software for macOS. This
document covers the dev setup, quality gates, and a few conventions used in
this repo.

## Dev setup

```
(cd backend && uv sync)
(cd frontend && npm install)
make dev
```

`make dev` runs the backend (uvicorn on `http://localhost:8320`) and the
frontend (Vite dev server on `http://localhost:5175`, proxying `/api` to the
backend) concurrently.

The backend opens the real PCA-100 spectrometer on startup. If none is
connected (and no fake device is configured), the app still starts; it just
reports the instrument as disconnected and live measurement won't produce
data.

## Calibration data

Calibration files (`dark.bin`, `lamp.bin`, `reference.bin`,
`colormeter.ini`, `dark_sweep.json`) are specific to one physical
spectrometer unit and are never committed. `backend/data/` is gitignored;
keep any local calibration files there or in
`~/Library/Application Support/PCA-100/calibration/` as described in the
README. Do not add calibration files to a commit or PR, even for testing.

## Quality gates

```
make check
```

This must pass before opening a PR. It runs, in order:

- **Backend**: `ruff check`, `mypy` (strict), `pytest`, `import-linter`
  (which enforces the layering below; fails the build if a module imports
  from a layer it isn't allowed to depend on), and the desktop test suite.
- **Frontend**: `eslint`, `tsc` (via `npm run typecheck`), `vitest`,
  `dependency-cruiser`, and a production `build`.
- **Repo-wide**: `scripts/check-loc.py`, a 300-line-of-code cap per source
  file (`.py`, `.ts`, `.tsx`). Split a file rather than exceed the cap.

CI runs the same `make check` gates on every push, so there are no surprises
between a local pass and CI.

### Backend layering

```
device      seabreeze wrapper (USB2000+), fake for tests
netguard    allow-list origin (same layer as device)
  -> calibration   per-unit calibration parsers + dark model
  -> pipeline      raw -> dark -> boxcar -> lamp -> radiance, grid guard
  -> colorimetry   spectrum -> XYZ -> x, y, luminance, CCT (colour-science)
  -> agc           auto integration time, saturation detection
  -> engine        measurement loop, averaging, scan/dark state, reconnect
  -> api           FastAPI REST + WebSocket (JSON), origin guard
```

Each layer may only import from the layers above it in this list. If a
change needs a dependency in the other direction, that's usually a sign the
logic belongs in a different module rather than a reason to bypass
import-linter.

## Commit style

Commits use conventional-ish prefixes:

- `feat:` a new feature
- `fix:` a bug fix
- `docs:` documentation only
- `chore:` maintenance (deps, config, tooling) with no behavior change

Keep the subject line short and in the imperative mood (e.g. `fix: correct
dark model interpolation`).

## Adding a language

The UI strings live in a single file, `frontend/src/lib/strings.ts`. Each
language is one dictionary object with a `label` field (the name shown in
the language switcher) plus every UI string, keyed by section (`header`,
`measurement`, `dci`, etc.).

To add a language:

1. Add a new dictionary object to `frontend/src/lib/strings.ts`, following
   the shape of the existing `cs` and `en` objects. Its type is
   `Strings = typeof cs`, so TypeScript will fail to compile if any key is
   missing.
2. Register it in the `STRINGS` map at the bottom of the same file.
3. Run `make check` (or at least the frontend gates) to confirm `tsc` and
   the existing i18n tests pass.

No other files need to change; the language switcher and `useI18n()` hook
read from `STRINGS` directly.

## Pull requests

- Keep PRs focused on one change.
- Make sure `make check` passes locally before opening the PR.
- Describe what changed and why; link any related issue.
