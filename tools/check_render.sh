#!/usr/bin/env bash
# Render the site (or the files given) and fail on unresolved cross-references,
# missing citations, or unbalanced blog shortcodes. Used by CI and by the
# definition of done in CLAUDE.md.
#
#   tools/check_render.sh                               # whole site
#   tools/check_render.sh posts/2026-10-slug/index.qmd  # one post (always re-executes)
set -uo pipefail

log="$(mktemp)"
trap 'rm -f "$log"' EXIT

quarto render "$@" 2>&1 | tee "$log"
status=${PIPESTATUS[0]}
if [ "$status" -ne 0 ]; then
  echo "check_render: quarto render failed (exit $status)."
  exit "$status"
fi

if grep -E "Unable to resolve crossref|Citeproc: citation .* not found|\(W\) blog:" "$log"; then
  echo "check_render: FAILED, unresolved cross-references, missing citations or unbalanced shortcodes (above)."
  exit 1
fi
echo "check_render: no unresolved cross-references, citations or shortcodes."
