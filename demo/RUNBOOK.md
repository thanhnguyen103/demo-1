# HVE Core demo: Computer Use recording runbook

Claude Desktop (Computer Use) drives the screen and records **one clip per scene**. You add the voice-over
from `demo.md` afterwards, so the agent's speed does not matter: every `HOLD` gives you a still frame to talk over.

---

## Part A: You, before handing over (≈15 min)

1. Services:
   ```bash
   docker compose -f gitlab-local/docker-compose.yml up -d          # GitLab + runner
   (cd payment-backend/kotlin-service && ./gradlew run) &            # :8081
   (cd frontend && npm start) &                                      # :4200
   ```
2. Scene 2 runs **live** on camera; Scene 3 is pre-made:
   - `./demo/reset-scene2.sh`: closes any open `[HVE-AutoFix]` MR and deletes `hve-autofix/*` branches, so the
     automation neither skips as a duplicate nor fails on an existing branch.
   - Scene 3 Draft MR !403 already exists. Do **not** re-run `harness2-hve/run.sh` before recording.
3. `./demo/reset-take.sh`: puts the demo source files back to the buggy baseline from GitLab `main`.
4. `./demo/preflight.sh`: must print `ALL GREEN`.
5. Screen setup:
   - macOS **Do Not Disturb** on, Dock auto-hide on, close Slack/mail.
   - Display at 1920×1080 (or "More Space" off), Claude Desktop on a **second display** if you have one.
   - Chrome: one window, sign in to GitLab as `root`, bookmarks bar hidden, zoom 125%.
   - VS Code: open `demo-1`, *View → Appearance → Zen Mode* off, font size 18, Copilot Chat panel visible, **Agent** mode selected.
   - `Cmd+Shift+5` → *Options* → Save to **Movies**, **Show Mouse Clicks** on, Microphone **None**.
6. Paste the prompt in Part B into Claude Desktop.

---

## Part B: Prompt to paste into Claude Desktop

> Use Computer Use to record my demo by following `demo/RUNBOOK.md` Part C in the repo at
> `~/Documents/GitHub/demo-1`. Open and read the whole file first. Record each clip separately, follow every
> HOLD, and verify every CHECK. If a CHECK fails, stop that clip and tell me what you saw. Do not improvise steps.
> Obey the "Never do" list absolutely.

---

## Part C: Agent instructions

### Never do

- Never click **Merge**, **Approve**, **Mark as ready**, **Close**, **Delete**, or anything in GitLab *Settings* other than viewing.
- In the Copilot app, click **Run now** only once, only on *GitLab Nightly HVE Quality & Security Gate*, only in Clip 2A. Never edit, pause or delete the automation.
- Never type a password or token. GitLab is already signed in; if you see a sign-in page, stop and report.
- Never edit files by typing in VS Code. Only Copilot makes edits, and only in Clip 1C/1D.
- Never run terminal commands except the two in *Recording controls*.
- Never show the Claude Desktop window inside a clip.

### Recording controls

- **Start clip:** press `Cmd+Shift+5`, choose **Record Entire Screen**, press `Return`. Wait 2 s.
- **Stop clip:** press `Cmd+Ctrl+Esc`. Wait 3 s for the file to save. Note its name in your report.
- **HOLD n:** do nothing for n seconds. Keep the mouse still and out of the way.
- **Highlight:** triple-click the line, or move the mouse slowly to underline it, then HOLD.

### Clip 1A: rules file (`demo.md` 0:00–1:00)

1. Focus VS Code. `Cmd+P` → type `company-security-stack.instructions.md` → `Return`.
2. Start clip. HOLD 3.
3. Highlight the `applyTo:` line (line 3). HOLD 8.
4. Scroll slowly through sections 1, 2, 3 (about 2 s each). HOLD 4.
5. Stop clip.
- CHECK: the `applyTo` line lists `payment-backend/**/*.scala`, `*.kt`, `frontend/src/**/*.ts`, `.gitlab-ci.yml`.

### Clip 1B: the bugs are real (B-roll for 1:00–2:00)

1. In Chrome open `http://localhost:4200`.
2. Start clip. HOLD 3.
3. In **Ghi chú** clear the field and type: `<img src=x onerror="alert('XSS từ cổng thanh toán')">`
4. Click **Thanh toán**. Wait for the popup.
   - CHECK: a browser alert with `XSS từ cổng thanh toán` appears. HOLD 4. Click **OK**.
5. HOLD 3 on the receipt (`Tổng: 10.200750000000001` is visible).
6. Switch to the Terminal running `./gradlew run`. HOLD 5 on the `Start payment: PaymentReq(... cardNumber=4111111111111234, cvv=123 ...)` line.
   - CHECK: card number and CVV are visible in the log.
7. Stop clip.

### Clip 1C: HVE review fixes backend + frontend (1:00–2:00)

1. VS Code: `Cmd+P` → `payment-backend/kotlin-service/src/main/kotlin/payment/PaymentService.kt`.
2. Start clip. HOLD 3. Highlight `logger.info("Start payment: $req")`. HOLD 4.
3. Click the Copilot Chat input, type `/hve-review`, press `Return`.
4. Wait until Copilot finishes (no spinner, summary table shown). Up to 3 min; that's fine, you'll cut it.
   - CHECK: the summary mentions `toString`/masking **and** `Dispatchers.IO`. If not, stop and report.
