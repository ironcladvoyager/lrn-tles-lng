"""
Real-Life English Situations & Roleplay - Video Generator (9:16 Vertical Reel)
Simulates authentic conversational roleplays (Café, Hotel, Job Interview, Airport).
Features:
- Dual-speaker dialogue simulation with contextual speaker bubbles
- Highlighting natural expressions
- Practical "Pro Native Tip" card
"""
import os, sys, json, subprocess, random, requests, re, asyncio
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from dotenv import load_dotenv
import edge_tts

load_dotenv()

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

WIDTH = 1080
HEIGHT = 1920
FPS = 30

BG_DARK = (13, 20, 36)
TEAL_ACCENT = (20, 184, 166)      # #14B8A6
AMBER_ACCENT = (245, 158, 11)     # #F59E0B
WHITE = (255, 255, 255)
GOLD = (250, 204, 21)
CARD_BG = (24, 33, 56)

VOICE_A = "en-US-AvaNeural"         # Customer / Speaker A
VOICE_B = "en-US-AndrewNeural"      # Barista / Speaker B

SCENARIOS = [
    {
        "title": "ORDERING AT A COFFEE SHOP",
        "icon": "☕",
        "tip": "Say 'Could I get...' instead of 'I want...' to sound polite and natural!",
        "dialogue": [
            {"speaker": "Customer ☕", "voice": VOICE_A, "text": "Hi there! Could I get a medium iced latte with **oat milk**, please?"},
            {"speaker": "Barista 🧑‍🍳", "voice": VOICE_B, "text": "Sure thing! Would you like any extra **flavor syrup** or whipped cream?"},
            {"speaker": "Customer ☕", "voice": VOICE_A, "text": "Just one pump of vanilla, and **easy ice**, please."},
            {"speaker": "Barista 🧑‍🍳", "voice": VOICE_B, "text": "You got it! That will be **five twenty-five** at the register."}
        ]
    },
    {
        "title": "CHECKING IN AT A HOTEL",
        "icon": "🏨",
        "tip": "Ask 'Is breakfast included?' to confirm hotel amenities politely!",
        "dialogue": [
            {"speaker": "Guest 🧳", "voice": VOICE_A, "text": "Good afternoon! I have a **reservation** under the name Emma."},
            {"speaker": "Front Desk 🛎️", "voice": VOICE_B, "text": "Welcome Emma! Let me pull up your booking. Yes, a **deluxe king** room for three nights."},
            {"speaker": "Guest 🧳", "voice": VOICE_A, "text": "Wonderful. What time is **checkout** on Sunday morning?"},
            {"speaker": "Front Desk 🛎️", "voice": VOICE_B, "text": "Checkout is at **eleven AM**, and breakfast starts daily at seven."}
        ]
    }
]

