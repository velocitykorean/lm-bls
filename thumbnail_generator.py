"""
Aesthetic YouTube Thumbnail Generator (LuminaBlooms)
High-CTR, minimalist typography with cinematic organic aesthetics:
- Zero container boxes or artificial borders
- Zero underline lines
- Smooth Gaussian ambient drop shadows (eliminates all harsh thick/jagged pixel borders)
- Large luxury serif typography (Cinzel) for maximum mobile & desktop clarity
- Top-Right corner badge ("1 HOUR · 432Hz")
- Warm champagne gold subtitle with crisp white headline
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

def draw_cinematic_text(draw_target, pos, text, font, fill_color, shadow_blur=8, shadow_offset=(3, 5), shadow_opacity=220):
    """
    Renders text with a smooth Gaussian ambient shadow + directional drop shadow.
    Eliminates all thick, jagged, blocky black outlines.
    """
    w, h = draw_target.size
    shadow_layer = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow_layer)
    
    # 1. Ambient soft shadow
    s_draw.text(pos, text, font=font, fill=(0, 0, 0, shadow_opacity))
    # 2. Directional offset shadow
    ox, oy = shadow_offset
    s_draw.text((pos[0] + ox, pos[1] + oy), text, font=font, fill=(0, 0, 0, int(shadow_opacity * 0.9)))
    
    # Gaussian blur for butter-smooth natural shadow
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(shadow_blur))
    draw_target.alpha_composite(shadow_layer)
    
    # Draw crisp, clean text on top
    text_layer = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    t_draw = ImageDraw.Draw(text_layer)
    t_draw.text(pos, text, font=font, fill=fill_color)
    draw_target.alpha_composite(text_layer)

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
    img = ImageEnhance.Color(img).enhance(1.08)
    img = ImageEnhance.Contrast(img).enhance(1.04)
    
    # 3. Smooth natural ambient dark shadow behind text area (seamless, zero boxes)
    scrim = Image.new("L", (target_w, target_h), 0)
    sdraw = ImageDraw.Draw(scrim)
    # Bottom-left text area smooth shadow
    for r in range(600, 0, -10):
        alpha = int((1.0 - (r / 600.0)**1.4) * 160)
        sdraw.ellipse([-120, target_h - 420, r * 1.8, target_h + 180], fill=alpha)
    # Top-right corner smooth shadow
    for r in range(350, 0, -10):
        alpha = int((1.0 - (r / 350.0)**1.4) * 130)
        sdraw.ellipse([target_w - r * 1.5, -80, target_w + 80, r * 1.2], fill=alpha)
    scrim = scrim.filter(ImageFilter.GaussianBlur(40))
    dark_bg = Image.new("RGBA", (target_w, target_h), (6, 8, 12, 255))
    canvas = Image.composite(dark_bg, img, scrim)
    
    font_main = get_font("Cinzel.ttf", size=96)
    font_sub = get_font("Cinzel.ttf", size=38)
    font_badge = get_font("Cinzel.ttf", size=34)
    
    # --- 1. TOP-RIGHT BADGE ---
    dummy = ImageDraw.Draw(canvas)
    bbox = dummy.textbbox((0, 0), badge_text, font=font_badge)
    bw = bbox[2] - bbox[0]
    bx = target_w - bw - 75
    by = 50
    draw_cinematic_text(canvas, (bx, by), badge_text, font_badge, fill_color=(255, 242, 215, 255), shadow_blur=6, shadow_offset=(2, 4))
    
    # --- 2. BOTTOM-LEFT TEXT STACK (No underline, perfectly smooth cinematic glow) ---
    x_pos = 75
    y_base = target_h - 165
    sub_y = y_base - 56
    
    # Subtitle (Warm Champagne Gold)
    if sub_text:
        draw_cinematic_text(canvas, (x_pos, sub_y), sub_text.upper(), font_sub, fill_color=(255, 225, 145, 255), shadow_blur=6, shadow_offset=(2, 3))
        
    # Main Headline (Crisp Pure White)
    draw_cinematic_text(canvas, (x_pos, y_base), main_text.upper(), font_main, fill_color=(255, 255, 255, 255), shadow_blur=10, shadow_offset=(3, 5))
    
    # 5. Merge and save
    final = canvas.convert("RGB")
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    final.save(output_path, quality=96)
    print(f"[+] Generated Beautiful Thumbnail: {output_path}")
    return output_path

if __name__ == "__main__":
    img_red = os.path.join(SCRIPT_DIR, "input_images", "Hummingbird_Thumbnail_Base.jpg")
    img_forest = os.path.join(SCRIPT_DIR, "input_images", "Emerald-green_hummingbird_in_forest_202608221441.jpeg")

    out_red = os.path.join(SCRIPT_DIR, "output_thumbnails", "LuminaBlooms_RedHibiscus.jpg")
    out_forest = os.path.join(SCRIPT_DIR, "output_thumbnails", "LuminaBlooms_ForestEmerald.jpg")

    create_relaxation_thumbnail(img_red, out_red, "STILLNESS", "MEDITATION & RELAXATION")
    create_relaxation_thumbnail(img_forest, out_forest, "DEEP PEACE", "CALM RELAXATION & SLEEP")
