# -*- coding: utf-8 -*-
"""Sample: AI-illustrated kids Short (images downloaded from ai_sample/urls.txt).
Ken-Burns motion on AI images + Arabic voice + melody. NOT published: output goes to a workflow artifact."""
import os, sys, subprocess, tempfile, urllib.request
from PIL import Image, ImageDraw, ImageFont
import shorts_generator as g

g.SCENE_SEC = 10
W, H, FPS, SEC = g.W, g.H, g.FPS, g.SCENE_SEC

SCENES = [  # (digit, word, line spoken/shown)
    ("١", "واحد", "أرنب واحد"),
    ("٢", "اثنان", "بطتان اثنتان"),
    ("٣", "ثلاثة", "ثلاث فراشات"),
]

def load(i, url, tmp):
    p = os.path.join(tmp, f"img{i}.png")
    urllib.request.urlretrieve(url.strip(), p)
    im = Image.open(p).convert("RGB")
    return im

def cover(im, zoom, pan):
    """Crop a 9:16 window out of a (landscape) image: scale to height H*zoom, pan horizontally."""
    sh = int(H * zoom); sw = int(im.width * sh / im.height)
    big = im.resize((sw, sh), Image.LANCZOS)
    x = int((sw - W) * pan); y = int((sh - H) / 2)
    return big.crop((x, y, x + W, y + H))

def overlay(fr, scene, t):
    digit, word, line = scene
    d = ImageDraw.Draw(fr, "RGBA")
    pop = min(1.0, t / 0.5); pop = 1 - (1 - pop) ** 3
    # number badge
    r = int(190 * pop)
    if r > 5:
        d.ellipse((W/2 - r, 330 - r, W/2 + r, 330 + r), fill=(255, 255, 255, 235), outline=(60, 60, 60, 255), width=8)
        if t > 0.3:
            f = ImageFont.truetype(g.FONT, int(r * 1.5), layout_engine=ImageFont.Layout.RAQM)
            d.text((W/2, 330), digit, font=f, fill="#6A1B9A", anchor="mm", direction="rtl", language="ar")
    # bottom band with words
    if t > 0.8:
        d.rounded_rectangle((90, 1440, W - 90, 1760), radius=60, fill=(255, 255, 255, 215))
        g.text_c(d, 1530, word, 150, "#222222")
        if t > 1.4: g.text_c(d, 1670, line, 85, "#444444")

def main():
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output"); os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "ai_sample.mp4")
    urls = [l.split("|", 1)[1] for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai_sample", "urls.txt"), encoding="utf-8") if "|" in l]
    with tempfile.TemporaryDirectory() as tmp:
        imgs = [load(i, u, tmp) for i, u in enumerate(urls)]
        wav = os.path.join(tmp, "a.wav"); g.melody(wav, SEC * len(SCENES))
        # narrate() expects (bg, kind, color, word, line) tuples
        sc = [("", "x", "", w, l) for (_, w, l) in SCENES]
        wav = g.narrate(sc, wav, os.path.join(tmp, "mix.wav"), tmp)
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
        for k, scene in enumerate(SCENES):
            n = SEC * FPS
            for i in range(n):
                u = i / (n - 1)
                fr = cover(imgs[k], 1.0 + 0.10 * u, 0.40 + 0.20 * u if k % 2 == 0 else 0.60 - 0.20 * u)
                overlay(fr, scene, i / FPS)
                p.stdin.write(fr.tobytes())
        p.stdin.close(); p.wait()
    print(out)

if __name__ == "__main__":
    main()