def load_font(size, bold=True):
    fonts_to_try = [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/trebucbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in fonts_to_try:
        if Path(p).exists():
            try: return ImageFont.truetype(p, size)
            except: continue
    return ImageFont.load_default()

def render_situation_frame(scenario, active_turn_idx, out_path):
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), BG_DARK)
    draw = ImageDraw.Draw(canvas)

    # Gradient background
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(13 + ratio * 15)
        g = int(20 + ratio * 20)
        b = int(36 + ratio * 30)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b, 255))

    # Header Bar
    draw.rounded_rectangle([(70, 90), (WIDTH - 70, 180)], radius=22, fill=(20, 30, 52), outline=TEAL_ACCENT, width=3)
    f_hdr = load_font(32, bold=True)
    draw.text((WIDTH // 2, 135), f"📍 REAL ENGLISH IN ACTION", fill=TEAL_ACCENT, font=f_hdr, anchor="mm")

    # Scenario Pill
    draw.rounded_rectangle([(70, 210), (WIDTH - 70, 310)], radius=25, fill=(30, 42, 70), outline=AMBER_ACCENT, width=3)
    f_scen = load_font(42, bold=True)
    draw.text((WIDTH // 2, 260), f"{scenario['icon']} {scenario['title']}", fill=GOLD, font=f_scen, anchor="mm")

    # Render All Dialogue Cards up to current active turn
    cur_y = 360
    f_spk = load_font(30, bold=True)
    f_body = load_font(40, bold=True)

    for i, turn in enumerate(scenario["dialogue"]):
        is_active = (i == active_turn_idx)
        card_h = 240
        is_spk_a = ("Customer" in turn["speaker"] or "Guest" in turn["speaker"])

        border_col = AMBER_ACCENT if is_spk_a else TEAL_ACCENT
        bg_col = (40, 50, 80) if is_active else (22, 30, 50)
        thickness = 5 if is_active else 2

        draw.rounded_rectangle([(70, cur_y), (WIDTH - 70, cur_y + card_h)], radius=25, fill=bg_col, outline=border_col, width=thickness)

        # Speaker Tag
        draw.text((110, cur_y + 40), turn["speaker"], fill=border_col, font=f_spk, anchor="lm")
        if is_active:
            f_now = load_font(24, bold=True)
            draw.rounded_rectangle([(WIDTH - 260, cur_y + 20), (WIDTH - 100, cur_y + 60)], radius=12, fill=border_col)
            draw.text((WIDTH - 180, cur_y + 40), "🗣️ SPEAKING", fill=WHITE, font=f_now, anchor="mm")

        # Dialogue text with wrapping
        raw_text = turn["text"].replace("**", "")
        words = raw_text.split()
        lines = []
        cur_l = []
        for w in words:
            tb = draw.textbbox((0, 0), " ".join(cur_l + [w]), font=f_body)
            if tb[2] - tb[0] > (WIDTH - 240):
                lines.append(" ".join(cur_l))
                cur_l = [w]
            else:
                cur_l.append(w)
        if cur_l:
            lines.append(" ".join(cur_l))

        for l_idx, line in enumerate(lines[:3]):
            text_col = GOLD if is_active else (220, 225, 240)
            draw.text((110, cur_y + 110 + l_idx * 55), line, fill=text_col, font=f_body, anchor="lm")

        cur_y += card_h + 25

    # Bottom Pro Tip Box
    draw.rounded_rectangle([(70, 1460), (WIDTH - 70, 1720)], radius=25, fill=(18, 28, 48), outline=GOLD, width=3)
    f_tip_lbl = load_font(30, bold=True)
    draw.text((110, 1505), "💡 PRO NATIVE TIP FOR LEARNERS:", fill=GOLD, font=f_tip_lbl, anchor="lm")

    f_tip_txt = load_font(36, bold=False)
    tip_words = scenario["tip"].split()
    tip_lines = []
    c_tl = []
    for tw in tip_words:
        tb = draw.textbbox((0, 0), " ".join(c_tl + [tw]), font=f_tip_txt)
        if tb[2] - tb[0] > (WIDTH - 240):
            tip_lines.append(" ".join(c_tl))
            c_tl = [tw]
        else:
            c_tl.append(tw)
    if c_tl:
        tip_lines.append(" ".join(c_tl))

    for tl_idx, tl in enumerate(tip_lines):
        draw.text((110, 1575 + tl_idx * 50), tl, fill=WHITE, font=f_tip_txt, anchor="lm")

    # Footer CTA
    f_cta = load_font(32, bold=True)
    draw.text((WIDTH // 2, 1800), "⭐ Save this reel for your next trip!", fill=TEAL_ACCENT, font=f_cta, anchor="mm")
    f_sub = load_font(26, bold=False)
    draw.text((WIDTH // 2, 1850), "Follow Real World English for daily dialogues!", fill=(148, 163, 184), font=f_sub, anchor="mm")

    canvas.convert("RGB").save(out_path, quality=95)

async def assemble_situation_reel(scenario, run_dir):
    frames_dir = run_dir / "frames"
    clips_dir = run_dir / "clips"
    audio_dir = run_dir / "audio"
    for d in [frames_dir, clips_dir, audio_dir]:
        d.mkdir(parents=True, exist_ok=True)

    clips = []
    for i, turn in enumerate(scenario["dialogue"]):
        mp3_p = audio_dir / f"turn_{i}.mp3"
        spoken = turn["text"].replace("**", "")
        await edge_tts.Communicate(spoken, turn["voice"], rate="-10%").save(str(mp3_p))

        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(mp3_p)],
            capture_output=True, text=True, check=True
        )
        dur = float(r.stdout.strip())

        frame_p = frames_dir / f"frame_{i}.png"
        render_situation_frame(scenario, i, str(frame_p))

        clip_p = clips_dir / f"clip_{i}.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-loop", "1", "-i", str(frame_p), "-i", str(mp3_p),
            "-vf", f"scale={WIDTH}:{HEIGHT},fps={FPS}",
            "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p", "-preset", "fast", "-t", f"{dur:.3f}", str(clip_p)
        ], check=True, capture_output=True)

        clips.append(clip_p)

    concat_txt = run_dir / "concat.txt"
    with open(concat_txt, "w") as f:
        for c in clips:
            f.write(f"file '{c.resolve().as_posix()}'\n")

    final_v = run_dir / "situation_roleplay_final.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_txt), "-c", "copy", str(final_v)], check=True, capture_output=True)
    return final_v

async def run_situation_generation(scen_idx=0):
    scenario = SCENARIOS[scen_idx % len(SCENARIOS)]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = OUTPUT_DIR / f"run_{ts}"
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"[Real Situations] Generating Roleplay: {scenario['title']}...")
    final_v = await assemble_situation_reel(scenario, run_dir)

    meta = {
        "title": f"Real English Roleplay: {scenario['title']} | Everyday Conversations",
        "description": f"Learn how to speak naturally in real-life situations! Watch this simulation of '{scenario['title']}'. Pro Tip: {scenario['tip']} Follow for more! ☕✈️",
        "scenario": scenario["title"]
    }
    with open(run_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"[Real Situations] Video ready: {final_v}")
    return final_v, meta
