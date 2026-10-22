#!/usr/bin/env python3
"""
Tự động tạo file phụ đề .srt tương ứng cho từng file âm thanh voice-over trong demo/voiceover_output.
Căn chỉnh thời gian dựa trên các khoảng dừng ngữ điệu thực tế của file âm thanh .wav.
"""

import os
import glob
import soundfile as sf
import numpy as np

SUBTITLE_DATA = {
    "clip_1a": [
        (
            0.0, 7.68,
            "Anh chị thấy đấy, dự án của chúng ta chạy đa ngôn ngữ: Backend là Scala và Kotlin, Frontend là Angular, và CI/CD chạy trên GitLab."
        ),
        (
            8.15, 11.41,
            "Bình thường một bạn Fullstack hoặc AI rất dễ quên quy tắc của từng công nghệ."
        ),
        (
            11.90, 14.53,
            "Nhưng với HVE Core, chỉ cần một dòng applyTo này,"
        ),
        (
            14.97, 18.82,
            "AI sẽ tự động nạp đúng bộ luật tương ứng với từng file mà lập trình viên đang mở."
        ),
    ],
    "clip_1c": [
        (
            0.0, 5.80,
            "Hãy nhìn vào lỗi kinh điển này ở Backend: Khi anh em dùng case class trong Scala hay data class trong Kotlin,"
        ),
        (
            5.80, 10.62,
            "hàm toString mặc định sẽ in sạch số thẻ và mã CVV của khách ra log hệ thống!"
        ),
        (
            11.12, 17.03,
            "Và ở phía Angular, AI hay tiện tay dùng bypassSecurityTrustHtml gây lỗi bảo mật XSS."
        ),
        (
            17.57, 20.98,
            "Khi chạy qua bước Review của HVE Core, nó lập tức tuýt còi cả hai:"
        ),
        (
            20.98, 25.29,
            "Tự động viết lại hàm toString() để che số thẻ thành ****-1234,"
        ),
        (
            25.64, 31.04,
            "đồng thời gỡ bỏ hàm nguy hiểm trên Angular và thêm luôn takeUntilDestroyed() để chống tràn bộ nhớ."
        ),
    ],
    "clip_1d": [
        (
            0.0, 2.08,
            "Và ngay cả với GitLab CI của công ty mình,"
        ),
        (
            2.55, 5.20,
            "khi chạm vào file .gitlab-ci.yml,"
        ),
        (
            5.71, 10.51,
            "HVE Core tự động ép ghim mã băm SHA-256 cho Docker image của Scala và Node,"
        ),
        (
            11.19, 13.36,
            "chặn đứng nguy cơ tấn công chuỗi cung ứng phần mềm."
        ),
    ],
    # clip_2a / clip_2b / clip_3a / clip_3b: phụ đề do generate_voiceover.py tạo từ thời lượng thật của từng câu.
}

def format_srt_time(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis >= 1000:
        secs += 1
        millis = 0
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def generate_srt_content(segments):
    lines = []
    for idx, (start, end, text) in enumerate(segments, 1):
        lines.append(str(idx))
        lines.append(f"{format_srt_time(start)} --> {format_srt_time(end)}")
        lines.append(text)
        lines.append("")  # Empty line between subtitle entries
    return "\n".join(lines)

def main():
    output_dir = "demo/voiceover_output"
    os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 60)
    print("Bắt đầu tạo file phụ đề (.srt) cho từng clip voice-over...")
    print("=" * 60)
    
    for clip_name, segments in SUBTITLE_DATA.items():
        wav_path = os.path.join(output_dir, f"{clip_name}.wav")
        srt_path = os.path.join(output_dir, f"{clip_name}.srt")
        
        actual_dur = None
        if os.path.exists(wav_path):
            info = sf.info(wav_path)
            actual_dur = info.duration

        srt_content = generate_srt_content(segments)
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(srt_content)
            
        dur_str = f" (độ dài audio: {actual_dur:.2f}s)" if actual_dur else ""
        print(f"[+] Đã tạo: {srt_path}{dur_str} - {len(segments)} dòng phụ đề")

    print("=" * 60)
    print("Hoàn tất! Tất cả file .srt đã sẵn sàng trong thư mục demo/voiceover_output.")

if __name__ == "__main__":
    main()
