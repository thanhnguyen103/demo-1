#!/usr/bin/env python3
"""Seeds MR !402 for Scene 3: a dev ships a refund calc with Double, Tech Lead catches the 1-cent
rounding bug in review, dev fixes it with BigDecimal, MR is merged. Harness² later learns from it.

Run after setup.sh. Safe to re-run (skips if !402 exists).
"""
import json
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request

API = "http://localhost:8929/api/v4"
PROJECT = urllib.parse.quote("root/payment-demo", safe="")
ROOT = "glpat-hve-demo-local-token-0001"
DEV = "glpat-hve-dev-local-token-0001"
LEAD = "glpat-hve-lead-local-token-0001"
BRANCH = "feature/refund"
REFUND = "payment-backend/kotlin-service/src/main/kotlin/payment/Refund.kt"
REFUND_TEST = "payment-backend/kotlin-service/src/test/kotlin/payment/RefundTest.kt"


def call(token, method, path, body=None, ok_missing=False):
    req = urllib.request.Request(
        f"{API}{path}",
        data=json.dumps(body).encode() if body is not None else None,
        method=method,
        headers={"PRIVATE-TOKEN": token, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        if ok_missing and e.code in (404, 409):
            return None
        raise SystemExit(f"{method} {path} -> {e.code}: {e.read().decode()[:300]}")


def file_action(path, ref):
    """'update' if the file already exists on ref (fresh setup.sh pushes the merged Refund.kt), else 'create'."""
    found = call(ROOT, "GET", f"/projects/{PROJECT}/repository/files/{urllib.parse.quote(path, safe='')}?ref={ref}", ok_missing=True)
    return "update" if found else "create"


def rails(code):
    subprocess.run(["docker", "exec", "hve-gitlab", "gitlab-rails", "runner", code], check=True)


def ensure_user(username, name, token, access_level):
    if not call(ROOT, "GET", f"/users?username={username}"):
        call(ROOT, "POST", "/users", {
            "username": username, "name": name, "email": f"{username}@example.local",
            "password": subprocess.run(["openssl", "rand", "-hex", "16"], capture_output=True, text=True).stdout.strip() + "Aa1",
            "skip_confirmation": True,
        })
    uid = call(ROOT, "GET", f"/users?username={username}")[0]["id"]
    call(ROOT, "POST", f"/projects/{PROJECT}/members", {"user_id": uid, "access_level": access_level}, ok_missing=True)
    return f"""
      u = User.find_by_username('{username}')
      u.personal_access_tokens.where(name: 'hve-demo').delete_all
      t = u.personal_access_tokens.new(name: 'hve-demo', scopes: %i[api], expires_at: 30.days.from_now)
      t.set_token('{token}')
      t.save!
    """


V1 = """package payment

import kotlin.math.round

/** Hoàn tiền: trả lại khách 98.5% số tiền, giữ lại phí xử lý 1.5%. */
fun refundAmount(amount: Double): Double = round(amount * 0.985 * 100) / 100
"""

V2 = """package payment

import java.math.BigDecimal
import java.math.RoundingMode

/** Hoàn tiền: trả lại khách 98.5% số tiền, giữ lại phí xử lý 1.5%. */
fun refundAmount(amount: BigDecimal): BigDecimal =
    (amount * BigDecimal("0.985")).setScale(2, RoundingMode.HALF_EVEN)
"""

TEST = """package payment

import java.math.BigDecimal
import kotlin.test.Test
import kotlin.test.assertEquals

class RefundTest {
    @Test
    fun `refund 11_00 is 10_84, not 10_83`() {
        assertEquals(BigDecimal("10.84"), refundAmount(BigDecimal("11.00")))
    }
}
"""

REVIEW = """🚨 **Không dùng `Double` cho tiền.**

`11.00 * 0.985` trong `Double` = `10.834999999999999` → làm tròn ra **10.83**, đúng phải là **10.84** (`10.835` HALF_EVEN). Khách bị hoàn thiếu 1 xu mỗi giao dịch kiểu này; với volume refund hàng ngày là lệch sổ đối soát.

Đổi sang `BigDecimal` + `RoundingMode.HALF_EVEN` (chuẩn ngân hàng), và nhận `BigDecimal` ngay từ lúc deserialize JSON (Jackson/Circe), đừng đi qua `Double`. Thêm test cho case `11.00`."""


def main():
    if call(ROOT, "GET", f"/projects/{PROJECT}/merge_requests/402", ok_missing=True):
        print("MR !402 already exists, nothing to do.")
        return

    print("Creating dev-payment / tech-lead users + tokens")
    rails(
        ensure_user("dev-payment", "Payment Dev", DEV, 30)
        + ensure_user("tech-lead", "Tech Lead", LEAD, 40)
        # Next MR in this project gets iid 402, to match the demo script.
        + "p = Project.find_by_full_path('root/payment-demo'); InternalId.where(project: p, usage: :merge_requests).update_all(last_value: 401)"
    )

    print("Dev opens MR with Double-based refund")
    call(DEV, "POST", f"/projects/{PROJECT}/repository/branches?branch={urllib.parse.quote(BRANCH, safe='')}&ref=develop")
    call(DEV, "POST", f"/projects/{PROJECT}/repository/commits", {
        "branch": BRANCH, "commit_message": "feat(refund): tính tiền hoàn cho khách",
        "actions": [{"action": file_action(REFUND, BRANCH), "file_path": REFUND, "content": V1}],
    })
    mr = call(DEV, "POST", f"/projects/{PROJECT}/merge_requests", {
        "source_branch": BRANCH, "target_branch": "develop",
        "title": "feat(refund): tính tiền hoàn cho khách (98.5%)",
        "description": "Thêm `refundAmount()` cho luồng hoàn tiền: trả lại 98.5%, giữ phí xử lý 1.5%.",
    })
    iid = mr["iid"]
    assert iid == 402, f"expected iid 402, got {iid}"

    print("Tech Lead leaves a line comment")
    for _ in range(30):
        versions = call(LEAD, "GET", f"/projects/{PROJECT}/merge_requests/{iid}/versions")
        if versions and versions[0].get("head_commit_sha"):
            break
        time.sleep(2)
    v = versions[0]
    disc = call(LEAD, "POST", f"/projects/{PROJECT}/merge_requests/{iid}/discussions", {
        "body": REVIEW,
        "position": {
            "position_type": "text", "base_sha": v["base_commit_sha"], "start_sha": v["start_commit_sha"],
            "head_sha": v["head_commit_sha"], "new_path": REFUND, "old_path": REFUND, "new_line": 6,
        },
    })

    print("Dev fixes with BigDecimal + test, replies")
    call(DEV, "POST", f"/projects/{PROJECT}/repository/commits", {
        "branch": BRANCH, "commit_message": "fix(refund): dùng BigDecimal + HALF_EVEN thay cho Double",
        "actions": [
            {"action": "update", "file_path": REFUND, "content": V2},
            {"action": file_action(REFUND_TEST, BRANCH), "file_path": REFUND_TEST, "content": TEST},
        ],
    })
    call(DEV, "POST", f"/projects/{PROJECT}/merge_requests/{iid}/discussions/{disc['id']}/notes",
         {"body": "Đã đổi sang `BigDecimal` + `RoundingMode.HALF_EVEN`, thêm `RefundTest` cho case `11.00 → 10.84`. Cảm ơn anh!"})

    print("Tech Lead resolves, approves, merges")
    call(LEAD, "PUT", f"/projects/{PROJECT}/merge_requests/{iid}/discussions/{disc['id']}?resolved=true")
    call(LEAD, "POST", f"/projects/{PROJECT}/merge_requests/{iid}/approve")
    call(LEAD, "POST", f"/projects/{PROJECT}/merge_requests/{iid}/notes", {"body": "LGTM 👍 Lỗi này nên thành quy tắc chung cho cả team."})
    for _ in range(30):
        req = urllib.request.Request(
            f"{API}/projects/{PROJECT}/merge_requests/{iid}/merge?should_remove_source_branch=true",
            method="PUT", headers={"PRIVATE-TOKEN": LEAD})
        try:
            urllib.request.urlopen(req)
            break
        except urllib.error.HTTPError as e:
            if e.code not in (405, 406, 409, 422):
                raise
            time.sleep(3)
    else:
        raise SystemExit("MR !402 could not be merged")

    print(f"Done: http://localhost:8929/root/payment-demo/-/merge_requests/{iid}")


if __name__ == "__main__":
    main()
