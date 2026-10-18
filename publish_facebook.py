"""
Facebook Page Video Upload Script for LuminaBlooms
Uses Facebook Graph API to upload calm relaxation videos to the Lumina Blooms Facebook Page.
Supports chunked resumable upload for large video files with automatic retries,
exponential backoff, and offset recovery.
"""
import os
import sys
import json
import time
import subprocess
import requests
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

GRAPH_API_VERSION = "v21.0"
# 50 MB chunks: Meta Graph API's official standard chunk size (52,428,800 bytes).
# Keeps total requests to ~50 for a 2.5 GB video while avoiding HTTP 413 body size limits.
CHUNK_SIZE = 50 * 1024 * 1024


def get_facebook_credentials():
    """Retrieve Facebook Page ID and Page Access Token from environment."""
    page_id = (
        os.getenv('FB_PAGE_ID') or
        os.getenv('FACEBOOK_PAGE_ID') or
        os.getenv('LUMINA_BLOOMS_FB_PAGE_ID', '')
    ).strip()

    access_token = (
        os.getenv('FB_PAGE_ACCESS_TOKEN') or
        os.getenv('FACEBOOK_PAGE_ACCESS_TOKEN') or
        os.getenv('LUMINA_BLOOMS_FB_PAGE_ACCESS_TOKEN', '')
    ).strip()

    def mask(s):
        return f"{s[:4]}...{s[-4:]}" if s and len(s) > 8 else ("PRESENT" if s else "MISSING")

    print(f"[facebook] Page ID: {mask(page_id)}")
    print(f"[facebook] Access Token: {'PRESENT (len=' + str(len(access_token)) + ')' if access_token else 'MISSING'}")

    if not page_id or not access_token:
        raise ValueError(
            "Missing Facebook credentials! Set these environment variables or GitHub Secrets:\n"
            "  - FB_PAGE_ID\n"
            "  - FB_PAGE_ACCESS_TOKEN"
        )

    return page_id, access_token


