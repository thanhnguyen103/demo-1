Việc đưa đúng **tech stack thực tế của công ty (GitLab + Backend Scala/Kotlin + Frontend Angular)** vào bài Demo sẽ tạo ra hiệu ứng tâm lý cực mạnh. Khi anh em Dev, QA và Sếp nhìn thấy đúng file `.gitlab-ci.yml`, những dòng code Scala/Kotlin và các Component Angular quen thuộc trên màn hình, họ sẽ lập tức thấy: **"À, cái này áp dụng được ngay vào dự án của mình ngày mai!"** chứ không phải lý thuyết xa vời.

Điểm cần lưu ý nhất khi đổi sang **GitLab**: Khán giả sẽ lập tức thắc mắc *"Ủa, HVE Core và GitHub Copilot sinh ra cho GitHub, vậy công ty mình dùng GitLab thì có chạy được không?"*. Bạn hãy biến chính câu hỏi này thành **điểm nhấn ăn tiền** trong bài nói của mình!

Dưới đây là kịch bản Demo 6 phút và bộ file mẫu chuẩn cú pháp HVE Core được "may đo" riêng cho hệ sinh thái **GitLab + Scala/Kotlin + Angular**.

---

## 1. Giải quyết bài toán kiến trúc: GitHub Copilot & HVE Core chạy với GitLab thế nào?

Trước khi vào Demo, bạn nói rõ 2 ý này (chỉ mất 30 giây nhưng giải tỏa hoàn toàn nghi ngờ của đội kỹ thuật):

1. **HVE Core nằm ở tầng Repository (Git-agnostic):** Toàn bộ `.instructions.md`, `.prompt.md`, `.agent.md` và thư mục `.copilot-tracking/` đều là các file Markdown nằm trực tiếp trong source code trên **GitLab** và vận hành ngay trong VS Code/IntelliJ.
2. **GitHub Copilot Desktop kết nối với GitLab qua MCP (Model Context Protocol):** Trên ứng dụng GitHub Copilot Desktop, tính năng **Automations** chạy trực tiếp trên workspace cục bộ (chứa repo GitLab của bạn) và gọi **GitLab MCP Server** (`@modelcontextprotocol/server-gitlab` hoặc `glab` CLI) để tự động đọc Issue, kiểm tra Pipeline và tạo **Merge Request (MR)** trực tiếp lên GitLab!

---

## 2. Bộ 3 "Bẫy lỗi thực tế" trong Demo (Scala/Kotlin + Angular + GitLab CI)

Chúng ta vẫn dùng bài toán **"Tính năng Thanh toán (Payment)"**, nhưng gài đúng 3 lỗi kinh điển của stack công nghệ bên bạn:

1. **Lỗi Backend (Scala / Kotlin):**
* *Lỗi bảo mật/Privacy:* Dùng `case class` (Scala) hoặc `data class` (Kotlin) cho thông tin thẻ `PaymentRequest`, sau đó gọi `logger.info(s"Processing $request")`. Vì `case class`/`data class` tự động sinh hàm `.toString()` in ra toàn bộ thuộc tính, số thẻ tín dụng và mã CVV của khách sẽ bị phơi bày nguyên vẹn trên hệ thống log (Kibana/Datadog)!
* *Lỗi hiệu năng/luồng (Concurrency):* Gọi tác vụ blocking I/O bên trong luồng bất đồng bộ mà không bọc trong `Blocking` context (Scala `Future` / Kotlin `Coroutines` dùng nhầm `Dispatchers.Default` thay vì `Dispatchers.IO`), gây nghẽn toàn bộ thread pool thanh toán.


2. **Lỗi Frontend (Angular):**
* *Lỗi bảo mật XSS:* Dùng `DomSanitizer.bypassSecurityTrustHtml()` để hiển thị thông báo trả về từ cổng thanh toán, mở toang cửa cho tấn công Cross-Site Scripting (XSS).
* *Lỗi Memory Leak:* Subscribe vào `HttpClient` trong Angular Component mà không có cơ chế tự hủy (`takeUntilDestroyed()`), gây rò rỉ bộ nhớ trên trình duyệt.


3. **Lỗi DevSecOps (GitLab CI - `.gitlab-ci.yml`):**
* Dùng Docker image trôi nổi `image: sbtscala/scala-sbt:latest` hoặc `node:latest` (không ghim cứng mã băm `@sha256:...`) và để biến nhạy cảm không được che (unmasked) trong log của GitLab Runner.



---

## 3. Các file mẫu chuẩn bị sẵn trong VS Code (Copy-Paste chạy được ngay)

Bạn tạo sẵn file này trong repo để chiếu lên màn hình ở **Cảnh 1**:

### File 1: `.github/instructions/company-security-stack.instructions.md`

