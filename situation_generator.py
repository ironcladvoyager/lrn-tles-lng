"""
KIDS ENGLISH CLUB - 16:9 FULL HD (1920x1080)
Format: 1920x1080 Landscape Studio Broadcast
Features:
- Photorealistic kids podcast studio setting: Lily on the left, Leo on the right
- Microsoft child neural voices (Ana child voice & Leo cheerful young voice)
- Dynamic host badges with live speaker indicator (Lily vs Leo)
- Frame-synchronized subtitles with active word karaoke highlighting
- Physically reactive 16-band audio equalizer responding directly to voice acoustics
- Permanent bottom branding ribbon with smooth progress line
"""
import os, sys, json, math, subprocess, random, requests, re, asyncio
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from dotenv import load_dotenv
import edge_tts
import numpy as np
from pydub import AudioSegment

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
FPS = 30

# Color Palette
GOLD_ACCENT = (255, 215, 0)         # Radiant Gold (#FFD700)
WHITE = (255, 255, 255)
MUTED_WHITE = (210, 218, 230)
DARK_BAR_ACTIVE = (16, 20, 32, 235)
DARK_BAR_INACTIVE = (12, 16, 24, 170)
BORDER_INACTIVE = (60, 75, 95, 160)
MUTED_TEXT = (160, 175, 195)
LIVE_GREEN = (34, 197, 94)
MUTED_GOLD = (235, 225, 200)

CHANNEL_NAME = "KIDS ENGLISH CLUB"
TAGLINE = "Fun Everyday English  •  Learn & Grow  •  Kids English Club"

# Kids Voices (Both authentic child voice models)
LILY_VOICE = "en-US-AnaNeural"      # Authentic Child Voice Model
LILY_PITCH = "+8Hz"                 # Cheerful girl child pitch (~305 Hz)
LILY_RATE = "-3%"

LEO_VOICE = "en-US-AnaNeural"       # Authentic Child Voice Model
LEO_PITCH = "-20Hz"                 # Young boy child resonance pitch (~248 Hz)
LEO_RATE = "-4%"

