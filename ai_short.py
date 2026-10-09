# -*- coding: utf-8 -*-
"""AI-illustrated kids Short. Input: ai_short/job.json
{ "title": "...", "description": "...", "scenes": [ {"digit": "١", "word": "واحد", "line": "أرنب واحد", "url": "https://..."} ] }
Ken-Burns motion on the images + Arabic voice (edge-tts) + melody. Writes output/ai_short.mp4 and .json"""
import os, json, subprocess, tempfile, urllib.request
from PIL import Image, ImageDraw, ImageFont
import shorts_generator as g

HERE = os.path.dirname(os.path.abspath(__file__))
g.SCENE_SEC = 10
W, H, FPS, SEC = g.W, g.H, g.FPS, g.SCENE_SEC

def load(i, url, tmp):
    p = os.path.join(tmp, f"img{i}.png")
    urllib.request.urlretrieve(url.strip(), p)
    return Image.open(p).convert("RGB")

def cover(im, zoom, pan):
    sh = int(H * zoom); sw = max(W, int(im.width * sh / im.height))
    big = im.resize((sw, sh), Image.LANCZOS)
    x = int((sw - W) * pan); y = int((sh - H) / 2)
    return big.crop((x, y, x + W, y + H))

def overlay(fr, sc, t):
    d = ImageDraw.Draw(fr, "RGBA")
    pop = min(1.0, t / 0.5); pop = 1 - (1 - pop) ** 3
    r = int(190 * pop)
    if r > 5:
        d.ellipse((W/2 - r, 330 - r, W/2 + r, 330 + r), fill=(255, 255, 255, 235), outline=(60, 60, 60, 255), width=8)
        if t > 0.3 and sc.get("digit"):
            f = ImageFont.truetype(g.FONT, int(r * 1.5), layout_engine=ImageFont.Layout.RAQM)
            d.text((W/2, 330), sc["digit"], font=f, fill="#6A1B9A", anchor="mm", direction="rtl", language="ar")
    if t > 0.8:
        d.rounded_rectangle((90, 1440, W - 90, 1760), radius=60, fill=(255, 255, 255, 215))
        g.text_c(d, 1530, sc["word"], 150, "#222222")
        if t > 1.4 and sc.get("line"): g.text_c(d, 1670, sc["line"], 85, "#444444")

def main():
    job = json.load(open(os.path.join(HERE, "ai_short", "job.json"), encoding="utf-8"))
    scenes = job["scenes"]
    out_dir = os.path.join(HERE, "output"); os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "ai_short.mp4")
    with tempfile.TemporaryDirectory() as tmp:
        imgs = [load(i, s["url"], tmp) for i, s in enumerate(scenes)]
        wav = os.path.join(tmp, "a.wav"); g.melody(wav, SEC * len(scenes))
        nar = [("", "x", "", s["word"], s.get("line", "")) for s in scenes]
        wav = g.narrate(nar, wav, os.path.join(tmp, "mix.wav"), tmp)
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
        for k, sc in enumerate(scenes):
            n = SEC * FPS
            for i in range(n):
                u = i / (n - 1)
                fr = cover(imgs[k], 1.0 + 0.10 * u, 0.40 + 0.20 * u if k % 2 == 0 else 0.60 - 0.20 * u)
                overlay(fr, sc, i / FPS)
                p.stdin.write(fr.tobytes())
        p.stdin.close(); p.wait()
    json.dump({"file": out, "title": job["title"], "description": job["description"]},
              open(out.replace(".mp4", ".json"), "w"), ensure_ascii=False, indent=1)
    print(out)

if __name__ == "__main__":
    main()