```markdown
---
description: "Tiêu chuẩn Bảo mật & Chất lượng cho Stack Scala/Kotlin, Angular và GitLab CI"
applyTo: ["backend/**/*.{scala,kt}", "frontend/src/**/*.ts", ".gitlab-ci.yml"]
---

### 1. Quy chuẩn Backend (Scala / Kotlin)
- **Bảo mật PII (Bắt buộc):** TUYỆT ĐỐI KHÔNG nội suy trực tiếp `case class` (Scala) hoặc `data class` (Kotlin) chứa dữ liệu thanh toán/cá nhân vào `logger`. Bắt buộc phải override `override def toString` (hoặc `override fun toString()`) để che (mask) các trường `cardNumber`, `cvv`, `token`.
- **Concurrency:** Không gọi trực tiếp blocking I/O trên default execution context. Với Kotlin Coroutines, bắt buộc chuyển sang `withContext(Dispatchers.IO)`. Với Scala Future, bắt buộc bọc trong `scala.concurrent.blocking`.

### 2. Quy chuẩn Frontend (Angular)
- **Chống XSS:** CẤM sử dụng `bypassSecurityTrustHtml`, `bypassSecurityTrustScript` từ `DomSanitizer` nếu chưa qua hàm lọc chuẩn của công ty.
- **Quản lý bộ nhớ & Hiệu năng:** Mọi Component phải sử dụng `ChangeDetectionStrategy.OnPush` và mọi RxJS stream phải đi kèm `takeUntilDestroyed()` từ `@angular/core/rxjs-interop`.

### 3. Quy chuẩn GitLab CI/CD (`.gitlab-ci.yml`)
- **Supply Chain Security:** Mọi khai báo `image:` trong `.gitlab-ci.yml` BẮT BUỘC phải ghim cứng digest `@sha256:...` thay vì dùng tag `:latest`.
- **Bảo mật Runner:** Bắt buộc thiết lập `FF_TIMESTAMPS: "true"` và không bao giờ dùng lệnh `echo $SECRET_VAR` trong phần `script:`.

```

---

## 4. Kịch bản bấm giờ 6 phút trên sân khấu (Đã cập nhật theo Stack của bạn)

### Cảnh 1: HVE Core bảo vệ từ Backend (Scala/Kotlin) sang Frontend (Angular) đến GitLab CI (3 phút)

* **[0:00 - 1:00] Chiếu file `company-security-stack.instructions.md`:**
* **Thao tác:** Mở file trên trong VS Code, phóng to dòng `applyTo: ["backend/**/*.{scala,kt}", "frontend/src/**/*.ts", ".gitlab-ci.yml"]`.
* **Lời thoại:** *"Anh chị thấy đấy, dự án của chúng ta chạy đa ngôn ngữ: Backend là Scala/Kotlin, Frontend là Angular, và CI/CD chạy trên GitLab. Bình thường một bạn Fullstack hoặc AI rất dễ quên quy tắc của từng thằng. Nhưng với HVE Core, chỉ cần 1 dòng `applyTo` này, AI sẽ tự động nạp đúng 'bộ luật' tương ứng với từng file mà lập trình viên đang mở."*


* **[1:00 - 2:00] Bắt sống lỗi lộ thông tin thẻ trên Scala/Kotlin & lỗi XSS trên Angular:**
* **Thao tác:** Mở song song 2 tab:
* Tab 1 (`PaymentService.kt` hoặc `PaymentService.scala`): Có dòng `case class PaymentReq(userId: String, cardNumber: String, cvv: String)` và dòng `logger.info(s" Start payment: $req")`.
* Tab 2 (`payment-receipt.component.ts` - Angular): Có dùng `this.sanitizer.bypassSecurityTrustHtml(response.receiptHtml)`.


* **Thao tác tiếp theo:** Chuyển sang cửa sổ kết quả **Review của HVE Core** (chạy sẵn).
* **Lời thoại:** *"Hãy nhìn vào lỗi kinh điển này ở Backend: Khi anh em dùng `case class` trong Scala hay `data class` trong Kotlin, hàm `toString` mặc định sẽ in sạch số thẻ và mã CVV của khách ra log hệ thống! Và ở phía Angular, AI hay tiện tay dùng `bypassSecurityTrustHtml` gây lỗi bảo mật XSS. Khi chạy qua bước Review của HVE Core, nó lập tức tuýt còi cả hai: Tự động viết lại hàm `toString()` để che số thẻ thành `****-1234`, đồng thời gỡ bỏ hàm nguy hiểm trên Angular và thêm luôn `takeUntilDestroyed()` để chống tràn bộ nhớ."*


