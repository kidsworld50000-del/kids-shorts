#!/usr/bin/env python3
"""Kids Shorts generator: builds one 30s vertical (1080x1920) video per run."""
import random, subprocess, sys, tempfile, datetime, os, json, math, wave, struct
from PIL import Image, ImageDraw, ImageFont

W, H, FPS, SCENE_SEC = 1080, 1920, 30, 5
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")


# Each script = title + 6 scenes (bg color, shape, shape color, big word, small line)
SCRIPTS = [
 {"id": "colors", "title": "تعلم الألوان مع الأشكال | ألوان للأطفال",
  "scenes": [("#FFF3C4","circle","#E53935","أحمر","تفاحة حمراء"),
             ("#E3F2FD","circle","#1E88E5","أزرق","بحر أزرق"),
             ("#FFFDE7","circle","#FDD835","أصفر","شمس صفراء"),
             ("#E8F5E9","circle","#43A047","أخضر","شجرة خضراء"),
             ("#FFF3E0","circle","#FB8C00","برتقالي","برتقالة لذيذة"),
             ("#F3E5F5","star","#8E24AA","أحسنت!","تعلمنا خمسة ألوان")]},
 {"id": "numbers", "title": "تعلم الأرقام من ١ إلى ٥ | أرقام للأطفال",
  "scenes": [("#E3F2FD","num:1","#E53935","واحد","نجمة واحدة"),
             ("#E8F5E9","num:2","#1E88E5","اثنان","نجمتان"),
             ("#FFFDE7","num:3","#43A047","ثلاثة","ثلاث نجمات"),
             ("#FFF3E0","num:4","#8E24AA","أربعة","أربع نجمات"),
             ("#FCE4EC","num:5","#FB8C00","خمسة","خمس نجمات"),
             ("#F3E5F5","star","#FDD835","أحسنت!","عددنا حتى خمسة")]},
 {"id": "shapes", "title": "تعلم الأشكال الهندسية | أشكال للأطفال",
  "scenes": [("#FFF3C4","circle","#E53935","دائرة","مثل الكرة"),
             ("#E3F2FD","square","#1E88E5","مربع","مثل النافذة"),
             ("#E8F5E9","triangle","#43A047","مثلث","مثل قطعة البيتزا"),
             ("#FFF3E0","rect","#FB8C00","مستطيل","مثل الباب"),
             ("#F3E5F5","star","#FDD835","نجمة","تلمع في السماء"),
             ("#FCE4EC","heart","#D81B60","أحسنت!","تعلمنا خمسة أشكال")]},
]

_BG = ["#FFF3C4","#E3F2FD","#E8F5E9","#FFF3E0","#FCE4EC","#F3E5F5"]
_COL = ["#E53935","#1E88E5","#43A047","#FB8C00","#8E24AA","#D81B60"]
def _mk(id_, title, items, kind_fn, closing):
    sc = [(_BG[i%6], kind_fn(it), _COL[i%6], it[0], it[1]) for i, it in enumerate(items)]
    sc.append(("#F3E5F5", "star", "#FDD835", "أحسنت!", closing))
    return {"id": id_, "title": title, "scenes": sc}

_LETTERS = [("أ","أرنب"),("ب","بطة"),("ت","تفاحة"),("ث","ثعلب"),("ج","جمل"),("ح","حصان"),("خ","خروف"),
 ("د","دب"),("ذ","ذرة"),("ر","رمان"),("ز","زرافة"),("س","سمكة"),("ش","شمس"),("ص","صقر"),("ض","ضفدع"),
 ("ط","طائرة"),("ظ","ظرف"),("ع","عصفور"),("غ","غزال"),("ف","فيل"),("ق","قمر"),("ك","كتاب"),
 ("ل","ليمون"),("م","موز"),("ن","نجمة"),("ه","هلال"),("و","وردة"),("ي","يد")]
for _i in range(0, 25, 5):
    _chunk = _LETTERS[_i:_i+5]
    SCRIPTS.append(_mk(f"letters{_i//5+1}", f"تعلم الحروف العربية {_chunk[0][0]} إلى {_chunk[-1][0]} | حروف للأطفال",
        [(l, f"{l} مثل {w}") for l, w in _chunk], lambda it: "letter:"+it[0], "تعلمنا خمسة حروف"))
SCRIPTS.append(_mk("letters6", "تعلم الحروف العربية ن إلى ي | حروف للأطفال",
    [(l, f"{l} مثل {w}") for l, w in _LETTERS[24:28]], lambda it: "letter:"+it[0], "أنهينا الحروف"))

_NUMS = ["واحد","اثنان","ثلاثة","أربعة","خمسة","ستة","سبعة","ثمانية","تسعة","عشرة"]
SCRIPTS.append({"id":"numbers2","title":"تعلم الأرقام من ٦ إلى ١٠ | أرقام للأطفال","scenes":
    [(_BG[i%6],"circle",_COL[i%6],_NUMS[i+5],f"الرقم {i+6}") for i in range(5)]
    + [("#F3E5F5","star","#FDD835","أحسنت!","عددنا حتى عشرة")]})
SCRIPTS.append({"id":"colors2","title":"ألوان جديدة للأطفال | وردي بني أبيض أسود","scenes":
    [("#FFFFFF","circle","#F06292","وردي","زهرة وردية"),("#FFF8E1","circle","#795548","بني","شوكولاتة بنية"),
     ("#ECEFF1","circle","#FFFFFF","أبيض","ثلج أبيض"),("#FFFDE7","circle","#212121","أسود","ليل أسود"),
     ("#E0F7FA","circle","#00ACC1","تركوازي","ماء تركوازي"),("#F3E5F5","star","#FDD835","أحسنت!","تعلمنا ألواناً جديدة")]})
