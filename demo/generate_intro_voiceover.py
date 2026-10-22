#!/usr/bin/env python3
"""
Tự động tạo âm thanh voice-over và phụ đề .srt cho Video 1: Giới thiệu HVE Core (FPT Software).
Sử dụng VieNeu-TTS (chạy 100% offline cục bộ).
Chia thành đúng 10 phân cảnh tương ứng 1-1 với 10 trang Slides trong demo/slides.md.
Nội dung chuẩn phong cách thuyết trình kỹ thuật (Technical Presentation).
"""

import os
import sys
import argparse
import numpy as np
import soundfile as sf

if "--online" not in sys.argv:
    os.environ["HF_HUB_OFFLINE"] = "1"

from vieneu import Vieneu
from generate_subtitles import generate_srt_content

SLIDE_GAP_S = 0.35  # khoảng lặng giữa hai slide trong intro_full.wav; render_intro_video.py dùng cùng giá trị

# Mỗi câu: (lời đọc cho TTS, chữ hiển thị trên phụ đề). Đọc từng câu nên phụ đề khớp thời lượng thật.
INTRO_SCRIPTS = {
    "slide_01": {
        "title": "Slide 1: HVE Core × GitHub Copilot",
        "segments": [
            ("Chào anh chị em FPT Software!",
             "Chào anh chị em FPT Software!"),
            ("Hôm nay chúng ta nói về giải pháp chuẩn hóa coding conventions cho GitHub câu pai lợt từ IDE đến GitLab.",
             "Hôm nay chúng ta nói về giải pháp chuẩn hóa coding conventions cho GitHub Copilot từ IDE đến GitLab."),
            ("Đó là <en>h v e core</en> của Microsoft — bộ quy chuẩn guardrails đóng gói sẵn cho doanh nghiệp, dễ dàng tùy biến và áp dụng ngay cho từng dự án.",
             "Đó là HVE Core của Microsoft — bộ quy chuẩn (Guardrails) đóng gói sẵn cho doanh nghiệp: Dễ dàng tùy biến, áp dụng ngay cho từng dự án."),
        ],
    },
    "slide_02": {
        "title": "Slide 2: Copilot viết đoạn này trong 3 giây. Bạn có duyệt không?",
        "segments": [
            ("Hãy nhìn đoạn code Kotlin này. câu pai lợt viết nó trong ba giây: biên dịch thành công, unit test pass, nhìn qua tưởng như ổn.",
             "Hãy nhìn đoạn code Kotlin này. Copilot viết nó trong 3 giây: biên dịch thành công, unit test pass, nhìn qua tưởng như ổn."),
            ("Nhưng khi chạy, dòng log làm lộ toàn bộ số thẻ và mã CVV của khách. Còn tiền tệ thì tính bằng kiểu Double, tiềm ẩn rủi ro sai số làm tròn.",
             "Nhưng khi chạy, dòng log làm lộ toàn bộ số thẻ và mã CVV của khách. Còn tiền tệ thì tính bằng kiểu Double, tiềm ẩn rủi ro sai số làm tròn."),
            ("câu pai lợt không sai về cú pháp. Nó chỉ chưa được định hướng theo chuẩn riêng của dự án.",
             "Copilot không sai về cú pháp. Nó chỉ chưa được định hướng theo chuẩn riêng của dự án."),
            ("Việc mỗi dự án tự viết prompt thủ công rất tốn thời gian, thiếu đồng nhất và dễ bị prompt drift. Trong khi Microsoft đã tối ưu sẵn bộ khung chuẩn dành riêng cho câu pai lợt.",
             "Việc mỗi dự án tự viết prompt thủ công rất tốn thời gian, thiếu đồng nhất và dễ bị Prompt Drift. Trong khi Microsoft đã tối ưu sẵn bộ khung chuẩn dành riêng cho Copilot."),
        ],
    },
    "slide_03": {
        "title": "Slide 3: HVE Core là gì? Bộ khung chuẩn từ Microsoft cho Copilot",
        "segments": [
            ("<en>h v e core</en>, viết tắt của Hypervelocity Engineering Core, là bộ instructions, prompts, agents và skills viết sẵn cho GitHub câu pai lợt.",
             "HVE Core (Hypervelocity Engineering Core) là bộ instructions, prompts, agents và skills viết sẵn cho GitHub Copilot."),
            ("Cốt lõi là quy trình <en>r p i</en> workflow: Research, Plan, Implement, Review.",
             "Cốt lõi là quy trình RPI Workflow: Research, Plan, Implement, Review."),
            ("Skill <en>h v e builder</en> giúp tự động nhân bản và tùy chỉnh pattern phù hợp với stack của dự án, đi kèm bộ instructions bảo mật chuẩn OWASP và NIST.",
             "Skill /hve-builder giúp tự động nhân bản và tùy chỉnh pattern phù hợp với stack của dự án, đi kèm bộ instructions bảo mật chuẩn OWASP và NIST."),
            ("Cài đặt linh hoạt qua Extension VS Code hoặc Plugin cho câu pai lợt CLI.",
             "Cài đặt linh hoạt qua Extension VS Code hoặc Plugin cho Copilot CLI."),
        ],
    },
    "slide_04": {
        "title": "Slide 4: Cơ chế hoạt động: Quy chuẩn theo ngữ cảnh (Context-Aware Rules)",
        "segments": [
            ("Cơ chế cốt lõi là ngữ cảnh hóa quy chuẩn theo từng loại file qua thuộc tính <en>apply to</en>.",
             "Cơ chế cốt lõi là ngữ cảnh hóa quy chuẩn theo từng loại file qua thuộc tính applyTo."),
            ("Mở file Kotlin, câu pai lợt tự động kích hoạt quy chuẩn Backend. Mở file TypeScript, nó kích hoạt quy chuẩn Frontend. Mở GitLab CI, nó nạp quy chuẩn CI/CD.",
             "Mở file Kotlin, Copilot tự động kích hoạt quy chuẩn Backend. Mở file TypeScript, nó kích hoạt quy chuẩn Frontend. Mở GitLab CI, nó nạp quy chuẩn CI/CD."),
            ("Quy chuẩn lưu trực tiếp trong Git repository, được review qua Merge Request và có lịch sử rõ ràng.",
             "Quy chuẩn lưu trực tiếp trong Git repo, được review qua Merge Request và có lịch sử rõ ràng."),
            ("Lưu ý rằng Custom Instructions chỉ định hướng cho <en>a i</en> sinh code đúng, không thay thế hoàn toàn SAST scanner. Vẫn cần Code Review và CI Pipeline.",
             "Lưu ý rằng Custom Instructions chỉ định hướng cho AI sinh code đúng, không thay thế hoàn toàn SAST scanner. Vẫn cần Code Review và CI Pipeline."),
        ],
    },
    "slide_05": {
        "title": "Slide 5: RPI Workflow: Tránh việc AI can thiệp code trực tiếp mà thiếu kiểm soát",
        "segments": [
            ("<en>r p i</en> workflow giải quyết triệt để rủi ro <en>a i</en> can thiệp code trực tiếp mà thiếu kiểm soát, chia việc thành bốn bước.",
             "RPI Workflow giải quyết triệt để rủi ro AI can thiệp code trực tiếp mà thiếu kiểm soát, chia việc thành 4 bước."),
            ("Bước một, Research là khảo sát chỉ đọc để hiểu rõ repo và APIs. Bước hai, Plan lập kế hoạch chi tiết bằng Markdown, tích hợp bước tự đánh giá Self-Validation để Tech Lead phê duyệt.",
             "Bước 1: Research là khảo sát chỉ đọc để hiểu rõ repo và APIs. Bước 2: Plan lập kế hoạch bằng Markdown, tích hợp bước tự đánh giá (Self-Validation) để Tech Lead phê duyệt."),
            ("Bước ba, Implement thực thi chính xác theo kế hoạch và chạy unit test. Bước bốn, Review đối chiếu kết quả với kế hoạch và tiêu chuẩn dự án.",
             "Bước 3: Implement thực thi chính xác theo kế hoạch và chạy unit test. Bước 4: Review đối chiếu kết quả với kế hoạch và tiêu chuẩn dự án."),
            ("Trong bài demo, lệnh <en>h v e review</en> là công cụ được customized từ pattern này.",
             "Trong bài demo, lệnh /hve-review là công cụ được customized từ pattern này."),
        ],
    },
    "slide_06": {
        "title": "Slide 6: Khuyến cáo từ Microsoft & Chiến lược Fork and Own",
        "segments": [
            ("Microsoft đưa ra khuyến cáo rất rõ ràng: <en>h v e core</en> phát triển nhanh và mang tính định hình cao. Hãy xem đây là nguồn pattern để học hỏi, không phải một thư viện phụ thuộc cứng cho production.",
             "Microsoft đưa ra khuyến cáo rất rõ ràng: HVE Core phát triển nhanh và mang tính định hình cao. Hãy xem đây là nguồn pattern để học hỏi, không phải một thư viện phụ thuộc cứng cho production."),
            ("Nếu dùng như thư viện ngoài, dự án sẽ gặp rủi ro khi phụ thuộc vào upstream và đòi hỏi tương thích ngược.",
             "Nếu dùng như thư viện ngoài, dự án sẽ gặp rủi ro khi phụ thuộc vào upstream và đòi hỏi tương thích ngược."),
            ("Chiến lược chuẩn là Fork and Own: chọn lọc pattern phù hợp đưa vào thư mục chấm github, dùng <en>h v e builder</en> tùy chỉnh theo stack của team.",
             "Chiến lược chuẩn là Fork & Own: chọn lọc pattern phù hợp đưa vào .github/, dùng /hve-builder tùy chỉnh theo stack của team."),
            ("Nhờ đó, dự án toàn quyền sở hữu rulebook và chủ động nâng cấp theo lộ trình riêng.",
             "Nhờ đó, dự án toàn quyền sở hữu Rulebook và chủ động nâng cấp theo lộ trình riêng."),
        ],
    },
    "slide_07": {
        "title": "Slide 7: Mở rộng ngoài IDE: Kết hợp Copilot Automations & GitLab MCP",
        "segments": [
            ("Bước tiếp theo là mở rộng năng lực của câu pai lợt ra ngoài IDE.",
             "Bước tiếp theo là mở rộng năng lực của Copilot ra ngoài IDE."),
            ("Với Copilot Automations kết hợp GitLab <en>m c p</en> Server, hệ thống có thể chạy tự động theo lịch nightly job lúc hai giờ sáng hoặc kích hoạt on-demand khi cần.",
             "Với Copilot Automations kết hợp GitLab MCP Server, hệ thống có thể chạy tự động theo lịch Nightly Job lúc 2:00 AM hoặc kích hoạt On-demand."),
            ("Agent đọc quy chuẩn <en>h v e core</en> và quét commit mới trên nhánh develop, tự sửa vi phạm trên nhánh riêng và mở Draft Merge Request kèm bảng phân tích lỗi.",
             "Agent đọc quy chuẩn HVE Core và quét commit mới trên develop, tự sửa vi phạm trên nhánh riêng và mở Draft Merge Request kèm bảng phân tích lỗi."),
            ("Cơ chế bảo mật ba lớp đảm bảo an toàn tuyệt đối: <en>m c p</en> chặn hoàn toàn quyền merge và xóa, tài khoản bot chỉ là Developer, và chỉ Maintainer con người mới có quyền merge vào nhánh chính.",
             "Cơ chế bảo mật 3 lớp (3-Tier Security Gate): MCP chặn quyền merge và xóa, bot chỉ là Developer, và chỉ Maintainer con người mới có quyền merge vào nhánh chính."),
        ],
    },
    "slide_08": {
        "title": "Slide 8: Harness² Framework: Cơ chế tự hoàn thiện quy chuẩn (Continuous Rule Learning)",
        "segments": [
            ("Quy chuẩn viết sẵn không thể lường trước mọi lỗi phát sinh.",
             "Quy chuẩn viết sẵn không thể lường trước mọi lỗi phát sinh."),
            ("Ở case-study Merge Request bốn trăm linh hai, lỗi sai số do dùng kiểu Double cho dữ liệu tài chính làm khách bị hoàn thiếu một xu. Tech Lead phát hiện và yêu cầu chuyển sang BigDecimal.",
             "Ở case-study MR !402, lỗi sai số do dùng kiểu Double cho dữ liệu tài chính làm khách bị hoàn thiếu 1 xu. Tech Lead phát hiện và yêu cầu chuyển sang BigDecimal."),
            ("Harness bình phương, framework mã nguồn mở của Google Research, chạy mô phỏng reviewer trên code của MR đó, đề xuất và thử nghiệm các phiên bản rule mới, rồi tự động mở Draft Merge Request bốn trăm linh ba.",
             "Harness², framework mã nguồn mở của Google Research, chạy mô phỏng reviewer trên code của MR đó, đề xuất và thử nghiệm các phiên bản rule mới, rồi tự động mở Draft MR !403."),
            ("Quy chuẩn được rút ra từ sự cố thực tế, có gắn tag máy sinh, và quyền quyết định cuối cùng hoàn toàn thuộc về Tech Lead.",
             "Quy chuẩn được rút ra từ sự cố thực tế, có gắn tag máy sinh, và quyền quyết định cuối cùng hoàn toàn thuộc về Tech Lead."),
        ],
    },
    "slide_09": {
        "title": "Slide 9: So sánh HVE Core và BMAD Framework: Lựa chọn theo bài toán",
        "segments": [
            ("So sánh với BMAD Framework, cả hai công cụ đều có thế mạnh riêng theo từng bài toán.",
             "So sánh với BMAD Framework, cả hai công cụ đều có thế mạnh riêng theo từng bài toán."),
            ("BMAD tối ưu cho các dự án phát triển mới từ đầu greenfield: phân vai Agile để xây dựng bộ tài liệu đặc tả PRD và kiến trúc kỹ thuật trước khi code.",
             "BMAD tối ưu cho các dự án phát triển mới từ đầu (Greenfield): phân vai Agile để xây dựng bộ tài liệu đặc tả PRD và kiến trúc kỹ thuật trước khi code."),
            ("<en>h v e core</en> tối ưu cho các dự án brownfield đang hoạt động, cần kiểm soát chất lượng code và đồng bộ coding conventions cho GitHub câu pai lợt.",
             "HVE Core tối ưu cho các dự án Brownfield đang hoạt động, cần kiểm soát chất lượng code và đồng bộ coding conventions cho GitHub Copilot."),
            ("Hai phương pháp hoàn toàn có thể bổ trợ cho nhau trong suốt vòng đời dự án.",
             "Hai phương pháp hoàn toàn có thể bổ trợ cho nhau trong suốt vòng đời dự án."),
        ],
    },
    "slide_10": {
        "title": "Slide 10: Live Demo Agenda (6 phút)",
        "segments": [
            ("Ngay sau đây, xin mời anh chị theo dõi bài Live Demo sáu phút trên môi trường thực tế: GitLab CE local, Backend Scala và Kotlin, cùng Frontend Angular.",
             "Ngay sau đây, xin mời anh chị theo dõi bài Live Demo 6 phút trên môi trường thực tế: GitLab CE local, Backend Scala/Kotlin, cùng Frontend Angular."),
            ("Demo một: <en>h v e core</en> bảo vệ code trong IDE. Demo hai: câu pai lợt Automation tự động quét và mở Merge Request. Demo ba: Harness bình phương tự học quy chuẩn từ lỗi thực tế.",
             "Demo 1: HVE Core bảo vệ code trong IDE. Demo 2: Copilot Automation tự động quét và mở Merge Request. Demo 3: Harness² tự học quy chuẩn từ lỗi thực tế."),
            ("Xin mời anh chị cùng bắt đầu phần Demo!",
             "Xin mời anh chị cùng bắt đầu phần Demo!"),
        ],
    },
}


