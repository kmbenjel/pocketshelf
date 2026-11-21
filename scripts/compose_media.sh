#!/usr/bin/env bash
# Compose the README images from the raw screenshots of scripts/make_media.mjs.  Usage: compose_media.sh RAWDIR OUTDIR
set -euo pipefail
RAW="$1"; OUT="$2"; mkdir -p "$OUT"
round() {  # round IN OUT RADIUS  -> rounded corners with a soft shadow
  local in="$1" out="$2" r="$3" w h
  w=$(identify -format %w "$in"); h=$(identify -format %h "$in")
  convert "$in" \( -size ${w}x${h} xc:none -fill white -draw "roundrectangle 0,0,$((w-1)),$((h-1)),$r,$r" \) -alpha set -compose DstIn -composite -compose Over \
    \( +clone -background '#0b1f3a' -shadow 38x16+0+14 \) +swap -background none -layers merge +repage "$out"
}
phone() { convert "$1" -resize 300x "$RAW/_p.png"; round "$RAW/_p.png" "$2" 34; }
desk()  { convert "$1" -resize "$3"x "$RAW/_d.png"; round "$RAW/_d.png" "$2" 14; }

phone "$RAW/phone-search.png" "$RAW/_ph1.png"
phone "$RAW/phone-ar-search.png" "$RAW/_ph2.png"
phone "$RAW/phone-authors-dark.png" "$RAW/_ph3.png"
desk "$RAW/desktop-editions.png" "$RAW/_dk.png" 880

# hero: desktop (left) + three phones (English, Arabic, dark)
convert -size 1900x790 gradient:'#dfe6dd'-'#c9d6e6' \
  "$RAW/_dk.png" -geometry +20+110 -composite \
  "$RAW/_ph1.png" -geometry +930+60 -composite \
  "$RAW/_ph2.png" -geometry +1250+120 -composite \
  "$RAW/_ph3.png" -geometry +1560+40 -composite \
  -resize 1600x -quality 88 "$OUT/hero.webp"

# landing card 1200x750: Arabic phone + English phone + desktop crop
desk "$RAW/desktop-search.png" "$RAW/_dk2.png" 760
convert -size 1200x750 gradient:'#e3e9e0'-'#cddaea' \
  "$RAW/_dk2.png" -geometry +30+140 -composite \
  "$RAW/_ph2.png" -geometry +850+40 -composite \
  "$OUT/card.png"
convert "$OUT/card.png" -quality 82 "$OUT/card.webp"

# individual shots for the docs, as WebP
for f in desktop-editions desktop-search desktop-ar-authors phone-search phone-ar-home phone-ar-search phone-ar-stats phone-ar-cats phone-authors-dark; do
  w=$([[ $f == desktop-* ]] && echo 1100 || echo 390)
  convert "$RAW/$f.png" -resize ${w}x -quality 80 "$OUT/$f.webp"
done
ffmpeg -y -loglevel error -framerate 9 -i "$RAW/frames/f%03d.png" \
  -vf "split[a][b];[a]palettegen=max_colors=96:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4" "$OUT/search.gif"
rm -f "$OUT/card.png" "$RAW"/_*.png
ls -la "$OUT"
