# Payment demo — HVE Core (GitLab + Scala/Kotlin + Angular)

Code chạy được, cố ý chứa các lỗi trong `demo.md` để HVE Core review bắt.

## Chạy

```bash
# Backend Kotlin (Ktor) — :8081
cd payment-backend/kotlin-service && ./gradlew run

# Backend Scala (JDK HttpServer + circe) — :8082
cd payment-backend/scala-service && sbt run

# Frontend Angular — http://localhost:4200 (proxy /api -> :8081, đổi trong proxy.conf.json)
cd frontend && npm install && npm start
```

Test: `./gradlew test` (Kotlin), `sbt test` (Scala), `npx ng build` (Angular).

## Tái hiện lỗi trên sân khấu

| Lỗi | Cách thấy |
|---|---|
| Lộ số thẻ/CVV ra log | Bấm *Thanh toán*, nhìn console backend: `Start payment: PaymentReq(... cardNumber=4111111111111234, cvv=123 ...)` |
| XSS | Ghi chú = `<img src=x onerror="alert('XSS')">` → popup chạy |
| `Double` cho tiền | Số tiền `10.05` → Tổng `10.200750000000001` |
| Blocking I/O sai dispatcher | `Thread.sleep` trong gateway chạy trên `Dispatchers.Default` / `ExecutionContext.global` |
| Memory leak | `payment-receipt.component.ts` subscribe không `takeUntilDestroyed()` |
| Supply chain / secret | `.gitlab-ci.yml`: `:latest`, không digest, `echo $PAYMENT_GATEWAY_API_KEY` |

Review: mở file lỗi trong VS Code, chạy prompt `/hve-review`.

## GitLab local (Docker)

```bash
./gitlab-local/setup.sh      # GitLab CE + Runner, tạo root/payment-demo, push code, chạy pipeline
```

- GitLab: http://localhost:8929 — `root` / `HveDemo-2026!` (cần ~5 GB RAM cho Docker)
- Script push snapshot working tree lên `main` và `develop` (không đụng branch local). Sửa code → chạy lại script.
- GitLab MCP cho Copilot: `.vscode/mcp.json` (nhập token script in ra).
- Dừng: `docker compose -f gitlab-local/docker-compose.yml stop` · Xoá sạch: `... down -v`

## Cảnh 2: Copilot Automation

- Prompt: `.github/prompts/gitlab-nightly-gate.prompt.md`
- MCP `gitlab` của Copilot app: `~/.copilot/mcp-config.json`, chạy bằng user `hve-bot` (Developer).
- 3 lớp khoá quyền: MCP chỉ có 3 tool ghi (`create_branch`, `push_files`, `create_merge_request`) · `hve-bot` là Developer · `main`/`develop` protected (chỉ Maintainer merge/push).

## Cảnh 3: Harness² (Propose – Probe – Compose)

```bash
python3 gitlab-local/seed-scene3.py   # tạo MR !402: Double → Tech Lead review → BigDecimal → merged
```

- MR !402: http://localhost:8929/root/payment-demo/-/merge_requests/402 (`refundAmount(11.00)`: Double ra 10.83, đúng là 10.84)
- Vòng lặp thật [google-research/harness2](https://github.com/google-research/harness2): `./harness2-hve/run.sh --mr 402` (dry run) → thêm `--open-mr` để mở Draft MR `harness2/learn-mr-402`.
- Harness² KHÔNG thấy comment của Tech Lead; comment đó chỉ dùng để kiểm chứng sau khi Harness² đã chọn.