* **[2:00 - 3:00] Khóa chặt bảo mật trên `.gitlab-ci.yml`:**
* **Thao tác:** Mở file `.gitlab-ci.yml`, chỉ vào dòng `image: sbtscala/scala-sbt:latest` được AI tự động sửa thành `image: sbtscala/scala-sbt:eclipse-temurin-21.0.2_13_1.9.9_3.4.0@sha256:7a8b9c...`.
* **Lời thoại:** *"Và ngay cả với GitLab CI của công ty mình, khi chạm vào file `.gitlab-ci.yml`, HVE Core tự động ép ghim mã băm SHA-256 cho Docker image của Scala/Node, chặn đứng nguy cơ tấn công chuỗi cung ứng phần mềm."*



---

### Cảnh 2: GitHub Copilot Desktop (Automations) + GitLab MCP = Agent tự mở Draft Merge Request (1 phút 30 giây)

Cảnh này chạy **thật, trực tiếp**: bấm *Run now* trên automation, chờ khoảng 1 phút, xem kết quả, rồi mở Draft MR vừa được tạo trên GitLab. Trước mỗi lần quay chạy `./demo/reset-scene2.sh`.

* **[3:00 - 3:50] Chạy automation ngay trên GitHub Copilot Desktop:**
* **Thao tác:** Mở tab **Automations**, chọn **`GitLab Nightly HVE Quality & Security Gate`** (lịch: hằng ngày 02:00, prompt: `.github/prompts/gitlab-nightly-gate.prompt.md`). Bấm **Run now**, chờ agent chạy xong, dừng ở 3 dòng kết quả cuối: số vi phạm, trạng thái pipeline, link Draft MR.
* **Lời thoại:** *"Nhiều người nghĩ dùng GitHub Copilot thì chỉ tự động hóa được trên GitHub. Không hề! Đây là GitHub Copilot Desktop, kết nối với **GitLab của công ty qua giao thức MCP**. Automation này được đặt lịch chạy lúc 2 giờ sáng mỗi đêm, nhưng để anh chị thấy tận mắt, tôi bấm chạy ngay bây giờ. Agent đọc bộ quy tắc HVE Core ngay trên GitLab, quét code Kotlin, Scala, Angular và file CI, rồi kiểm tra pipeline. Chỉ khoảng một phút là xong: agent báo số vi phạm, trạng thái pipeline và đường link tới bản nháp Merge Request."*

* **[3:50 - 4:30] Draft MR vừa được tạo + quyền bị khóa:**
* **Thao tác:** Mở danh sách MR đang mở trên GitLab, bấm vào `Draft: [HVE-AutoFix] …` mới nhất (tác giả `HVE Bot`, tạo cách đây một phút). Cuộn bảng *Lỗi | File:dòng | Quy tắc vi phạm | Cách sửa*, mở tab **Changes**. Sau đó mở trang **Members** (`hve-bot` = Developer) và **Protected branches** (`main`, `develop` chỉ Maintainer).
* **Lời thoại:** *"Đây là bản nháp Merge Request vừa được tạo, tác giả là HVE Bot. Mô tả liệt kê từng lỗi, vị trí, quy tắc bị vi phạm và cách sửa. Quyền được khóa ở ba lớp: MCP chỉ cho phép ba thao tác ghi là tạo nhánh, đẩy file và mở Merge Request; HVE Bot chỉ là Developer; còn nhánh main và develop được bảo vệ. Agent chỉ mở được bản nháp, không bao giờ tự merge được. Người duyệt cuối cùng vẫn là Tech Lead."*



---

### Cảnh 3: Harness² (Google Research) – Bộ quy tắc tự học từ lỗi trên GitLab Merge Request (1 phút 30 giây)

