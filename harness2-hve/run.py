#!/usr/bin/env python3
"""Runs the real Harness² loop (google-research/harness2) on the HVE Core code reviewer.

Harness  = the HVE rules (.github/instructions/company-security-stack.instructions.md) as systemprompt.md
Task     = review the code of GitLab MR !<iid> as first submitted (before the Tech Lead's review)
Executor = `claude -p` reviewer that may only report violations of written rules
Editors  = Harness² propose / compose / select / experience sessions on Claude Code

The Tech Lead's review comment is never shown to the loop; it is only used afterwards to check
whether the adopted harness catches what the human caught. With --open-mr the adopted rules
become a Draft MR on GitLab, opened by hve-bot.
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from harness2.core import tree
from harness2.core.proposer import _DROP_ENV, Proposer
from harness2.core.schedule import run_domain
from harness2.core.spec import BenchPrompts, BenchSpec, ChannelSpec
from harness2.substrate.opencode import OpencodeSubstrate

REPO = Path(__file__).resolve().parent.parent
RULES = REPO / ".github/instructions/company-security-stack.instructions.md"
API = "http://localhost:8929/api/v4"
PROJECT = urllib.parse.quote("root/payment-demo", safe="")
ROOT_TOKEN = os.environ.get("GITLAB_DEMO_TOKEN", "glpat-hve-demo-local-token-0001")
BOT_TOKEN = os.environ.get("GITLAB_BOT_TOKEN", "glpat-hve-bot-local-token-0001")
DOMAIN = "payment-backend"

TASK_PROMPT = """Bạn là reviewer code của team Payment. Thư mục làm việc chứa code của một Merge Request
(xem MR.md) đúng như lúc tác giả gửi review.

Review code đó theo bộ quy tắc của team trong system prompt.
- CHỈ báo vi phạm các quy tắc được viết trong system prompt. Không báo vấn đề nào ngoài các quy tắc đó.
- Ghi kết quả vào file review.md trong thư mục làm việc. Mỗi vi phạm một mục:
  `- <file>:<dòng> | <quy tắc bị vi phạm, trích nguyên văn> | <cách sửa>`
- Nếu không có vi phạm nào, ghi đúng một dòng: `Không có vi phạm.`
"""


def gitlab(path: str, token: str = ROOT_TOKEN, method: str = "GET", body: dict | None = None, raw=False):
    req = urllib.request.Request(
        f"{API}{path}", method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"PRIVATE-TOKEN": token, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        data = r.read()
    return data.decode() if raw else json.loads(data)


def rules_body() -> tuple[str, str]:
    """(frontmatter, body) of the HVE instructions file."""
    text = RULES.read_text(encoding="utf-8")
    m = re.match(r"(---\n.*?\n---\n)(.*)", text, re.S)
    return (m.group(1), m.group(2).lstrip("\n")) if m else ("", text)


class ClaudeProposer(Proposer):
    """Harness²'s claude_cli channel forces Vertex AI; this one uses the local Claude Code login."""

    def env(self) -> dict[str, str]:
        e = {k: v for k, v in os.environ.items() if k not in _DROP_ENV}
        e["ANTHROPIC_MODEL"] = self.spec.model
        return e


