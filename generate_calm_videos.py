"""
YouTube Calm Relaxation Video Generator
- Automatically removes AI watermarks (Grok, Gemini/SynthID)
- Generates seamless looping calm relaxation videos (Ping-Pong / Crossfade)
- Loops and synchronizes relaxation background music (Driftwood Breath.mp3)
- Supports customizable duration (e.g., 5-minute preview or 1-hour full video)
- Hardware-accelerated (NVENC) with CPU (libx264) fallback
"""

import os
import sys
import argparse
import subprocess
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def get_media_duration(file_path):
    cmd = [
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'json', file_path
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(res.stdout)
    return float(data['format']['duration'])

def create_seamless_loop_block(clean_clip_path, output_loop_path, mode='pingpong', xfade_dur=1.5):
    """
    Creates a perfectly seamless loopable block.
    - 'pingpong': Forward + Reverse (100% zero-jump continuous motion)
    - 'crossfade': Crossfades end to beginning
    """
    print(f"[*] Generating {mode} seamless loop block...")
    if mode == 'pingpong':
        filter_complex = "[0:v]reverse[v_rev];[0:v][v_rev]concat=n=2:v=1:a=0[v_out]"
        cmd = [
            'ffmpeg', '-y',
            '-i', clean_clip_path,
            '-filter_complex', filter_complex,
            '-map', '[v_out]',
            '-c:v', 'libx264', '-crf', '15', '-preset', 'fast',
            output_loop_path
        ]
        subprocess.run(cmd, check=True)
    elif mode == 'crossfade':
        dur = get_media_duration(clean_clip_path)
        offset = dur - xfade_dur
        filter_complex = f"[0:v]split[v1][v2];[v2]trim=0:{xfade_dur},setpts=PTS-STARTPTS[v2_head];[v1]trim={xfade_dur}:{dur},setpts=PTS-STARTPTS[v1_tail];[v1_tail][v2_head]xfade=transition=fade:duration={xfade_dur}:offset={offset-xfade_dur}[v_out]"
        cmd = [
            'ffmpeg', '-y',
            '-i', clean_clip_path,
            '-filter_complex', filter_complex,
            '-map', '[v_out]',
            '-c:v', 'libx264', '-crf', '15', '-preset', 'fast',
            output_loop_path
        ]
        subprocess.run(cmd, check=True)
    print(f"[+] Created seamless loop block: {output_loop_path}")

def render_calm_video(input_video, input_audio, output_path, target_duration=300, delogo_params=None, mode='pingpong', encoder='h264_nvenc'):
    """
    Renders the final full video with watermark removal, seamless looping, and audio sync.
    """
    print(f"\n=======================================================")
    print(f"Starting render: {os.path.basename(output_path)}")
    print(f"Target Duration: {target_duration}s ({target_duration/60:.1f} minutes)")
    print(f"=======================================================\n")
    
    temp_clean = os.path.join(SCRIPT_DIR, "temp_clean.mp4")
    temp_block = os.path.join(SCRIPT_DIR, "temp_block.mp4")
    
    # 1. Remove watermark from base clip
    vf_chain = []
    if delogo_params:
        x, y, w, h = delogo_params
        vf_chain.append(f"delogo=x={x}:y={y}:w={w}:h={h}:show=0")
        print(f"[*] Applying watermark removal filter: x={x}, y={y}, w={w}, h={h}")
    
    vf_arg = ",".join(vf_chain) if vf_chain else "null"
    
    cmd_clean = [
        'ffmpeg', '-y',
        '-i', input_video,
        '-vf', vf_arg,
        '-c:v', 'libx264', '-crf', '15', '-preset', 'fast', '-an',
        temp_clean
    ]
    subprocess.run(cmd_clean, check=True)
    
    # 2. Create seamless loop unit
    create_seamless_loop_block(temp_clean, temp_block, mode=mode)
    
    # 3. Assemble full length video
    block_dur = get_media_duration(temp_block)
    loop_count = int(target_duration / block_dur) + 2
    
    print(f"[*] Assembling full video ({loop_count} loops) with background music...")
    
    fade_start = max(0, target_duration - 3)
    video_codec_args = ['-c:v', encoder, '-cq', '19', '-b:v', '12M'] if encoder == 'h264_nvenc' else ['-c:v', 'libx264', '-crf', '17', '-preset', 'medium']
    
    cmd_render = [
        'ffmpeg', '-y',
        '-stream_loop', str(loop_count), '-i', temp_block,
        '-stream_loop', '-1', '-i', input_audio,
        '-filter_complex', (
            f"[0:v]trim=0:{target_duration},setpts=PTS-STARTPTS,fade=t=out:st={fade_start}:d=3[v_out];"
            f"[1:a]atrim=0:{target_duration},asetpts=PTS-STARTPTS,afade=t=out:st={fade_start}:d=3[a_out]"
        ),
        '-map', '[v_out]',
        '-map', '[a_out]',
        *video_codec_args,
        '-c:a', 'aac', '-b:a', '320k',
        '-pix_fmt', 'yuv420p',
        '-movflags', '+faststart',
        output_path
    ]
    
    try:
        subprocess.run(cmd_render, check=True)
    except subprocess.CalledProcessError:
        print("[!] NVENC failed, falling back to libx264 CPU encoder...")
        cmd_render[cmd_render.index(encoder)] = 'libx264'
        subprocess.run(cmd_render, check=True)
        
    for temp in [temp_clean, temp_block]:
        if os.path.exists(temp):
            try:
                os.remove(temp)
            except Exception:
                pass
                
    print(f"\n[SUCCESS] Render complete: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Calm Relaxation Video Looper")
    parser.add_argument("--duration", type=int, default=300, help="Target duration in seconds (300 for 5m, 3600 for 1h)")
    parser.add_argument("--video", choices=['1', '2', 'both'], default='both', help="Which video to render (1=Grok, 2=Gemini, both=Both)")
    parser.add_argument("--mode", choices=['pingpong', 'crossfade'], default='pingpong', help="Loop mode")
    args = parser.parse_args()
    
    audio_path = os.path.join(SCRIPT_DIR, "Driftwood Breath.mp3")
    video1_path = os.path.join(SCRIPT_DIR, "video1_grok.mp4")
    video2_path = os.path.join(SCRIPT_DIR, "video2_gemini_1080p.mp4")
    
    dur_label = f"{args.duration//60}min" if args.duration >= 60 else f"{args.duration}s"
    
    delogo_grok = (1080, 620, 195, 95)
    delogo_gemini = (1700, 840, 90, 95)
    
    if args.video in ['1', 'both']:
        out1 = os.path.join(SCRIPT_DIR, f"Calm_Relaxation_Grok_{dur_label}.mp4")
        render_calm_video(
            input_video=video1_path,
            input_audio=audio_path,
            output_path=out1,
            target_duration=args.duration,
            delogo_params=delogo_grok,
            mode=args.mode
        )
        
    if args.video in ['2', 'both']:
        out2 = os.path.join(SCRIPT_DIR, f"Calm_Relaxation_Gemini_{dur_label}.mp4")
        render_calm_video(
            input_video=video2_path,
            input_audio=audio_path,
            output_path=out2,
            target_duration=args.duration,
            delogo_params=delogo_gemini,
            mode=args.mode
        )

if __name__ == '__main__':
    main()
