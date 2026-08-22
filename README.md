# Calm Relaxation YouTube Automation Bot 🌿🎶

A fully automated production pipeline for YouTube Calm & Relaxation channels (nature loops, ambient music, deep sleep, meditation).

---

## 📁 Architecture Overview

```
Calm relaxation/
├── .env                       # Environment configuration & Google Drive folder IDs
├── google_drive_fetch.py      # Downloads Video, Audio, Image triplets from Google Drive
├── thumbnail_generator.py     # Creates minimalist, high-CTR aesthetic thumbnails
├── video_generator.py         # Removes watermarks, builds seamless ping-pong loops & syncs audio
├── auto_pipeline.py           # Master end-to-end automation orchestrator
├── publish_youtube.py         # YouTube Data API upload module
├── published_videos.json      # Publication history tracking
├── input_videos/              # Local / synced 10s AI video loops (Gemini, Grok, etc.)
├── input_audio/               # Local / synced ambient relaxation music tracks (MP3/WAV)
├── input_images/              # Local / synced thumbnail background images
├── output_thumbnails/         # Generated YouTube thumbnails (1280x720)
└── output_videos/             # Rendered 1080p full-length videos (1 Hour)
```

---

## ⚙️ Configuration (`.env`)

Add your Google Drive Folder IDs in `.env`:

```env
# Google Drive Folder IDs
GOOGLE_DRIVE_VIDEO_FOLDER_ID=your_video_folder_id
GOOGLE_DRIVE_AUDIO_FOLDER_ID=your_audio_folder_id
GOOGLE_DRIVE_IMAGE_FOLDER_ID=your_image_folder_id

# Google Service Account Key
GOOGLE_SERVICE_ACCOUNT_KEY=service_account.json
```

> **Note:** Make sure you share each of your 3 Google Drive folders with the Service Account email found in `service_account.json` with **Viewer** access.

---

## 🚀 Usage Commands

### 1. Run Complete Automation Pipeline (1-Hour Video)
```powershell
python auto_pipeline.py --duration 3600
```

### 2. Run Preview Test (5-Minute Video Dry-Run)
```powershell
python auto_pipeline.py --duration 300 --dry-run
```

### 3. Generate Thumbnail Only
```powershell
python thumbnail_generator.py
```
