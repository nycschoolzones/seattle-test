# AGENTS.md

A test of the nycschoolzones.com map on Seattle Public Schools' data (see README.md). The code was copied from
nycschoolzones/nycschoolzones at v1.67.0 and cut down. No framework and no npm; Python 3 and one HTML template.

## Build

```sh
python3 scripts/fetch_seattle.py   # data/*.json
python3 scripts/build.py           # index.html, assets/
python3 -m http.server 8000        # preview at http://localhost:8000
```

- Edit the sources, never the built files: `src/template.html` (the map), `scripts/build.py` (data → page), `scripts/fetch_seattle.py` (downloads).
- Per-city settings live in `CITY` at the top of the template's script. When something else turns out to differ by city, move it there instead of adding another `if`.
- Run the build before committing and commit `index.html` and `assets/` with the source change.
- **Start with ARCHITECTURE.md**: its first section says what changed from the NYC code. Much NYC-only code is still in the template, switched off; say so in ARCHITECTURE.md when you remove some.

## Branches

- One branch per change, from an up-to-date `main`. Changes reach `main` through a pull request.
- After every push, give the maintainer a preview link for the commit: `https://raw.githack.com/nycschoolzones/seattle-test/<full commit SHA>/index.html` (the full SHA, not the branch name). Map views use hashes: `#middle`, `#high`, `#es-<school id>`.
- `upstream` is nycschoolzones/nycschoolzones. Don't merge it in; port single fixes by hand.

## Changelog

- Every change adds a plain-English line under `## Unreleased` in `CHANGELOG.md`.
- Never edit `VERSION` or create tags.

## Data

- Files in `data/` come from `scripts/fetch_seattle.py`. Don't hand-edit them.
- If a source refuses a scripted request, don't work around it; say so.

## Testing

Check changes in a real browser (Playwright/Chromium) against the local server, at desktop width and at phone width (390px): zone and school selection, the card, Color by, the level switch, address search, light and dark. Check what is actually visible, not just attributes. The page must also open from disk (`file://`).

## Conventions

- School ids are the district's numbers (`"201"`); the code still calls them `dbn`.
- Map links use hashes: `#es-201`, `#ms-115`, `#hs-11`, `#middle`, `#high`.
- No new libraries or build steps without asking.
