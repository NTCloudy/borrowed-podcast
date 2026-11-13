#!/usr/bin/env bash
set -euo pipefail
cd /usr/local/google/home/linyuwei/.gemini/jetski/scratch/borrowed-podcast

while true; do
  before=$(ls -1 docs/audio/*.mp3 2>/dev/null | wc -l)
  if [ "$before" -ge 80 ]; then
    echo "All 80 chapters complete!"
    break
  fi
  MAX_NEW=10 python3 -u tools/batch.py
  python3 tools/build_feed.py
  after=$(ls -1 docs/audio/*.mp3 2>/dev/null | wc -l)
  if [ -n "$(git status --porcelain)" ]; then
    git add -A
    git commit -m "audio batch: ${after}/80 episodes"
    git push
  fi
  if [ "$after" -eq "$before" ]; then
    echo "No new episodes produced, stopping at ${after}/80."
    break
  fi
done
