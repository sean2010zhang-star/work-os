# Known Issues

1. **api_key masking on profile model-copy** (v1.4.x): install.sh copies the user's
   `model:` block but masks `api_key` to empty (secrets-never-duplicate policy). Providers
   whose `model.api_key` is a placeholder string rather than a real secret (e.g., local
   gateway shims) will 401 until the user runs `hermes -p work-os model` once. This is
   intentional; the installer prints the remediation. Post-v1.5: detect placeholder form and
   preserve, mask only high-entropy values.

2. **cold-start 401 silent stop** (v1.4.2-v1.8.2): empty `api_key` + no ANTHROPIC_API_KEY
   in profile .env => first message dies with non-retryable auth error; users read it as
   "agent got stuck and won't self-heal". Fixed in v1.8.3: installer pre-checks key presence
   and fallback_providers existence before first-run (warns loudly); manual FAQ documents the
   recovery. Residual truth: auth errors are intentionally non-retryable — recovery IS a
   human act; the fix is telling users BEFORE the dead session, not pretending agents can
   self-heal a bad key.
