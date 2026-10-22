#!/usr/bin/env python3
"""
Tự động tạo voice-over cho các phân cảnh demo HVE Core (khớp với demo/RUNBOOK.md và demo.md).
Sử dụng VieNeu-TTS để tổng hợp âm thanh giọng tiếng Việt chất lượng cao.
"""

import os
import sys
import argparse

# Mặc định chạy hoàn toàn OFFLINE (không gửi bất kỳ request nào lên Hugging Face)
if "--online" not in sys.argv:
    os.environ["HF_HUB_OFFLINE"] = "1"

from vieneu import Vieneu

# Kịch bản lời thoại đã được chuẩn hóa để AI phát âm tự nhiên nhất
SCRIPTS = {
    "clip_1a": {
        "title": "Clip 1A: Giới thiệu rules file và scope applyTo (0:00 - 1:00)",
        "text": (
            "Anh chị thấy đấy, dự án của chúng ta chạy đa ngôn ngữ: Backend là Scala và Kotlin, "
            "Frontend là Angular, và CI/CD chạy trên GitLab. Bình thường một bạn Fullstack hoặc AI rất dễ "
            "quên quy tắc của từng công nghệ. Nhưng với HVE Core, chỉ cần một dòng applyTo này, AI sẽ tự động "
            "nạp đúng bộ luật tương ứng với từng file mà lập trình viên đang mở."
        )
    },
    "clip_1c": {
        "title": "Clip 1C: HVE Review sửa lỗi PII backend và XSS frontend (1:00 - 2:00)",
        "text": (
            "Hãy nhìn vào lỗi kinh điển này ở Backend: Khi anh em dùng case class trong Scala hay data class trong Kotlin, "
            "hàm toString mặc định sẽ in sạch số thẻ và mã <en>c v v</en> của khách ra log hệ thống! Và ở phía Angular, AI hay "
            "tiện tay dùng bypassSecurityTrustHtml gây lỗi bảo mật <en>x s s</en>. Khi chạy qua bước Review của HVE Core, "
            "nó lập tức tuýt còi cả hai: Tự động viết lại hàm toString để che số thẻ thành sao sao sao sao một hai ba bốn, "
            "đồng thời gỡ bỏ hàm nguy hiểm trên Angular và thêm luôn takeUntilDestroyed để chống tràn bộ nhớ."
        )
    },
    "clip_1d": {
        "title": "Clip 1D: Khóa chặt bảo mật trên GitLab CI (2:00 - 3:00)",
        "text": (
            "Và ngay cả với GitLab CI của công ty mình, khi chạm vào file gitlab-ci.yml, HVE Core tự động "
            "ép ghim mã băm SHA-256 cho Docker image của Scala và Node, chặn đứng nguy cơ tấn công chuỗi cung ứng phần mềm."
        )
    },
    # Các clip dùng "segments" được đọc từng câu rồi ghép lại, nên phụ đề khớp đúng thời lượng thật.
    # Mỗi câu: (lời đọc cho TTS, chữ hiển thị trên phụ đề).
    "clip_2a": {
        "title": "Clip 2A: Chạy automation trực tiếp trên GitHub Copilot Desktop (3:00 - 3:50)",
        "segments": [
            ("Nhiều người nghĩ dùng GitHub Copilot thì chỉ tự động hóa được trên GitHub. Không hề!",
             "Nhiều người nghĩ dùng GitHub Copilot thì chỉ tự động hóa được trên GitHub. Không hề!"),
            ("Đây là GitHub Copilot Desktop, kết nối với GitLab của công ty qua giao thức <en>m c p</en>.",
             "Đây là GitHub Copilot Desktop, kết nối với GitLab của công ty qua giao thức MCP."),
            ("Automation này được đặt lịch chạy lúc hai giờ sáng mỗi đêm, nhưng để anh chị thấy tận mắt, tôi bấm chạy ngay bây giờ.",
             "Automation này được đặt lịch chạy lúc 2 giờ sáng mỗi đêm, nhưng để anh chị thấy tận mắt, tôi bấm chạy ngay bây giờ."),
            ("Agent đọc bộ quy tắc HVE Core ngay trên GitLab, quét code Kotlin, Scala, Angular và file CI, rồi kiểm tra pipeline.",
             "Agent đọc bộ quy tắc HVE Core ngay trên GitLab, quét code Kotlin, Scala, Angular và file CI, rồi kiểm tra pipeline."),
            ("Chỉ khoảng một phút là xong: agent báo số vi phạm, trạng thái pipeline và đường link tới bản nháp Merge Request.",
             "Chỉ khoảng 1 phút là xong: agent báo số vi phạm, trạng thái pipeline và đường link tới bản nháp Merge Request."),
        ],
    },
    "clip_2b": {
        "title": "Clip 2B: Draft MR vừa được tạo + quyền bị khóa (3:50 - 4:30)",
        "segments": [
            ("Đây là bản nháp Merge Request vừa được tạo, tác giả là HVE Bot.",
             "Đây là bản nháp Merge Request vừa được tạo, tác giả là HVE Bot."),
            ("Mô tả liệt kê từng lỗi, vị trí, quy tắc bị vi phạm và cách sửa.",
             "Mô tả liệt kê từng lỗi, vị trí, quy tắc bị vi phạm và cách sửa."),
            ("Quyền được khóa ở ba lớp: MCP chỉ cho phép ba thao tác ghi là tạo nhánh, đẩy file và mở Merge Request; HVE Bot chỉ là Developer; còn nhánh main và develop được bảo vệ.",
             "Quyền được khóa ở 3 lớp: MCP chỉ cho phép 3 thao tác ghi là tạo nhánh, đẩy file và mở Merge Request; HVE Bot chỉ là Developer; còn nhánh main và develop được bảo vệ."),
            ("Agent chỉ mở được bản nháp, không bao giờ tự merge được. Người duyệt cuối cùng vẫn là Tech Lead.",
             "Agent chỉ mở được bản nháp, không bao giờ tự merge được. Người duyệt cuối cùng vẫn là Tech Lead."),
        ],
    },
    "clip_3a": {
        "title": "Clip 3A: MR !402, lỗi mà con người bắt được (4:30 - 5:15)",
        "segments": [
            ("Đây là Merge Request bốn trăm linh hai. Một bạn viết hàm tính tiền hoàn bằng kiểu Double.",
             "Đây là MR !402. Một bạn viết hàm tính tiền hoàn bằng kiểu Double."),
            ("Hoàn mười một đô thì máy tính ra mười phẩy tám ba, trong khi đúng phải là mười phẩy tám tư: khách bị hoàn thiếu một xu.",
             "Hoàn 11 đô thì máy tính ra 10.83, trong khi đúng phải là 10.84: khách bị hoàn thiếu 1 xu."),
            ("Tech Lead bắt được lỗi này khi review, bạn dev sửa sang BigDecimal, và Merge Request được merge.",
             "Tech Lead bắt được lỗi này khi review, bạn dev sửa sang BigDecimal, và MR được merge."),
            ("Nhưng câu hỏi là: lần sau ai bắt lỗi này? Bộ quy tắc HVE Core của chúng ta hiện chưa có dòng nào nói về tiền tệ.",
             "Nhưng câu hỏi là: lần sau ai bắt lỗi này? Bộ quy tắc HVE Core của chúng ta hiện chưa có dòng nào nói về tiền tệ."),
        ],
    },
    "clip_3b": {
        "title": "Clip 3B: Harness² tự học ra quy tắc, MR !403 (5:15 - 6:00)",
        "segments": [
            ("Mảnh ghép cuối cùng là Harness bình phương, framework mã nguồn mở của Google Research, giúp agent tự cải thiện bộ khung của chính nó.",
             "Mảnh ghép cuối cùng là Harness², framework mã nguồn mở của Google Research, giúp agent tự cải thiện bộ khung của chính nó."),
            ("Ở đây, bộ khung đó chính là file quy tắc HVE Core.",
             "Ở đây, bộ khung đó chính là file quy tắc HVE Core."),
            ("Điểm quan trọng: Harness bình phương không hề được xem bình luận của Tech Lead. Nó chỉ nhận code của Merge Request bốn trăm linh hai đúng lúc vừa gửi.",
             "Điểm quan trọng: Harness² không hề được xem bình luận của Tech Lead. Nó chỉ nhận code của MR !402 đúng lúc vừa gửi."),
            ("Đề xuất: nó đưa ra hai hướng sửa, một về quy trình review, một bổ sung kiến thức nghiệp vụ.",
             "Đề xuất: nó đưa ra hai hướng sửa, một về quy trình review, một bổ sung kiến thức nghiệp vụ."),
            ("Thăm dò: nó chạy thật cả hai. Chỉ hướng thêm quy tắc tiền tệ là bắt được đúng dòng sáu của file Refund.",
             "Thăm dò: nó chạy thật cả hai. Chỉ hướng thêm quy tắc tiền tệ là bắt được đúng dòng 6 của Refund.kt."),
            ("Kết hợp: nó gộp lại thành bộ quy tắc mới và mở bản nháp Merge Request này.",
             "Kết hợp: nó gộp lại thành bộ quy tắc mới và mở Draft MR này."),
            ("Đến lúc đó mới đem ra đối chiếu: quy tắc mới bắt đúng dòng mà Tech Lead đã bắt.",
             "Đến lúc đó mới đem ra đối chiếu: quy tắc mới bắt đúng dòng mà Tech Lead đã bắt."),
            ("Harness bình phương tự đánh giá độ tin cậy là thấp, và đánh dấu quy tắc này cần đội xác nhận. Máy học ra quy tắc, con người quyết định có đưa vào hay không.",
             "Harness² tự đánh giá độ tin cậy là thấp, và đánh dấu quy tắc này cần đội xác nhận. Máy học ra quy tắc, con người quyết định có đưa vào hay không."),
        ],
    },
}

