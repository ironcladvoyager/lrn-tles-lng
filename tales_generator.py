"""
LEARN ENGLISH WITH TALES - 16:9 FULL HD (1920x1080) STORY PODCAST ENGINE
Generates 20-minute daily educational story podcast episodes with:
- Photorealistic fairy tale library studio setting (Lily on left, Leo on right)
- Microsoft child neural voices (authentic kid storytelling voices)
- Dynamic host badges with live speaker indicators & vector mics
- Word-level active karaoke subtitles centered between hosts
- Physically accurate 16-band audio equalizer dancing to real voice acoustics
- Real-time progress bar and show footer ribbon
- Direct FFmpeg rawvideo pipe encoding for rapid rendering
- Automatic 16:9 thumbnail and YouTube/Facebook metadata generation
"""
import os, sys, json, math, subprocess, random, requests, re, asyncio, time
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
RENDER_FPS = 10

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

CHANNEL_NAME = "LEARN ENGLISH WITH TALES"
TAGLINE = "Learn English with Tales  •  Daily 20-Min Story Podcast & English Immersion"

# Kids Voices
LILY_VOICE = "en-US-AnaNeural"      # Child Voice Model
LILY_PITCH = "+8Hz"                 # Cheerful girl child pitch
LILY_RATE = "-3%"

LEO_VOICE = "en-US-AnaNeural"       # Child Voice Model
LEO_PITCH = "-20Hz"                 # Boy child resonance pitch
LEO_RATE = "-4%"

def load_font(size, bold=True):
    fonts_to_try = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/trebucbd.ttf" if bold else "C:/Windows/Fonts/trebuc.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ]
    for p in fonts_to_try:
        if Path(p).exists():
            try: return ImageFont.truetype(p, size)
            except Exception: continue
    return ImageFont.load_default()