def render_segments(tts: Vieneu, key: str, info: dict, args) -> list:
    """Tạo audio cho từng câu, ghép lại thành file của slide, trả về danh sách phụ đề đã căn chỉnh."""
    os.makedirs(args.output_dir, exist_ok=True)
    pieces = []
    subs = []
    cursor = 0.0
    sr = 48000

    for i, (tts_text, sub_text) in enumerate(info["segments"]):
        audio = (tts.infer(text=tts_text, ref_audio=args.ref_audio)
                 if args.ref_audio and os.path.exists(args.ref_audio)
                 else tts.infer(text=tts_text, voice=args.voice))
        dur = len(audio) / sr
        pieces.append(audio)
        subs.append((cursor, cursor + dur, sub_text))
        cursor += dur
        # nghỉ ngắn 0.15s giữa hai câu trong cùng một slide
        if i + 1 < len(info["segments"]):
            pieces.append(np.zeros(int(sr * 0.15), dtype=np.float32))
            cursor += 0.15

    slide_audio = np.concatenate(pieces)
    wav_p = os.path.join(args.output_dir, f"{key}.wav")
    sf.write(wav_p, slide_audio, sr)

    srt_p = os.path.join(args.output_dir, f"{key}.srt")
    with open(srt_p, "w", encoding="utf-8") as f:
        f.write(generate_srt_content(subs))

    print(f"    -> Đã xuất Audio:   {wav_p} ({cursor:.2f}s, {len(info['segments'])} câu)")
    print(f"    -> Đã xuất Phụ đề: {srt_p}")
    return subs