def query_session_offset(upload_session_id, page_id, access_token):
    """Queries Meta Graph API to find the current acknowledged start_offset for this upload session."""
    try:
        url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{page_id}/videos"
        params = {
            "upload_phase": "transfer",
            "upload_session_id": upload_session_id,
            "access_token": access_token
        }
        resp = requests.get(url, params=params, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            if "start_offset" in data:
                return int(data["start_offset"])
    except Exception as e:
        print(f"[facebook] Note: could not query session offset: {e}")
    return None


def upload_video_resumable(video_path, title, description, page_id, access_token):
    """
    Upload video using Meta Graph API chunked resumable upload protocol.
    Features:
    - 20MB chunking to prevent server timeouts and reduce API request count.
    - Automatic retry with exponential backoff on HTTP 500, network errors, or rate limits.
    - Offset recovery querying Meta if an upload chunk is interrupted.
    - Multi-attempt finalize phase.
    """
    file_size = os.path.getsize(video_path)
    print(f"[facebook] Starting resumable upload for '{title}' ({file_size / (1024 * 1024):.2f} MB)...")

    # Phase 1: START
    start_url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{page_id}/videos"
    start_payload = {
        "upload_phase": "start",
        "file_size": file_size,
        "access_token": access_token
    }

    start_resp = None
    for s_attempt in range(1, 4):
        try:
            resp = requests.post(start_url, data=start_payload, timeout=60)
            if resp.status_code == 200:
                start_resp = resp.json()
                break
            else:
                print(f"[facebook] Start phase attempt {s_attempt} failed ({resp.status_code}): {resp.text}")
        except Exception as e:
            print(f"[facebook] Start phase attempt {s_attempt} error: {e}")
        time.sleep(3 * s_attempt)

    if not start_resp or "upload_session_id" not in start_resp:
        raise RuntimeError("Resumable upload START phase failed to obtain upload_session_id.")

    upload_session_id = start_resp["upload_session_id"]
    video_id = start_resp.get("video_id")
    start_offset = int(start_resp.get("start_offset", 0))

    print(f"[facebook] Session initialized (Session ID: {upload_session_id[:10]}...)")

    # Phase 2: TRANSFER CHUNKS
    chunk_size = CHUNK_SIZE
    max_chunk_retries = 5

    with open(video_path, "rb") as f:
        while start_offset < file_size:
            pct = min(100, int((start_offset / file_size) * 100))
            print(f"[facebook] Upload progress: {pct}% (offset {start_offset:,} / {file_size:,} bytes)")

            chunk_success = False
            for attempt in range(1, max_chunk_retries + 1):
                try:
                    f.seek(start_offset)
                    chunk_data = f.read(chunk_size)
                    if not chunk_data:
                        break

                    transfer_url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{page_id}/videos"
                    transfer_data = {
                        "upload_phase": "transfer",
                        "upload_session_id": upload_session_id,
                        "start_offset": start_offset,
                        "access_token": access_token
                    }
                    transfer_files = {
                        "video_file_chunk": ("chunk.mp4", chunk_data, "video/mp4")
                    }

                    t_resp = requests.post(transfer_url, data=transfer_data, files=transfer_files, timeout=600)

                    if t_resp.status_code == 200:
                        t_data = t_resp.json()
                        new_start = int(t_data.get("start_offset", start_offset + len(chunk_data)))
                        start_offset = new_start
                        chunk_size = CHUNK_SIZE
                        chunk_success = True
                        time.sleep(1)  # 1-second pause to prevent hammering the API
                        break
                    else:
                        print(f"[facebook] Chunk error at offset {start_offset} (HTTP {t_resp.status_code}, attempt {attempt}/{max_chunk_retries}): {t_resp.text}")
                except Exception as exc:
                    print(f"[facebook] Chunk exception at offset {start_offset} (attempt {attempt}/{max_chunk_retries}): {exc}")

                if attempt < max_chunk_retries:
                    backoff = 4 * (2 ** (attempt - 1))  # 4s, 8s, 16s, 32s
                    print(f"[facebook] Waiting {backoff}s before retrying chunk at offset {start_offset}...")
                    time.sleep(backoff)

                    # Check if Facebook acknowledged partial or full chunk
                    queried_offset = query_session_offset(upload_session_id, page_id, access_token)
                    if queried_offset is not None and queried_offset > start_offset:
                        print(f"[facebook] Recovered offset from Meta: {queried_offset:,} (was {start_offset:,})")
                        start_offset = queried_offset
                        chunk_success = True
                        break

            if not chunk_success:
                raise RuntimeError(f"Resumable upload TRANSFER failed at offset {start_offset} after {max_chunk_retries} attempts.")

    print(f"[facebook] Upload progress: 100% - All chunks transferred!")

    # Phase 3: FINISH
    print("[facebook] Finalizing video processing with title & description...")
    finish_url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{page_id}/videos"
    finish_payload = {
        "upload_phase": "finish",
        "upload_session_id": upload_session_id,
        "title": title,
        "description": description,
        "access_token": access_token
    }

    finish_data = None
    for f_attempt in range(1, 6):
        try:
            f_resp = requests.post(finish_url, data=finish_payload, timeout=90)
            if f_resp.status_code == 200:
                finish_data = f_resp.json()
                break
            else:
                print(f"[facebook] Finish phase attempt {f_attempt} returned {f_resp.status_code}: {f_resp.text}")
        except Exception as e:
            print(f"[facebook] Finish phase attempt {f_attempt} exception: {e}")
        time.sleep(10)

    if not finish_data:
        raise RuntimeError("Resumable upload FINISH failed: could not finalize video upload with Meta.")

    final_video_id = finish_data.get("id") or video_id
    print(f"🎉 [facebook] Video uploaded successfully! Video ID: {final_video_id}")
    print(f"🎉 [facebook] Watch URL: https://www.facebook.com/{page_id}/videos/{final_video_id}")
    return {"id": final_video_id, "success": True, "data": finish_data}


def upload_video_direct(video_path, title, description, page_id, access_token):
    """Fallback single-request multipart upload for small video files only (<100MB)."""
    print(f"[facebook] Direct uploading: {title}")
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{page_id}/videos"
    payload = {
        "title": title,
        "description": description,
        "access_token": access_token
    }
    with open(video_path, "rb") as f:
        files = {"source": (os.path.basename(video_path), f, "video/mp4")}
        resp = requests.post(url, data=payload, files=files, timeout=600)

    if resp.status_code != 200:
        raise RuntimeError(f"Direct video upload failed ({resp.status_code}): {resp.text}")

    data = resp.json()
    video_id = data.get("id")
    print(f"[facebook] Uploaded! Video ID: {video_id}")
    print(f"[facebook] URL: https://www.facebook.com/{page_id}/videos/{video_id}")
    return data


def create_facebook_optimized_video(input_path):
    """
    Creates an optimized video copy specifically for Facebook upload (~700-850 MB).
    The original uncompressed master file (CRF 18) was already uploaded to YouTube.
    Facebook recompresses all videos anyway, so optimizing the file to ~750 MB
    slashes Facebook API chunks from 524 calls down to ~15-18 calls.
    """
    if not os.path.exists(input_path):
        return input_path

    file_size_mb = os.path.getsize(input_path) / (1024 * 1024)
    if file_size_mb <= 850:
        return input_path

    output_path = os.path.splitext(input_path)[0] + "_fb_optimized.mp4"
    print(f"[facebook] Generating optimized Facebook video copy from {os.path.basename(input_path)} ({file_size_mb:.1f} MB)...")
    start_t = time.time()

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-c:v", "libx264",
        "-preset", "superfast",
        "-crf", "26",
        "-c:a", "copy",
        "-movflags", "+faststart",
        output_path
    ]

    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if res.returncode == 0 and os.path.exists(output_path):
        out_mb = os.path.getsize(output_path) / (1024 * 1024)
        elapsed = time.time() - start_t
        print(f"[facebook] Optimization complete in {elapsed:.1f}s: {file_size_mb:.1f} MB -> {out_mb:.1f} MB ({((file_size_mb - out_mb) / file_size_mb) * 100:.1f}% reduction)")
        return output_path
    else:
        print("[facebook] Note: Optimization failed or skipped, using original video.")
        return input_path


