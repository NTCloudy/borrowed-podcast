"""這個男朋友是借的: novels/borrowed/chNNN.txt -> docs/audio/eNN.mp3.

Generates chapters 28..80 first, then backfills chapters 1..27.
Skips existing audio; regenerates when chapter text is newer than its MP3.
"""
import json, os, re, subprocess, sys
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

SRC = os.path.expanduser("~/.gemini/jetski/scratch/novels/borrowed")
VOLS = {
    1: "借來的",
    2: "續借",
    3: "不想還",
    4: "不還了",
}
CN = "零一二三四五六七八九"


def cn(n):
    if n < 10:
        return CN[n]
    if n < 20:
        return "十" + (CN[n % 10] if n % 10 else "")
    return CN[n // 10] + "十" + (CN[n % 10] if n % 10 else "")


eps = json.load(open("episodes.json", encoding="utf-8")) if os.path.exists("episodes.json") else []
have = {e["file"] for e in eps}
MAX_NEW = int(os.environ.get("MAX_NEW", "80"))
made = 0


def save():
    json.dump(
        sorted(eps, key=lambda e: (e["season"], e["n"])),
        open("episodes.json.tmp", "w", encoding="utf-8"),
        ensure_ascii=False,
        indent=1,
    )
    os.replace("episodes.json.tmp", "episodes.json")


base = datetime(2026, 11, 13, 12, tzinfo=timezone(timedelta(hours=8)))
order = list(range(28, 81)) + list(range(1, 28))

for n in order:
    if made >= MAX_NEW:
        break
    txt = f"{SRC}/ch{n:03d}.txt"
    if not os.path.exists(txt):
        continue
    first_line = open(txt, encoding="utf-8").readline().strip()
    title = first_line if first_line.startswith("第") else f"第{cn(n)}章"
    season = (n - 1) // 20 + 1
    vol = VOLS[season]
    f = f"e{n:02d}.mp3"
    mp3 = f"docs/audio/{f}"
    if os.path.exists(mp3) and os.path.getmtime(txt) > os.path.getmtime(mp3) + 60:
        os.remove(mp3)
    meta = {
        "title": f"這個男朋友是借的｜{title}",
        "summary": f"《這個男朋友是借的》第{cn(season)}卷「{vol}」　{title}。",
    }
    old = next((e for e in eps if e["file"] == f), None)
    if old and old["title"] != meta["title"]:
        old.update(meta)
        if os.path.exists(mp3):
            os.remove(mp3)
    if f in have and os.path.exists(mp3):
        continue
    if not os.path.exists(mp3):
        subprocess.run(
            [
                sys.executable, "-u", "tools/tts.py", txt, mp3,
                f"這個男朋友是借的。{title.replace('　', '，')}。",
                f"{title.split('　')[0]}，完。感謝收聽這個男朋友是借的。",
            ],
            check=True,
        )
        made += 1
    if f not in have:
        eps.append({
            "n": n,
            "season": season,
            "file": f,
            **meta,
            "pub": format_datetime(base + timedelta(minutes=n)),
        })
        have.add(f)
    save()
    print("done", f, flush=True)
