"""
Topics Manager for Learn English with Tales
Handles rotating daily story topics, tracking used topics, and retrieving curated topic metadata.
"""
import os
import json
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

def get_next_topic(preferred_topic=None):
    topics = load_all_topics()
    if not topics:
        raise ValueError("No topics available in tales_topics.json!")

    if preferred_topic:
        for t in topics:
            if preferred_topic.lower() in t["topic"].lower():
                return t
        return {
            "id": 999,
            "topic": preferred_topic,
            "keyword": "DISCOVERY & ADVENTURE",
            "summary": f"Lily and Leo explore the captivating tale of '{preferred_topic}'.",
            "level": "A2-B1",
            "starter_turns": [
                {"speaker": "Host1", "text": f"Welcome everyone to Learn English with Tales! Today our story is all about **{preferred_topic}**."},
                {"speaker": "Host2", "text": "Listen carefully as we discover ancient mysteries, exciting characters, and valuable English **phrases**."},
                {"speaker": "Host1", "text": "Pay close attention to the highlighted words to build your conversational English **fluency**."},
                {"speaker": "Host2", "text": "Let us begin this wonderful adventure together and enjoy every **moment**!"}
            ]
        }

    used = load_used_topics()
    for t in topics:
        if t["topic"] not in used:
            return t

    # All topics used once, reset or cycle
    print("[topics] All topics have been used. Cycling through catalog...")
    USED_TOPICS_FILE.unlink(missing_ok=True)
    return topics[0]

if __name__ == "__main__":
    next_t = get_next_topic()
    print("Next topic:", next_t["topic"])
