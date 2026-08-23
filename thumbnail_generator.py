"""
Aesthetic YouTube Thumbnail Generator (LuminaBlooms)
High-CTR, minimalist typography with clean organic aesthetics:
- Zero container boxes or artificial borders
- Bold luxury serif typography (Cinzel) with deep multi-pass shadows
- Top-Right corner badge ("1 HOUR · 432Hz")
- Warm champagne gold subtitle with elegant accent divider line
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

def get_font(font_name="Cinzel.ttf", size=48):
    fonts = [
        os.path.join(SCRIPT_DIR, "assets", "fonts", font_name),
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
    Creates a clean, box-free minimalist relaxation thumbnail.
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
    img = ImageEnhance.Contrast(img).enhance(1.05)
    
    # 3. Smooth natural ambient dark shadow behind text area (seamless, zero boxes)
    scrim = Image.new("L", (target_w, target_h), 0)
    sdraw = ImageDraw.Draw(scrim)
    # Bottom-left text area smooth shadow
    for r in range(650, 0, -10):
        alpha = int((1.0 - (r / 650.0)**1.3) * 190)
        sdraw.ellipse([-150, target_h - 450, r * 1.8, target_h + 200], fill=alpha)
    # Top-right corner smooth shadow
    for r in range(350, 0, -10):
        alpha = int((1.0 - (r / 350.0)**1.3) * 150)
        sdraw.ellipse([target_w - r * 1.6, -100, target_w + 100, r * 1.2], fill=alpha)
    scrim = scrim.filter(ImageFilter.GaussianBlur(35))
    dark_bg = Image.new("RGBA", (target_w, target_h), (8, 10, 14, 255))
    img = Image.composite(dark_bg, img, scrim)
    
    # 4. Draw pure typography overlays
    overlay = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    font_main = get_font("Cinzel.ttf", size=92)
    font_sub = get_font("Cinzel.ttf", size=40)
    font_badge = get_font("Cinzel.ttf", size=36)
    
    # --- Top-Right Badge (Pure Typography) ---
    bbox = draw.textbbox((0, 0), badge_text, font=font_badge)
    bw, bh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    bx = target_w - bw - 75
    by = 50
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            if dx*dx + dy*dy <= 9:
                draw.text((bx + dx, by + dy), badge_text, font=font_badge, fill=(0, 0, 0, 240))
    draw.text((bx, by), badge_text, font=font_badge, fill=(255, 240, 205, 255))
    
    # --- Bottom-Left Text Stack ---
    x_pos = 75
    y_base = target_h - 165
    sub_y = y_base - 62
    
    # Subtitle (Large, warm champagne gold with multi-pass shadow)
    if sub_text:
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                if dx*dx + dy*dy <= 9:
                    draw.text((x_pos + dx, sub_y + dy), sub_text.upper(), font=font_sub, fill=(0, 0, 0, 245))
        draw.text((x_pos, sub_y), sub_text.upper(), font=font_sub, fill=(255, 222, 145, 255))
        
        # Subtle gold accent line
        line_y = y_base - 14
        line_w = max(320, int(len(sub_text) * 16))
        draw.line([(x_pos, line_y), (x_pos + line_w, line_y)], fill=(255, 222, 145, 220), width=3)
    
    # Main Headline (Large, crisp pure white with heavy multi-pass shadow)
    for dx in range(-4, 5):
        for dy in range(-4, 5):
            if dx*dx + dy*dy <= 16:
                draw.text((x_pos + dx, y_base + dy), main_text.upper(), font=font_main, fill=(0, 0, 0, 255))
    draw.text((x_pos, y_base), main_text.upper(), font=font_main, fill=(255, 255, 255, 255))
    
    # 5. Merge and save
    final = Image.alpha_composite(img, overlay).convert("RGB")
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    final.save(output_path, quality=96)
    print(f"[+] Generated Clean Aesthetic Thumbnail: {output_path}")
    return output_path

if __name__ == "__main__":
    test_bg = os.path.join(SCRIPT_DIR, "input_images", "Hummingbird_Thumbnail_Base.jpg")
    test_out = os.path.join(SCRIPT_DIR, "output_thumbnails", "Test_Relaxation_Thumb.jpg")
    create_relaxation_thumbnail(test_bg, test_out, "STILLNESS", "MEDITATION & RELAXATION")
