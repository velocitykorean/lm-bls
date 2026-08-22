"""
Calm Relaxation YouTube Thumbnail Generator
- Takes base nature / ambient background images
- Adds elegant, minimal, high-CTR relaxation typography (Cinzel / Playfair)
- Subtle atmospheric vignette & soft text glow
- YouTube standard 1280x720 (16:9)
"""

import os
import sys
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

RELAXATION_HOOKS = [
    {"main": "DEEP PEACE", "sub": "1 HOUR · 432Hz CALM"},
    {"main": "CALM MIND", "sub": "INSTANT STRESS RELIEF"},
    {"main": "DEEP SLEEP", "sub": "HEALING AMBIENCE"},
    {"main": "INSTANT RELIEF", "sub": "RAIN & NATURE SOUNDS"},
    {"main": "STILLNESS", "sub": "MEDITATION & RELAXATION"},
    {"main": "SERENITY", "sub": "STOP OVERTHINKING"}
]

def get_font(font_name="Cinzel.ttf", size=56):
    """Load font with project fallback hierarchy."""
    font_path = os.path.join(SCRIPT_DIR, "assets", "fonts", font_name)
    if os.path.exists(font_path):
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            pass
            
    # Fallback to Playfair
    pf = os.path.join(SCRIPT_DIR, "assets", "fonts", "PlayfairDisplay.ttf")
    if os.path.exists(pf):
        try:
            return ImageFont.truetype(pf, size)
        except Exception:
            pass

    # Windows system fonts
    for f in [r"C:\Windows\Fonts\georgiab.ttf", r"C:\Windows\Fonts\georgia.ttf", r"C:\Windows\Fonts\arialbd.ttf"]:
        if os.path.exists(f):
            try:
                return ImageFont.truetype(f, size)
            except Exception:
                pass

    return ImageFont.load_default()

def apply_ambient_vignette(img, intensity=0.35):
    """Applies a cinematic soft vignette to enhance text readability."""
    W, H = img.size
    mask = Image.new("L", (W, H), 0)
    draw_m = ImageDraw.Draw(mask)
    draw_m.ellipse([-W * 0.15, -H * 0.15, W * 1.15, H * 1.15], fill=int(255 * (1.0 - intensity)))
    mask = mask.filter(ImageFilter.GaussianBlur(radius=int(W * 0.07)))
    dark = Image.new("RGBA", (W, H), (10, 15, 20, 255))
    return Image.composite(img, dark, mask)

def create_relaxation_thumbnail(bg_path, output_path, main_text=None, sub_text=None, layout="bottom_left"):
    """
    Creates a minimal, elegant relaxation thumbnail.
    """
    if not main_text:
        preset = random.choice(RELAXATION_HOOKS)
        main_text = preset["main"]
        sub_text = preset["sub"]

    # 1. Open and resize/crop to 1280x720 (16:9)
    img = Image.open(bg_path).convert("RGBA")
    target_w, target_h = 1280, 720
    
    img_ratio = img.width / img.height
    target_ratio = target_w / target_h
    
    if img_ratio > target_ratio:
        new_w = int(img.height * target_ratio)
        offset = (img.width - new_w) // 2
        img = img.crop((offset, 0, offset + new_w, img.height))
    else:
        new_h = int(img.width / target_ratio)
        offset = (img.height - new_h) // 2
        img = img.crop((0, offset, img.width, offset + new_h))
        
    img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
    
    # Slight color boost for rich organic tones
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(1.08)
    
    # 2. Add subtle vignette
    img = apply_ambient_vignette(img, intensity=0.30)
    
    # 3. Create text overlay
    overlay = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    font_main = get_font("Cinzel.ttf", size=68)
    font_sub = get_font("PlayfairDisplay.ttf", size=32)
    font_badge = get_font("Cinzel.ttf", size=24)
    
    # Layout positioning (left-aligned with elegant margin)
    x_pos = 75
    y_base = target_h - 170
    
    # Subtitle / Category
    if sub_text:
        # Subtle glowing line or tag
        draw.text((x_pos + 1, y_base - 45 + 1), sub_text.upper(), font=font_badge, fill=(0, 0, 0, 180))
        draw.text((x_pos, y_base - 45), sub_text.upper(), font=font_badge, fill=(240, 220, 180, 240))
        # Small accent line
        line_y = y_base - 18
        draw.line([(x_pos, line_y), (x_pos + 200, line_y)], fill=(240, 220, 180, 180), width=2)
        
    # Main Headline (White with soft dark drop shadow)
    # Shadow pass
    for dx, dy in [(-2,2), (2,2), (0,3), (3,3)]:
        draw.text((x_pos + dx, y_base + dy), main_text.upper(), font=font_main, fill=(0, 0, 0, 200))
    # Crisp white text
    draw.text((x_pos, y_base), main_text.upper(), font=font_main, fill=(255, 255, 255, 255))
    
    # Badge (e.g. 432Hz / 1 HOUR) in top right corner
    badge_text = "1 HOUR · 432Hz"
    bbox = draw.textbbox((0, 0), badge_text, font=font_badge)
    bw, bh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    bx = target_w - bw - 75
    by = 50
    # Pill background for badge
    padding = 12
    draw.rounded_rectangle([bx - padding, by - padding, bx + bw + padding, by + bh + padding], radius=8, fill=(0, 0, 0, 130))
    draw.text((bx, by), badge_text, font=font_badge, fill=(255, 245, 220, 240))
    
    # Merge overlay
    final = Image.alpha_composite(img, overlay).convert("RGB")
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    final.save(output_path, quality=95)
    print(f"[+] Generated Relaxation Thumbnail: {output_path}")
    return output_path

if __name__ == "__main__":
    test_bg = os.path.join(SCRIPT_DIR, "input_images", "Hummingbird_Thumbnail_Base.jpg")
    if not os.path.exists(test_bg):
        test_bg = os.path.join(SCRIPT_DIR, "gemini_1080p_frame.png")
    test_out = os.path.join(SCRIPT_DIR, "output_thumbnails", "Test_Relaxation_Thumb.jpg")
    create_relaxation_thumbnail(test_bg, test_out, "DEEP PEACE", "CALM RELAXATION & SLEEP")