SEGMENT_GAP_S = 0.4


def synthesize(tts, text, args):
    if args.ref_audio and os.path.exists(args.ref_audio):
        return tts.infer(text=text, ref_audio=args.ref_audio)
    if args.voice:
        return tts.infer(text=text, voice=args.voice)
    return tts.infer(text=text)


def render_segments(tts, key, info, args):
    """Đọc từng câu, ghép với khoảng lặng, và ghi .wav + .srt theo thời lượng thật của từng câu."""
    import numpy as np
    from generate_subtitles import generate_srt_content

    gap = np.zeros(int(tts.sample_rate * SEGMENT_GAP_S), dtype=np.float32)
    parts, subs, t = [], [], 0.0
    for spoken, shown in info["segments"]:
        wav = np.asarray(synthesize(tts, spoken, args), dtype=np.float32)
        dur = len(wav) / tts.sample_rate
        subs.append((t, t + dur, shown))
        parts += [wav, gap]
        t += dur + SEGMENT_GAP_S
    out_path = os.path.join(args.output_dir, f"{key}.wav")
    tts.save(np.concatenate(parts[:-1]), out_path)
    srt_path = os.path.join(args.output_dir, f"{key}.srt")
    with open(srt_path, "w", encoding="utf-8") as sf:
        sf.write(generate_srt_content(subs))
    print(f"    -> Đã xuất: {out_path} ({subs[-1][1]:.1f}s) + {srt_path} ({len(subs)} dòng)")
    return subs

