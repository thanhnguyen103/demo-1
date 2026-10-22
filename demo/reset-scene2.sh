#!/usr/bin/env bash
# Clears the way for a live Scene 2 take: the automation skips if an [HVE-AutoFix] MR is open, and fails
# if its branch hve-autofix/<date> already exists. Closes open hve-autofix MRs (kept in history) and
# deletes hve-autofix/* branches. Closed MRs keep their diffs after the branch is gone.
set -euo pipefail
TOKEN=${GITLAB_DEMO_TOKEN:-glpat-hve-demo-local-token-0001}
P="http://localhost:8929/api/v4/projects/root%2Fpayment-demo"
api() { curl -sf -H "PRIVATE-TOKEN: $TOKEN" "$@"; }

for iid in $(api "$P/merge_requests?state=opened&per_page=100" \
  | python3 -c "import sys,json;print(' '.join(str(m['iid']) for m in json.load(sys.stdin) if m['source_branch'].startswith('hve-autofix/')))"); do
  api -X PUT "$P/merge_requests/$iid?state_event=close" >/dev/null && echo "closed !$iid"
done
for b in $(api "$P/repository/branches?search=%5Ehve-autofix%2F&per_page=100" \
  | python3 -c "import sys,json;print(' '.join(b['name'] for b in json.load(sys.stdin)))"); do
  api -X DELETE "$P/repository/branches/$(python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1],safe=''))" "$b")" && echo "deleted branch $b"
done
echo "Scene 2 ready for a live run."
