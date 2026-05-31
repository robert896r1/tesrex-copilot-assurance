# Public Release Notes

This public tree is the clean starter-kit distribution of Tesrex Copilot Assurance.

It intentionally excludes maintainer-history material, private validation notes and internal project-decision logs. The private maintainer repository remains the source for implementation history.

Public users should start with:

- `README.md`
- `docs/README.md`
- `docs/limitations.md`
- `samples/copilot-assurance/evidence_pack.md`

Generated assessment outputs are written under ignored `artifacts/` and must not be committed.

## Release hardening

A GitHub Actions workflow is included to run repository guards, sample verification, JSON validation, compile checks, unit tests, and whitespace checks on pull requests and pushes to `main`.
