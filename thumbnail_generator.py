"""
Aesthetic YouTube Thumbnail Generator (LuminaBlooms)
High-CTR, minimalist typography with enhanced contrast backing:
- Gold-framed pill badge for subtitle ("MEDITATION & RELAXATION") for 100% readability over flowers/bright backgrounds
- Bold serif luxury headline ("STILLNESS" / "DEEP PEACE") with multi-pass shadow
- Top gold accent badge ("1 HOUR · 432Hz")
- 1280x720 16:9 output
"""

import os
import sys
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

RELAXATION_HOOKS = [
    {"main": "STILLNESS", "sub": "Meditation & Relaxation"},
    {"main": "DEEP PEACE", "sub": "Calm Relaxation & Sleep"},
    {"main": "SLEEP INSTANTLY", "sub": "Deep Healing & Stress Relief"},
    {"main": "CALM YOUR MIND", "sub": "432Hz Positive Energy"},
    {"main": "QUIET STILLNESS", "sub": "Meditation & Anxiety Release"},
    {"main": "NATURE EMBRACE", "sub": "Serene Ambient Soundscape"},
    {"main": "VELVET SLUMBER", "sub": "Instant Stress & Insomnia Relief"},
    {"main": "HEALING HARMONY", "sub": "Restorative Mind & Soul"}
]

def get_font(size=48):
    fonts = [
        os.path.join(SCRIPT_DIR, "assets", "fonts", "Cinzel.ttf"),
        r"C:\Windows\Fonts\georgiab.ttf",
        r"C:\Windows\Fonts\georgia.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
    ]
    for f in fonts:
        if os.path.exists(f):
            try:
                return ImageFont.truetype(f, size)
            except Exception:
                pass
    return ImageFont.load_default()

def create_relaxation_thumbnail(bg_path, output_path, main_text=None, sub_text=None, badge_text="1 HOUR · 432Hz"):
    """
    Creates an enhanced, high-contrast, elegant relaxation thumbnail.
    """
    if not main_text:
        preset = random.choice(RELAXATION_HOOKS)
        main_text = preset["main"]
        sub_text = preset["sub"]

    # 1. Open and resize/crop to 1280x720 (16:9)
    img = Image.open(bg_path).convert("RGBA")
    target_w, target_h = 1280, 720
    
    if img.width / img.height > target_w / target_h:
        new_w = int(img.height * (target_w / target_h))
        offset = (img.width - new_w) // 2
        img = img.crop((offset, 0, offset + new_w, img.height))
    else:
        new_h = int(img.width * (target_h / target_w))
        offset = (img.height - new_h) // 2
        img = img.crop((0, offset, img.width, offset + new_h))
        
    img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
    
    # 2. Rich color and contrast enhancement
    img = ImageEnhance.Color(img).enhance(1.10)
    img = ImageEnhance.Contrast(img).enhance(1.06)
    
    # 3. Soft directional gradient backing for maximum text contrast
    scrim = Image.new("L", (target_w, target_h), 0)
    sdraw = ImageDraw.Draw(scrim)
    for r in range(650, 0, -10):
        alpha = int((1.0 - (r / 650.0)**1.2) * 190)
        sdraw.ellipse([-150, target_h - 450, r * 1.8, target_h + 200], fill=alpha)
    scrim = scrim.filter(ImageFilter.GaussianBlur(30))
    dark_bg = Image.new("RGBA", (target_w, target_h), (6, 8, 12, 255))
    img = Image.composite(dark_bg, img, scrim)
    
    # 4. Draw overlays
    overlay = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    font_main = get_font(88)
    font_sub = get_font(32)
    font_badge = get_font(30)
    
    # --- Top-Left High-Visibility Gold Badge ---
    bx, by = 65, 45
    draw.rounded_rectangle([bx + 2, by + 3, bx + 250 + 2, by + 46 + 3], radius=10, fill=(0, 0, 0, 180))
    draw.rounded_rectangle([bx, by, bx + 250, by + 46], radius=10, fill=(14, 18, 24, 240), outline=(240, 205, 125, 255), width=2)
    draw.text((bx + 20, by + 8), badge_text, font=font_badge, fill=(255, 245, 215, 255))
    
    # --- Bottom-Left Text Stack ---
    x_pos = 65
    y_base = target_h - 170
    sub_y = y_base - 56
    
    # Subtitle Pill Tag (Ensures 100% readability over flowers & bright colors)
    if sub_text:
        s_bbox = draw.textbbox((0, 0), sub_text.upper(), font=font_sub)
        sw, sh = s_bbox[2] - s_bbox[0], s_bbox[3] - s_bbox[1]
        draw.rounded_rectangle([x_pos - 12, sub_y - 6, x_pos + sw + 16, sub_y + sh + 8], radius=8, fill=(14, 18, 24, 235), outline=(240, 205, 125, 255), width=2)
        draw.text((x_pos + 2, sub_y), sub_text.upper(), font=font_sub, fill=(255, 225, 140, 255))
        
    # Main Headline (Multi-directional heavy drop shadow for crisp white typography)
    for dx in range(-4, 5):
        for dy in range(-4, 5):
            if dx*dx + dy*dy <= 16:
                draw.text((x_pos + dx, y_base + dy), main_text.upper(), font=font_main, fill=(0, 0, 0, 255))
    draw.text((x_pos, y_base), main_text.upper(), font=font_main, fill=(255, 255, 255, 255))
    
    # 5. Merge and save
    final = Image.alpha_composite(img, overlay).convert("RGB")
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    final.save(output_path, quality=96)
    print(f"[+] Generated High-Visibility Thumbnail: {output_path}")
    return output_path

if __name__ == "__main__":
    test_bg = os.path.join(SCRIPT_DIR, "input_images", "Hummingbird_Thumbnail_Base.jpg")
    test_out = os.path.join(SCRIPT_DIR, "output_thumbnails", "Test_Relaxation_Thumb.jpg")
    create_relaxation_thumbnail(test_bg, test_out, "STILLNESS", "MEDITATION & RELAXATION")
