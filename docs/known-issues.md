# Known Issues

1. **api_key masking on profile model-copy** (v1.4.x): install.sh copies the user's
   `model:` block but masks `api_key` to empty (secrets-never-duplicate policy). Providers
   whose `model.api_key` is a placeholder string rather than a real secret (e.g., local
   gateway shims) will 401 until the user runs `hermes -p work-os model` once. This is
   intentional; the installer prints the remediation. Post-v1.5: detect placeholder form and
   preserve, mask only high-entropy values.
