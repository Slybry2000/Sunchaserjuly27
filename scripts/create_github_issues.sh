#!/usr/bin/env bash
# Create GitHub issues from markdown drafts in the `issues/` folder using the `gh` CLI.
# Usage: ./scripts/create_github_issues.sh
# Requires: GitHub CLI `gh` installed and authenticated, run from repository root.

set -euo pipefail

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI not found. Install it from https://cli.github.com/ and authenticate 'gh auth login'"
  exit 1
fi

for f in issues/*.md; do
  echo "Processing $f"
  title=$(grep -m1 "^Title: " "$f" | sed 's/^Title: //')
  body=$(sed -n '/^Body:/,$p' "$f" | sed '1d')
  labels=$(grep -m1 "^labels:" -n "$f" || true)
  # create issue
  if [ -n "$title" ]; then
    if [ -n "$labels" ]; then
      gh issue create --title "$title" --body "$body" --label "$(grep '^labels:' "$f" | sed 's/labels: //')"
    else
      gh issue create --title "$title" --body "$body"
    fi
  fi
done

echo "Done. Created issues from drafts (if gh auth is configured)."