def main():
    parser = argparse.ArgumentParser(description="Sinh file âm thanh & phụ đề cho 10 Slides Video 1: Giới thiệu HVE Core")
    parser.add_argument("--scene", choices=list(INTRO_SCRIPTS.keys()) + ["all"], default="all",
                        help="Chọn cảnh/slide cụ thể hoặc all (mặc định: all)")
    parser.add_argument("--voice", default="Hải Đăng",
                        help="Tên giọng đọc (mặc định: Hải Đăng)")
    parser.add_argument("--output-dir", default="demo/intro_output",
                        help="Thư mục lưu file đầu ra")
    parser.add_argument("--ref-audio", default=None,
                        help="File audio mẫu (3-8s) nếu muốn nhân bản giọng")
    parser.add_argument("--online", action="store_true",
                        help="Kết nối online kiểm tra Hugging Face")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    print("=" * 65)
    print(f"Khởi tạo mô hình VieNeu-TTS (Giọng: {args.voice})...")
    print("=" * 65)
    tts = Vieneu()

    target_scenes = sorted(INTRO_SCRIPTS) if args.scene == "all" else [args.scene]
    all_subs = {}
    for key in target_scenes:
        print(f"\n[+] Đang tạo âm thanh: {INTRO_SCRIPTS[key]['title']}")
        all_subs[key] = render_segments(tts, key, INTRO_SCRIPTS[key], args)

    # Nếu chạy all, ghép nối thành 1 file hoàn chỉnh intro_full.wav và intro_full.srt
    if args.scene == "all" and len(all_subs) == len(INTRO_SCRIPTS):
        print("\n" + "-" * 65)
        print("Đang ghép nối toàn bộ 10 Slide thành file hoàn chỉnh: intro_full.wav & intro_full.srt...")
        full_audio_pieces = []
        full_subs = []
        current_offset = 0.0
        sr = 48000

        for key in sorted(INTRO_SCRIPTS):
            wav_p = os.path.join(args.output_dir, f"{key}.wav")
            data, cur_sr = sf.read(wav_p)
            dur = len(data) / cur_sr
            full_audio_pieces.append(data)

            # dời mốc thời gian phụ đề theo offset hiện tại
            for s, e, txt in all_subs[key]:
                full_subs.append((current_offset + s, current_offset + e, txt))

            # khoảng lặng giữa các slide
            full_audio_pieces.append(np.zeros(int(cur_sr * SLIDE_GAP_S), dtype=np.float32))
            current_offset += dur + SLIDE_GAP_S

        full_audio = np.concatenate(full_audio_pieces)
        full_wav_p = os.path.join(args.output_dir, "intro_full.wav")
        sf.write(full_wav_p, full_audio, sr)

        full_srt_p = os.path.join(args.output_dir, "intro_full.srt")
        with open(full_srt_p, "w", encoding="utf-8") as f:
            f.write(generate_srt_content(full_subs))

        total_dur = len(full_audio) / sr
        print(f"-> [THÀNH CÔNG] File âm thanh tổng: {full_wav_p} ({total_dur:.2f}s / {total_dur/60:.2f} phút)")
        print(f"-> [THÀNH CÔNG] File phụ đề tổng:   {full_srt_p} ({len(full_subs)} phụ đề)")

    print("\n" + "=" * 65)
    print(f"Hoàn tất! Tất cả assets đã sẵn sàng tại: {os.path.abspath(args.output_dir)}")
    print("=" * 65)


if __name__ == "__main__":
    main()
