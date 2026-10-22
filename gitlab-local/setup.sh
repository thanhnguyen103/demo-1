#!/usr/bin/env bash
# Boots local GitLab + Runner, creates root/payment-demo, pushes this repo, triggers pipelines.
# Safe to re-run.
set -euo pipefail

cd "$(dirname "$0")"
REPO_ROOT=$(git rev-parse --show-toplevel)
GITLAB=http://localhost:8929
TOKEN=${GITLAB_DEMO_TOKEN:-glpat-hve-demo-local-token-0001}
PROJECT=payment-demo

docker compose up -d

printf 'Waiting for GitLab (first boot takes 3-5 min)'
until [ "$(curl -s -o /dev/null -w '%{http_code}' "$GITLAB/users/sign_in")" = 200 ]; do printf .; sleep 5; done
echo " up"

api() { curl -sf -H "PRIVATE-TOKEN: $TOKEN" "$@"; }

if ! api "$GITLAB/api/v4/user" >/dev/null 2>&1; then
  echo "Creating root personal access token"
  docker exec hve-gitlab gitlab-rails runner "
    u = User.find_by_username('root')
    u.personal_access_tokens.where(name: 'hve-demo').delete_all
    t = u.personal_access_tokens.new(name: 'hve-demo', scopes: %i[api read_repository write_repository], expires_at: 30.days.from_now)
    t.set_token('$TOKEN')
    t.save!
  "
fi

if ! docker exec hve-runner grep -q '\[\[runners\]\]' /etc/gitlab-runner/config.toml 2>/dev/null; then
  echo "Registering runner"
  RUNNER_TOKEN=$(api -X POST "$GITLAB/api/v4/user/runners" -d runner_type=instance_type -d run_untagged=true -d description=local-docker \
    | python3 -c 'import sys,json;print(json.load(sys.stdin)["token"])')
  # Job containers reach GitLab by service name on the compose network, not localhost.
  docker exec hve-runner gitlab-runner register --non-interactive \
    --url http://gitlab:8929 --clone-url http://gitlab:8929 --token "$RUNNER_TOKEN" \
    --executor docker --docker-image alpine:3.22 --docker-network-mode hve-demo-net
fi

if ! api "$GITLAB/api/v4/projects/root%2F$PROJECT" >/dev/null 2>&1; then
  echo "Creating project root/$PROJECT"
  api -X POST "$GITLAB/api/v4/projects" -d name=$PROJECT -d visibility=private >/dev/null
fi

# Copilot automation identity: Developer role, so GitLab itself refuses merges into protected branches.
BOT_TOKEN=${GITLAB_BOT_TOKEN:-glpat-hve-bot-local-token-0001}
if ! curl -sf -H "PRIVATE-TOKEN: $BOT_TOKEN" "$GITLAB/api/v4/user" >/dev/null 2>&1; then
  echo "Creating hve-bot user + token"
  api -X POST "$GITLAB/api/v4/users" -d username=hve-bot -d "name=HVE Bot" -d email=hve-bot@example.local \
    -d "password=$(openssl rand -hex 16)Aa1" -d skip_confirmation=true >/dev/null 2>&1 || true
  docker exec hve-gitlab gitlab-rails runner "
    u = User.find_by_username('hve-bot')
    u.personal_access_tokens.where(name: 'copilot-automation').delete_all
    t = u.personal_access_tokens.new(name: 'copilot-automation', scopes: %i[api], expires_at: 30.days.from_now)
    t.set_token('$BOT_TOKEN')
    t.save!
  "
fi
BOT_ID=$(api "$GITLAB/api/v4/users?username=hve-bot" | python3 -c 'import sys,json;print(json.load(sys.stdin)[0]["id"])')
api -X POST "$GITLAB/api/v4/projects/root%2F$PROJECT/members" -d user_id="$BOT_ID" -d access_level=30 >/dev/null 2>&1 || true
# main is protected by default; protect develop too (Maintainers only), keep force push for re-seeding.
api -X POST "$GITLAB/api/v4/projects/root%2F$PROJECT/protected_branches" \
  -d name=develop -d push_access_level=40 -d merge_access_level=40 -d allow_force_push=true >/dev/null 2>&1 || true

# Fake secret on purpose: the deploy job echoes it (demo bug), unmasked.
api -X POST "$GITLAB/api/v4/projects/root%2F$PROJECT/variables" \
  -d key=PAYMENT_GATEWAY_API_KEY -d value=sk_test_hve_demo_4242424242 >/dev/null 2>&1 || true

# Push a snapshot of the working tree (incl. uncommitted files and the globally-ignored .github/)
# without touching your local branch or index.
echo "Pushing working tree snapshot to main and develop"
TMP_INDEX=$(mktemp)
trap 'rm -f "$TMP_INDEX"' EXIT
cd "$REPO_ROOT"
GIT_INDEX_FILE=$TMP_INDEX git read-tree HEAD
GIT_INDEX_FILE=$TMP_INDEX git add -A
GIT_INDEX_FILE=$TMP_INDEX git add -f .github
REMOTE="http://oauth2:$TOKEN@localhost:8929/root/$PROJECT.git"
TREE=$(GIT_INDEX_FILE=$TMP_INDEX git write-tree)
# Fast-forward each branch from its own remote head: no force push, keeps merged MRs in history.
for BRANCH in main develop; do
  PARENT=HEAD
  git fetch -q "$REMOTE" "$BRANCH" 2>/dev/null && PARENT=FETCH_HEAD
  [ "$(git rev-parse "$PARENT^{tree}")" = "$TREE" ] && { echo "$BRANCH already up to date"; continue; }
  git push "$REMOTE" "$(git commit-tree "$TREE" -p "$PARENT" -m "HVE demo snapshot"):refs/heads/$BRANCH"
done

cat <<MSG

Done.
  GitLab:    $GITLAB  (root / ${GITLAB_ROOT_PASSWORD:-HveDemo-2026!})
  Project:   $GITLAB/root/$PROJECT
  Pipelines: $GITLAB/root/$PROJECT/-/pipelines
  API token: $TOKEN   (root, for glab / manual use)
  Bot token: $BOT_TOKEN   (hve-bot, Developer: used by Copilot automation MCP)

glab:  glab auth login --hostname localhost:8929 --api-protocol http --git-protocol http --token $TOKEN
MSG