TOPICS = [
    {
        "topic": "Super Animal Powers: How Dolphins & Bats Communicate",
        "keyword": "ANIMALS",
        "turns": [
            {"speaker": "Host1", "text": "Hi everyone! Welcome to Kids English Club! Today we are learning about animals with amazing **superpowers**!"},
            {"speaker": "Host2", "text": "Did you know that dolphins talk to each other underwater using special clicking **sounds**?"},
            {"speaker": "Host1", "text": "That is so cool! And bats use echolocation to fly in the dark without bumping into **trees**!"},
            {"speaker": "Host2", "text": "Tell us in the comments what your favorite animal is, and keep practicing your **English**!"}
        ]
    },
    {
        "topic": "Exploring Outer Space: Rockets, Stars, and Planets",
        "keyword": "SPACE",
        "turns": [
            {"speaker": "Host1", "text": "Welcome back friends! Today we are zooming into space to explore our giant solar **system**!"},
            {"speaker": "Host2", "text": "Astronauts float weightlessly inside spaceships because there is very little **gravity**!"},
            {"speaker": "Host1", "text": "And planet Saturn has huge sparkling rings made of ice and giant chunks of **rock**!"},
            {"speaker": "Host2", "text": "Keep your curiosity high and never stop asking questions about our **universe**!"}
        ]
    },
    {
        "topic": "Healthy Habits: Super Foods for Super Brains",
        "keyword": "HEALTH",
        "turns": [
            {"speaker": "Host1", "text": "Hey everyone! Today we are talking about delicious foods that give our bodies extra **energy**!"},
            {"speaker": "Host2", "text": "Eating fresh fruits and crunchy vegetables helps you grow strong and stay **healthy**!"},
            {"speaker": "Host1", "text": "Drinking plenty of water also keeps your brain sharp so you can learn English **faster**!"},
            {"speaker": "Host2", "text": "Remember to eat your greens today and have an awesome day of **learning**!"}
        ]
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

def generate_script_ai(topic_item, target_turns=4):
    prompt = f"""Write {target_turns} turns of a cheerful, educational English learning dialogue for kids between Lily (young girl) and Leo (young boy) discussing: {topic_item['topic']}.

RULES:
- Dialogue alternating between Host1 (Lily) and Host2 (Leo)
- Each turn MUST be 2 short, clear sentences (16-24 words)
- Cheerful, friendly, positive kids tone
- Wrap exactly 1 key learning word per turn in **asterisks**
- Return as clean JSON array only:
[{{"speaker":"Host1","text":"..."}},{{"speaker":"Host2","text":"..."}}]"""

    key = os.getenv("POLLINATIONS_API_KEY")
    if key:
        try:
            resp = requests.post("https://gen.pollinations.ai/v1/chat/completions", json={
                "model": "gemini-fast",
                "messages": [
                    {"role": "system", "content": "You write fun, engaging English educational dialogues for kids. Wrap 1 key word per turn in **asterisks**."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.8
            }, headers={"Authorization": f"Bearer {key}"}, timeout=20)
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

    return topic_item.get("turns", [
        {"speaker": "Host1", "text": "Hi everyone! Welcome to Kids English Club! Today we are learning about animals with amazing **superpowers**!"},
        {"speaker": "Host2", "text": "Did you know that dolphins talk to each other underwater using special clicking **sounds**?"},
        {"speaker": "Host1", "text": "That is so cool! And bats use echolocation to fly in the dark without bumping into **trees**!"},
        {"speaker": "Host2", "text": "Tell us in the comments what your favorite animal is, and keep practicing your **English**!"}
    ])[:target_turns]

async def generate_audio_files(turns, run_dir):
    audio_dir = run_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    audio_list = []
    
    for i, turn in enumerate(turns):
        mp3_p = audio_dir / f"turn_{i:03d}.mp3"
        spoken = re.sub(r'\*\*(.*?)\*\*', r'\1', turn["text"])
        
        if turn["speaker"] == "Host1":
            comm = edge_tts.Communicate(spoken, LILY_VOICE, rate=LILY_RATE, pitch=LILY_PITCH)
        else:
            comm = edge_tts.Communicate(spoken, LEO_VOICE, rate=LEO_RATE, pitch=LEO_PITCH)
            
        sentences = []
        audio_bytes = bytearray()
        
        async for chunk in comm.stream():
            if chunk.get("type") == "SentenceBoundary":
                start_s = chunk["offset"] / 10_000_000.0
                dur_s = chunk["duration"] / 10_000_000.0
                sentences.append({
                    "text": chunk["text"],
                    "start": start_s,
                    "duration": dur_s,
                    "end": start_s + dur_s
                })
            elif chunk.get("type") == "audio":
                audio_bytes.extend(chunk["data"])
                
        with open(mp3_p, "wb") as f:
            f.write(audio_bytes)

        try:
            r = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", str(mp3_p)],
                capture_output=True, text=True, check=True
            )
            duration = float(r.stdout.strip())
        except:
            duration = sentences[-1]["end"] if sentences else 5.0

        # Subdivide long sentences into short bite-sized clauses (max 8 words) for clean subtitles
        timed_phrases = []
        for s in sentences:
            s_text = s["text"]
            s_start = s["start"]
            s_dur = s["duration"]
            words = s_text.split()
            
            if len(words) <= 8:
                timed_phrases.append({
                    "text": s_text,
                    "start": s_start,
                    "end": s_start + s_dur,
                    "duration": s_dur
                })
            else:
                parts = [p.strip() for p in re.split(r'(?<=[,;:])\s+', s_text) if p.strip()]
                if len(parts) > 1:
                    total_w = sum(len(p.split()) for p in parts)
                    cur_t = s_start
                    for p in parts:
                        p_w = len(p.split())
                        p_dur = s_dur * (p_w / max(1, total_w))
                        timed_phrases.append({
                            "text": p,
                            "start": cur_t,
                            "end": cur_t + p_dur,
                            "duration": p_dur
                        })
                        cur_t += p_dur
                else:
                    mid = len(words) // 2
                    p1 = " ".join(words[:mid])
                    p2 = " ".join(words[mid:])
                    dur1 = s_dur * (len(p1.split()) / len(words))
                    dur2 = s_dur - dur1
                    timed_phrases.append({"text": p1, "start": s_start, "end": s_start + dur1, "duration": dur1})
                    timed_phrases.append({"text": p2, "start": s_start + dur1, "end": s_start + s_dur, "duration": dur2})

        # Load raw audio samples for 100% physical FFT frequency equalizer calculation
        audio_seg = AudioSegment.from_file(str(mp3_p))
        sample_rate = audio_seg.frame_rate
        raw_samples = np.array(audio_seg.get_array_of_samples(), dtype=float)
        if audio_seg.channels > 1:
            raw_samples = raw_samples.reshape((-1, audio_seg.channels)).mean(axis=1)

        audio_list.append({
            "path": str(mp3_p),
            "duration": duration,
            "speaker": turn["speaker"],
            "turn_text": turn["text"],
            "timed_phrases": timed_phrases,
            "raw_samples": raw_samples,
            "sample_rate": sample_rate
        })
        
    return audio_list

def load_base_studio_canvas():
    studio_path = ASSETS_DIR / "kids_studio.png"
    if studio_path.exists():
        img = Image.open(studio_path).convert("RGBA")
        return img.resize((VIDEO_WIDTH, VIDEO_HEIGHT), Image.Resampling.LANCZOS)
    else:
        canvas = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), (16, 20, 32, 255))
        return canvas

def draw_vector_mic(draw, center_x, center_y, color=GOLD_ACCENT):
    draw.rounded_rectangle([(center_x - 6, center_y - 12), (center_x + 6, center_y + 4)], radius=4, fill=color)
    draw.arc([(center_x - 10, center_y - 4), (center_x + 10, center_y + 10)], start=0, end=180, fill=color, width=3)
    draw.line([(center_x, center_y + 10), (center_x, center_y + 16)], fill=color, width=3)
    draw.line([(center_x - 6, center_y + 16), (center_x + 6, center_y + 16)], fill=color, width=3)

def compute_physical_equalizer_bars(raw_samples, sample_rate, t_sec, num_bars=16):
    """
    Computes 16-band physical frequency spectrum directly from voice audio samples at timestamp t_sec.
    When speaking: bars dance to actual vocal frequencies.
    When pausing/silent: smoothly drops to 4px resting floor.
    """
    win_size = int(0.06 * sample_rate) # 60ms analysis window
    center_idx = int(t_sec * sample_rate)
    start_idx = max(0, center_idx - win_size // 2)
    end_idx = min(len(raw_samples), center_idx + win_size // 2)
    chunk = raw_samples[start_idx:end_idx]

    if len(chunk) < 100:
        return [4] * num_bars

    rms = np.sqrt(np.mean(chunk**2))
    if rms < 350.0:  # Silence / breath between words
        return [4] * num_bars

    fft_vals = np.abs(np.fft.rfft(chunk))
    fft_freqs = np.fft.rfftfreq(len(chunk), 1.0 / sample_rate)

    bar_heights = []
    for b in range(num_bars):
        f_min = 120 * (1.28 ** b)
        f_max = 120 * (1.28 ** (b + 1))
        mask = (fft_freqs >= f_min) & (fft_freqs < f_max)
        if np.any(mask):
            val = np.mean(fft_vals[mask])
            h = int(min(1.0, val / 300000.0) * 44)
        else:
            h = 4
        bar_heights.append(max(4, min(48, h)))

    return bar_heights

def render_podcast_frame(base_canvas, speaker, phrase_text, active_w_idx, eq_bars, frame_idx, elapsed, total_dur, out_path):
    canvas = base_canvas.copy()
    draw = ImageDraw.Draw(canvas)

    f_pills = load_font(28, bold=True)
    pill_h = 66
    pill_t = 40
    pill_b = pill_t + pill_h

    # 1. Left Host Badge: LILY (Active when Host1 speaks)
    is_lily_active = (speaker == "Host1")
    spk_lily = "KID HOST: LILY"
    tb_lily = draw.textbbox((0, 0), spk_lily, font=f_pills)
    tw_lily = tb_lily[2] - tb_lily[0]
    lily_w = tw_lily + 130
    lily_l = 60
    lily_r = lily_l + lily_w

    bg_lily = DARK_BAR_ACTIVE if is_lily_active else DARK_BAR_INACTIVE
    outline_lily = GOLD_ACCENT if is_lily_active else BORDER_INACTIVE
    text_col_lily = GOLD_ACCENT if is_lily_active else MUTED_TEXT
    mic_col_lily = GOLD_ACCENT if is_lily_active else (120, 135, 155)

    draw.rounded_rectangle([(lily_l, pill_t), (lily_r, pill_b)], radius=20, fill=bg_lily, outline=outline_lily, width=3 if is_lily_active else 2)
    mic_x_s = lily_l + 35
    mic_y_s = pill_t + pill_h // 2
    draw_vector_mic(draw, mic_x_s, mic_y_s, color=mic_col_lily)

    dot_x_s = mic_x_s + 22
    dot_col_s = LIVE_GREEN if is_lily_active else (80, 95, 115)
    draw.ellipse([(dot_x_s - 4, mic_y_s - 4), (dot_x_s + 4, mic_y_s + 4)], fill=dot_col_s)
    draw.text((dot_x_s + 18, mic_y_s), spk_lily, fill=text_col_lily, font=f_pills, anchor="lm")

    # 2. Right Host Badge: LEO (Active when Host2 speaks)
    is_leo_active = (speaker == "Host2")
    spk_leo = "KID HOST: LEO"
    tb_leo = draw.textbbox((0, 0), spk_leo, font=f_pills)
    tw_leo = tb_leo[2] - tb_leo[0]
    leo_w = tw_leo + 130
    leo_r = 1860
    leo_l = leo_r - leo_w

    bg_leo = DARK_BAR_ACTIVE if is_leo_active else DARK_BAR_INACTIVE
    outline_leo = GOLD_ACCENT if is_leo_active else BORDER_INACTIVE
    text_col_leo = GOLD_ACCENT if is_leo_active else MUTED_TEXT
    mic_col_leo = GOLD_ACCENT if is_leo_active else (120, 135, 155)

    draw.rounded_rectangle([(leo_l, pill_t), (leo_r, pill_b)], radius=20, fill=bg_leo, outline=outline_leo, width=3 if is_leo_active else 2)
    mic_x_l = leo_l + 35
    mic_y_l = pill_t + pill_h // 2
    draw_vector_mic(draw, mic_x_l, mic_y_l, color=mic_col_leo)

    dot_x_l = mic_x_l + 22
    dot_col_l = LIVE_GREEN if is_leo_active else (80, 95, 115)
    draw.ellipse([(dot_x_l - 4, mic_y_l - 4), (dot_x_l + 4, mic_y_l + 4)], fill=dot_col_l)
    draw.text((dot_x_l + 18, mic_y_l), spk_leo, fill=text_col_leo, font=f_pills, anchor="lm")

    # 3. Center Channel Pill: KIDS ENGLISH CLUB
    tb_c = draw.textbbox((0, 0), CHANNEL_NAME, font=f_pills)
    tw_c = tb_c[2] - tb_c[0]
    chan_w = tw_c + 150
    chan_cx = 960
    chan_l = chan_cx - chan_w // 2
    chan_r = chan_cx + chan_w // 2

    draw.rounded_rectangle([(chan_l, pill_t), (chan_r, pill_b)], radius=20, fill=(16, 20, 32, 230), outline=(255, 215, 0, 180), width=2)
    wave_x = chan_l + 28
    wave_cy = pill_t + pill_h // 2
    for b in range(6):
        bh = int(12 + 12 * abs(math.sin(frame_idx * 0.45 + b * 1.15)))
        bx = wave_x + b * 10
        draw.line([(bx, wave_cy - bh // 2), (bx, wave_cy + bh // 2)], fill=GOLD_ACCENT, width=3)
    draw.text((wave_x + 75, wave_cy), CHANNEL_NAME, fill=WHITE, font=f_pills, anchor="lm")

    # 4. Center Subtitle Phrase Rendering (Between Lily and Leo, center_x = 960, center_y = 330)
    words_raw = phrase_text.split()
    clean_words = [re.sub(r'[\*\*\.]', '', w).strip() for w in words_raw if w.strip()]
    if not clean_words: clean_words = ["Listen", "carefully"]

    f_sub = load_font(74, bold=True)
    max_sub_w = 780   # Fits neatly between both microphones
    lines = []
    cur_line = []
    cur_w = 0

    for w_i, raw_w in enumerate(words_raw):
        clean_w = re.sub(r'\*\*(.*?)\*\*', r'\1', raw_w)
        wb = draw.textbbox((0, 0), clean_w + " ", font=f_sub)
        wl = wb[2] - wb[0]
        if cur_w + wl > max_sub_w and cur_line:
            lines.append(cur_line)
            cur_line = [(w_i, clean_w, wl)]
            cur_w = wl
        else:
            cur_line.append((w_i, clean_w, wl))
            cur_w += wl
    if cur_line:
        lines.append(cur_line)

    line_h = 100
    total_h = len(lines) * line_h
    center_x = 960
    center_y = 330
    start_y = max(180, center_y - total_h // 2)

    # Soft dark radial background glow
    glow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    glow_w = max(sum(item[2] for item in l) for l in lines) + 140
    glow_h = total_h + 90
    gdraw.rounded_rectangle([
        (center_x - glow_w // 2, start_y + total_h // 2 - glow_h // 2),
        (center_x + glow_w // 2, start_y + total_h // 2 + glow_h // 2)
    ], radius=30, fill=(0, 0, 0, 160))
    glow = glow.filter(ImageFilter.GaussianBlur(25))
    canvas.paste(glow, (0, 0), glow)

    # Deep drop shadow
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    for l_i, line in enumerate(lines):
        lw = sum(item[2] for item in line)
        lx = center_x - lw // 2
        ly = start_y + l_i * line_h
        for (w_i, clean_w, wl) in line:
            sdraw.text((lx + 4, ly + 5), clean_w, fill=(0, 0, 0, 255), font=f_sub)
            lx += wl
    shadow = shadow.filter(ImageFilter.GaussianBlur(5))
    canvas.paste(shadow, (0, 0), shadow)

    # Foreground text with active spoken word highlighted in Gold (#FFD700)
    draw = ImageDraw.Draw(canvas)
    for l_i, line in enumerate(lines):
        lw = sum(item[2] for item in line)
        lx = center_x - lw // 2
        ly = start_y + l_i * line_h
        for (w_i, clean_w, wl) in line:
            is_active = (w_i == active_w_idx)
            col = GOLD_ACCENT if is_active else WHITE
            draw.text((lx, ly), clean_w, fill=col, font=f_sub)
            lx += wl

    # 5. Physically Synchronized Sound Equalizer Plate in the Center
    # Generous breathing gap below subtitle text (center_y = 585)
    eq_cx = 960
    eq_cy = 585
    eq_w = 440
    eq_h = 58
    draw.rounded_rectangle([
        (eq_cx - eq_w // 2, eq_cy - eq_h // 2),
        (eq_cx + eq_w // 2, eq_cy + eq_h // 2)
    ], radius=16, fill=(14, 18, 28, 220), outline=(255, 215, 0, 180), width=2)

    num_b = 16
    bw = 12
    gap = 12
    total_bars_w = num_b * bw + (num_b - 1) * gap
    start_bx = eq_cx - total_bars_w // 2

    for b_i in range(num_b):
        bh = eq_bars[b_i] if b_i < len(eq_bars) else 4
        bx = start_bx + b_i * (bw + gap)
        by_top = eq_cy - bh // 2
        by_bot = eq_cy + bh // 2
        draw.rounded_rectangle([(bx, by_top), (bx + bw, by_bot)], radius=6, fill=GOLD_ACCENT)

    # 6. Fixed Bottom Footer Ribbon (Permanent, NO jumping text, NO timers)
    draw.line([(0, 1025), (VIDEO_WIDTH, 1025)], fill=(45, 52, 72), width=2)
    ratio = min(1.0, elapsed / max(1.0, total_dur))
    draw.line([(0, 1025), (int(VIDEO_WIDTH * ratio), 1025)], fill=GOLD_ACCENT, width=4)

    f_foot = load_font(28, bold=False)
    draw.text((center_x, 1052), TAGLINE, fill=MUTED_GOLD, font=f_foot, anchor="mm")

    canvas.convert("RGB").save(out_path, quality=95)

def assemble_video(topic_item, turns, audio_list, run_dir):
    frames_dir = run_dir / "frames"
    clips_dir = run_dir / "clips"
    frames_dir.mkdir(parents=True, exist_ok=True)
    clips_dir.mkdir(parents=True, exist_ok=True)

    base_canvas = load_base_studio_canvas()
    total_dur = sum(a["duration"] for a in audio_list)
    elapsed = 0.0
    clips = []

    for i, audio in enumerate(audio_list):
        dur = audio["duration"]
        speaker = audio["speaker"]
        timed_phrases = audio["timed_phrases"]
        raw_samples = audio["raw_samples"]
        sample_rate = audio["sample_rate"]

        turn_frames_dir = frames_dir / f"turn_{i:03d}"
        turn_frames_dir.mkdir(parents=True, exist_ok=True)

        fps_turn = 10
        total_turn_frames = max(1, int(dur * fps_turn))

        for f_idx in range(total_turn_frames):
            frame_p = turn_frames_dir / f"frame_{f_idx:04d}.png"
            t_in_turn = (f_idx / total_turn_frames) * dur
            sub_elapsed = elapsed + t_in_turn

            # 1. Active phrase from Edge TTS timestamps
            active_phrase = timed_phrases[0] if timed_phrases else {"text": "Listen carefully", "start": 0, "end": dur}
            for p in timed_phrases:
                if p["start"] <= t_in_turn <= p["end"]:
                    active_phrase = p
                    break
                elif t_in_turn > p["end"]:
                    active_phrase = p

            # 2. Active word within active phrase
            p_text = active_phrase["text"]
            p_words = p_text.split()
            p_dur = max(0.2, active_phrase["end"] - active_phrase["start"])
            rel_t = max(0.0, min(p_dur, t_in_turn - active_phrase["start"]))
            active_w_idx = min(len(p_words) - 1, int((rel_t / p_dur) * len(p_words)))

            # 3. 16-band physical audio equalizer directly from real voice audio
            eq_bars = compute_physical_equalizer_bars(raw_samples, sample_rate, t_in_turn, num_bars=16)

            render_podcast_frame(
                base_canvas, speaker, p_text, active_w_idx,
                eq_bars, f_idx, sub_elapsed, total_dur, str(frame_p)
            )

        clip_p = clips_dir / f"clip_{i:03d}.mp4"
        input_pattern = str(turn_frames_dir / "frame_%04d.png")

        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(fps_turn),
            "-i", input_pattern,
            "-i", audio["path"],
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "-preset", "ultrafast",
            str(clip_p)
        ]
        subprocess.run(cmd, check=True, capture_output=True)

        clips.append(clip_p)
        elapsed += dur

    concat_txt = run_dir / "concat.txt"
    with open(concat_txt, "w") as f:
        for c in clips:
            f.write(f"file '{c.resolve().as_posix()}'\n")

    final_video = run_dir / "kids_english_final.mp4"
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_txt),
        "-c", "copy",
        str(final_video)
    ], check=True, capture_output=True)

    return final_video, total_dur

async def run_situation_generation(topic_idx=0, turns_count=4):
    topic_item = TOPICS[topic_idx % len(TOPICS)]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = OUTPUT_DIR / f"run_{ts}"
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"[Kids English Club] Generating 16:9 Broadcast: '{topic_item['topic']}' ({turns_count} turns)...")
    turns = generate_script_ai(topic_item, target_turns=turns_count)
    audio_list = await generate_audio_files(turns, run_dir)
    video_p, dur = assemble_video(topic_item, turns, audio_list, run_dir)

    meta = {
        "title": f"Kids English Club: {topic_item['topic']} 🌟 Lily & Leo",
        "description": f"Learn English with fun facts! Today: '{topic_item['topic']}'. Follow for daily kids English practice! 🎒✨",
        "topic": topic_item["topic"],
        "duration_seconds": dur
    }
    with open(run_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"[Kids English Club] Video ready: {video_p}")
    return video_p, meta

if __name__ == "__main__":
    asyncio.run(run_situation_generation(topic_idx=0, turns_count=4))
