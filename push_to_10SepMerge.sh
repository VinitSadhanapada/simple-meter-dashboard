#!/usr/bin/env bash
# push_to_10SepMerge.sh
# Push the current (or provided) branch to the existing GitHub repo '10SepMerge'
# Usage:
#   ./push_to_10SepMerge.sh YOUR_GITHUB_USERNAME [BRANCH]
# Example:
#   ./push_to_10SepMerge.sh isha 20NovMain

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 YOUR_GITHUB_USERNAME [BRANCH]"
  exit 2
fi

GITHUB_USER="$1"
BRANCH="${2:-}"
REPO_NAME="10SepMerge"
REMOTE_URL="git@github.com:${GITHUB_USER}/${REPO_NAME}.git"

# ensure inside a git repo
if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Not a git repository. Run this from the repository root." >&2
  exit 3
fi

# determine branch if not provided
if [[ -z "$BRANCH" ]]; then
  BRANCH=$(git rev-parse --abbrev-ref HEAD)
  if [[ "$BRANCH" == "HEAD" ]]; then
    echo "You are in a detached HEAD. Provide a branch name explicitly." >&2
    exit 4
  fi
fi

echo "Branch to push: $BRANCH"

# Create branch locally if missing
if ! git show-ref --verify --quiet "refs/heads/${BRANCH}"; then
  echo "Local branch ${BRANCH} doesn't exist. Creating from current HEAD." 
  git switch -c "${BRANCH}"
else
  echo "Switching to local branch ${BRANCH}"
  git switch "${BRANCH}"
fi

# Commit any uncommitted changes as safe WIP commit
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Uncommitted changes detected. Making a WIP commit."
  git add -A
  if ! git diff --cached --quiet; then
    git commit -m "WIP: snapshot before pushing ${BRANCH} -- $(date --iso-8601=seconds)" || true
  fi
fi

# Quick SSH connectivity check (non-fatal)
if ssh -T -o BatchMode=yes git@github.com 2>&1 | grep -q "successfully authenticated"; then
  echo "SSH to github.com OK"
else
  echo "Warning: SSH to github.com may not be authenticated. You may be prompted for a password or the push may fail."
  echo "If you prefer HTTPS, use the https URL manually instead."
fi

# Push directly to remote URL (does not alter configured remotes)
echo "Pushing ${BRANCH} -> ${REMOTE_URL}:${BRANCH}"
# Use --progress to show progress for large pushes; use --set-upstream to track
if git push --progress "${REMOTE_URL}" "${BRANCH}:refs/heads/${BRANCH}" -u; then
  echo "Push succeeded. Now local branch ${BRANCH} tracks ${GITHUB_USER}/${REPO_NAME}:${BRANCH}"
  exit 0
else
  echo "Push failed. Possible network/timeout or remote rejected the push." >&2
  echo "If the push failed due to size/timeouts, try one of the following:" >&2
  echo " - Ensure SSH keys are registered with GitHub and retry (recommended)." >&2
  echo " - Create a shallow snapshot and push from it (see script docs)." >&2
  echo " - Increase git http.postBuffer and retry (only for HTTPS pushes)." >&2
  exit 5
fi
