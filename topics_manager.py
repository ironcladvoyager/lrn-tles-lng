"""
Topics Manager for Learn English with Tales
Handles generating fresh daily story topics with Pollinations AI,
topic rotation, and tracking used topics.
"""
import os
import json
import re
import requests
from pathlib import Path

BASE_DIR = Path(__file__).parent
TOPICS_FILE = BASE_DIR / "tales_topics.json"
USED_TOPICS_FILE = BASE_DIR / "used_topics.txt"

def load_all_topics():
    if not TOPICS_FILE.exists():
        return []
    with open(TOPICS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_used_topics():
    if not USED_TOPICS_FILE.exists():
        return set()
    with open(USED_TOPICS_FILE, "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}

def mark_topic_used(topic_name):
    with open(USED_TOPICS_FILE, "a", encoding="utf-8") as f:
        f.write(f"{topic_name}\n")

def generate_ai_story_topic():
    """Generates an original, imaginative story topic using Pollinations AI."""
    key = os.getenv("POLLINATIONS_API_KEY")
    if not key:
        return None

    prompt = (
        "Create 1 brand new, completely original children's fairy tale or adventure story topic "
        "for an English learning podcast (Show: 'Learn English with Tales'). "
        "Return strictly valid JSON only with keys: "
        "'topic' (concise creative tale title, e.g. 'The Clockwork Fox and the Whispering River'), "
        "'keyword' (1-3 words moral or vocabulary focus in UPPERCASE, e.g. 'COURAGE & KINDNESS'), "
        "'summary' (2-sentence captivating plot synopsis), "
        "'level' ('A2-B1')."
    )

    try:
        resp = requests.post(
            "https://gen.pollinations.ai/v1/chat/completions",
            json={
                "model": "gemini-fast",
                "messages": [
                    {"role": "system", "content": "You are a master children's author creating captivating fairy tale concepts for an English learning show."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.95
            },
            headers={"Authorization": f"Bearer {key}"},
            timeout=20
        )
        if resp.status_code == 200:
            raw = resp.json()["choices"][0]["message"]["content"].strip()
            if "```json" in raw: raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw: raw = raw.split("```")[1].split("```")[0].strip()
            item = json.loads(raw)
            if "topic" in item and "summary" in item:
                # Clean up keyword
                kw = item.get("keyword", "ADVENTURE & LEARNING").strip().upper()
                kw = re.sub(r'[^A-Z\s&•]', '', kw)[:32]
                topic_item = {
                    "id": int(os.environ.get("RUN_ID", 100)) + len(load_used_topics()),
                    "topic": item["topic"].strip(),
                    "keyword": kw if kw else "STORY ADVENTURE",
                    "summary": item["summary"].strip(),
                    "level": item.get("level", "A2-B1")
                }
                print(f"[topics] 🤖 Generated new AI story topic: '{topic_item['topic']}'")
                return topic_item
    except Exception as e:
        print(f"[topics] AI topic generation note: {e}")
    return None

def get_next_topic(preferred_topic=None, use_ai=True):
    """
    Retrieves the next story topic.
    1. If custom preferred_topic is given, uses that.
    2. If use_ai=True and API key is set, generates a brand new unique AI story.
    3. Fallback: rotates to the next unused topic in tales_topics.json.
    """
    topics = load_all_topics()
    used = load_used_topics()

    # 1. Preferred topic
    if preferred_topic:
        for t in topics:
            if preferred_topic.lower() in t["topic"].lower():
                return t
        return {
            "id": 999,
            "topic": preferred_topic,
            "keyword": "DISCOVERY & ADVENTURE",
            "summary": f"Lily and Leo explore the captivating tale of '{preferred_topic}'.",
            "level": "A2-B1"
        }

    # 2. Dynamic Pollinations AI Story Generation
    if use_ai and os.getenv("POLLINATIONS_API_KEY"):
        ai_topic = generate_ai_story_topic()
        if ai_topic and ai_topic["topic"] not in used:
            return ai_topic

    # 3. Catalog rotation fallback
    for t in topics:
        if t["topic"] not in used:
            return t

    # All topics used once, reset cycle
    print("[topics] Catalog cycle complete. Resetting used topics tracker...")
    USED_TOPICS_FILE.unlink(missing_ok=True)
    return topics[0] if topics else {
        "id": 1,
        "topic": "The Secret of the Whispering Tree",
        "keyword": "CURIOSITY & COURAGE",
        "summary": "Lily and Leo discover an ancient willow tree that speaks in riddles.",
        "level": "A2-B1"
    }

if __name__ == "__main__":
    next_t = get_next_topic()
    print("Next selected topic:", next_t["topic"])
    print("Keyword:", next_t.get("keyword"))
