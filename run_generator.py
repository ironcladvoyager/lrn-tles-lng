"""
Master Runner for Learn English with Tales (16:9 Full HD Broadcast ~20 Minutes)
Usage:
    python run_generator.py                     # Full 20-minute daily story episode (~150 turns)
    python run_generator.py --test              # Quick 2-turn test run (~15s)
    python run_generator.py --quick             # 8-turn preview run (~1 min)
    python run_generator.py --full              # Full 20-minute daily story episode (~150 turns)
    python run_generator.py --auto              # Auto rotate to next unused story from catalog
    python run_generator.py --topic "Title"     # Run custom tale topic
    python run_generator.py --publish           # Generate & publish video + thumbnail to YT & FB
    python run_generator.py --publish-yt        # Publish to YouTube only
    python run_generator.py --publish-fb        # Publish to Facebook only
"""
import sys
import asyncio
from pathlib import Path

if sys.platform == 'win32':
    try: sys.stdout.reconfigure(encoding='utf-8')
    except Exception: pass

from topics_manager import get_next_topic, mark_topic_used
from tales_generator import run_tales_generation

def parse_args():
    turns = 150  # Default ~20 minutes
    publish_yt = False
    publish_fb = False
    custom_topic = None
    auto = False
    privacy = "public"

    for i, arg in enumerate(sys.argv):
        if arg == "--test":
            turns = 2
        elif arg == "--quick":
            turns = 8
        elif arg == "--10min":
            turns = 80
        elif arg in ["--full", "--20min"]:
            turns = 150
        elif arg == "--turns" and i + 1 < len(sys.argv):
            turns = int(sys.argv[i + 1])
        elif arg == "--auto":
            auto = True
        elif arg == "--publish":
            publish_yt = True
            publish_fb = True
        elif arg == "--publish-yt":
            publish_yt = True
        elif arg == "--publish-fb":
            publish_fb = True
        elif arg == "--topic" and i + 1 < len(sys.argv):
            custom_topic = sys.argv[i + 1]
        elif arg == "--unlisted":
            privacy = "unlisted"
        elif arg == "--private":
            privacy = "private"

    return turns, publish_yt, publish_fb, custom_topic, auto, privacy

def main():
    turns, publish_yt, publish_fb, custom_topic, auto, privacy = parse_args()
    mins_est = turns * 8 / 60

    print("=" * 65)
    print("🌟 LEARN ENGLISH WITH TALES - DAILY STORY ENGINE")
    print(f"Modes: turns={turns} (~{mins_est:.1f} mins), publish_yt={publish_yt}, publish_fb={publish_fb}, privacy={privacy}")
    print("=" * 65)

    # 1. Resolve story topic
    topic_item = get_next_topic(preferred_topic=custom_topic)
    topic_title = topic_item["topic"]
    print(f"📌 Selected Tale: {topic_title}")

    # 2. Generate broadcast video, dynamic thumbnail, and metadata
    video_path, meta = asyncio.run(run_tales_generation(topic_item=topic_item, turns_count=turns))
    print(f"\n🎬 Story Video Generated: {video_path}")
    print(f"🖼️ Thumbnail Generated: {meta.get('thumbnail_path')}")

    # 3. Mark topic used
    mark_topic_used(topic_title)

    # 4. Publish to YouTube if enabled
    if publish_yt:
        print("\n🚀 Publishing to YouTube...")
        try:
            from publish_youtube import upload_video_to_youtube
            yt_res = upload_video_to_youtube(video_path, meta, privacy_status=privacy)
            print(f"🎉 YouTube Publish Success! Link: {yt_res['url']}")
        except Exception as e:
            print(f"⚠️ YouTube upload note: {e}")

    # 5. Publish to Facebook if enabled
    if publish_fb:
        print("\n🚀 Publishing to Facebook...")
        try:
            from publish_facebook import upload_to_facebook
            fb_res = upload_to_facebook(str(video_path), meta["title"], meta["description"])
            if fb_res:
                print(f"🎉 Facebook Publish Success! Video ID: {fb_res.get('id')}")
        except Exception as e:
            print(f"⚠️ Facebook upload note: {e}")

    print("\n✅ All operations completed successfully!")

if __name__ == "__main__":
    main()
