set shell := ["bash", "-euo", "pipefail", "-c"]

check:
    python3 scripts/check_repository_boundary.py
    python3 scripts/check_no_committed_evidence.py
    python3 scripts/verify_sample_assets.py
    PYTHONPATH=src python3 scripts/check_read_only_contract.py
    jq . config/microsoft_capability_map.json >/dev/null
    jq . config/dlp_copilot_location_map.json >/dev/null
    PYTHONPATH=src python3 -m compileall -q src tests
    PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_*.py'
    git diff --check


demo:
    PYTHONPATH=src scripts/create_demo_report.py

serve port="8766" dir="artifacts":
    PYTHONPATH=src scripts/serve_artifacts.py --port {{port}} --directory {{dir}}
