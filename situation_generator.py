"""
REAL ENGLISH DIALOGUES PODCAST - 16:9 FULL HD (1920x1080) VIDEO GENERATOR
Theme: Cozy Lofi Coffeehouse Studio & Real Situations
Visuals: Dual Vintage Acoustic Mics + 24-Bar Amber VU Equalizer + Single-Line Highlighted Subtitles
"""
import os, sys, json, math, subprocess, random, requests, re, asyncio
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from dotenv import load_dotenv
import edge_tts

if sys.platform == 'win32':
    try: sys.stdout.reconfigure(encoding='utf-8')
    except Exception: pass

load_dotenv()

BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
SUBFRAMES_PER_SEC = 2

AMBER_GOLD = (245, 158, 11)
WARM_HONEY = (251, 191, 36)
CREAM = (254, 243, 199)
WHITE = (255, 255, 255)
DARK_BG = (16, 12, 10)
CARD_BG = (28, 20, 16)
CARD_BORDER = (60, 42, 32)
MUTED_TEXT = (180, 160, 145)

EMMA_VOICE = "en-US-AvaNeural"
ANDREW_VOICE = "en-US-AndrewNeural"
VOICE_RATE = "-15%"

TOPICS = [
    {
        "topic": "Ordering Food & Drinks at a Café Like a Native",
        "scenario": "ORDERING AT A COFFEE SHOP ☕",
        "keyword": "COFFEE",
        "sub": "NATURAL RESTAURANT & CAFÉ ENGLISH"
    },
    {
        "topic": "Checking into a Hotel & Asking for Amenities",
        "scenario": "HOTEL CHECK-IN 🏨",
        "keyword": "HOTEL",
        "sub": "ESSENTIAL TRAVEL & VACATION ENGLISH"
    },
    {
        "topic": "Navigating Airport Customs and Flight Boarding",
        "scenario": "AIRPORT & FLIGHTS ✈️",
        "keyword": "AIRPORT",
        "sub": "SMOOTH INTERNATIONAL TRAVEL"
    },
    {
        "topic": "Small Talk with Neighbors and Making Friends",
        "scenario": "EVERYDAY SMALL TALK 👋",
        "keyword": "CONVERSATION",
        "sub": "CONFIDENT SOCIAL INTERACTIONS"
    }
]

def load_font(size, bold=True):
    fonts_to_try = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/trebucbd.ttf" if bold else "C:/Windows/Fonts/trebuc.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in fonts_to_try:
        if Path(p).exists():
            try: return ImageFont.truetype(p, size)
            except: continue
    return ImageFont.load_default()

