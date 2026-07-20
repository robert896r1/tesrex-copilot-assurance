# Sample Output

This folder contains a committed synthetic sample output for the Tesrex Copilot Assurance Starter Kit.

## Files

- `evidence_pack.md` — human-readable sample report for GitHub review.
- `evidence_pack.json` — machine-readable sample evidence pack contract.
- `generated-source/` — committed synthetic source artifacts referenced by the sample, retained so every recorded SHA-256 hash can be independently verified.

## Important

This sample is synthetic-only. It was generated without live Microsoft tenant access and must not be used as customer evidence or audit proof.

Maintainers can deterministically regenerate the committed sample from the repository root:

```bash
PYTHONPATH=src python3 scripts/regenerate_public_sample.py
python3 scripts/verify_sample_assets.py
```

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
