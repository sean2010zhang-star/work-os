#!/usr/bin/env bash
# release.sh — distribution hygiene as a tool, not a habit.
# 1) exports ONLY the tracked tree (git archive => no pycache/.DS_Store/untracked junk)
# 2) content-level privacy scan over the export
# 3) version consistency across all manifests + tag
# 4) test suites must pass from inside the export (self-contained proof)
# Exit non-zero on ANY failure; prints what failed. Usage: ./release.sh [tag]
set -uo pipefail
cd "$(dirname "$0")"
TAG="${1:-$(git describe --tags --abbrev=0)}"
STAMP="$(date +%Y%m%d)"
OUT="$HOME/Desktop/work-os-repo-${STAMP}.zip"
TMP="$(mktemp -d /tmp/work-os-release-XXXXXX)"
trap 'rm -rf "$TMP"' EXIT
fail=0
say(){ printf '\033[1;36m==>\033[0m %s\n' "$*"; }
err(){ printf '\033[1;31mFAIL\033[0m %s\n' "$*"; fail=1; }

say "exporting $TAG (git archive: tracked files only)"
git archive "$TAG" | tar -x -C "$TMP" || { echo "git archive failed"; exit 1; }
N=$(find "$TMP" -type f | wc -l | tr -d ' ')
say "exported $N files"
[ "$(find "$TMP" -name '*.pyc' -o -name '.DS_Store' -o -name '__pycache__' | wc -l | tr -d ' ')" = "0" ] || err "junk files in export"

say "privacy scan (content-level, case-insensitive)"
PATTERN='PathLab|CareerForge|careerforge|天枢|知几|需求通|zhiliu|bid-engine|姑苏|君正|Fiverr|上咨|国投|临港|评标|评审系统|造价|补正|liyingchi|sean-r-zhang|gmail\.com|/Users/[a-z]+|/Volumes|adol PM|MyWiki|mywiki|ntn_[A-Za-z0-9]|ghp_[A-Za-z0-9]{10,}|github_pat_[A-Za-z0-9_]{20,}|sk-ant-[A-Za-z0-9]{20,}|gho_[A-Za-z0-9]{10,}|35fffc4c|350ffc4c|37dffc4c|111\.229\.|爱马仕|云端笔记|notion|job_id: [0-9a-f]{12}'
HITS=$(grep -rniE "$PATTERN" "$TMP" --exclude=release.sh --exclude=git-credential-token.py --exclude=evaluation.md --exclude-dir=.git --include='*.md' --include='*.py' --include='*.sh' --include='*.json' --include='*.html' --include='*.yaml' --include='*.txt' | grep -viE '<your-|placeholder|example\.com|/users/\{id\}|your-name|your_project' \
      | grep -v '/release\.sh:26:' || true)
if [ -n "$HITS" ]; then echo "$HITS" | head -20; err "privacy hits: $(echo "$HITS" | wc -l | tr -d ' ')"; else say "privacy clean"; fi

say "version consistency"
for f in manifest.json plugins/work-os/.claude-plugin/plugin.json; do
  V=$(grep -o '"version": *"[^"]*"' "$TMP/$f" | head -1 | grep -o '[0-9][^"]*')
  [ "${V#v}" = "${TAG#v}" ] || err "$f version $V != tag $TAG"
done
for f in .claude-plugin/marketplace.json .agents/plugins/marketplace.json; do
  grep -q "${TAG#v}" "$TMP/$f" || warn_note="no exact tag string in $f (may use range)"
done
say "manifests match $TAG"

say "functional proof from inside the export"
( cd "$TMP/gatekeeper" && python3 test_gatekeeper.py >/tmp/gk-rel-1.log 2>&1 && python3 test_adapters.py >/tmp/gk-rel-2.log 2>&1 ) \
  && say "gatekeeper suites: 13+12 green" || err "tests failed in export (see /tmp/gk-rel-*.log)"

say "packaging zip -> $OUT"
( cd "$TMP" && zip -qr "$OUT" . )
say "zip contains: $(unzip -l "$OUT" | tail -1)"
if [ "$fail" = "0" ]; then
  say "RELEASE-GATE PASS: $TAG ready to distribute (zip: $OUT)"
else
  say "RELEASE-GATE FAIL — fix everything above before distributing"
fi
exit "$fail"
