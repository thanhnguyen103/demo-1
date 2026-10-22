#!/usr/bin/env bash
# Read-only check that everything the recording runbook needs is in place.
cd "$(git rev-parse --show-toplevel)"
TOKEN=${GITLAB_DEMO_TOKEN:-glpat-hve-demo-local-token-0001}
P="http://localhost:8929/api/v4/projects/root%2Fpayment-demo"
fail=0
check() { if eval "$2" >/dev/null 2>&1; then echo "✅ $1"; else echo "❌ $1  → $3"; fail=1; fi; }
mr_open() { curl -sf -H "PRIVATE-TOKEN: $TOKEN" "$P/merge_requests?state=opened&per_page=100" \
  | python3 -c "import sys,json;sys.exit(0 if any(m['title'].startswith('$1') and m['draft'] for m in json.load(sys.stdin)) else 1)"; }

check "GitLab up" '[ "$(curl -s -o /dev/null -w %{http_code} http://localhost:8929/users/sign_in)" = 200 ]' "docker compose -f gitlab-local/docker-compose.yml up -d"
check "MR !402 merged" 'curl -sf -H "PRIVATE-TOKEN: $TOKEN" $P/merge_requests/402 | grep -q "\"state\":\"merged\""' "python3 gitlab-local/seed-scene3.py"
check "Copilot automation exists + enabled" '[ "$(sqlite3 "file:$HOME/.copilot/data.db?mode=ro" "select count(*) from workflows where name like '"'"'GitLab Nightly HVE%'"'"' and enabled=1")" -ge 1 ]' "create it in the Copilot app (Automations)"
check "Scene 2 clear for live run (no open [HVE-AutoFix] MR)" '! mr_open "Draft: [HVE-AutoFix]"' "./demo/reset-scene2.sh"
check "Scene 2 clear for live run (no hve-autofix/* branch)" '[ "$(curl -sf -H "PRIVATE-TOKEN: $TOKEN" "$P/repository/branches?search=%5Ehve-autofix%2F" | python3 -c "import sys,json;print(len(json.load(sys.stdin)))")" = 0 ]' "./demo/reset-scene2.sh"
check "Scene 3 Draft MR [Harness²]" 'mr_open "Draft: [Harness²]"' "./harness2-hve/run.sh --mr 402 --open-mr"
check "Kotlin backend :8081" '[ "$(curl -s -o /dev/null -w %{http_code} localhost:8081/api/payments/x/receipt)" = 404 ]' "cd payment-backend/kotlin-service && ./gradlew run"
check "Angular :4200" 'curl -sf localhost:4200' "cd frontend && npm start"
git fetch -q "http://oauth2:$TOKEN@localhost:8929/root/payment-demo.git" main 2>/dev/null
# Demo files are uncommitted: snapshot the working tree (as setup.sh does) and compare trees.
IDX=$(mktemp); GIT_INDEX_FILE=$IDX git read-tree HEAD; GIT_INDEX_FILE=$IDX git add -A 2>/dev/null; GIT_INDEX_FILE=$IDX git add -f .github
TREE=$(GIT_INDEX_FILE=$IDX git write-tree); rm -f "$IDX"
check "Demo files = buggy baseline" 'git diff --quiet FETCH_HEAD $TREE -- payment-backend frontend/src .gitlab-ci.yml .github' "./demo/reset-take.sh"
check "HVE prompts present" '[ -f .github/prompts/hve-review.prompt.md ] && [ -f .github/prompts/gitlab-nightly-gate.prompt.md ]' "restore .github/prompts"

[ $fail = 0 ] && echo "ALL GREEN: hand over to Claude Desktop" || { echo "Fix the ❌ items first"; exit 1; }
