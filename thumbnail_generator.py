"""
Thumbnail Generator for Learn English with Tales (16:9 1920x1080 Full HD)
Renders high-contrast, clickable YouTube & Facebook thumbnails featuring the
story studio kid hosts and daily tale title badge.
"""
import os, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

if sys.platform == 'win32':
    try: sys.stdout.reconfigure(encoding='utf-8')
    except Exception: pass

BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"

GOLD_ACCENT = (255, 215, 0)       # Radiant Gold (#FFD700)
WHITE = (255, 255, 255)
DARK_CARD = (14, 18, 28, 225)
BORDER_GOLD = (255, 215, 0, 220)

def load_bold_font(size):
    fonts_to_try = [
        "C:/Windows/Fonts/impact.ttf",
        "C:/Windows/Fonts/ariblk.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/segoeuib.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    for p in fonts_to_try:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()

def create_thumbnail(topic_title: str, keyword: str = "STORY ADVENTURE", output_path: Path = None):
    """
    Renders an eye-catching YouTube / Facebook thumbnail for the given story topic.
    """
    studio_path = ASSETS_DIR / "tales_studio.png"
    if not studio_path.exists():
        studio_path = ASSETS_DIR / "kids_studio.png"

    if studio_path.exists():
        canvas = Image.open(studio_path).convert("RGBA").resize((1920, 1080), Image.Resampling.LANCZOS)
    else:
        canvas = Image.new("RGBA", (1920, 1080), (16, 20, 32, 255))

    # Dark cinematic vignette in the center zone to make the title pop
    vignette = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    vdraw = ImageDraw.Draw(vignette)
    vdraw.rectangle([(0, 0), (1920, 1080)], fill=(8, 12, 20, 80))
    # Center darkening box between left host and right host
    vdraw.rounded_rectangle([(440, 140), (1480, 820)], radius=40, fill=(4, 7, 14, 150))
    vignette = vignette.filter(ImageFilter.GaussianBlur(32))
    canvas.paste(vignette, (0, 0), vignette)

    draw = ImageDraw.Draw(canvas)

    # 1. Top Channel Tag Pill (Centered at top)
    f_tag = load_bold_font(30)
    tag_text = "LEARN ENGLISH WITH TALES • 20 MIN STORY PODCAST"
    tb_t = draw.textbbox((0, 0), tag_text, font=f_tag)
    tw_t = tb_t[2] - tb_t[0]
    pill_w = tw_t + 90
    pill_h = 58
    pill_x = 960 - pill_w // 2
    pill_y = 175
    draw.rounded_rectangle(
        [(pill_x, pill_y), (pill_x + pill_w, pill_y + pill_h)],
        radius=16,
        fill=(14, 18, 30, 240),
        outline=GOLD_ACCENT,
        width=2
    )

    # Vector Mic Icon
    mic_cx = pill_x + 35
    mic_cy = pill_y + pill_h // 2
    draw.rounded_rectangle([(mic_cx - 5, mic_cy - 10), (mic_cx + 5, mic_cy + 3)], radius=3, fill=GOLD_ACCENT)
    draw.arc([(mic_cx - 8, mic_cy - 3), (mic_cx + 8, mic_cy + 8)], start=0, end=180, fill=GOLD_ACCENT, width=2)
    draw.line([(mic_cx, mic_cy + 8), (mic_cx, mic_cy + 13)], fill=GOLD_ACCENT, width=2)
    draw.line([(mic_cx - 5, mic_cy + 13), (mic_cx + 5, mic_cy + 13)], fill=GOLD_ACCENT, width=2)

    draw.text((mic_cx + 20, pill_y + pill_h // 2), tag_text, fill=GOLD_ACCENT, font=f_tag, anchor="lm")

    # 2. Main Story Title (Multi-line auto-wrap, bold, high contrast)
    words = topic_title.upper().split()
    max_w = 960

    font_size = 92
    lines = []
    while font_size >= 44:
        f_main = load_bold_font(font_size)
        lines = []
        cur_line = []
        for w in words:
            test_line = " ".join(cur_line + [w])
            bb = draw.textbbox((0, 0), test_line, font=f_main)
            if bb[2] - bb[0] > max_w and cur_line:
                lines.append(" ".join(cur_line))
                cur_line = [w]
            else:
                cur_line.append(w)
        if cur_line:
            lines.append(" ".join(cur_line))

        if len(lines) <= 3:
            break
        font_size -= 6

    f_main = load_bold_font(font_size)
    line_h = int(font_size * 1.18)
    total_text_h = len(lines) * line_h
    start_y = 440 - total_text_h // 2

    # Draw Heavy Drop Shadows for crisp readability
    for i, line in enumerate(lines):
        y_pos = start_y + i * line_h
        for ox, oy in [(-3, -3), (3, -3), (-3, 3), (3, 3), (0, 5), (0, -5), (5, 0), (-5, 0)]:
            draw.text((960 + ox, y_pos + oy), line, fill=(0, 0, 0), font=f_main, anchor="mm")

    # Draw Main Title Text (Alternating Gold & White)
    for i, line in enumerate(lines):
        y_pos = start_y + i * line_h
        col = GOLD_ACCENT if (i % 2 == 1 or len(lines) == 1) else WHITE
        draw.text((960, y_pos), line, fill=col, font=f_main, anchor="mm")

    # 3. Keyword / Moral Theme Badge (Below Main Title)
    sub_pill_y = start_y + total_text_h + 35
    f_sub = load_bold_font(34)
    sub_text = f"• {keyword.upper()} • DAILY STORY LISTENING •"
    tb_s = draw.textbbox((0, 0), sub_text, font=f_sub)
    tw_s = tb_s[2] - tb_s[0]
    sw = tw_s + 70
    sh = 54
    draw.rounded_rectangle(
        [(960 - sw // 2, sub_pill_y), (960 + sw // 2, sub_pill_y + sh)],
        radius=14,
        fill=(22, 28, 44, 230),
        outline=GOLD_ACCENT,
        width=2
    )
    draw.text((960, sub_pill_y + sh // 2), sub_text, fill=WHITE, font=f_sub, anchor="mm")

    # 4. Bottom Host Names Badge (Lily & Leo)
    f_hosts = load_bold_font(28)
    hosts_text = "STORY HOSTS: LILY & LEO  •  DAILY ENGLISH IMMERSION"
    draw.text((960, 755), hosts_text, fill=(235, 225, 200), font=f_hosts, anchor="mm")

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # Save high quality JPEG for YouTube thumbnail (< 2MB requirement)
        canvas.convert("RGB").save(output_path, "JPEG", quality=95)
        # Also save PNG if requested
        png_path = output_path.with_suffix(".png")
        canvas.save(png_path, "PNG")
        print(f"[thumbnail] Generated YouTube thumbnail: {output_path}")

    return canvas

if __name__ == "__main__":
    test_out = BASE_DIR / "output" / "test_thumbnail.jpg"
    create_thumbnail("The Secret of the Whispering Tree", keyword="CURIOSITY & COURAGE", output_path=test_out)
    print("Done generating test thumbnail:", test_out)
