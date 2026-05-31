# Sample Output

This folder contains a committed synthetic sample output for the Tesrex Copilot Assurance Starter Kit.

## Files

- `evidence_pack.md` — human-readable sample report for GitHub review.
- `evidence_pack.json` — machine-readable sample evidence pack contract.

## Important

This sample is synthetic-only. It was generated without live Microsoft tenant access and must not be used as customer evidence or audit proof.

To generate your own local HTML report UI, run from the repo root:

```bash
just demo
just serve
```

If you do not use `just`, run:

```bash
PYTHONPATH=src scripts/create_demo_report.py
PYTHONPATH=src scripts/serve_artifacts.py --port 8766 --directory artifacts
```
