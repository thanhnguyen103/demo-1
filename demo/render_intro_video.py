#!/usr/bin/env python3
"""
Tự động ghép 10 ảnh Slides (Marp PNG) + File âm thanh AI Voice-over (VieNeu-TTS) + Phụ đề (.srt)
thành file video MP4 hoàn chỉnh (1080p) bằng FFmpeg.
Thời lượng mỗi slide được tính toán ĐỘNG chính xác 100% theo độ dài file audio từng slide.
"""

import os
import subprocess
import soundfile as sf

def main():
    slides_dir = "demo/slides_images"
    audio_full_path = "demo/intro_output/intro_full.wav"
    sub_full_path = "demo/intro_output/intro_full.srt"
    output_mp4 = "demo/video_intro_hve_core.mp4"

    if not os.path.exists(audio_full_path):
        print(f"Lỗi: Không tìm thấy file âm thanh tại {audio_full_path}")
        return

    # Lấy tổng thời lượng audio
    audio_info = sf.info(audio_full_path)
    total_audio_dur = audio_info.duration

    slide_titles = [
        "Slide 1: HVE Core × GitHub Copilot",
        "Slide 2: Copilot viết đoạn này trong 3 giây. Bạn có duyệt không?",
        "Slide 3: HVE Core là gì? Bộ khung chuẩn từ Microsoft cho Copilot",
        "Slide 4: Cơ chế hoạt động: Quy chuẩn theo ngữ cảnh (Context-Aware Rules)",
        "Slide 5: RPI Workflow: Tránh AI can thiệp code trực tiếp thiếu kiểm soát",
        "Slide 6: Khuyến cáo từ Microsoft: Chiến lược Fork & Own",
        "Slide 7: Mở rộng ngoài IDE: Kết hợp Copilot Automations & GitLab MCP",
        "Slide 8: Harness² Framework: Cơ chế tự hoàn thiện quy chuẩn",
        "Slide 9: So sánh HVE Core và BMAD Framework: Lựa chọn theo bài toán",
        "Slide 10: Live Demo Agenda (6 phút)",
    ]

    print("=" * 65)
    print("Tính toán thời lượng hiển thị từng slide theo từng file audio tương ứng...")
    print("=" * 65)

    slide_timings = []
    # Khoảng lặng giữa các slide trong intro_full.wav là 0.35s
    pause_per_slide = 0.35

    for i in range(1, 11):
        img_name = f"slide.{i:03d}.png"
        wav_name = f"demo/intro_output/slide_{i:02d}.wav"
        desc = slide_titles[i - 1]

        if not os.path.exists(wav_name):
            print(f"Lỗi: Không tìm thấy file {wav_name}")
            return

        dur = sf.info(wav_name).duration
        display_dur = dur + pause_per_slide
        slide_timings.append((img_name, display_dur, desc, dur))

    # Căn chỉnh slide cuối cùng khớp tổng thời lượng audio
    sum_prev = sum(d for _, d, _, _ in slide_timings[:-1])
    last_dur = max(1.0, total_audio_dur - sum_prev)
    slide_timings[-1] = (slide_timings[-1][0], last_dur, slide_timings[-1][2], slide_timings[-1][3])

    for img_name, disp_dur, desc, audio_dur in slide_timings:
        print(f" - [{disp_dur:5.2f}s] (Audio: {audio_dur:5.2f}s) {desc} ({img_name})")

    print("-" * 65)
    print(f"Tổng thời lượng video: {total_audio_dur:.2f}s ({total_audio_dur/60:.2f} phút)")
    print("=" * 65)

    # Tạo file danh sách concat cho FFmpeg
    concat_txt_path = "demo/concat_slides.txt"
    with open(concat_txt_path, "w", encoding="utf-8") as f:
        for img_name, dur, _, _ in slide_timings:
            full_img = os.path.abspath(os.path.join(slides_dir, img_name))
            f.write(f"file '{full_img}'\n")
            f.write(f"duration {dur:.3f}\n")
        # Dòng cuối lặp lại file cuối cùng theo chuẩn concat demuxer của ffmpeg
        last_img = os.path.abspath(os.path.join(slides_dir, slide_timings[-1][0]))
        f.write(f"file '{last_img}'\n")

    # Lệnh FFmpeg ghép ảnh slide + audio + soft subtitle stream
    ffmpeg_bin = "/opt/homebrew/bin/ffmpeg"
    cmd = [
        ffmpeg_bin,
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_txt_path,
        "-i", audio_full_path,
        "-i", sub_full_path,
        "-vf", "fps=25,format=yuv420p",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-c:a", "aac",
        "-b:a", "192k",
        "-c:s", "mov_text",
        "-metadata:s:s:0", "language=vie",
        "-metadata:s:s:0", "title=Tiếng Việt",
        "-shortest",
        output_mp4
    ]

    print("\nĐang mã hóa video MP4 bằng FFmpeg...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("Lỗi FFmpeg:")
        print(res.stderr[-500:])
        return

    print("=" * 65)
    print(f"🎉 RENDER THÀNH CÔNG: {os.path.abspath(output_mp4)}")
    print("=" * 65)

if __name__ == "__main__":
    main()
