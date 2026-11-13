"""Chapter text -> MP3 with edge-tts (zh-TW female HsiaoChen), chunked + concatenated."""
import asyncio, re, subprocess, sys, tempfile, os
import edge_tts

VOICE = os.environ.get("VOICE", "zh-TW-HsiaoChenNeural")


def clean(text):
    text = re.sub(r"^第[一二三四五六七八九十百零\d]+章[^\n]*\n*", "", text, count=1)
    text = re.sub(r"^【插圖[A-Za-z0-9]*】\s*$", "", text, flags=re.M)
    text = re.sub(r"^\s*＊\s*$", "。", text, flags=re.M)
    text = text.replace("——", "，").replace("……", "。")
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def chunks(text, n=1200):
    out, cur = [], ""
    for para in text.split("\n"):
        if len(cur) + len(para) > n and cur:
            out.append(cur)
            cur = ""
        cur += para + "\n"
    if cur.strip():
        out.append(cur)
    return out


async def synth(sem, text, path):
    async with sem:
        for attempt in range(5):
            try:
                await edge_tts.Communicate(text, VOICE, rate="+0%").save(path)
                return
            except Exception as e:
                print("retry", attempt + 1, e, flush=True)
                await asyncio.sleep(3 * (attempt + 1))
    raise RuntimeError("tts failed")


async def synth_all(parts, td):
    sem = asyncio.Semaphore(3)
    files = [f"{td}/{i:03d}.mp3" for i in range(len(parts))]
    await asyncio.gather(*(synth(sem, t, p) for t, p in zip(parts, files)))
    return files


def main(src, out, intro, outro):
    body = clean(open(src, encoding="utf-8").read())
    parts = [intro] + chunks(body) + [outro]
    tmp = out + ".part.mp3"
    with tempfile.TemporaryDirectory() as td:
        files = asyncio.run(synth_all(parts, td))
        lst = f"{td}/list.txt"
        open(lst, "w").write("".join(f"file '{f}'\n" for f in files))
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst,
             "-ac", "1", "-ar", "24000", "-b:a", "64k", tmp],
            check=True,
        )
        os.replace(tmp, out)  # never leave a half-written MP3 behind
    dur = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out],
        capture_output=True, text=True,
    ).stdout.strip()
    print(out, dur, flush=True)


if __name__ == "__main__":
    main(*sys.argv[1:5])
