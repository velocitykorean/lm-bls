"""
Calm Relaxation Video Generator Module
- Removes watermarks dynamically based on video resolution / source
- Auto-Upscales 720p videos to 1080p Full HD using high-fidelity Lanczos + Unsharp filtering
- Ping-pong seamless 20s loop units
- Audio track loop with end fade-out
- Auto-detects NVENC GPU acceleration with smart CPU (libx264 veryfast) fallback
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

def is_nvenc_available():
    try:
        res = subprocess.run(
            ['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'testsrc=duration=1:size=64x64:rate=24', '-c:v', 'h264_nvenc', '-f', 'null', '-'],
            capture_output=True, text=True
        )
        return res.returncode == 0
    except Exception:
        return False

def get_video_filter_chain(width, height, upscale_to_1080p=True):
    """
    Returns optimal filter chain for watermark removal and optional 1080p upscaling.
    """
    filters = []
    
    # 1. Delogo at native resolution
    if width == 1920 and height == 1080:
        filters.append("delogo=x=1700:y=840:w=90:h=95:show=0")
    elif width == 1280 and height == 720:
        # Gemini 720p star removal
        filters.append("delogo=x=1130:y=555:w=65:h=70:show=0")
    else:
        rx = int(width * 0.88)
        ry = int(height * 0.82)
        rw = int(width * 0.10)
        rh = int(height * 0.10)
        filters.append(f"delogo=x={rx}:y={ry}:w={rw}:h={rh}:show=0")
        
    # 2. High Quality 1080p Upscaling (if input is 720p or lower)
    if upscale_to_1080p and (width < 1920 or height < 1080):
        print(f"[VIDEO] Auto-upscaling from {width}x{height} to 1920x1080 Full HD (Lanczos + Unsharp)...")
        filters.append("scale=1920:1080:flags=lanczos+accurate_rnd")
        filters.append("unsharp=5:5:0.8:5:5:0.0")
        
    return ",".join(filters) if filters else "null"

def build_calm_relaxation_video(input_video, input_audio, output_path, duration_seconds=3600, remove_watermark=True, upscale_to_1080p=True):
    """
    Main entry point to build a full 1-hour (or custom duration) 1080p HD video.
    """
    print(f"\n[VIDEO] Building Calm Relaxation Video...")
    print(f"  Input Video: {os.path.basename(input_video)}")
    print(f"  Input Audio: {os.path.basename(input_audio)}")
    print(f"  Target Duration: {duration_seconds}s ({duration_seconds/60:.1f} mins)")
    print(f"  Output Path: {output_path}")

    temp_clean = os.path.join(SCRIPT_DIR, "temp_clean.mp4")
    temp_block = os.path.join(SCRIPT_DIR, "temp_block.mp4")

    # Step 1: Delogo clean & Upscale
    w, h, orig_dur = get_media_info(input_video)
    vf_arg = get_video_filter_chain(w, h, upscale_to_1080p=upscale_to_1080p)

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

    # Check encoder
    if is_nvenc_available():
        print("[VIDEO] Using NVIDIA NVENC Hardware Acceleration...")
        video_codec_args = ['-c:v', 'h264_nvenc', '-cq', '19', '-b:v', '14M']
    else:
        print("[VIDEO] Using CPU libx264 encoder (veryfast preset)...")
        video_codec_args = ['-c:v', 'libx264', '-crf', '18', '-preset', 'veryfast']

    # Step 3: Full assemble with audio loop and fade out
    print(f"[VIDEO] Assembling full 1080p video...")
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
        *video_codec_args,
        '-c:a', 'aac', '-b:a', '320k',
        '-pix_fmt', 'yuv420p',
        '-movflags', '+faststart',
        output_path
    ]

    subprocess.run(cmd_full, check=True)

    # Cleanup temp
    for t in [temp_clean, temp_block]:
        if os.path.exists(t):
            try:
                os.remove(t)
            except Exception:
                pass

    print(f"[SUCCESS] 1080p Video rendered successfully: {output_path}")
    return True
