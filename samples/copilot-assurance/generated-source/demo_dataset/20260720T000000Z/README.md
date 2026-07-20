# TCA Demo Dataset 20260720T000000Z

Purpose: enrich local evidence-pack review and demos without representing synthetic material as production governance evidence.

Important boundaries:

- Demo fixtures are explicitly marked `demo_mode=true` and `is_synthetic=true`.
- Synthetic chat transcripts are not Teams messages, not CopilotInteraction records, and not Purview audit records.
- Tenant eDiscovery case created: False.
- If a tenant eDiscovery case was created, it must be manually deleted before or at the expiry target; this tool does not auto-delete tenant cases.
- Expiry target: 2026-08-19.
- Do not use this dataset as customer audit proof.

