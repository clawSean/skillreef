#!/usr/bin/env bash
# Copy to credentials.local.sh and replace placeholders with local 1Password
# references. Never put API key material in either file.

case "${PERPLEXITY_KEY_PROFILE:-default}" in
  default)
    PERPLEXITY_1PASSWORD_REF='op://<vault>/<primary-item>/<field>'
    ;;
  fallback)
    PERPLEXITY_1PASSWORD_REF='op://<vault>/<fallback-item>/<field>'
    ;;
  *)
    echo "Unknown PERPLEXITY_KEY_PROFILE: ${PERPLEXITY_KEY_PROFILE}" >&2
    return 64 2>/dev/null || exit 64
    ;;
esac
export PERPLEXITY_1PASSWORD_REF
