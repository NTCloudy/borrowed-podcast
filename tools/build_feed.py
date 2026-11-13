"""Build docs/feed.xml (Apple/Spotify podcast RSS) and docs/index.html from episodes.json."""
import json, os, subprocess, html

BASE = "https://ntcloudy.github.io/borrowed-podcast"
EMAIL = os.environ.get("PODCAST_EMAIL", "robinhood126936@gmail.com")
eps = sorted(json.load(open("episodes.json", encoding="utf-8")), key=lambda e: (e["season"], e["n"]))
desc = (
    "《這個男朋友是借的》有聲書。凌晨十二點五十分，資深婚企許若心被鎖在門外，"
    "對門搬來一年半只點過頭的工程師陳廷川和一隻賓士貓「肉圓」成了救兵。"
    "為了應付媽媽催婚，「借男朋友一個月」的交易就這樣開始——從頭甜到尾的台灣都會戀愛故事。"
)
items = []
for e in eps:
    f = f"docs/audio/{e['file']}"
    if not os.path.exists(f):
        continue
    size = os.path.getsize(f)
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f],
        capture_output=True, text=True,
    ).stdout.strip()
    if not out:
        print("skip unreadable", f)
        continue
    dur = float(out)
    e["duration"] = int(dur)
    items.append(f"""    <item>
      <title>{html.escape(e['title'])}</title>
      <description>{html.escape(e.get('summary', e['title']))}</description>
      <enclosure url="{BASE}/audio/{e['file']}" length="{size}" type="audio/mpeg"/>
      <guid isPermaLink="false">borrowed-{e['file']}</guid>
      <pubDate>{e['pub']}</pubDate>
      <itunes:duration>{int(dur)}</itunes:duration>
      <itunes:episode>{e['n']}</itunes:episode>
      <itunes:season>{e['season']}</itunes:season>
      <itunes:episodeType>full</itunes:episodeType>
      <itunes:explicit>false</itunes:explicit>
      <itunes:image href="{BASE}/img/{e.get('img', 'cover.jpg')}"/>
    </item>""")

feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>這個男朋友是借的｜有聲書</title>
    <link>{BASE}/</link>
    <atom:link href="{BASE}/feed.xml" rel="self" type="application/rss+xml"/>
    <language>zh-tw</language>
    <description>{html.escape(desc)}</description>
    <itunes:author>NTCloudy</itunes:author>
    <itunes:owner><itunes:name>NTCloudy</itunes:name><itunes:email>{EMAIL}</itunes:email></itunes:owner>
    <itunes:image href="{BASE}/img/cover.jpg"/>
    <itunes:category text="Fiction"/>
    <itunes:explicit>false</itunes:explicit>
    <itunes:type>serial</itunes:type>
{chr(10).join(items)}
  </channel>
</rss>
"""
open("docs/feed.xml", "w", encoding="utf-8").write(feed)
rows = "".join(
    f"<li><b>{html.escape(e['title'])}</b><br><audio controls preload='none' src='audio/{e['file']}'></audio></li>"
    for e in eps
)
open("docs/index.html", "w", encoding="utf-8").write(
    f"""<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>這個男朋友是借的｜有聲書</title><style>body{{font-family:sans-serif;max-width:720px;margin:auto;padding:16px;background:#111;color:#eee}}img{{width:100%;max-width:360px}}li{{margin:14px 0}}audio{{width:100%}}a{{color:#f66}}</style>
<img src="img/cover.jpg"><h1>這個男朋友是借的｜有聲書</h1><p>{html.escape(desc)}</p><p>RSS：<a href="feed.xml">{BASE}/feed.xml</a></p><ol>{rows}</ol>"""
)
json.dump(eps, open("episodes.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("episodes", len(eps))
