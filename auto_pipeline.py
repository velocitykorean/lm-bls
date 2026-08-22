"""
Calm Relaxation YouTube Automation Pipeline
Full End-to-End Orchestrator:
1. Fetches Video, Audio, Image triplets from Google Drive (or local folders)
2. Watermark elimination
3. Minimalist aesthetic thumbnail creation
4. 1-Hour HD Video rendering (NVENC)
5. YouTube publish & metadata tagging
"""

import os
import sys
import json
import glob
import random
import time
from datetime import datetime
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

from google_drive_fetch import fetch_assets_triplet
from thumbnail_generator import create_relaxation_thumbnail, RELAXATION_HOOKS
from video_generator import build_calm_relaxation_video

PUBLISHED_LOG = "published_videos.json"
ALLOW_REPOST = os.getenv("ALLOW_REPOST", "true").lower() == "true"

def get_published_history():
    if os.path.exists(PUBLISHED_LOG):
        try:
            with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_published_entry(video_name, audio_name, image_name, yt_video_id=None, title=""):
    history = get_published_history()
    entry = {
        "video_file": os.path.basename(video_name),
        "audio_file": os.path.basename(audio_name),
        "image_file": os.path.basename(image_name) if image_name else "",
        "youtube_id": yt_video_id,
        "youtube_url": f"https://youtu.be/{yt_video_id}" if yt_video_id else "LOCAL_RENDER",
        "title": title,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    history.append(entry)
    with open(PUBLISHED_LOG, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    print(f"[LOG] Saved publication record to {PUBLISHED_LOG}")

def generate_youtube_metadata(audio_path, video_path):
    """Generate SEO-optimized calm relaxation title, description, and tags."""
    base_name = os.path.splitext(os.path.basename(audio_path))[0].replace("_", " ").title()
    vid_name = os.path.splitext(os.path.basename(video_path))[0].replace("_", " ").title()
    
    titles_templates = [
        f"1 Hour {base_name} | Deep Relaxation, Sleep & Stress Relief Music 432Hz",
        f"Calm Your Mind & Sleep Instantly | {base_name} Ambient Relaxation (1 Hour)",
        f"Deep Peace & Positive Energy | {base_name} Nature & Meditation Music",
        f"Instant Stress Relief & Anxiety Release | 1 Hour Peaceful {base_name}"
    ]
    
    title = random.choice(titles_templates)
    
    desc = (
        f"Immerse yourself in 1 hour of serene calm relaxation with '{base_name}'.\n\n"
        f"Designed for deep sleep, meditation, stress relief, reading, and anxiety reduction. "
        f"Let the gentle ambient music and tranquil nature visuals calm your mind and bring deep inner peace.\n\n"
        f"✨ Benefits:\n"
        f"• Instant calm and stress relief\n"
        f"• Deep sleep and insomnia relief\n"
        f"• Focus, study, and meditation background\n"
        f"• Positive energy alignment (432Hz)\n\n"
        f"#CalmMusic #RelaxationMusic #DeepSleep #StressRelief #Meditation #432Hz #1HourRelaxation"
    )
    
    tags = [
        "calm music", "relaxation music", "deep sleep music", "stress relief",
        "sleep instantly", "meditation music", "peaceful music", "1 hour relaxation",
        "nature sounds", "ambient music", "432hz", "calm relaxation", "deep peace"
    ]
    
    return title, desc, tags

def run_pipeline(duration=3600, dry_run=False):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_thumb_dir = os.path.join(script_dir, "output_thumbnails")
    output_video_dir = os.path.join(script_dir, "output_videos")
    
    os.makedirs(output_thumb_dir, exist_ok=True)
    os.makedirs(output_video_dir, exist_ok=True)
    
    print("\n" + "="*60)
    print("      CALM RELAXATION BOT - AUTOMATED PIPELINE")
    print("="*60)
    
    # Step 1: Fetch triplet
    vid_path, aud_path, img_path, is_repost = fetch_assets_triplet(allow_repost=ALLOW_REPOST)
    if not vid_path or not aud_path:
        print("[ERROR] Could not fetch required video and audio assets.")
        return False
        
    print(f"\n[STEP 1] Assets Selected:")
    print(f"  • Video: {os.path.basename(vid_path)}")
    print(f"  • Audio: {os.path.basename(aud_path)}")
    print(f"  • Image: {os.path.basename(img_path) if img_path else 'None (extracting from video)'}")
    
    # If no thumbnail image, extract frame 2s from video
    if not img_path or not os.path.exists(img_path):
        img_path = os.path.join(script_dir, "input_images", f"frame_{os.path.splitext(os.path.basename(vid_path))[0]}.jpg")
        import subprocess
        subprocess.run(['ffmpeg', '-y', '-ss', '00:00:02', '-i', vid_path, '-frames:v', '1', img_path], check=True)
        
    # Step 2: Generate Thumbnail
    safe_name = "".join(c for c in os.path.splitext(os.path.basename(aud_path))[0] if c.isalnum() or c in (' ', '_', '-')).strip()
    thumb_output = os.path.join(output_thumb_dir, f"Thumb_{safe_name}.jpg")
    
    hook = random.choice(RELAXATION_HOOKS)
    print(f"\n[STEP 2] Creating Thumbnail with Hook: '{hook['main']}'...")
    create_relaxation_thumbnail(img_path, thumb_output, main_text=hook['main'], sub_text=hook['sub'])
    
    # Step 3: Render Full Video
    dur_label = f"{duration//60}min" if duration >= 60 else f"{duration}s"
    final_video_path = os.path.join(output_video_dir, f"Calm_{safe_name}_{dur_label}.mp4")
    
    print(f"\n[STEP 3] Rendering {dur_label} Looping Video...")
    success = build_calm_relaxation_video(
        input_video=vid_path,
        input_audio=aud_path,
        output_path=final_video_path,
        duration_seconds=duration,
        remove_watermark=True
    )
    
    if not success:
        print("[ERROR] Video generation failed.")
        return False
        
    # Step 4: Metadata & Publishing
    title, desc, tags = generate_youtube_metadata(aud_path, vid_path)
    print(f"\n[STEP 4] Generated YouTube Metadata:")
    print(f"  • Title: {title}")
    print(f"  • Tags: {', '.join(tags[:6])}...")
    
    if dry_run:
        print(f"\n[DRY RUN] Finished. Video saved at: {final_video_path}")
        print(f"[DRY RUN] Thumbnail saved at: {thumb_output}")
        save_published_entry(vid_path, aud_path, img_path, yt_video_id=None, title=title)
        return True
        
    # Optional Step 5: Upload to YouTube if publish_youtube exists
    try:
        from publish_youtube import upload_to_youtube, set_video_thumbnail
        print(f"\n[STEP 5] Uploading to YouTube...")
        video_id = upload_to_youtube(final_video_path, title, desc, tags=tags)
        if video_id:
            set_video_thumbnail(video_id, thumb_output)
            save_published_entry(vid_path, aud_path, img_path, yt_video_id=video_id, title=title)
            print(f"🎉 SUCCESS! Published to YouTube: https://youtu.be/{video_id}")
            return True
    except Exception as e:
        print(f"[YOUTUBE NOTE] YouTube API upload skipped or not configured ({e}). Video is ready in output_videos/")
        save_published_entry(vid_path, aud_path, img_path, yt_video_id=None, title=title)
        return True

if __name__ == "__main__":
    dur = 3600
    is_dry = "--dry-run" in sys.argv
    for idx, arg in enumerate(sys.argv):
        if arg == "--duration" and idx + 1 < len(sys.argv):
            dur = int(sys.argv[idx + 1])
    run_pipeline(duration=dur, dry_run=is_dry)