class HveReviewAdapter:
    def __init__(self, root: Path, mr_iid: int, executor_model: str, editor: ChannelSpec):
        self.root, self.mr_iid, self.executor_model = root, mr_iid, executor_model
        self.substrate = OpencodeSubstrate()
        self.spec = BenchSpec(
            name="hve",
            runs_root=root / "runs",
            install_mode="workspace_config",
            prompts=BenchPrompts(
                work=(
                    "review a merge request of a Kotlin/Scala payment backend against the team's "
                    "written rules, and report every rule violation with file:line, the rule and the fix"
                ),
                domain_word="codebase",
                deliverable_word="review",
                # Deliberately neutral: no hint at money/rounding or at "add a rule" as the fix.
                domain_guidance="A payment backend written in Kotlin and Scala.",
            ),
            channels={"proposer": editor, "selector": editor},
        )
        self.task_id = f"mr-{mr_iid}"
        self._prepare()

    def _prepare(self) -> None:
        _, body = rules_body()
        base = {name: "" for name in self.substrate.surface().always_on}
        base["systemprompt.md"] = body
        tree.write_tree(self.substrate.surface(), base, self.base_harness(), stubs=False)

        # The MR exactly as first submitted: its first commit, before review feedback.
        mr = gitlab(f"/projects/{PROJECT}/merge_requests/{self.mr_iid}")
        commits = gitlab(f"/projects/{PROJECT}/merge_requests/{self.mr_iid}/commits")
        first = commits[-1]["id"]  # API lists newest first
        src = self.task_files(self.task_id)
        shutil.rmtree(src, ignore_errors=True)
        src.mkdir(parents=True)
        for d in gitlab(f"/projects/{PROJECT}/repository/commits/{first}/diff"):
            if d["deleted_file"]:
                continue
            path = d["new_path"]
            content = gitlab(
                f"/projects/{PROJECT}/repository/files/{urllib.parse.quote(path, safe='')}/raw?ref={first}",
                raw=True,
            )
            (src / path).parent.mkdir(parents=True, exist_ok=True)
            (src / path).write_text(content, encoding="utf-8")
        (src / "MR.md").write_text(
            f"# MR !{self.mr_iid}: {mr['title']}\n\n{mr['description'] or ''}\n", encoding="utf-8"
        )

    # --- BenchmarkAdapter -------------------------------------------------------------------
    def tasks(self, split: str = "all") -> list[str]:
        return [self.task_id]

    def domain_of(self, task_id: str) -> str:
        return DOMAIN

    def task_prompt(self, task_id: str) -> str:
        return TASK_PROMPT

    def task_files(self, task_id: str) -> Path:
        return self.root / "sources" / task_id

    def base_harness(self) -> Path:
        return self.root / "base"

    def validate_tree(self, harness: tree.Tree) -> None:
        if not harness.get("systemprompt.md", "").strip():
            raise ValueError("systemprompt.md must hold the team's review rules; it is empty")

    def execute(self, task_id: str, harness_dir: Path | None, run_id: str, *, timeout: int | None = None) -> Path:
        run_dir = self.root / "executions" / run_id
        if self.delivered(run_dir):
            return run_dir
        work = run_dir / "work"
        shutil.rmtree(run_dir, ignore_errors=True)
        shutil.copytree(self.task_files(task_id), work)
        harness = Path(harness_dir or self.base_harness())
        parts = [
            (harness / f).read_text(encoding="utf-8").strip()
            for f in self.substrate.surface().always_on
            if (harness / f).is_file() and (harness / f).read_text(encoding="utf-8").strip()
        ]
        # Harness skills become real Claude Code project skills; skill/script paths the editor wrote
        # (skills/<name>/..., scripts/...) also resolve relative to the workspace.
        for sub in ("skills", "scripts"):
            if (harness / sub).is_dir():
                shutil.copytree(harness / sub, work / sub, dirs_exist_ok=True)
        if (harness / "skills").is_dir():
            shutil.copytree(harness / "skills", work / ".claude" / "skills", dirs_exist_ok=True)
        system = "\n\n---\n\n".join(parts)
        (run_dir / "system.md").write_text(system, encoding="utf-8")
        p = subprocess.run(
            ["claude", "-p", "--model", self.executor_model, "--output-format", "stream-json", "--verbose",
             "--permission-mode", "acceptEdits",
             "--allowedTools", "Read", "Glob", "Grep", "Write", "Edit", "Skill", "Bash(python3 *)",
             "--append-system-prompt", system],
            input=self.task_prompt(task_id), cwd=work, text=True, capture_output=True,
            timeout=timeout or 900,
        )
        (run_dir / "stream.jsonl").write_text(p.stdout, encoding="utf-8")
        if p.returncode != 0:
            (run_dir / "error.txt").write_text(p.stderr[-4000:], encoding="utf-8")
        return run_dir

    def delivered(self, run_dir: Path) -> bool:
        review = run_dir / "work" / "review.md"
        return review.is_file() and bool(review.read_text(encoding="utf-8").strip())

    def trajectory(self, run_dir: Path, *, obs_trunc: int) -> str:
        out = []
        stream = run_dir / "stream.jsonl"
        for line in stream.read_text(encoding="utf-8").splitlines() if stream.is_file() else []:
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            msg = ev.get("message") if isinstance(ev, dict) else None
            content = msg.get("content") if isinstance(msg, dict) else None
            for block in content if isinstance(content, list) else []:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_use":
                    out.append(f"[ACTION] {block['name']} {json.dumps(block.get('input'), ensure_ascii=False)[:2000]}")
                elif block.get("type") == "tool_result":
                    c = block.get("content")
                    text = c if isinstance(c, str) else json.dumps(c, ensure_ascii=False)
                    out.append(("[ERROR] " if block.get("is_error") else "[OBSERVATION] ") + text[:obs_trunc])
                elif block.get("type") == "text" and ev.get("type") == "assistant":
                    out.append(f"[ACTION] say: {block['text'][:2000]}")
        if (run_dir / "error.txt").is_file():
            out.append("[ERROR] " + (run_dir / "error.txt").read_text(encoding="utf-8"))
        return "\n".join(out) or "[ERROR] no trajectory captured"

    def deliverable_text(self, run_dir: Path) -> str:
        review = run_dir / "work" / "review.md"
        return review.read_text(encoding="utf-8") if review.is_file() else ""

    def deliverable_files(self, run_dir: Path) -> dict[str, str]:
        return {"review.md": self.deliverable_text(run_dir)}


