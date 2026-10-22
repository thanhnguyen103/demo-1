#!/usr/bin/env bash
# Restores the buggy demo files from GitLab main (the pushed baseline). Overwrites local edits in these paths only.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
git fetch -q "http://oauth2:${GITLAB_DEMO_TOKEN:-glpat-hve-demo-local-token-0001}@localhost:8929/root/payment-demo.git" main
git restore --source=FETCH_HEAD --worktree -- payment-backend frontend/src .gitlab-ci.yml .github
echo "Demo files reset to GitLab main ($(git rev-parse --short FETCH_HEAD))"