def clean_text(text):
    text = re.sub(r'\b(mm+|um+|uh+|ah+)\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def generate_script_ai(topic_item, target_turns=6):
    prompt = f"""Write {target_turns} turns of a slow, clear English podcast between Emma and Andrew.
Topic: {topic_item['topic']}
Scenario: {topic_item['scenario']}

RULES:
- Dialogue alternating between Host1 (Emma) and Host2 (Andrew)
- Each turn MUST be 2-3 short, clear sentences (18-28 words)
- The hosts demonstrate polite, practical native phrases and roleplay real dialogue lines
- Wrap exactly 1 key phrase or word per turn in **asterisks**
- Return as clean JSON array only:
[{{"speaker":"Host1","text":"..."}},{{"speaker":"Host2","text":"..."}}]"""

    key = os.getenv("POLLINATIONS_API_KEY")
    if key:
        try:
            resp = requests.post("https://gen.pollinations.ai/v1/chat/completions", json={
                "model": "gemini-fast",
                "messages": [
                    {"role": "system", "content": "You write practical, natural English learning podcast dialogue for real-life situations. Wrap 1 key word per turn in **asterisks**."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.8
            }, headers={"Authorization": f"Bearer {key}"}, timeout=60)
            if resp.status_code == 200:
                raw = resp.json()["choices"][0]["message"]["content"].strip()
                if "```json" in raw: raw = raw.split("```json")[1].split("```")[0].strip()
                elif "```" in raw: raw = raw.split("```")[1].split("```")[0].strip()
                script = json.loads(raw)
                if isinstance(script, list) and len(script) > 0:
                    for i, turn in enumerate(script):
                        turn["speaker"] = "Host1" if i % 2 == 0 else "Host2"
                        turn["text"] = clean_text(turn["text"])
                        if "**" not in turn["text"]:
                            words = turn["text"].split()
                            if len(words) > 2:
                                idx = len(words) // 2
                                words[idx] = f"**{words[idx]}**"
                                turn["text"] = " ".join(words)
                    return script[:target_turns]
        except Exception as e:
            print(f"[script] AI note: {e}, using curated fallback.")

    return [
        {"speaker": "Host1", "text": f"Welcome back everyone! Today we are mastering {topic_item['topic']}, so you can order with **confidence**."},
        {"speaker": "Host2", "text": f"Instead of saying 'I want coffee', native speakers always say: Could I get a medium **iced latte**, please?"},
        {"speaker": "Host1", "text": f"That sounds so much more polite and natural. Then if they ask about milk, you can simply say with **oat milk**."},
        {"speaker": "Host2", "text": f"Exactly Emma! Practicing these realistic roleplays makes everyday speaking completely **effortless**!"}
    ][:target_turns]

async def generate_audio_files(turns, run_dir):
    audio_dir = run_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    audio_list = []
    for i, turn in enumerate(turns):
        mp3_p = audio_dir / f"turn_{i:03d}.mp3"
        spoken = re.sub(r'\*\*(.*?)\*\*', r'\1', turn["text"])
        voice = EMMA_VOICE if turn["speaker"] == "Host1" else ANDREW_VOICE
        comm = edge_tts.Communicate(spoken, voice, rate=VOICE_RATE)
        await comm.save(str(mp3_p))

        try:
            r = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", str(mp3_p)],
                capture_output=True, text=True, check=True
            )
            duration = float(r.stdout.strip())
        except:
            duration = 5.0
        audio_list.append({"path": str(mp3_p), "duration": duration, "speaker": turn["speaker"]})
    return audio_list

def draw_vintage_mic(draw, center_x, center_y, is_active, label):
    # Base stand
    stand_color = (80, 60, 50) if not is_active else (180, 120, 40)
    draw.ellipse([(center_x - 70, center_y + 110), (center_x + 70, center_y + 130)], fill=(30, 22, 18), outline=stand_color, width=3)
    # Stem
    draw.rectangle([(center_x - 8, center_y - 20), (center_x + 8, center_y + 115)], fill=(60, 48, 40))
    # U-mount
    draw.arc([(center_x - 55, center_y - 80), (center_x + 55, center_y + 10)], start=0, end=180, fill=stand_color, width=6)

    # Active glow halo behind capsule
    if is_active:
        halo_r = 75
        draw.ellipse([(center_x - halo_r, center_y - 120), (center_x + halo_r, center_y + 10)], outline=WARM_HONEY, width=4)

    # Microphone capsule (vintage pill shape)
    mic_bg = (45, 34, 28) if not is_active else (80, 52, 26)
    draw.rounded_rectangle([(center_x - 38, center_y - 105), (center_x + 38, center_y - 5)], radius=24, fill=mic_bg, outline=WARM_HONEY if is_active else (100, 80, 65), width=3)

    # Grille horizontal ribs
    for y_rib in range(center_y - 95, center_y - 15, 12):
        draw.line([(center_x - 32, y_rib), (center_x + 32, y_rib)], fill=(130, 100, 75) if not is_active else (250, 200, 100), width=2)

    # Center band
    draw.rectangle([(center_x - 38, center_y - 55), (center_x + 38, center_y - 45)], fill=AMBER_GOLD if is_active else (90, 70, 55))

    # Host Name Plate
    f_lbl = load_font(22, bold=True)
    box_w = 160
    draw.rounded_rectangle([(center_x - box_w//2, center_y + 140), (center_x + box_w//2, center_y + 175)], radius=8, fill=(35, 25, 20), outline=AMBER_GOLD if is_active else CARD_BORDER, width=2)
    tag = f"🎙️ {label}" + (" (LIVE)" if is_active else "")
    c_text = WARM_HONEY if is_active else MUTED_TEXT
    draw.text((center_x, center_y + 157), tag, fill=c_text, font=f_lbl, anchor="mm")

def draw_cozy_equalizer(draw, center_x, center_y, width, height, sub_idx, is_speaking):
    num_bars = 24
    bar_w = 8
    gap = (width - (num_bars * bar_w)) // (num_bars - 1)

    # Console background
    draw.rounded_rectangle([(center_x - width//2 - 20, center_y - height//2 - 15),
                            (center_x + width//2 + 20, center_y + height//2 + 15)],
                           radius=16, fill=(24, 18, 14), outline=(65, 45, 32), width=2)

    f_meter = load_font(18, bold=True)
    draw.text((center_x, center_y - height//2 - 2), "• ACOUSTIC STEREO SOUND METER •", fill=MUTED_TEXT, font=f_meter, anchor="mm")

    start_x = center_x - width//2
    for b in range(num_bars):
        if is_speaking:
            phase = sub_idx * 0.85 + b * 0.42
            wave = abs(math.sin(phase)) * 0.75 + abs(math.cos(phase * 1.3)) * 0.25
            bar_h = int(12 + wave * (height - 30))
        else:
            bar_h = 8

        bx = start_x + b * (bar_w + gap)
        by = center_y + height//2 - 10 - bar_h

        # Warm amber to gold gradient
        fill_c = AMBER_GOLD if b % 2 == 0 else WARM_HONEY
        draw.rounded_rectangle([(bx, by), (bx + bar_w, center_y + height//2 - 10)], radius=3, fill=fill_c)

def render_podcast_subframe(topic_item, turn, turn_idx, sub_idx, total_subframes, elapsed, total_dur, out_path):
    canvas = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), DARK_BG)
    draw = ImageDraw.Draw(canvas)

    # Studio warm wooden gradient background
    for y in range(VIDEO_HEIGHT):
        ratio = y / VIDEO_HEIGHT
        r = int(22 + ratio * 15)
        g = int(14 + ratio * 10)
        b = int(10 + ratio * 6)
        draw.line([(0, y), (VIDEO_WIDTH, y)], fill=(r, g, b, 255))

    # Warm cafe string light bokeh circles in background
    bokeh_coords = [(200, 180, 60), (450, 120, 80), (800, 160, 50), (1200, 130, 70), (1600, 170, 90)]
    for bx, by, br in bokeh_coords:
        draw.ellipse([(bx - br, by - br), (bx + br, by + br)], fill=(45, 30, 18, 120))

    # Top Header Deck
    # Left: Channel badge
    draw.rounded_rectangle([(60, 36), (560, 106)], radius=16, fill=CARD_BG, outline=AMBER_GOLD, width=2)
    f_brand = load_font(28, bold=True)
    draw.text((310, 71), "☕ REAL SITUATIONS STUDIO", fill=CREAM, font=f_brand, anchor="mm")

    # Center: Scenario badge
    draw.rounded_rectangle([(590, 36), (1450, 106)], radius=16, fill=(35, 24, 18), outline=WARM_HONEY, width=2)
    f_scen = load_font(26, bold=True)
    draw.text((1020, 71), f"📍 SCENARIO: {topic_item['scenario']}", fill=WARM_HONEY, font=f_scen, anchor="mm")

    # Right: Live On Air Pill
    draw.rounded_rectangle([(1480, 36), (1860, 106)], radius=16, fill=(50, 18, 14), outline=(220, 38, 38), width=3)
    f_air = load_font(26, bold=True)
    dot_color = (255, 60, 60) if (sub_idx % 2 == 0) else (150, 20, 20)
    draw.ellipse([(1515, 61), (1535, 81)], fill=dot_color)
    draw.text((1685, 71), "LIVE BROADCAST", fill=WHITE, font=f_air, anchor="mm")

    # Visual Studio Centerpiece: Dual Mics & Center Equalizer
    is_emma = (turn["speaker"] == "Host1")
    is_andrew = not is_emma

    # Left Mic: Emma
    draw_vintage_mic(draw, center_x=340, center_y=380, is_active=is_emma, label="EMMA")

    # Center Equalizer Deck
    draw_cozy_equalizer(draw, center_x=960, center_y=370, width=540, height=130, sub_idx=sub_idx, is_speaking=True)

    # Center Topic Card
    draw.rounded_rectangle([(690, 470), (1230, 550)], radius=14, fill=CARD_BG, outline=CARD_BORDER, width=2)
    f_top = load_font(24, bold=True)
    draw.text((960, 510), f"Topic: {topic_item['topic']}", fill=CREAM, font=f_top, anchor="mm")

    # Right Mic: Andrew
    draw_vintage_mic(draw, center_x=1580, center_y=380, is_active=is_andrew, label="ANDREW")

    # LOWER THIRD: SLEEK SINGLE-LINE SUBTITLE DISPLAY WITH WORD-BY-WORD HIGHLIGHTING
    # Clean dialogue container
    draw.rounded_rectangle([(100, 680), (1820, 930)], radius=24, fill=(24, 18, 14, 240), outline=AMBER_GOLD, width=3)

    # Speaker Tag Bar
    active_name = "EMMA (Host)" if is_emma else "ANDREW (Host)"
    draw.rounded_rectangle([(140, 650), (450, 705)], radius=12, fill=AMBER_GOLD)
    f_spk = load_font(26, bold=True)
    draw.text((295, 677), f"🎙️ {active_name}", fill=(20, 14, 10), font=f_spk, anchor="mm")

    # Sentence & Spoken Word Highlighting
    raw_text = turn["text"]
    words_clean = [re.sub(r'[\*\*\.]', '', w).strip() for w in raw_text.split() if w.strip()]
    if not words_clean:
        words_clean = ["Listen", "carefully"]

    active_word_idx = min(len(words_clean) - 1, int((sub_idx / max(1, total_subframes)) * len(words_clean)))

    # Display text on clean lines inside the lower third
    f_sub = load_font(42, bold=True)
    rendered_words = raw_text.split()

    # Layout words horizontally
    line_words = []
    lines = []
    max_w = 1600
    curr_w = 0

    for w_i, w in enumerate(rendered_words):
        clean_w = re.sub(r'\*\*(.*?)\*\*', r'\1', w)
        wb = draw.textbbox((0, 0), clean_w + " ", font=f_sub)
        w_len = wb[2] - wb[0]
        if curr_w + w_len > max_w and line_words:
            lines.append(line_words)
            line_words = [(w_i, w, clean_w, w_len)]
            curr_w = w_len
        else:
            line_words.append((w_i, w, clean_w, w_len))
            curr_w += w_len
    if line_words:
        lines.append(line_words)

    # Render lines centered
    y_start = 740 if len(lines) == 1 else 725
    line_h = 55
    for l_idx, line in enumerate(lines[:2]):
        total_line_w = sum(item[3] for item in line)
        start_x = 960 - total_line_w // 2
        curr_x = start_x
        y_pos = y_start + l_idx * line_h

        for (w_i, raw_w, clean_w, w_len) in line:
            is_active_word = (w_i == active_word_idx)
            is_key_word = ("**" in raw_w)

            if is_active_word:
                # Active karaoke glow pill
                draw.rounded_rectangle([(curr_x - 4, y_pos - 6), (curr_x + w_len - 2, y_pos + 46)], radius=8, fill=AMBER_GOLD)
                draw.text((curr_x, y_pos), clean_w, fill=(18, 12, 8), font=f_sub)
            elif is_key_word:
                draw.text((curr_x, y_pos), clean_w, fill=WARM_HONEY, font=f_sub)
            else:
                draw.text((curr_x, y_pos), clean_w, fill=WHITE, font=f_sub)
            curr_x += w_len

    # Tip Ribbon inside the Lower Third
    f_tip = load_font(22, bold=False)
    draw.text((960, 885), "💡 Tip: Shadow and repeat each phrase out loud for natural pronunciation flow.", fill=MUTED_TEXT, font=f_tip, anchor="mm")

    # Bottom Progress Deck
    draw.line([(0, 1020), (VIDEO_WIDTH, 1020)], fill=(45, 32, 24), width=3)
    ratio = min(1.0, elapsed / max(1.0, total_dur))
    draw.line([(0, 1020), (int(VIDEO_WIDTH * ratio), 1020)], fill=AMBER_GOLD, width=6)

    f_bot = load_font(24, bold=False)
    draw.text((70, 1050), "Real Situations • Practical English Dialogue • Daily Native Practice", fill=CREAM, font=f_bot, anchor="lm")
    time_str = f"{int(elapsed // 60):02d}:{int(elapsed % 60):02d} / {int(total_dur // 60):02d}:{int(total_dur % 60):02d}"
    draw.text((1850, 1050), time_str, fill=WARM_HONEY, font=f_bot, anchor="rm")

    canvas.convert("RGB").save(out_path, quality=90)

def assemble_video(topic_item, turns, audio_list, run_dir):
    frames_dir = run_dir / "frames"
    clips_dir = run_dir / "clips"
    frames_dir.mkdir(parents=True, exist_ok=True)
    clips_dir.mkdir(parents=True, exist_ok=True)

    total_dur = sum(a["duration"] for a in audio_list)
    elapsed = 0.0
    clips = []

    for i, (turn, audio) in enumerate(zip(turns, audio_list)):
        dur = audio["duration"]
        subframes_count = max(8, int(dur * SUBFRAMES_PER_SEC))

        turn_frames_dir = frames_dir / f"turn_{i:03d}"
        turn_frames_dir.mkdir(parents=True, exist_ok=True)

        for s_idx in range(subframes_count):
            frame_p = turn_frames_dir / f"frame_{s_idx:04d}.png"
            sub_elapsed = elapsed + (s_idx / subframes_count) * dur
            render_podcast_subframe(
                topic_item, turn, i, s_idx, subframes_count,
                sub_elapsed, total_dur, str(frame_p)
            )

        clip_p = clips_dir / f"clip_{i:03d}.mp4"
        input_pattern = str(turn_frames_dir / "frame_%04d.png")

        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(SUBFRAMES_PER_SEC),
            "-i", input_pattern,
            "-i", audio["path"],
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "-preset", "veryfast",
            str(clip_p)
        ]
        subprocess.run(cmd, check=True, capture_output=True)

        clips.append(clip_p)
        elapsed += dur

    concat_txt = run_dir / "concat.txt"
    with open(concat_txt, "w") as f:
        for c in clips:
            f.write(f"file '{c.resolve().as_posix()}'\n")

    final_video = run_dir / "real_situations_podcast_final.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_txt), "-c", "copy", str(final_video)], check=True, capture_output=True)
    return final_video, total_dur

async def run_situation_generation(topic_idx=0, turns_count=4):
    topic_item = TOPICS[topic_idx % len(TOPICS)]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = OUTPUT_DIR / f"run_{ts}"
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"[Situations Podcast] Generating 16:9 Coffeehouse Studio: '{topic_item['topic']}' ({turns_count} turns)...")
    turns = generate_script_ai(topic_item, target_turns=turns_count)
    audio_list = await generate_audio_files(turns, run_dir)
    video_p, dur = assemble_video(topic_item, turns, audio_list, run_dir)

    meta = {
        "title": f"Real English Conversations: {topic_item['topic']} 🎙️ Slow English Podcast",
        "description": f"Learn how to speak naturally in real-life situations! Listen to our slow English dialogue lesson for '{topic_item['scenario']}'. Follow for daily lessons! ☕✈️",
        "scenario": topic_item["scenario"],
        "duration_seconds": dur
    }
    with open(run_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"[Situations Podcast] Video ready: {video_p}")
    return video_p, meta

if __name__ == "__main__":
    asyncio.run(run_situation_generation(topic_idx=0, turns_count=2))
