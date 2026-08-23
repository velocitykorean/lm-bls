"""
Aesthetic YouTube Thumbnail Generator (LuminaBlooms)
High-CTR, minimalist typography with enhanced contrast backing:
- Serif luxury typography (Cinzel & PlayfairDisplay)
- High-visibility golden glass badge (1 HOUR · 432Hz)
- Directional contrast shadow gradient ensuring 100% legibility on mobile/desktop
- 1280x720 16:9 output
"""

import os
import sys
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

RELAXATION_HOOKS = [
    {"main": "DEEP PEACE", "sub": "Calm Relaxation & Sleep"},
    {"main": "SLEEP INSTANTLY", "sub": "Deep Healing & Stress Relief"},
    {"main": "CALM YOUR MIND", "sub": "432Hz Positive Energy"},
    {"main": "QUIET STILLNESS", "sub": "Meditation & Anxiety Release"},
    {"main": "NATURE EMBRACE", "sub": "Serene Ambient Soundscape"},
    {"main": "VELVET SLUMBER", "sub": "Instant Stress & Insomnia Relief"},
    {"main": "HEALING HARMONY", "sub": "Restorative Mind & Soul"}
]

def get_font(font_name="Cinzel.ttf", size=48):
    font_path = os.path.join(SCRIPT_DIR, "assets", "fonts", font_name)
    if os.path.exists(font_path):
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            pass
    for f in [r"C:\Windows\Fonts\georgiab.ttf", r"C:\Windows\Fonts\georgia.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"]:
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
    
    # 2. Rich color and contrast enhancement
    img = ImageEnhance.Color(img).enhance(1.10)
    img = ImageEnhance.Contrast(img).enhance(1.06)
    
    # 3. Soft directional gradient backing for maximum text contrast
    shadow_mask = Image.new("L", (target_w, target_h), 0)
    sdraw = ImageDraw.Draw(shadow_mask)
    for x in range(0, 680, 10):
        alpha = int((1.0 - (x / 680.0)**1.2) * 175)
        sdraw.rectangle([x, 0, x + 10, target_h], fill=alpha)
    shadow_mask = shadow_mask.filter(ImageFilter.GaussianBlur(25))
    dark_layer = Image.new("RGBA", (target_w, target_h), (8, 12, 16, 255))
    img = Image.composite(dark_layer, img, shadow_mask)
    
    # 4. Draw overlays
    overlay = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    font_main = get_font("Cinzel.ttf", size=88)
    font_sub = get_font("Cinzel.ttf", size=36)
    font_badge = get_font("Cinzel.ttf", size=32)
    
    # --- Top-Left High-Visibility Gold Badge ---
    bx, by = 75, 55
    bbox = draw.textbbox((0, 0), badge_text, font=font_badge)
    bw, bh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad_x, pad_y = 22, 12
    # Shadow
    draw.rounded_rectangle([bx - pad_x + 2, by - pad_y + 3, bx + bw + pad_x + 2, by + bh + pad_y + 3], radius=10, fill=(0, 0, 0, 200))
    # Pill with gold stroke
    draw.rounded_rectangle([bx - pad_x, by - pad_y, bx + bw + pad_x, by + bh + pad_y], radius=10, fill=(16, 20, 26, 240), outline=(240, 205, 125, 255), width=2)
    # Badge text
    draw.text((bx, by), badge_text, font=font_badge, fill=(255, 245, 215, 255))
    
    # --- Bottom-Left Text Stack ---
    x_pos = 75
    y_base = target_h - 170
    
    # Subtitle / Category
    if sub_text:
        sub_y = y_base - 55
        for dx, dy in [(-2,2), (2,2), (0,3), (3,3)]:
            draw.text((x_pos + dx, sub_y + dy), sub_text.upper(), font=font_sub, fill=(0, 0, 0, 240))
        draw.text((x_pos, sub_y), sub_text.upper(), font=font_sub, fill=(255, 218, 135, 255))
        
        # Gold accent line
        line_y = y_base - 14
        draw.line([(x_pos, line_y), (x_pos + 300, line_y)], fill=(255, 218, 135, 230), width=3)
        
    # Main Headline (Multi-directional heavy drop shadow for 100% readability)
    for dx, dy in [(-3,3), (3,3), (0,4), (4,4), (-2,0), (2,0), (0,-2), (0,2), (-3,-3), (3,-3)]:
        draw.text((x_pos + dx, y_base + dy), main_text.upper(), font=font_main, fill=(0, 0, 0, 255))
    draw.text((x_pos, y_base), main_text.upper(), font=font_main, fill=(255, 255, 255, 255))
    
    # 5. Merge and save
    final = Image.alpha_composite(img, overlay).convert("RGB")
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    final.save(output_path, quality=96)
    print(f"[+] Generated High-Visibility Thumbnail: {output_path}")
    return output_path

if __name__ == "__main__":
    test_bg = os.path.join(SCRIPT_DIR, "input_images", "Emerald-green_hummingbird_in_forest_202608221441.jpeg")
    if not os.path.exists(test_bg):
        test_bg = os.path.join(SCRIPT_DIR, "input_images", "Hummingbird_Thumbnail_Base.jpg")
    test_out = os.path.join(SCRIPT_DIR, "output_thumbnails", "Test_Relaxation_Thumb.jpg")
    create_relaxation_thumbnail(test_bg, test_out, "DEEP PEACE", "CALM RELAXATION & SLEEP")
