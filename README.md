# 🌟 Learn English with Tales (Daily 20-Min Story Podcast)

Automated video generator and publishing engine for **Learn English with Tales** — a 16:9 Full HD (1920x1080) storytelling podcast for kids, young learners, and ESL students.

---

## 🎭 Show Concept & Setting
- **Hosts**: Lily (cheerful girl, host 1) & Leo (enthusiastic boy, host 2).
- **Studio Setting**: Enchanted storybook library with mahogany bookshelves, soft fairy lights, glowing lanterns, and an arched window overlooking twilight castle towers.
- **Audio**: Microsoft child neural voices (`en-US-AnaNeural` calibrated for distinct girl and boy resonance).
- **Target Episode Duration**: ~20 minutes (~150 dialogue turns across 5 narrative acts).
- **Daily Variety**:
  - The studio background and hosts remain permanent and recognizable every day.
  - The story topic, vocabulary spotlight, and **custom YouTube thumbnail change dynamically every day**.

---

## 🌟 Key Features
- **5-Act Story Structure**:
  1. *Act 1: The Magic Begins* — Welcome, setting the scene, and introducing characters.
  2. *Act 2: The Journey & The Obstacle* — Exploration, sensory vocabulary, and riddles.
  3. *Act 3: The Climax & Hidden Wonder* — Plot twist, courage, and teamwork.
  4. *Act 4: Moral Lesson & Language Spotlight* — Key vocabulary, idioms, and life wisdom.
  5. *Act 5: Listener Quiz & Cheerful Farewell* — Comprehension challenge and outro.
- **Word-by-Word Karaoke Subtitles**: Centered between Lily and Leo, highlighting active spoken words in radiant gold (`#FFD700`).
- **Physical 16-Band Equalizer**: Accurately computes vocal frequencies via FFT directly from active speech audio.
- **Dynamic 16:9 Thumbnail Generator**: Renders high-CTR, bold 1920x1080 thumbnails for YouTube & Facebook.
- **Automated Publishing**: Resumable video upload with thumbnail attachment to YouTube Data API v3 and Facebook Meta Graph API v20.0.
- **GitHub Actions Daily Automation**: Cron schedule running daily at 06:00 UTC with artifact upload.

---

## 🚀 Quick Start & CLI Usage

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```
*(Requires `ffmpeg` installed on your system).*

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your keys:
```env
# Optional AI generation
POLLINATIONS_API_KEY=your_key

# YouTube Data API v3
YT_CLIENT_ID=your_client_id
YT_CLIENT_SECRET=your_client_secret
YT_REFRESH_TOKEN=your_refresh_token

# Facebook Page API
FB_PAGE_ID=your_page_id
FB_PAGE_ACCESS_TOKEN=your_token
```

### 3. Running the Generator

```bash
# Quick 2-turn test (~15 seconds) to verify audio, visual, and thumbnail rendering:
python run_generator.py --test

# Short preview (8 turns, ~1 minute):
python run_generator.py --quick

# Full 20-minute daily episode (~150 turns):
python run_generator.py --full --auto

# Run a custom story title:
python run_generator.py --topic "The Dragon Who Wanted to Read"

# Generate and publish directly to YouTube & Facebook:
python run_generator.py --full --auto --publish
```

---

## 📁 Repository Structure
```
Learn-English-with-Tales/
├── .github/workflows/
│   └── daily_video_generator.yml   # Daily scheduled GitHub Actions workflow
├── assets/
│   ├── tales_studio.png            # 1920x1080 enchanted library studio canvas
│   └── kids_studio.png             # Studio backup canvas
├── output/                         # Output runs (video, thumbnail, metadata)
├── tales_topics.json               # Rich catalog of 20+ story topics
├── topics_manager.py               # Topic rotation & used tracker
├── tales_generator.py              # Core video rendering engine (fast pipe)
├── thumbnail_generator.py          # Dynamic 16:9 YouTube thumbnail engine
├── publish_youtube.py              # YouTube Data API v3 publisher with thumbnail
├── publish_facebook.py             # Facebook Graph API v20.0 publisher
├── run_generator.py                # Master CLI runner
├── requirements.txt                # Python dependencies
└── .env.example                    # Environment secrets template
```