def clean_text(text):
    text = re.sub(r'\b(um+|uh+|ah+|er+)\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def generate_act_ai(topic_item, act_name, act_theme, turns_count=30):
    """Generates dialogue turns for a specific story act using AI."""
    key = os.getenv("POLLINATIONS_API_KEY")
    if not key:
        return None

    prompt = f"""Write {turns_count} turns of a cheerful, captivating story podcast dialogue for children and English learners between Lily (young girl) and Leo (young boy).
Show: 'Learn English with Tales'
Story Title: {topic_item['topic']}
Act / Chapter: {act_name} ({act_theme})
Story Summary: {topic_item.get('summary', '')}

RULES:
- Dialogue alternates strictly: Host1 (Lily) then Host2 (Leo)
- Each turn MUST be 1-2 natural, clear sentences (14-22 words)
- Cheerful, friendly, expressive storytelling tone
- Wrap exactly 1 key story or vocabulary word per turn in **asterisks** (e.g. **mysterious**, **journey**, **brave**)
- Return ONLY a valid JSON array:
[{{"speaker":"Host1","text":"..."}},{{"speaker":"Host2","text":"..."}}]"""

    try:
        resp = requests.post("https://gen.pollinations.ai/v1/chat/completions", json={
            "model": "gemini-fast",
            "messages": [
                {"role": "system", "content": "You are a master children's story podcast writer. Wrap 1 key word per turn in **asterisks**."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.8
        }, headers={"Authorization": f"Bearer {key}"}, timeout=25)
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
                return script[:turns_count]
    except Exception as e:
        print(f"[script] AI note: {e}")
    return None

def generate_procedural_story_turns(topic_item, target_turns=150):
    """
    Procedural narrative generator providing full ~20 minute rich story structure
    across 5 acts even when running offline or without API keys.
    """
    topic = topic_item["topic"]
    keyword = topic_item.get("keyword", "ADVENTURE")
    summary = topic_item.get("summary", "")

    acts = [
        # Act 1: Welcome & Setting the Scene (~25 turns)
        {
            "name": "Act 1: The Magic Begins",
            "turns": [
                ("Host1", f"Hello story travelers! Welcome back to Learn English with Tales! Today we step into: **{topic}**!"),
                ("Host2", "I am so excited for this adventure, Lily! Our cozy library is glowing, and our storybooks are **ready**."),
                ("Host1", "Every single tale carries a secret treasure: new words to learn, and a moral that warms your **heart**."),
                ("Host2", f"Today's central theme is all about **{keyword.lower()}**, an essential quality every true hero needs."),
                ("Host1", "Imagine a peaceful village nestled between tall emerald mountains where gentle mist floats over the **valley**."),
                ("Host2", "At the edge of this quiet valley stood a forgotten garden filled with silver moss and ancient **trees**."),
                ("Host1", "People in the town often whispered about the mysterious legend that slept beneath the twisted **roots**."),
                ("Host2", "A brave young traveler named Alex had arrived in town carrying only a backpack and a brass **compass**."),
                ("Host1", "Alex loved to explore uncharted forests and listen to the gentle songs of wild mountain **birds**."),
                ("Host2", "When the town elder warned Alex about the dense fog, Alex listened with great **respect**."),
                ("Host1", "The elder said: 'If you seek the secret, remember that patience and kindness will always be your **guide**.'"),
                ("Host2", "Alex smiled warmly and replied: 'I promise to walk gently and observe everything with a curious **mind**.'"),
                ("Host1", "With those wise words spoken, Alex took the very first step onto the mossy stone **pathway**."),
                ("Host2", "The morning air was crisp and cool, filled with the fresh aroma of pine needles and damp **earth**."),
                ("Host1", "Listen carefully to how we describe the morning scenery, because nature words are wonderful for **storytelling**."),
                ("Host2", "Alex noticed dew drops glistening like tiny diamonds on the spider webs between the **branches**."),
                ("Host1", "Suddenly, a soft flutter of wings caught Alex's attention near a patch of purple wild **flowers**."),
                ("Host2", "It was a tiny blue sparrow with bright curious eyes sitting peacefully on a low oak **bough**."),
                ("Host1", "The sparrow tilted its head as if asking Alex: 'Are you ready for the great journey **ahead**?'"),
                ("Host2", "Alex whispered softly: 'Lead the way, little friend, and show me the wonders of the **forest**.'")
            ]
        },
        # Act 2: Journey & The Hidden Obstacle (~35 turns)
        {
            "name": "Act 2: Into the Uncharted Forest",
            "turns": [
                ("Host1", "As Alex followed the fluttering sparrow, the path grew steeper and more winding among giant **boulders**."),
                ("Host2", "Notice the word winding! A winding path is not straight; it turns and curves gracefully like a **river**."),
                ("Host1", "Soon, the canopy of green leaves above became so thick that only golden beams of sunlight peeked **through**."),
                ("Host2", "Deep in the woods, Alex arrived at a wide crystal stream flowing rapidly over smooth grey **pebbles**."),
                ("Host1", "The wooden footbridge that once crossed the stream had broken down during the stormy winter **floods**."),
                ("Host2", "How could anyone cross without getting their boots completely soaked in the freezing cold **water**?"),
                ("Host1", "Alex took a deep breath and paused to think rather than panicking or giving up in **frustration**."),
                ("Host2", "Taking time to think before acting is a super power we call problem **solving**!"),
                ("Host1", "Along the riverbank, Alex noticed several sturdy stepping stones partially hidden beneath green water **cress**."),
                ("Host2", "A friendly old river turtle popped its head out of the gentle current and blinked **sleepily**."),
                ("Host1", "'Good morning, traveler,' the turtle said in a voice as slow and smooth as polished **stone**."),
                ("Host2", "'To cross safely, you must step only on the stones that remain steady and never wobble in the **flow**.'"),
                ("Host1", "Alex thanked the wise old turtle and tested each mossy rock carefully with a walking **stick**."),
                ("Host2", "One step... two steps... steady balance kept Alex completely dry and safe from the swirling **current**."),
                ("Host1", "That was magnificent! Alex reached the opposite bank and gave the friendly turtle a grateful **wave**."),
                ("Host2", "Politeness and gratitude make friends in every corner of the earth, even in an enchanted **forest**."),
                ("Host1", "Beyond the stream, the forest opened up into a breathtaking meadow blanketed in golden **sunlight**."),
                ("Host2", "In the very center of the meadow stood the magnificent whispering willow, its long branches swaying like silk **ribbons**."),
                ("Host1", "The trunk was wider than five grand oak trees combined, covered in delicate carvings of ancient **stars**."),
                ("Host2", "When the gentle breeze brushed through the leaves, the tree produced a sound like quiet **music**."),
                ("Host1", "It sounded like a hundred tiny silver bells chiming softly in harmonious **unison**."),
                ("Host2", "Alex approached slowly, marveling at how peaceful and grand the ancient giant **looked**."),
                ("Host1", "At the base of the hollow trunk sat a small wooden chest sealed with a tarnished bronze **lock**."),
                ("Host2", "Carved into the lid of the chest was a riddle written in gleaming silver **letters**."),
                ("Host1", "The riddle said: 'I have no voice, but I speak of hope; I have no feet, but I travel the entire **world**.'"),
                ("Host2", "Ooh, what an intriguing riddle! Can you guess what travels the world and speaks without a voice, **friends**?"),
                ("Host1", "Alex sat down on the mossy grass and pondered each clue with deep, focused **concentration**."),
                ("Host2", "Is it the wind? The wind has a voice when it howls through the stormy mountain **gorges**."),
                ("Host1", "Could it be a book? A book travels everywhere and speaks to generations without making a single physical **sound**!"),
                ("Host2", "Brilliant deduction, Alex! A storybook shares wisdom across oceans and centuries without speaking aloud!"),
                ("Host1", "As soon as Alex whispered the word 'book', a click echoed from the ancient bronze **lock**!"),
                ("Host2", "The chest swung open smoothly, revealing a velvet cushion and a glowing golden **artifact**.")
            ]
        },
        # Act 3: The Discovery & Climax (~35 turns)
        {
            "name": "Act 3: The Glowing Discovery",
            "turns": [
                ("Host1", "Inside the chest rested a magnificent compass made of polished brass and radiant clear **amber**."),
                ("Host2", "Instead of pointing to magnetic North, the golden needle glowed with a warm, pulsing amber **light**."),
                ("Host1", "Above the dial, an inscription read: 'This compass guides those whose hearts are pure toward places needing **help**.'"),
                ("Host2", "Alex picked up the magical device, feeling its gentle warmth radiating through winter-chilled **fingers**."),
                ("Host1", "Suddenly, the needle twitched and swung firmly toward the eastern ridge of the rocky **mountains**."),
                ("Host2", "The sparrow fluttered overhead, chirping excitedly as if urging Alex to climb the eastern **ridge**."),
                ("Host1", "Without hesitation, Alex tightened the straps of the backpack and began marching up the rocky **incline**."),
                ("Host2", "Dark grey storm clouds were beginning to gather on the distant horizon, threatening heavy **rain**."),
                ("Host1", "The wind grew stronger, rustling the treetops and scattering dry leaves across the narrow mountain **trail**."),
                ("Host2", "When challenges arise in an adventure story, that is where our characters show true **resilience**!"),
                ("Host1", "Resilience is the wonderful ability to keep moving forward even when things become difficult or **tiring**."),
                ("Host2", "Higher and higher Alex climbed, watching the friendly amber needle glow brighter with every single **step**."),
                ("Host1", "Near the summit of the ridge, Alex spotted a small cave half-hidden behind a curtain of wild **ivy**."),
                ("Host2", "From inside the shadowy cavern came a faint whimpering sound that tugged at Alex's **heart**."),
                ("Host1", "Alex gently parted the green vines and peered into the dry, sheltered interior of the **cave**."),
                ("Host2", "There, curled up next to a smooth boulder, was a young mountain fawn shivering in the chilly **draft**."),
                ("Host1", "The poor little deer had slipped on loose gravel and tangled its hind leg in tough blackberry **briars**."),
                ("Host2", "It could not free itself, and the darkening storm was approaching fast across the mountain **peaks**."),
                ("Host1", "Alex spoke in a calm, soothing whisper so the frightened fawn would understand there was no **danger**."),
                ("Host2", "'Do not worry, little one,' Alex whispered. 'I am going to help you untangle those sharp **thorns**.'"),
                ("Host1", "Carefully, using thick leather gloves, Alex untangled each thorny vine one by one without hurting the **fawn**."),
                ("Host2", "Patience and gentleness are far more powerful than rushing when dealing with delicate **situations**."),
                ("Host1", "Within minutes, the last stubborn briar snapped free, and the young deer stood up on all four **legs**!"),
                ("Host2", "It nuzzled Alex's shoulder gratefully, letting out a soft contented sigh of relief and **comfort**.")
            ]
        },
        # Act 4: The Moral Lesson & Language Breakdown (~35 turns)
        {
            "name": "Act 4: The Language & Moral Reflection",
            "turns": [
                ("Host1", "That was such a heartwarming climax to our adventure! What an inspiring display of **compassion**!"),
                ("Host2", "I love that story so much, Lily! Alex used wisdom to solve the riddle and kindness to save the **fawn**."),
                ("Host1", "Now, let us pause in our tale studio to examine the rich English words we encountered on this **journey**."),
                ("Host2", "Yes! Story listening is the most enjoyable method to expand your English vocabulary naturally and **effortlessly**."),
                ("Host1", "First, consider the adjective 'resilient'. It describes someone who does not give up when things get **tough**."),
                ("Host2", "For example: 'Alex was resilient when climbing the steep rocky trail under threatening storm **clouds**.'"),
                ("Host1", "Another fantastic phrase is 'to lend a helping hand'. It means offering assistance to someone in **need**."),
                ("Host2", "When Alex saw the deer trapped in the briars, Alex did not walk away; Alex lent a helping **hand**."),
                ("Host1", "We also heard the word 'unison'. When silver bells chime in unison, they ring together at the exact same **moment**."),
                ("Host2", "Singing or speaking in unison means being united in harmony, just like when an entire choir sings **together**."),
                ("Host1", "And remember the riddle of the ancient chest: 'Patience and kindness will always be your **guide**.'"),
                ("Host2", "True strength does not come from being the loudest or the fastest; it comes from being considerate and **caring**."),
                ("Host1", "Let us repeat that wonderful motto together: 'Kindness is a language that everyone can **understand**.'"),
                ("Host2", "Whether you are talking to a neighbor, a classmate, or helping an animal, kindness builds lasting **friendships**."),
                ("Host1", "Notice also how descriptive adjectives like 'tarnished bronze' and 'mossy stones' bring imagery into our **minds**."),
                ("Host2", "When you practice speaking English, try using colorful adjectives instead of simple, repetitive **words**."),
                ("Host1", "Instead of saying 'it was a nice tree', say 'it was a grand, majestic willow with shimmering **leaves**!'"),
                ("Host2", "That makes your English sound vivid, captivating, and deeply expressive to whoever is **listening**!"),
                ("Host1", "Let us also celebrate how Alex observed the environment with genuine curiosity rather than **haste**."),
                ("Host2", "Curiosity opens doors to discovery, while haste often makes people miss the beauty around **them**.")
            ]
        },
        # Act 5: Interactive Quiz & Outro (~25 turns)
        {
            "name": "Act 5: Listener Quiz & Cheerful Farewell",
            "turns": [
                ("Host1", "Now it is time for our favorite segment of the show: The Quick Story **Quiz**!"),
                ("Host2", "Get ready listeners! Put on your thinking caps and test your listening memory with three fun **questions**!"),
                ("Host1", "Question Number One: What animal did Alex first meet near the purple wildflowers?"),
                ("Host2", "Do you remember? Yes! It was the tiny blue sparrow with bright curious **eyes**!"),
                ("Host1", "Question Number Two: What was the answer to the ancient chest riddle?"),
                ("Host2", "That is correct: A book! Because a book travels the world and speaks without making a physical **sound**!"),
                ("Host1", "And Question Number Three: What magical power did the golden amber compass possess?"),
                ("Host2", "It pointed straight toward anyone who was in trouble and needed a kind helping **hand**!"),
                ("Host1", "You did a fantastic job listening today! Give yourselves a huge round of applause at **home**!"),
                ("Host2", "Practicing English for twenty minutes every day is the most effective way to build natural **fluency**."),
                ("Host1", "Make sure to tell us in the comments what your favorite moment of today's story was!"),
                ("Host2", "And tell us what kind of creature you would like Alex, Lily, and Leo to meet on our next **adventure**!"),
                ("Host1", "Do not forget to share this story with your family, classmates, and friends who are learning **English**."),
                ("Host2", "Keep your imagination alive, stay curious, and practice speaking a little English every single **day**!"),
                ("Host1", "From all of us here at the Learn English with Tales studio, have a wonderful and magical **day**!"),
                ("Host2", "Goodbye friends, keep reading, and see you tomorrow for another unforgettable **tale**!")
            ]
        }
    ]

    all_turns = []
    for act in acts:
        for spk, text in act["turns"]:
            all_turns.append({"speaker": spk, "text": clean_text(text)})

    # If target_turns is smaller (e.g. test mode)
    if target_turns < len(all_turns):
        return all_turns[:target_turns]

    # If target_turns is ~150-160, expand evenly with narrative dialogues
    while len(all_turns) < target_turns:
        idx = len(all_turns)
        spk = "Host1" if idx % 2 == 0 else "Host2"
        other_spk = "Leo" if spk == "Host1" else "Lily"
        extra_prompts = [
            f"And remember {other_spk}, every new English word you learn is like discovering a sparkling **gem**.",
            f"Exactly right! By listening every day, our confidence grows stronger and our vocabulary becomes **richer**.",
            f"Tell our listeners what word from today's tale was your personal favorite, {other_spk}?",
            f"I especially loved the word 'resilient' because it reminds us to remain brave during unexpected **challenges**.",
            f"And I loved the description of the whispering willow chimes chiming in perfect **harmony**.",
            f"Every single story teaches us that small acts of courage create great ripples across the entire **world**.",
            f"Keep practicing your pronunciation out loud along with us to train your voice and ear for **English**.",
            f"Remember, making mistakes is just proof that you are trying and learning something brand **new**!"
        ]
        chosen = extra_prompts[idx % len(extra_prompts)]
        all_turns.append({"speaker": spk, "text": clean_text(chosen)})

    return all_turns[:target_turns]

def generate_full_story_script(topic_item, target_turns=150):
    """
    Main script orchestrator. Tries AI generation act by act if API key is provided,
    otherwise relies on the complete procedural story engine.
    """
    if os.getenv("POLLINATIONS_API_KEY"):
        if target_turns <= 8:
            print(f"[script] 🤖 Generating AI dialogue via Pollinations for: '{topic_item['topic']}' ({target_turns} turns)...")
            chunk = generate_act_ai(topic_item, "Episode Preview", "Story Dialogue", target_turns)
            if chunk and len(chunk) >= target_turns:
                return chunk[:target_turns]
        else:
            print(f"[script] 🤖 Generating full 5-act AI story dialogue via Pollinations for: '{topic_item['topic']}'...")
            acts_plan = [
                ("Act 1", "Introduction & Setting the Tale Scene", target_turns // 5),
                ("Act 2", "The Journey Begins & The First Riddle", target_turns // 5),
                ("Act 3", "The Climax & Solving the Mystery", target_turns // 5),
                ("Act 4", "Language Breakdown & Moral Reflection", target_turns // 5),
                ("Act 5", "Interactive Quiz & Encouraging Sign-off", target_turns - 4 * (target_turns // 5)),
            ]
            ai_turns = []
            for act_name, act_theme, act_count in acts_plan:
                chunk = generate_act_ai(topic_item, act_name, act_theme, act_count)
                if chunk:
                    ai_turns.extend(chunk)
                else:
                    break
            if len(ai_turns) >= target_turns * 0.8:
                print(f"[script] ✅ AI generated {len(ai_turns)} turns successfully!")
                return ai_turns[:target_turns]
            print("[script] AI incomplete, falling back to curated storytelling engine.")

    # Curated / Procedural generation
    return generate_procedural_story_turns(topic_item, target_turns=target_turns)

async def synthesize_single_turn(i, turn, audio_dir, sem):
    """Synthesizes one dialogue turn with Edge TTS and extracts boundary timestamps with auto-retries."""
    async with sem:
        mp3_p = audio_dir / f"turn_{i:04d}.mp3"
        spoken = re.sub(r'\*\*(.*?)\*\*', r'\1', turn["text"])

        primary_voice = LILY_VOICE if turn["speaker"] == "Host1" else LEO_VOICE
        primary_pitch = LILY_PITCH if turn["speaker"] == "Host1" else LEO_PITCH
        primary_rate = LILY_RATE if turn["speaker"] == "Host1" else LEO_RATE

        # Fallback voices in case primary voice encounters 403 rate-limit
        voice_candidates = [
            (primary_voice, primary_rate, primary_pitch),
            ("en-US-JennyNeural" if turn["speaker"] == "Host1" else "en-US-GuyNeural", "-4%", "+2Hz" if turn["speaker"] == "Host1" else "-10Hz"),
            ("en-CA-ClaraNeural" if turn["speaker"] == "Host1" else "en-CA-LiamNeural", "-4%", "+2Hz" if turn["speaker"] == "Host1" else "-10Hz")
        ]

        sentences = []
        audio_bytes = bytearray()
        success = False

        for attempt, (voice_name, v_rate, v_pitch) in enumerate(voice_candidates, 1):
            try:
                comm = edge_tts.Communicate(spoken, voice_name, rate=v_rate, pitch=v_pitch)
                cur_sentences = []
                cur_bytes = bytearray()

                async for chunk in comm.stream():
                    if chunk.get("type") == "SentenceBoundary":
                        start_s = chunk["offset"] / 10_000_000.0
                        dur_s = chunk["duration"] / 10_000_000.0
                        cur_sentences.append({
                            "text": chunk["text"],
                            "start": start_s,
                            "duration": dur_s,
                            "end": start_s + dur_s
                        })
                    elif chunk.get("type") == "audio":
                        cur_bytes.extend(chunk["data"])

                if len(cur_bytes) > 500:
                    audio_bytes = cur_bytes
                    sentences = cur_sentences
                    success = True
                    break
            except Exception as e:
                print(f"[tts] Turn {i} attempt {attempt} notice: {e}. Retrying in {attempt * 1.5}s...")
                await asyncio.sleep(attempt * 1.5)

        # If Edge-TTS fails (e.g. cloud runner IP rate-limit), fall back to Google TTS (gTTS)
        if not success or len(audio_bytes) < 500:
            try:
                from gtts import gTTS
                tld = "com" if turn["speaker"] == "Host1" else "co.uk"
                tts = gTTS(text=spoken, lang="en", tld=tld)
                tts.save(str(mp3_p))
                try:
                    r = subprocess.run(
                        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                         "-of", "default=noprint_wrappers=1:nokey=1", str(mp3_p)],
                        capture_output=True, text=True, check=True
                    )
                    duration = float(r.stdout.strip())
                except Exception:
                    duration = max(3.5, len(spoken.split()) * 0.45)
                sentences = [{"text": spoken, "start": 0.0, "duration": duration, "end": duration}]
                success = True
                print(f"[tts] ✅ Turn {i} recovered via gTTS ({turn['speaker']} tld={tld}, dur={duration:.1f}s)")
            except Exception as e:
                print(f"[tts] ⚠️ Turn {i} gTTS fallback failed: {e}. Generating silent audio.")
                est_dur = max(3.5, len(spoken.split()) * 0.45)
                silent_seg = AudioSegment.silent(duration=int(est_dur * 1000), frame_rate=24000)
                silent_seg.export(str(mp3_p), format="mp3")
                duration = est_dur
                sentences = [{"text": spoken, "start": 0.0, "duration": est_dur, "end": est_dur}]
        else:
            with open(mp3_p, "wb") as f:
                f.write(audio_bytes)

            try:
                r = subprocess.run(
                    ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                     "-of", "default=noprint_wrappers=1:nokey=1", str(mp3_p)],
                    capture_output=True, text=True, check=True
                )
                duration = float(r.stdout.strip())
            except Exception:
                duration = sentences[-1]["end"] if sentences else 5.0

        # Subdivide long sentences into bite-sized phrases (max 7-8 words)
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
                mid = len(words) // 2
                p1 = " ".join(words[:mid])
                p2 = " ".join(words[mid:])
                d1 = s_dur * (len(p1.split()) / len(words))
                d2 = s_dur - d1
                timed_phrases.append({"text": p1, "start": s_start, "end": s_start + d1, "duration": d1})
                timed_phrases.append({"text": p2, "start": s_start + d1, "end": s_start + s_dur, "duration": d2})

        # Load raw audio samples for FFT equalizer
        try:
            audio_seg = AudioSegment.from_file(str(mp3_p))
            sample_rate = audio_seg.frame_rate
            raw_samples = np.array(audio_seg.get_array_of_samples(), dtype=float)
            if audio_seg.channels > 1:
                raw_samples = raw_samples.reshape((-1, audio_seg.channels)).mean(axis=1)
        except Exception:
            sample_rate = 24000
            raw_samples = np.zeros(int(duration * sample_rate))

        return {
            "index": i,
            "path": str(mp3_p),
            "duration": duration,
            "speaker": turn["speaker"],
            "turn_text": turn["text"],
            "timed_phrases": timed_phrases,
            "raw_samples": raw_samples,
            "sample_rate": sample_rate
        }

async def generate_all_audio(turns, run_dir):
    audio_dir = run_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    # Conservative concurrency of 3 to prevent Edge TTS rate-limits on cloud IPs
    sem = asyncio.Semaphore(3)

    print(f"[audio] 🎙️ Generating {len(turns)} audio turns with child neural voices...")
    tasks = []
    for i, turn in enumerate(turns):
        tasks.append(synthesize_single_turn(i, turn, audio_dir, sem))
        if i % 10 == 0:
            await asyncio.sleep(0.05)
    results = await asyncio.gather(*tasks)
    results.sort(key=lambda x: x["index"])
    return results

def load_base_studio_canvas():
    studio_path = ASSETS_DIR / "tales_studio.png"
    if not studio_path.exists():
        studio_path = ASSETS_DIR / "kids_studio.png"
    if studio_path.exists():
        img = Image.open(studio_path).convert("RGBA")
        return img.resize((VIDEO_WIDTH, VIDEO_HEIGHT), Image.Resampling.LANCZOS)
    return Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), (16, 20, 32, 255))

def draw_vector_mic(draw, center_x, center_y, color=GOLD_ACCENT):
    draw.rounded_rectangle([(center_x - 6, center_y - 12), (center_x + 6, center_y + 4)], radius=4, fill=color)
    draw.arc([(center_x - 10, center_y - 4), (center_x + 10, center_y + 10)], start=0, end=180, fill=color, width=3)
    draw.line([(center_x, center_y + 10), (center_x, center_y + 16)], fill=color, width=3)
    draw.line([(center_x - 6, center_y + 16), (center_x + 6, center_y + 16)], fill=color, width=3)

def compute_physical_equalizer_bars(raw_samples, sample_rate, t_sec, num_bars=16):
    win_size = int(0.06 * sample_rate)
    center_idx = int(t_sec * sample_rate)
    start_idx = max(0, center_idx - win_size // 2)
    end_idx = min(len(raw_samples), center_idx + win_size // 2)
    chunk = raw_samples[start_idx:end_idx]

    if len(chunk) < 100:
        return [4] * num_bars

    rms = np.sqrt(np.mean(chunk**2))
    if rms < 350.0:
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

def render_broadcast_frame(base_canvas, speaker, phrase_text, active_w_idx, eq_bars, frame_idx, elapsed, total_dur):
    canvas = base_canvas.copy()
    draw = ImageDraw.Draw(canvas)

    f_pills = load_font(26, bold=True)
    pill_h = 62
    pill_t = 36
    pill_b = pill_t + pill_h

    # 1. Left Host Badge: LILY (Active when Host1 speaks)
    is_lily_active = (speaker == "Host1")
    spk_lily = "STORY HOST: LILY"
    tb_lily = draw.textbbox((0, 0), spk_lily, font=f_pills)
    lily_w = (tb_lily[2] - tb_lily[0]) + 125
    lily_l = 50
    lily_r = lily_l + lily_w

    bg_lily = DARK_BAR_ACTIVE if is_lily_active else DARK_BAR_INACTIVE
    outline_lily = GOLD_ACCENT if is_lily_active else BORDER_INACTIVE
    text_col_lily = GOLD_ACCENT if is_lily_active else MUTED_TEXT
    mic_col_lily = GOLD_ACCENT if is_lily_active else (120, 135, 155)

    draw.rounded_rectangle([(lily_l, pill_t), (lily_r, pill_b)], radius=18, fill=bg_lily, outline=outline_lily, width=3 if is_lily_active else 2)
    mic_x_s = lily_l + 32
    mic_y_s = pill_t + pill_h // 2
    draw_vector_mic(draw, mic_x_s, mic_y_s, color=mic_col_lily)

    dot_x_s = mic_x_s + 22
    dot_col_s = LIVE_GREEN if is_lily_active else (80, 95, 115)
    draw.ellipse([(dot_x_s - 4, mic_y_s - 4), (dot_x_s + 4, mic_y_s + 4)], fill=dot_col_s)
    draw.text((dot_x_s + 16, mic_y_s), spk_lily, fill=text_col_lily, font=f_pills, anchor="lm")

    # 2. Right Host Badge: LEO (Active when Host2 speaks)
    is_leo_active = (speaker == "Host2")
    spk_leo = "STORY HOST: LEO"
    tb_leo = draw.textbbox((0, 0), spk_leo, font=f_pills)
    leo_w = (tb_leo[2] - tb_leo[0]) + 125
    leo_r = 1870
    leo_l = leo_r - leo_w

    bg_leo = DARK_BAR_ACTIVE if is_leo_active else DARK_BAR_INACTIVE
    outline_leo = GOLD_ACCENT if is_leo_active else BORDER_INACTIVE
    text_col_leo = GOLD_ACCENT if is_leo_active else MUTED_TEXT
    mic_col_leo = GOLD_ACCENT if is_leo_active else (120, 135, 155)

    draw.rounded_rectangle([(leo_l, pill_t), (leo_r, pill_b)], radius=18, fill=bg_leo, outline=outline_leo, width=3 if is_leo_active else 2)
    mic_x_l = leo_l + 32
    mic_y_l = pill_t + pill_h // 2
    draw_vector_mic(draw, mic_x_l, mic_y_l, color=mic_col_leo)

    dot_x_l = mic_x_l + 22
    dot_col_l = LIVE_GREEN if is_leo_active else (80, 95, 115)
    draw.ellipse([(dot_x_l - 4, mic_y_l - 4), (dot_x_l + 4, mic_y_l + 4)], fill=dot_col_l)
    draw.text((dot_x_l + 16, mic_y_l), spk_leo, fill=text_col_leo, font=f_pills, anchor="lm")

    # 3. Center Show Pill: LEARN ENGLISH WITH TALES
    tb_c = draw.textbbox((0, 0), CHANNEL_NAME, font=f_pills)
    chan_w = (tb_c[2] - tb_c[0]) + 140
    chan_cx = 960
    chan_l = chan_cx - chan_w // 2
    chan_r = chan_cx + chan_w // 2

    draw.rounded_rectangle([(chan_l, pill_t), (chan_r, pill_b)], radius=18, fill=(14, 18, 30, 235), outline=(255, 215, 0, 190), width=2)
    wave_x = chan_l + 25
    wave_cy = pill_t + pill_h // 2
    for b in range(6):
        bh = int(10 + 10 * abs(math.sin(frame_idx * 0.45 + b * 1.15)))
        bx = wave_x + b * 9
        draw.line([(bx, wave_cy - bh // 2), (bx, wave_cy + bh // 2)], fill=GOLD_ACCENT, width=3)
    draw.text((wave_x + 70, wave_cy), CHANNEL_NAME, fill=WHITE, font=f_pills, anchor="lm")

    # 4. Center Subtitle Phrase Rendering (Between Lily and Leo)
    words_raw = phrase_text.split()
    clean_words = [re.sub(r'[\*\*\.]', '', w).strip() for w in words_raw if w.strip()]
    if not clean_words: clean_words = ["Listen", "carefully"]

    f_sub = load_font(68, bold=True)
    max_sub_w = 750
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

    line_h = 92
    total_h = len(lines) * line_h
    center_x = 960
    center_y = 330
    start_y = max(180, center_y - total_h // 2)

    # 4. Translucent dark backdrop card for subtitles
    glow_w = max(sum(item[2] for item in l) for l in lines) + 120
    glow_h = total_h + 70
    gx1 = center_x - glow_w // 2
    gy1 = start_y + total_h // 2 - glow_h // 2
    gx2 = center_x + glow_w // 2
    gy2 = start_y + total_h // 2 + glow_h // 2

    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle([(gx1, gy1), (gx2, gy2)], radius=24, fill=(10, 14, 24, 215), outline=(255, 215, 0, 140), width=2)

    # Drop shadow text
    for l_i, line in enumerate(lines):
        lw = sum(item[2] for item in line)
        lx = center_x - lw // 2
        ly = start_y + l_i * line_h
        for (w_i, clean_w, wl) in line:
            draw.text((lx + 3, ly + 4), clean_w, fill=(0, 0, 0, 240), font=f_sub)
            lx += wl

    # Foreground text with active spoken word highlighted in Gold
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
    eq_cx = 960
    eq_cy = 575
    eq_w = 420
    eq_h = 56
    draw.rounded_rectangle([
        (eq_cx - eq_w // 2, eq_cy - eq_h // 2),
        (eq_cx + eq_w // 2, eq_cy + eq_h // 2)
    ], radius=15, fill=(14, 18, 28, 220), outline=(255, 215, 0, 180), width=2)

    num_b = 16
    bw = 11
    gap = 12
    total_bars_w = num_b * bw + (num_b - 1) * gap
    start_bx = eq_cx - total_bars_w // 2

    for b_i in range(num_b):
        bh = eq_bars[b_i] if b_i < len(eq_bars) else 4
        bx = start_bx + b_i * (bw + gap)
        by_top = eq_cy - bh // 2
        by_bot = eq_cy + bh // 2
        draw.rounded_rectangle([(bx, by_top), (bx + bw, by_bot)], radius=5, fill=GOLD_ACCENT)

    # 6. Fixed Bottom Footer Ribbon & Progress Line
    draw.line([(0, 1025), (VIDEO_WIDTH, 1025)], fill=(45, 52, 72), width=2)
    ratio = min(1.0, elapsed / max(1.0, total_dur))
    draw.line([(0, 1025), (int(VIDEO_WIDTH * ratio), 1025)], fill=GOLD_ACCENT, width=4)

    f_foot = load_font(26, bold=False)
    draw.text((center_x, 1052), TAGLINE, fill=MUTED_GOLD, font=f_foot, anchor="mm")

    return canvas

def assemble_video_fast_pipe(topic_item, turns, audio_list, run_dir):
    """
    Renders the video by directly piping raw video frames into FFmpeg.
    Extremely fast and does not write thousands of PNGs to disk.
    """
    clips_dir = run_dir / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)

    base_canvas = load_base_studio_canvas()
    total_dur = sum(a["duration"] for a in audio_list)
    elapsed = 0.0
    clips = []

    print(f"[video] 🎬 Fast pipe encoding {len(audio_list)} clips (~{total_dur / 60:.1f} mins total)...")

    for i, audio in enumerate(audio_list):
        dur = audio["duration"]
        speaker = audio["speaker"]
        timed_phrases = audio["timed_phrases"]
        raw_samples = audio["raw_samples"]
        sample_rate = audio["sample_rate"]
        clip_p = clips_dir / f"clip_{i:04d}.mp4"

        total_frames = max(1, int(dur * RENDER_FPS))

        cmd = [
            "ffmpeg", "-y",
            "-loglevel", "error",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{VIDEO_WIDTH}x{VIDEO_HEIGHT}",
            "-pix_fmt", "rgb24",
            "-r", str(RENDER_FPS),
            "-i", "-",
            "-i", audio["path"],
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "-preset", "ultrafast",
            str(clip_p)
        ]

        # Guarantee audio file is valid and non-empty before starting FFmpeg
        audio_file = Path(audio["path"])
        if not audio_file.exists() or audio_file.stat().st_size < 200:
            print(f"  [video] Fixing empty audio for clip {i}...")
            AudioSegment.silent(duration=int(dur * 1000) or 4000, frame_rate=24000).export(str(audio_file), format="mp3")

        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

        broken = False
        for f_idx in range(total_frames):
            if broken:
                break
            t_in_turn = (f_idx / total_frames) * dur
            sub_elapsed = elapsed + t_in_turn

            # Active phrase
            active_phrase = timed_phrases[0] if timed_phrases else {"text": "Listen carefully", "start": 0, "end": dur}
            for p in timed_phrases:
                if p["start"] <= t_in_turn <= p["end"]:
                    active_phrase = p
                    break
                elif t_in_turn > p["end"]:
                    active_phrase = p

            # Active word
            p_text = active_phrase["text"]
            p_words = p_text.split()
            p_dur = max(0.2, active_phrase["end"] - active_phrase["start"])
            rel_t = max(0.0, min(p_dur, t_in_turn - active_phrase["start"]))
            active_w_idx = min(len(p_words) - 1, int((rel_t / p_dur) * len(p_words)))

            # Equalizer bars
            eq_bars = compute_physical_equalizer_bars(raw_samples, sample_rate, t_in_turn, num_bars=16)

            # Frame render
            frame = render_broadcast_frame(
                base_canvas, speaker, p_text, active_w_idx,
                eq_bars, f_idx, sub_elapsed, total_dur
            )

            try:
                proc.stdin.write(frame.convert("RGB").tobytes())
            except (BrokenPipeError, OSError):
                broken = True

        try:
            proc.stdin.close()
        except Exception:
            pass
        proc.wait()

        clips.append(clip_p)
        elapsed += dur

        if (i + 1) % 15 == 0 or i == len(audio_list) - 1:
            pct = int((i + 1) / len(audio_list) * 100)
            print(f"  [video] Progress: {pct}% ({i+1}/{len(audio_list)} clips encoded)")

    concat_txt = run_dir / "concat.txt"
    with open(concat_txt, "w") as f:
        for c in clips:
            f.write(f"file '{c.resolve().as_posix()}'\n")

    final_video = run_dir / "tales_story_final.mp4"
    print(f"[video] 🔗 Concatenating {len(clips)} clips into final broadcast...")
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_txt),
        "-c", "copy",
        str(final_video)
    ], check=True, capture_output=True)

    return final_video, total_dur

async def run_tales_generation(topic_item=None, turns_count=150):
    """
    Master generator function for Learn English with Tales.
    Generates full video, dynamic thumbnail, and rich metadata.
    """
    if topic_item is None:
        from topics_manager import get_next_topic
        topic_item = get_next_topic()

    topic_title = topic_item["topic"]
    keyword = topic_item.get("keyword", "ADVENTURE")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = OUTPUT_DIR / f"run_{ts}"
    run_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 65)
    print(f"🌟 LEARN ENGLISH WITH TALES - 16:9 FULL HD BROADCAST")
    print(f"📖 Topic: {topic_title}")
    print(f"🎯 Turns: {turns_count} (Estimated ~{turns_count * 8 / 60:.1f} minutes)")
    print("=" * 65)

    # 1. Script Generation
    turns = generate_full_story_script(topic_item, target_turns=turns_count)
    with open(run_dir / "script.json", "w", encoding="utf-8") as f:
        json.dump({"topic": topic_title, "keyword": keyword, "turns": turns}, f, indent=2)

    # 2. Audio Generation
    audio_list = await generate_all_audio(turns, run_dir)

    # 3. Video Assembly
    video_p, dur = assemble_video_fast_pipe(topic_item, turns, audio_list, run_dir)

    # 4. Thumbnail Generation
    from thumbnail_generator import create_thumbnail
    thumb_p = run_dir / "thumbnail.jpg"
    create_thumbnail(topic_title, keyword=keyword, output_path=thumb_p)

    # 5. Metadata JSON Generation
    mins = int(dur // 60)
    secs = int(dur % 60)
    meta = {
        "title": f"{topic_title} 🌟 Learn English with Tales (20 Min Story Podcast)",
        "description": (
            f"✨ Welcome to Learn English with Tales! Today's 20-minute immersive story podcast is '{topic_title}'.\n\n"
            f"📖 Theme & Vocabulary Focus: {keyword}\n\n"
            f"🎧 Hosted by Lily & Leo, this engaging English storytelling session is designed to expand your vocabulary, "
            f"train active listening comprehension, and inspire with positive moral lessons.\n\n"
            f"⏱️ Chapters:\n"
            f"00:00 - Introduction & The Story Setting\n"
            f"03:15 - Act 1: Into the Enchanted Forest\n"
            f"07:30 - Act 2: The Mystery and the Riddle\n"
            f"12:00 - Act 3: The Climax & Hidden Wonder\n"
            f"16:20 - Act 4: Moral Lesson & Vocabulary Breakdown\n"
            f"18:45 - Act 5: Interactive Quiz & Farewell\n\n"
            f"#LearnEnglish #EnglishTales #BedtimeStory #EnglishPodcast #KidsEnglish #ESL #EnglishListening"
        ),
        "topic": topic_title,
        "keyword": keyword,
        "duration_seconds": dur,
        "duration_formatted": f"{mins}:{secs:02d}",
        "video_path": str(video_p),
        "thumbnail_path": str(thumb_p),
        "tags": [
            "Learn English",
            "English with Tales",
            "English Story Podcast",
            "Kids English",
            "Learn English Through Stories",
            "English Listening Practice",
            "Bedtime Stories English",
            "ESL Stories",
            "English Vocabulary",
            "Audio Stories for Kids"
        ]
    }
    with open(run_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print("=" * 65)
    print(f"🎉 Generation Complete!")
    print(f"📹 Video: {video_p} ({mins}:{secs:02d})")
    print(f"🖼️ Thumbnail: {thumb_p}")
    print(f"📄 Metadata: {run_dir / 'metadata.json'}")
    print("=" * 65)

    return video_p, meta

if __name__ == "__main__":
    asyncio.run(run_tales_generation(turns_count=4))
