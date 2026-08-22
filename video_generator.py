"""
Calm Relaxation Video Generator Module
- Removes watermarks dynamically based on video resolution / source
- Ping-pong seamless 20s loop units
- Audio track loop with end fade-out
- Fast hardware-accelerated NVENC encoding
"""

import os
import sys
import json
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def get_media_info(file_path):
    cmd = [
        'ffprobe', '-v', 'error',
        '-show_entries', 'stream=width,height,codec_name:format=duration',
        '-of', 'json', file_path
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(res.stdout)
    duration = float(data['format']['duration'])
    v_stream = next((s for s in data.get('streams', []) if s.get('width')), None)
    width = int(v_stream['width']) if v_stream else 1920
    height = int(v_stream['height']) if v_stream else 1080
    return width, height, duration

def get_delogo_filter_for_video(width, height):
    """
    Returns optimal delogo filter coordinates based on resolution.
    - 1080p (Gemini Flow 4-star icon): x=1700, y=840, w=90, h=95
    - 720p (Grok Imagine logo & bar): x=1080, y=620, w=195, h=95
    """
    if width == 1920 and height == 1080:
        return "delogo=x=1700:y=840:w=90:h=95:show=0"
    elif width == 1280 and height == 720:
        return "delogo=x=1080:y=620:w=195:h=95:show=0"
    else:
        # Scale proportionally to bottom right
        rx = int(width * 0.88)
        ry = int(height * 0.82)
        rw = int(width * 0.10)
        rh = int(height * 0.10)
        return f"delogo=x={rx}:y={ry}:w={rw}:h={rh}:show=0"

def build_calm_relaxation_video(input_video, input_audio, output_path, duration_seconds=3600, remove_watermark=True):
    """
    Main entry point to build a full 1-hour (or custom duration) HD video.
    """
    print(f"\n[VIDEO] Building Calm Relaxation Video...")
    print(f"  Input Video: {os.path.basename(input_video)}")
    print(f"  Input Audio: {os.path.basename(input_audio)}")
    print(f"  Target Duration: {duration_seconds}s ({duration_seconds/60:.1f} mins)")
    print(f"  Output Path: {output_path}")

    temp_clean = os.path.join(SCRIPT_DIR, "temp_clean.mp4")
    temp_block = os.path.join(SCRIPT_DIR, "temp_block.mp4")

    # Step 1: Delogo clean
    w, h, orig_dur = get_media_info(input_video)
    vf_list = []
    if remove_watermark:
        delogo_str = get_delogo_filter_for_video(w, h)
        vf_list.append(delogo_str)
        print(f"[VIDEO] Applied watermark removal: {delogo_str}")

    vf_arg = ",".join(vf_list) if vf_list else "null"

    cmd_clean = [
        'ffmpeg', '-y',
        '-i', input_video,
        '-vf', vf_arg,
        '-c:v', 'libx264', '-crf', '15', '-preset', 'fast', '-an',
        temp_clean
    ]
    subprocess.run(cmd_clean, check=True)

    # Step 2: Create ping-pong loop block (Forward + Reverse = seamless continuous flow)
    cmd_block = [
        'ffmpeg', '-y',
        '-i', temp_clean,
        '-filter_complex', "[0:v]reverse[v_rev];[0:v][v_rev]concat=n=2:v=1:a=0[v_out]",
        '-map', '[v_out]',
        '-c:v', 'libx264', '-crf', '15', '-preset', 'fast',
        temp_block
    ]
    subprocess.run(cmd_block, check=True)

    _, _, block_dur = get_media_info(temp_block)
    loop_count = int(duration_seconds / block_dur) + 2
    fade_start = max(0, duration_seconds - 3)

    # Step 3: Full assemble with audio loop and fade out
    print(f"[VIDEO] Assembling full video with hardware acceleration...")
    cmd_full = [
        'ffmpeg', '-y',
        '-stream_loop', str(loop_count), '-i', temp_block,
        '-stream_loop', '-1', '-i', input_audio,
        '-filter_complex', (
            f"[0:v]trim=0:{duration_seconds},setpts=PTS-STARTPTS,fade=t=out:st={fade_start}:d=3[v_out];"
            f"[1:a]atrim=0:{duration_seconds},asetpts=PTS-STARTPTS,afade=t=out:st={fade_start}:d=3[a_out]"
        ),
        '-map', '[v_out]',
        '-map', '[a_out]',
        '-c:v', 'h264_nvenc', '-cq', '19', '-b:v', '14M',
        '-c:a', 'aac', '-b:a', '320k',
        '-pix_fmt', 'yuv420p',
        '-movflags', '+faststart',
        output_path
    ]

    try:
        subprocess.run(cmd_full, check=True)
    except subprocess.CalledProcessError:
        print("[VIDEO WARN] NVENC failed, falling back to libx264...")
        cmd_full[cmd_full.index('h264_nvenc')] = 'libx264'
        subprocess.run(cmd_full, check=True)

    # Cleanup temp
    for t in [temp_clean, temp_block]:
        if os.path.exists(t):
            try:
                os.remove(t)
            except Exception:
                pass

    print(f"[SUCCESS] Video rendered successfully: {output_path}")
    return True
