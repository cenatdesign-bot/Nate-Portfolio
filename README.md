# Nataly Cetre — Portfolio (deploy repo)

Public static deploy of the portfolio. Source of truth is
`Documents/CLAUDE/Portfolio_2026/`; this folder is a **published copy** of
its public files only.

## What's in here
- `index.html` — copy of `Portfolio_2026/portfolio.html` (renamed so `/` serves it).
  One delta from source: the Lab "Design Process Framework" card links to
  `https://process-framework.up.railway.app` instead of the local editor file.
- `portfolio-config.json`, `assets/`, `case-studies/published/*.json` — copied verbatim.
- `server.py`, `Procfile` — Railway static server.

**Not** included (kept off the public site): `design-process-framework.html`
(the editor — deployed separately), `config.json`, drafts/archives/internal.

## Redeploy after updating a case study
1. In the framework (local), edit + Publish so the JSON lands in
   `Portfolio_2026/case-studies/published/`.
2. Re-sync this folder from `Portfolio_2026` (index.html, portfolio-config.json,
   assets/, case-studies/published/*.json), keeping the framework-link delta.
3. `git add -A && git commit && railway up`.