SCRIPTS.append({"id":"shapes2","title":"أشكال جديدة للأطفال | قلب ونجمة ومعين","scenes":
    [("#FCE4EC","heart","#D81B60","قلب","نحب أمي وأبي"),("#FFF3C4","star","#FDD835","نجمة","تلمع بالليل"),
     ("#E3F2FD","triangle","#1E88E5","مثلث","جبل عالٍ"),("#E8F5E9","circle","#43A047","دائرة","عجلة السيارة"),
     ("#FFF3E0","square","#FB8C00","مربع","صندوق الألعاب"),("#F3E5F5","star","#8E24AA","أحسنت!","تعلمنا أشكالاً جديدة")]})

def star_pts(cx, cy, r, n=5):
    pts = []
    for i in range(n * 2):
        rr = r if i % 2 == 0 else r * 0.45
        a = -math.pi / 2 + i * math.pi / n
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts

def draw_shape(d, kind, color, cx, cy, r):
    o = dict(outline="#333333", width=10)
    if kind == "circle": d.ellipse([cx-r, cy-r, cx+r, cy+r], fill=color, **o)
    elif kind == "square": d.rounded_rectangle([cx-r, cy-r, cx+r, cy+r], 30, fill=color, **o)
    elif kind == "rect": d.rounded_rectangle([cx-r*0.65, cy-r, cx+r*0.65, cy+r], 30, fill=color, **o)
    elif kind == "triangle": d.polygon([(cx, cy-r), (cx+r, cy+r*0.85), (cx-r, cy+r*0.85)], fill=color, outline="#333333", width=10)
    elif kind == "star": d.polygon(star_pts(cx, cy, r), fill=color, outline="#333333", width=10)
    elif kind == "heart":
        d.ellipse([cx-r, cy-r*0.9, cx, cy+r*0.1], fill=color); d.ellipse([cx, cy-r*0.9, cx+r, cy+r*0.1], fill=color)
        d.polygon([(cx-r*0.93, cy-r*0.15), (cx+r*0.93, cy-r*0.15), (cx, cy+r)], fill=color)
    elif kind.startswith("letter:"):
        f = ImageFont.truetype(FONT, max(1, int(r * 2.2)), layout_engine=ImageFont.Layout.RAQM)
        d.text((cx, cy), kind[7:], font=f, fill=color, anchor="mm", direction="rtl", language="ar", stroke_width=10, stroke_fill="#333333")
    elif kind.startswith("num:"):
        n = int(kind[4:])
        f = ImageFont.truetype(FONT, max(1, int(r * 1.5)))
        d.text((cx, cy - r*0.35), str(n), font=f, fill=color, anchor="mm", stroke_width=8, stroke_fill="#333333")
        sr = 60; total = n * sr * 2.4; x0 = cx - total/2 + sr*1.2
        for i in range(n):
            d.polygon(star_pts(x0 + i*sr*2.4, cy + r*0.75, sr), fill="#FDD835", outline="#333333", width=5)

def text_c(d, y, txt, size, fill):
    f = ImageFont.truetype(FONT, size, layout_engine=ImageFont.Layout.RAQM)
    d.text((W/2, y), txt, font=f, fill=fill, anchor="mm", direction="rtl", language="ar", stroke_width=6, stroke_fill="white")

def frame(scene, t):
    bg, kind, color, word, line = scene
    im = Image.new("RGB", (W, H), bg); d = ImageDraw.Draw(im)
    pop = min(1.0, t / 0.4)                       # pop-in
    pop = 1 - (1 - pop) ** 3
    bounce = 1 + 0.04 * math.sin(t * 2 * math.pi * 1.2)
    draw_shape(d, kind, color, W/2, 760, 330 * pop * bounce)
    if t > 0.5: text_c(d, 1330, word, 200, "#222222")
    if t > 1.2: text_c(d, 1540, line, 90, "#444444")
    return im

def melody(path, seconds):
    notes = [523, 587, 659, 784, 659, 587, 523, 659, 784, 880, 784, 659]  # C major, gentle
    sr = 44100
    with wave.open(path, "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        buf = bytearray()
        for i in range(int(seconds * sr)):
            t = i / sr; k = int(t / 0.5); lt = t - k * 0.5
            f = notes[k % len(notes)]
            env = math.exp(-4 * lt) * min(1, lt / 0.01)
            v = 0.35 * env * (math.sin(2*math.pi*f*t) + 0.3*math.sin(4*math.pi*f*t))
            buf += struct.pack("<h", int(max(-1, min(1, v)) * 32767))
        w.writeframes(bytes(buf))

def main():
    os.makedirs(OUT, exist_ok=True)
    want = sys.argv[1] if len(sys.argv) > 1 else None
    s = next((x for x in SCRIPTS if x["id"] == want), None) or SCRIPTS[datetime.date.today().toordinal() % len(SCRIPTS)]
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = os.path.join(OUT, f"short_{s['id']}_{stamp}.mp4")
    total = len(s["scenes"]) * SCENE_SEC
    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, "a.wav"); melody(wav, total)
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
        for sc in s["scenes"]:
            for i in range(SCENE_SEC * FPS):
                p.stdin.write(frame(sc, i / FPS).tobytes())
        p.stdin.close(); p.wait()
    json.dump({"file": out, "title": s["title"] + " #shorts",
               "description": "مقطع تعليمي قصير للأطفال.\n#shorts #اطفال #تعليم_الاطفال",
               "tags": ["اطفال", "تعليم الاطفال", "kids", "learning", "shorts"]},
              open(out.replace(".mp4", ".json"), "w"), ensure_ascii=False, indent=1)
    print(out)

if __name__ == "__main__":
    main()
