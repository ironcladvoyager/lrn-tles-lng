import sys
import asyncio
from situation_generator import run_situation_generation

def main():
    print("Starting Real Life Situations & Roleplay generator (9:16 Vertical Reel)...")
    video_p, meta = asyncio.run(run_situation_generation(scen_idx=0))
    print(f"Done! Final video generated: {video_p}")

if __name__ == "__main__":
    main()