def reviewer_line(mr_iid: int) -> tuple[str, int, str]:
    """(file, line, body) of the first reviewer thread on the MR: the human verdict."""
    for d in gitlab(f"/projects/{PROJECT}/merge_requests/{mr_iid}/discussions"):
        note = d["notes"][0]
        if not note["system"] and note.get("position"):
            return note["position"]["new_path"], note["position"]["new_line"], note["body"]
    raise SystemExit(f"MR !{mr_iid} has no line comment to check against")


def caught(review: str, path: str, line: int) -> bool:
    name = Path(path).name
    return any(name in row and re.search(rf"\b{line}\b", row) for row in review.splitlines())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mr", type=int, default=402)
    ap.add_argument("--k", type=int, default=1)
    ap.add_argument("--editor-model", default=os.environ.get("HVE_EDITOR_MODEL", "opus"))
    ap.add_argument("--executor-model", default=os.environ.get("HVE_EXECUTOR_MODEL", "sonnet"))
    # Outside $HOME: the isolation denies every read under ~, so run folders must live elsewhere.
    ap.add_argument("--out", type=Path, default=Path(tempfile.gettempdir()) / "harness2-hve")
    ap.add_argument("--open-mr", action="store_true", help="open a Draft MR with the adopted rules")
    args = ap.parse_args()

    root = args.out.resolve() / f"mr-{args.mr}-k{args.k}"
    if root.is_relative_to(Path.home()):
        raise SystemExit(f"--out must be outside {Path.home()} (isolation denies reads under ~)")
    # Every `claude` session (Harness² editors and our reviewers) runs through isolation/claude:
    # no web tools, no MCP, no reads under ~, Bash sandboxed without network.
    os.environ["PATH"] = f"{Path(__file__).resolve().parent / 'isolation'}{os.pathsep}{os.environ['PATH']}"
    editor = ChannelSpec("claude_cli", args.editor_model, effort="high", timeout=1800)
    adapter = HveReviewAdapter(root, args.mr, args.executor_model, editor)
    prop = ClaudeProposer(editor, audit_dir=root / "audit")
    library = root / "library"
    result = run_domain(DOMAIN, adapter.tasks(), args.k, adapter=adapter, prop=prop,
                        runs_root=adapter.spec.runs_root, library_root=library, modes=("agg",))
    (root / "result.json").write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    if result["failed"]:
        print(json.dumps(result, indent=2, default=str))
        return 1

    # Human verdict check, done only after Harness² has committed to its choice.
    path, line, comment = reviewer_line(args.mr)
    print(f"\nTech Lead flagged {path}:{line}. Did each reviewer run catch it?")
    for review in sorted((root / "executions").rglob("work/review.md")):
        run = review.parent.parent
        print(f"  {'✅' if caught(adapter.deliverable_text(run), path, line) else '❌'} {run.name}")

    adopted_dir = next(library.glob(f"agg/*/harnesses/{adapter.task_id}"), None)
    if adopted_dir is None:
        print("\nHarness² kept the base harness (KEEP_BASE): nothing learned, no MR.")
        return 0
    experience = (adopted_dir / "EXPERIENCE.md").read_text(encoding="utf-8")
    new_body = (adopted_dir / "harness/systemprompt.md").read_text(encoding="utf-8")
    front, old_body = rules_body()
    diff = "".join(difflib.unified_diff(old_body.splitlines(True), new_body.splitlines(True),
                                        "systemprompt.md (base)", "systemprompt.md (adopted)"))
    m = re.search(r"adopted: `([^`]+)`.*?run `([^`]+)`", experience)
    adopted_run = root / "executions" / m.group(2) if m else None
    adopted_ok = bool(adopted_run and caught(adapter.deliverable_text(adopted_run), path, line))
    print(f"\nAdopted harness: {m.group(1) if m else '?'} | catches Tech Lead's line: {'✅' if adopted_ok else '❌'}")
    print(f"\n{experience}\n\n{diff or '(systemprompt.md unchanged; edits were in other harness files)'}")
    (root / "systemprompt.diff").write_text(diff, encoding="utf-8")

    if not args.open_mr:
        print(f"\nDry run. Re-run with --open-mr to open the Draft MR. Artifacts: {root}")
        return 0
    if not diff:
        print("\nNo change to the rules text, so no MR.")
        return 0
    branch = f"harness2/learn-mr-{args.mr}"
    q_branch = urllib.parse.quote(branch, safe="")
    rules_path = str(RULES.relative_to(REPO))
    try:
        gitlab(f"/projects/{PROJECT}/repository/branches/{q_branch}", BOT_TOKEN)
    except urllib.error.HTTPError:
        gitlab(f"/projects/{PROJECT}/repository/branches?branch={q_branch}&ref=develop", BOT_TOKEN, "POST")
        gitlab(f"/projects/{PROJECT}/repository/commits", BOT_TOKEN, "POST", {
            "branch": branch, "commit_message": f"docs(hve): thêm quy tắc Harness² học từ MR !{args.mr}",
            "actions": [{"action": "update", "file_path": rules_path, "content": front + "\n" + new_body}],
        })
    report = vietnamese_report(experience, args.editor_model)
    # Title names the added rule by its bold label, e.g. "**Tiền tệ (Bắt buộc):**" -> "Tiền tệ".
    added = [l for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")]
    label = next((m.group(1) for l in added if (m := re.search(r"\*\*([^*(:]+)", l))), "mới")
    title = f"Thêm quy tắc {label.strip()} từ MR !{args.mr}"
    check = (f"Trưởng nhóm kỹ thuật đã bình luận tại `{path}:{line}` trong MR !{args.mr}. Bộ rà soát dùng quy tắc mới "
             f"{'**phát hiện được** dòng này ✅' if adopted_ok else '**chưa phát hiện được** dòng này ❌'} "
             "(Harness² hoàn toàn không thấy bình luận đó khi học).")
    fields = {
        "title": f"Draft: [Harness²] {title}",
        "description": (
            f"Harness² đã chạy vòng Đề xuất – Thăm dò – Kết hợp trên bộ rà soát mã HVE Core, với nhiệm vụ "
            f"rà soát mã của MR !{args.mr} ngay lúc vừa gửi.\n\n"
            f"## Đối chiếu với nhận xét của con người\n\n{check}\n\n"
            f"## Báo cáo của Harness²\n\n{report}\n\n"
            "---\n🤖 Tạo tự động bởi [google-research/harness2](https://github.com/google-research/harness2) "
            "(giấy phép Apache-2.0), chạy trên Claude Code. Cần trưởng nhóm kỹ thuật duyệt trước khi hợp nhất."
        ),
    }
    existing = gitlab(f"/projects/{PROJECT}/merge_requests?state=opened&source_branch={q_branch}", BOT_TOKEN)
    if existing:
        mr = gitlab(f"/projects/{PROJECT}/merge_requests/{existing[0]['iid']}", BOT_TOKEN, "PUT", fields)
    else:
        mr = gitlab(f"/projects/{PROJECT}/merge_requests", BOT_TOKEN, "POST",
                    {"source_branch": branch, "target_branch": "develop", **fields})
    print(f"\nDraft MR: {mr['web_url']}\n{mr['title']}")
    return 0


def vietnamese_report(experience: str, model: str) -> str:
    """Harness² writes EXPERIENCE.md in English; translate it for the Vietnamese team."""
    prompt = (
        "Dịch báo cáo dưới đây sang tiếng Việt hoàn toàn, kể cả tiêu đề và các nhãn "
        "(adopted, components, candidates, change, observed, verdict, cue, lesson, evidence, confidence). "
        "Dịch cả các đoạn trích trong ngoặc kép. Chỉ giữ nguyên: định dạng Markdown, mọi thứ trong dấu `...`, "
        "tên file, tên run (base1, inv1, dom1, agg1) và tên riêng (Harness², Claude Code, GitLab). "
        "Dịch tự nhiên cho lập trình viên Việt Nam, sửa lỗi gõ dấu tiếng Việt hiển nhiên, "
        "không để lại từ tiếng Anh nào ngoài những thứ được giữ nguyên ở trên. Bảng thuật ngữ bắt buộc: "
        "review/reviewer → rà soát/bộ rà soát; run/rollout → lượt chạy; skill → kỹ năng; "
        "system prompt → lời nhắc hệ thống; workspace → thư mục làm việc; checker/verifier → trình kiểm tra; "
        "hardcode → ghi cứng; deliverable → kết quả bàn giao; chat → phần trả lời; "
        "trivial pool → chỉ có một ứng viên; confounded → chưa tách được nguyên nhân; "
        "always-on → luôn nạp; trigger line → dòng kích hoạt; blocking I/O → I/O chặn; logger → bộ ghi log. "
        "không thêm, bớt hay diễn giải nội dung.\n"
        'Chỉ trả về JSON: {"report": "..."}\n\n---\n\n' + experience
    )
    p = subprocess.run(["claude", "-p", "--model", model, "--output-format", "json"],
                       input=prompt, text=True, capture_output=True, timeout=600, check=True)
    text = json.loads(p.stdout)["result"]
    data = json.loads(text[text.index("{"): text.rindex("}") + 1])
    return data["report"].strip()


if __name__ == "__main__":
    raise SystemExit(main())