def upload_to_facebook(video_path, title, description):
    """
    Upload a video to the configured Facebook Page.
    1. Optimizes video for Facebook (~750 MB) while YouTube gets the full-quality master.
    2. Uploads via 50 MB chunked resumable upload (~15-18 calls total).
    3. Immediately removes the temporary optimized video after upload.
    """
    page_id, access_token = get_facebook_credentials()

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    fb_video_path = create_facebook_optimized_video(video_path)
    is_temp = (fb_video_path != video_path)

    try:
        return upload_video_resumable(fb_video_path, title, description, page_id, access_token)
    finally:
        if is_temp and os.path.exists(fb_video_path):
            try:
                os.remove(fb_video_path)
                print(f"[facebook] Cleaned up temporary optimized file: {fb_video_path}")
            except Exception as e_clean:
                print(f"[facebook] Note: could not remove temporary file: {e_clean}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python publish_facebook.py <video_path> [title] [description]")
        sys.exit(1)

    video_file = sys.argv[1]
    video_title = sys.argv[2] if len(sys.argv) > 2 else "Lumina Blooms - Ambient Relaxation"
    video_desc = sys.argv[3] if len(sys.argv) > 3 else "Calm relaxation music to soothe your soul and mind. 🌸✨"

    try:
        upload_to_facebook(video_file, video_title, video_desc)
    except Exception as exc:
        print(f"[facebook] Upload failed: {exc}")
        sys.exit(1)
