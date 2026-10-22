#!/usr/bin/env bash
# Installs google-research/harness2 (pinned) into harness2-hve/.venv with uv, then runs run.py.
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  uv venv -q --python 3.12 .venv
  uv pip install -q --python .venv/bin/python "harness2 @ git+https://github.com/google-research/harness2@1cfe254e8d25b15f37048c3730134686abe60335"
fi
exec .venv/bin/python run.py "$@"