def main():
    parser = argparse.ArgumentParser(description="Sinh file âm thanh lồng tiếng tự động bằng VieNeu-TTS")
    parser.add_argument("--clip", choices=list(SCRIPTS.keys()) + ["all"], default="all",
                        help="Chọn clip cụ thể để sinh âm thanh (mặc định: all)")
    parser.add_argument("--voice", default=None,
                        help="Tên hoặc ID giọng mẫu có sẵn (chạy --list-voices để xem)")
    parser.add_argument("--list-voices", action="store_true",
                        help="Liệt kê danh sách các giọng có sẵn")
    parser.add_argument("--output-dir", default="demo/voiceover_output",
                        help="Thư mục lưu file audio đầu ra")
    parser.add_argument("--ref-audio", default=None,
                        help="Đường dẫn file audio mẫu (3-8s) nếu muốn nhân bản giọng (voice cloning)")
    parser.add_argument("--ref-text", default=None,
                        help="Nội dung lời nói của file audio mẫu (dùng cho voice cloning)")
    parser.add_argument("--online", action="store_true",
                        help="Bật kết nối Hugging Face để kiểm tra hoặc cập nhật bản mới nhất")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    print("=" * 60)
    print("Khởi tạo mô hình VieNeu-TTS...")
    print("=" * 60)
    tts = Vieneu()

    if args.list_voices:
        voices = tts.list_preset_voices() if hasattr(tts, "list_preset_voices") else []
        print("\nDanh sách các giọng đọc có sẵn:")
        for desc, vid in voices:
            print(f" - [{vid}]: {desc}")
        return

    target_clips = SCRIPTS.keys() if args.clip == "all" else [args.clip]

    for key in target_clips:
        info = SCRIPTS[key]
        print(f"\n[+] Đang xử lý: {info['title']}")
        if "segments" in info:
            render_segments(tts, key, info, args)
            continue
        print(f"    Lời thoại: \"{info['text'][:80]}...\"")

        # Nếu có audio mẫu thì thực hiện clone giọng, nếu không thì dùng voice hoặc mặc định
        if args.ref_audio and os.path.exists(args.ref_audio):
            audio = tts.infer(text=info["text"], ref_audio=args.ref_audio)
        elif args.voice:
            audio = tts.infer(text=info["text"], voice=args.voice)
        else:
            audio = tts.infer(text=info["text"])

        out_path = os.path.join(args.output_dir, f"{key}.wav")
        tts.save(audio, out_path)
        print(f"    -> Đã xuất file âm thanh: {out_path}")

        # Tự động tạo file phụ đề .srt tương ứng
        try:
            from generate_subtitles import SUBTITLE_DATA, generate_srt_content
            if key in SUBTITLE_DATA:
                srt_path = os.path.join(args.output_dir, f"{key}.srt")
                with open(srt_path, "w", encoding="utf-8") as sf:
                    sf.write(generate_srt_content(SUBTITLE_DATA[key]))
                print(f"    -> Đã xuất file phụ đề:   {srt_path}")
        except Exception:
            try:
                from demo.generate_subtitles import SUBTITLE_DATA, generate_srt_content
                if key in SUBTITLE_DATA:
                    srt_path = os.path.join(args.output_dir, f"{key}.srt")
                    with open(srt_path, "w", encoding="utf-8") as sf:
                        sf.write(generate_srt_content(SUBTITLE_DATA[key]))
                    print(f"    -> Đã xuất file phụ đề:   {srt_path}")
            except Exception:
                pass

    print("\n" + "=" * 60)
    print(f"Hoàn thành tất cả! Các file audio được lưu tại thư mục: {os.path.abspath(args.output_dir)}")
    print("=" * 60)

if __name__ == "__main__":
    main()