Harness² là framework mã nguồn mở của Google Research ([google-research/harness2](https://github.com/google-research/harness2), Apache-2.0, bài báo *Recursive Agent Harnessing for an Open World*). README ghi rõ đây không phải sản phẩm chính thức của Google, nên khi nói hãy gọi là "Harness² của Google Research", đừng gọi là "Google Harness²". Trong demo, Harness² chạy thật trên Claude Code ở máy local (`./harness2-hve/run.sh --mr 402 --open-mr`).

* **[4:30 - 5:15] MR !402: lỗi mà con người bắt được**
* **Thao tác:** Mở MR !402 `feat(refund): tính tiền hoàn cho khách (98.5%)` (đã merge), cuộn tới thread của Tech Lead trên `Refund.kt` dòng 6.
* **Trên màn hình:** `fun refundAmount(amount: Double): Double = round(amount * 0.985 * 100) / 100`, kèm comment: `11.00 * 0.985` trong `Double` ra `10.834999999999999`, làm tròn thành **10.83** trong khi đúng phải là **10.84**.
* **Lời thoại:** *"Đây là MR !402. Một bạn viết hàm tính tiền hoàn bằng `Double`. Hoàn 11 đô thì máy tính ra 10.83, trong khi đúng phải là 10.84: khách bị hoàn thiếu 1 xu. Tech Lead bắt được lỗi này khi review, bạn dev sửa sang `BigDecimal`, và MR được merge. Nhưng câu hỏi là: lần sau ai bắt lỗi này? Bộ quy tắc HVE Core của chúng ta hiện chưa có dòng nào nói về tiền tệ."*

* **[5:15 - 6:00] MR !403: Harness² tự học ra quy tắc**
* **Thao tác:** Mở Draft MR !403 `Draft: [Harness²] Thêm quy tắc Tiền tệ từ MR !402` (tác giả `HVE Bot`). Cuộn chậm qua mô tả: *Đối chiếu với nhận xét của con người* → *Tác dụng của từng chỉnh sửa* → *Bài học có thể áp dụng rộng*. Sau đó mở tab **Changes**.
* **Nội dung Diff trên màn hình GitLab** (file duy nhất thay đổi: `.github/instructions/company-security-stack.instructions.md`):
```diff
 ### 1. Quy chuẩn Backend (Scala / Kotlin)
 - **Bảo mật PII (Bắt buộc):** ...
+- **Tiền tệ (Bắt buộc):** Số tiền (amount, fee, refund, balance, price) KHÔNG được dùng kiểu `Double`/`Float` (tham số, giá trị trả về, field, hằng số tỉ lệ hay JSON Jackson/Circe). Bắt buộc dùng `BigDecimal` (tạo từ String, không từ `Double`) hoặc `Long` theo đơn vị nhỏ nhất, và mọi phép làm tròn tiền phải chỉ rõ `RoundingMode` qua `setScale(...)`.
 - **Concurrency:** ...
```

* **Lời thoại:** *"Mảnh ghép cuối cùng là Harness², framework mã nguồn mở của Google Research, giúp agent tự cải thiện 'bộ khung' của chính nó. Ở đây bộ khung đó chính là file quy tắc HVE Core.*
* *Điểm quan trọng: Harness² **không hề được xem** comment của Tech Lead. Nó chỉ nhận code của MR !402 đúng lúc vừa gửi, rồi chạy vòng **Đề xuất – Thăm dò – Kết hợp**:*
  * ***Đề xuất:** reviewer dùng bộ quy tắc hiện tại kết luận "Không có vi phạm". Harness² đề xuất hai hướng sửa: một hướng cải tiến quy trình review, một hướng bổ sung kiến thức nghiệp vụ.*
  * ***Thăm dò:** nó chạy thật cả hai. Sửa quy trình vẫn ra "Không có vi phạm". Chỉ hướng thêm quy tắc tiền tệ là bắt được đúng `Refund.kt` dòng 6.*
  * ***Kết hợp:** nó gộp lại thành bộ quy tắc mới và mở Draft MR này.*
* *Đến lúc đó mới đem ra đối chiếu: reviewer với quy tắc mới bắt **đúng dòng mà Tech Lead đã bắt**.*
* *Và Harness² khá trung thực: nó tự đánh giá độ tin cậy là **thấp**, vì mới chỉ thử trên một MR, và nó đánh dấu quy tắc này là do máy tự viết, cần đội xác nhận. Ví dụ, quy tắc chỉ bắt buộc ghi rõ `RoundingMode`, còn đội mình chuẩn hóa `HALF_EVEN` thì Tech Lead sẽ chốt khi duyệt. Máy học ra quy tắc, con người quyết định có đưa vào hay không. Một khi merge, từ MR sau, cả đội và mọi AI agent dùng HVE Core sẽ tự động kiểm tra lỗi tiền tệ này."*



---

## Điểm cộng cực lớn khi bạn dùng kịch bản này

* **Đội Backend (Scala/Kotlin):** Sẽ gật gù tâm đắc ngay ở ví dụ `case class / data class toString()` làm lộ thông tin thẻ và lỗi `Double` vs `BigDecimal` — vì đây là nỗi đau quá thật trong nghề của họ.
* **Đội Frontend (Angular):** Thấy ngay giá trị thực tế qua `bypassSecurityTrustHtml`, `OnPush` và `takeUntilDestroyed()`.
* **Đội DevOps / Security & Quản lý:** Bị thuyết phục hoàn toàn khi thấy giải pháp chạy mượt mà trên **GitLab** (qua `.gitlab-ci.yml` và **GitLab MCP Server** tạo **Draft Merge Request**), không hề bị rào cản nền tảng giữa GitHub và GitLab.

Bạn có muốn mình phác thảo thêm **1 sơ đồ kiến trúc (Architecture Diagram)** gói gọn luồng đi từ `VS Code (HVE Core)` $\leftrightarrow$ `Copilot Desktop Automations` $\leftrightarrow$ `GitLab MCP` $\leftrightarrow$ `Harness² Loop` để bạn đưa thẳng vào slide đinh của bài thuyết trình không?