5. Scroll the editor diff to the new `toString()`. HOLD 6. Click **Keep** (or **Accept**) on the edits.
6. `Cmd+P` → `payment-receipt.component.ts`. Highlight `bypassSecurityTrustHtml`. HOLD 4.
7. Type `/hve-review` in Copilot Chat, `Return`. Wait until done.
   - CHECK: `bypassSecurityTrustHtml` is removed **and** `takeUntilDestroyed` + `OnPush` are added.
8. HOLD 6 on the diff. Click **Keep**.
9. Stop clip.

### Clip 1D: GitLab CI hardening (2:00–3:00)

1. VS Code: `Cmd+P` → `.gitlab-ci.yml`.
2. Start clip. HOLD 3. Highlight `image: node:latest`. HOLD 4.
3. `/hve-review` in Copilot Chat, `Return`. Wait until done.
   - CHECK: every `image:` now has `@sha256:`, the `echo "...$PAYMENT_GATEWAY_API_KEY"` line is gone, `FF_TIMESTAMPS: "true"` is added.
4. HOLD 8 on the diff showing the `@sha256:` lines. Click **Keep**.
5. Stop clip.

### Clip 2A: run the Copilot automation live (3:00–3:50)

1. Open the **GitHub Copilot** desktop app → **Automations**.
2. Start clip. HOLD 3.
3. Click *GitLab Nightly HVE Quality & Security Gate*. HOLD 4 on the schedule (daily 02:00). Scroll the prompt slowly. HOLD 4.
   - CHECK: you see the automation name and its daily 02:00 schedule. If the layout differs, find them visually; if missing, stop and report.
4. Click **Run now**. HOLD 3.
5. Wait for the run to finish (it usually takes about 1 minute). Every 15 s, look without clicking. If the app shows the run's live activity, keep it on screen. Stop waiting after 5 minutes and report.
   - CHECK: the run is marked finished and its final message ends with 3 lines: số vi phạm, trạng thái pipeline, link Draft MR.
   - If the final message says it stopped because an `hve-autofix/` MR is already open, or that it couldn't create the branch, stop the clip and report: I need to run `./demo/reset-scene2.sh`.
6. HOLD 6 on the final 3 lines. Stop clip.

### Clip 2B: the new Draft MR + locked permissions (3:50–4:30)

1. Chrome: `http://localhost:8929/root/payment-demo/-/merge_requests?state=opened`.
2. Start clip. HOLD 3.
3. Click the MR whose title starts with `Draft: [HVE-AutoFix]` (the newest; created a minute ago). HOLD 5 on the title, author `HVE Bot` and "Draft".
   - CHECK: exactly one open `[HVE-AutoFix]` MR exists and it was created just now. If not, stop and report.
4. Scroll the description table slowly. HOLD 5. Click the **Changes** tab. HOLD 6.
5. Open `http://localhost:8929/root/payment-demo/-/project_members`. Highlight the `hve-bot` row (role **Developer**). HOLD 5.
6. Open `http://localhost:8929/root/payment-demo/-/settings/repository`, expand **Protected branches** (view only). HOLD 5 on `main`/`develop` → *Maintainers*.
7. Stop clip.

### Clip 3A: the review that taught us (4:30–5:15)

1. Chrome: `http://localhost:8929/root/payment-demo/-/merge_requests/402`.
2. Start clip. HOLD 3 on title, **Merged** badge.
3. Scroll to the `tech-lead` thread on `Refund.kt` (`🚨 Không dùng Double cho tiền`). HOLD 8.
4. Scroll to the `dev-payment` reply. HOLD 4.
5. Stop clip.

### Clip 3B: Harness² MR updates the rules (5:15–6:00)

1. Chrome: `http://localhost:8929/root/payment-demo/-/merge_requests?state=opened`, click the MR whose title starts with `Draft: [Harness²]`.
2. Start clip. HOLD 4 on title, then scroll the description slowly: *Đối chiếu với nhận xét của con người* (HOLD 5), *Tác dụng của từng chỉnh sửa* (HOLD 5), *Bài học có thể áp dụng lại* (HOLD 5).
3. Click **Changes**. HOLD 8 on the added `**Tiền tệ (Bắt buộc):**` line.
   - CHECK: the diff touches only `.github/instructions/company-security-stack.instructions.md`.
4. Stop clip.

### Report

List each clip: file name in `~/Movies`, CHECK results, anything that looked wrong.

---

## Part D: You, after recording

- `./demo/reset-take.sh` before every re-take of Clips 1C/1D (Copilot edits files).
- `./demo/reset-scene2.sh` before every re-take of Clip 2A (it closes the MR the last take created).
- Don't run `gitlab-local/setup.sh` while the working tree has Copilot's fixes: it would push them as the new baseline.
- Edit: cut the waits, lay the voice-over (`demo/voiceover_output/`) on the HOLDs:

  | Recorded clip | Voice-over | Length |
  |---|---|---|
  | 1A | `clip_1a.wav` | 18.8 s |
  | 1B | none (proof B-roll under 1C) | |
  | 1C | `clip_1c.wav` | 31.0 s |
  | 1D | `clip_1d.wav` | 13.4 s |
  | 2A | `clip_2a.wav` | 29.1 s |
  | 2B | `clip_2b.wav` | 23.1 s |
  | 3A | `clip_3a.wav` | 23.5 s |
  | 3B | `clip_3b.wav` | 46.2 s |
