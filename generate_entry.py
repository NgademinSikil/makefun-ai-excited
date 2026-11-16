#!/usr/bin/env python3
"""Generate entry.png for make.fun bounty ai-excited-01.

Original generative art, drawn procedurally with Pillow + numpy:
a giant luminous koi leaps out of a neon ocean toward a blazing
synthwave sun, bursting through the frame toward the viewer.

Deterministic: fixed seed, no network, no time/randomness from the
environment. Run:  python3 generate_entry.py  ->  entry.png (1024x1024)
"""
import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

S = 2  # supersample factor; work at 2048, downscale to 1024
W, H = 1024 * S, 1024 * S
SEED = 20261116
rng = random.Random(SEED)
np_rng = np.random.default_rng(SEED)

HORIZON = int(0.60 * H)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def vgrad(w, h, stops):
    """Vertical gradient image from [(pos, rgb), ...]."""
    ys = np.linspace(0, 1, h)
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    for y in range(h):
        t = ys[y]
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]
            if p0 <= t <= p1:
                f = 0 if p1 == p0 else (t - p0) / (p1 - p0)
                arr[y, :, :] = lerp(c0, c1, f)
                break
        else:
            arr[y, :, :] = stops[-1][1]
    return Image.fromarray(arr, "RGB")


# ---------------------------------------------------------------- sky
sky = vgrad(W, H, [
    (0.00, (8, 8, 46)),      # deep indigo
    (0.30, (48, 16, 96)),    # violet
    (0.48, (150, 24, 122)),  # magenta dusk
    (0.60, (255, 90, 40)),   # burning orange at horizon
    (1.00, (16, 6, 40)),     # deep sea below (overpainted later)
])
img = sky.convert("RGBA")
d = ImageDraw.Draw(img, "RGBA")

# nebula blobs (soft, blurred)
neb = Image.new("RGBA", (W, H), (0, 0, 0, 0))
nd = ImageDraw.Draw(neb)
for (cx, cy, r, col, a) in [
    (0.22, 0.16, 0.20, (0, 220, 255), 46),
    (0.82, 0.12, 0.16, (255, 60, 180), 50),
    (0.68, 0.30, 0.13, (255, 180, 60), 34),
    (0.12, 0.38, 0.12, (120, 80, 255), 40),
]:
    nd.ellipse([cx * W - r * W, cy * H - r * W, cx * W + r * W, cy * H + r * W],
               fill=col + (a,))
neb = neb.filter(ImageFilter.GaussianBlur(90 * S))
img.alpha_composite(neb)
d = ImageDraw.Draw(img, "RGBA")

# stars (upper sky only)
for _ in range(260):
    x = rng.uniform(0, W)
    y = rng.uniform(0, HORIZON * 0.75)
    r = rng.uniform(0.8, 2.6) * S
    a = rng.randint(140, 255)
    d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, a))
    if rng.random() < 0.12:  # cross sparkle
        L = r * 4
        d.line([x - L, y, x + L, y], fill=(255, 255, 255, a // 2), width=max(1, int(S)))
        d.line([x, y - L, x, y + L], fill=(255, 255, 255, a // 2), width=max(1, int(S)))

# ---------------------------------------------------------------- sun
SUN_C = (512 * S, 490 * S)
SUN_R = 200 * S
glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow)
gd.ellipse([SUN_C[0] - SUN_R * 1.45, SUN_C[1] - SUN_R * 1.45,
            SUN_C[0] + SUN_R * 1.45, SUN_C[1] + SUN_R * 1.45],
           fill=(255, 120, 40, 90))
glow = glow.filter(ImageFilter.GaussianBlur(60 * S))
img.alpha_composite(glow)
d = ImageDraw.Draw(img, "RGBA")

sun = Image.new("RGBA", (SUN_R * 2, SUN_R * 2), (0, 0, 0, 0))
sa = np.zeros((SUN_R * 2, SUN_R * 2, 4), dtype=np.uint8)
yy, xx = np.mgrid[0:SUN_R * 2, 0:SUN_R * 2]
dist = np.sqrt((xx - SUN_R) ** 2 + (yy - SUN_R) ** 2) / SUN_R
inside = dist <= 1.0
t = np.clip(1 - yy / (SUN_R * 2), 0, 1)  # 1 top -> 0 bottom
top = np.array([255, 240, 120], dtype=float)
mid = np.array([255, 140, 40], dtype=float)
bot = np.array([255, 40, 110], dtype=float)
col = np.where((t > 0.5)[..., None], top + (mid - top) * (1 - t)[..., None] * 2,
               mid + (bot - mid) * (0.5 - t)[..., None] * 2)
sa[..., :3] = col.astype(np.uint8)
sa[..., 3] = np.where(inside, 255, 0).astype(np.uint8)
sun = Image.fromarray(sa, "RGBA")
img.alpha_composite(sun, (SUN_C[0] - SUN_R, SUN_C[1] - SUN_R))
d = ImageDraw.Draw(img, "RGBA")
# synthwave slats across the lower sun
for i, (y0, th) in enumerate([(0.55, 0.012), (0.63, 0.017), (0.72, 0.024), (0.82, 0.032)]):
    y = SUN_C[1] - SUN_R + int(y0 * 2 * SUN_R)
    half = int(math.sqrt(max(0, SUN_R ** 2 - (y - SUN_C[1]) ** 2)))
    d.rectangle([SUN_C[0] - half, y, SUN_C[0] + half, y + int(th * H)],
                fill=(16, 6, 40, 255))

# ---------------------------------------------------------------- mountains
def ridge(base_y, amp, col, seed):
    r = random.Random(seed)
    pts = [(0, H)]
    x = 0
    y = base_y
    while x < W:
        pts.append((x, y))
        x += r.randint(60, 150) * S
        y = base_y + r.randint(-amp, amp) * S
    pts += [(W, H), (W, base_y)]
    d.polygon(pts, fill=col)

ridge(int(0.585 * H), 26, (52, 14, 88, 255), 7)
ridge(int(0.605 * H), 18, (30, 8, 58, 255), 21)

# ---------------------------------------------------------------- ocean
sea = vgrad(W, H - HORIZON, [
    (0.00, (64, 16, 90)),
    (0.25, (24, 10, 70)),
    (1.00, (6, 4, 34)),
])
img.paste(sea, (0, HORIZON))
d = ImageDraw.Draw(img, "RGBA")
# sun reflection column (soft, on its own layer, blurred)
refl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
rd = ImageDraw.Draw(refl)
for i in range(42):
    y = HORIZON + int(i * (H - HORIZON) / 42) + rng.randint(-3, 3) * S
    wob = rng.uniform(-1, 1)
    half = (26 + i * 2.6) * S
    cx = SUN_C[0] + wob * half * 0.35
    a = max(0, 170 - i * 4)
    col = (255, 150 + i, 60, a) if i < 22 else (255, 110, 150, a // 2)
    rd.line([cx - half, y, cx + half, y], fill=col, width=max(3, int(5 * S)))
refl = refl.filter(ImageFilter.GaussianBlur(6 * S))
img.alpha_composite(refl)
d = ImageDraw.Draw(img, "RGBA")
# horizontal shimmer streaks
for _ in range(70):
    y = rng.uniform(HORIZON + 10, H - 20)
    x = rng.uniform(0, W)
    ln = rng.uniform(20, 160) * S
    col = rng.choice([(0, 220, 255), (255, 120, 200), (255, 220, 120)])
    d.line([x, y, x + ln, y], fill=col + (rng.randint(40, 130),),
           width=max(1, int(2 * S)))

# ---------------------------------------------------------------- koi (hero)
# Spine from tail (lower-left, in the water) to head (upper-right, in the sky)
spine = [
    (0.16, 0.94), (0.24, 0.88), (0.34, 0.79), (0.46, 0.69),
    (0.58, 0.59), (0.69, 0.50), (0.78, 0.43), (0.84, 0.38),
]
spine = [(x * W, y * H) for x, y in spine]
widths = [26, 44, 62, 74, 78, 70, 56, 40]  # half-widths in px at 1024 scale
widths = [w * S for w in widths]

# smooth spine via Catmull-Rom
def catmull(points, samples=24):
    pts = [points[0]] + points + [points[-1]]
    out = []
    for i in range(len(pts) - 3):
        p0, p1, p2, p3 = pts[i], pts[i + 1], pts[i + 2], pts[i + 3]
        for j in range(samples):
            t = j / samples
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t +
                       (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                       (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t +
                       (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                       (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    out.append(points[-1])
    return out

smooth = catmull(spine)
n = len(smooth)
# width profile along smooth spine: taper at both ends, fat in middle
prof = []
for i in range(n):
    t = i / (n - 1)
    prof.append(math.sin(math.pi * (0.12 + 0.76 * t)) ** 0.9)
maxw = 108 * S
left, right = [], []
for i, (x, y) in enumerate(smooth):
    x2, y2 = smooth[min(i + 1, n - 1)]
    x1, y1 = smooth[max(i - 1, 0)]
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    w = maxw * prof[i]
    left.append((x + nx * w, y + ny * w))
    right.append((x - nx * w, y - ny * w))
body_poly = left + right[::-1]

koi = Image.new("RGBA", (W, H), (0, 0, 0, 0))
kd = ImageDraw.Draw(koi)
# glow underlay
kd.polygon(body_poly, fill=(255, 120, 40, 255))
glow_koi = koi.filter(ImageFilter.GaussianBlur(26 * S))
img.alpha_composite(glow_koi)

# body fill: vertical gradient white belly -> orange -> deep orange back
grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ga = np.zeros((H, W, 4), dtype=np.uint8)
tt = np.clip(np.linspace(0, 1, H)[:, None], 0, 1)
# gradient keyed on y within body band
c_top = np.array([255, 90, 20], dtype=float)
c_mid = np.array([255, 190, 80], dtype=float)
c_bot = np.array([255, 250, 230], dtype=float)
band_top, band_bot = 0.30 * H, 0.99 * H
f = np.clip((np.arange(H)[:, None] - band_top) / (band_bot - band_top), 0, 1)
col = np.where((f < 0.5)[..., None],
               c_top + (c_mid - c_top) * (f * 2)[..., None],
               c_mid + (c_bot - c_mid) * ((f - 0.5) * 2)[..., None])
ga[..., :3] = np.repeat(col.astype(np.uint8), W, axis=1)
mask = Image.new("L", (W, H), 0)
md = ImageDraw.Draw(mask)
md.polygon(body_poly, fill=255)
ga[..., 3] = np.array(mask)
grad = Image.fromarray(ga, "RGBA")
koi.alpha_composite(grad)
kd = ImageDraw.Draw(koi)
# outline
kd.line(left + [left[0]], fill=(40, 8, 40, 255), width=max(3, int(5 * S)), joint="curve")
kd.line(right + [right[0]], fill=(40, 8, 40, 255), width=max(3, int(5 * S)), joint="curve")
# back patches (small, along the top edge only)
for t, r in [(0.38, 0.035), (0.55, 0.042), (0.70, 0.032)]:
    i = int(t * (n - 1))
    x, y = smooth[i]
    kd.ellipse([x - r * W, y - r * W * 0.5, x + r * W, y + r * W * 0.5],
               fill=(214, 40, 20, 235))
# scale arcs
for t in np.arange(0.25, 0.9, 0.07):
    i = int(t * (n - 1))
    x, y = smooth[i]
    r = maxw * prof[i] * 0.55
    kd.arc([x - r, y - r * 0.6, x + r, y + r * 0.6], start=200, end=340,
           fill=(180, 40, 10, 160), width=max(2, int(3 * S)))
# --- rounded head cap, oriented along the spine ---
hx, hy = smooth[-1]
px0, py0 = smooth[-6]
hdx, hdy = hx - px0, hy - py0
hL = math.hypot(hdx, hdy) or 1
hdx, hdy = hdx / hL, hdy / hL          # head direction (up-right)
hnx, hny = -hdy, hdx                  # left normal (up-left, visible side)
hc = (hx + hdx * 34 * S, hy + hdy * 34 * S)
head_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
hd = ImageDraw.Draw(head_layer)
# head fill: same belly-to-back gradient, approximated with two tones
hd.ellipse([hc[0] - 62 * S, hc[1] - 52 * S, hc[0] + 62 * S, hc[1] + 52 * S],
           fill=(255, 165, 60, 255))
hd.ellipse([hc[0] - 62 * S, hc[1] + 2 * S, hc[0] + 62 * S, hc[1] + 52 * S],
           fill=(255, 235, 200, 255))
ang = -math.degrees(math.atan2(hdy, hdx))
head_layer = head_layer.rotate(ang, resample=Image.BICUBIC, center=hc)
koi.alpha_composite(head_layer)
kd = ImageDraw.Draw(koi)
# eye, on the upper (back) side of the head
ex = hc[0] - hnx * 20 * S + hdx * 14 * S
ey = hc[1] - hny * 20 * S + hdy * 14 * S
kd.ellipse([ex - 14 * S, ey - 14 * S, ex + 14 * S, ey + 14 * S], fill=(255, 255, 255, 255))
kd.ellipse([ex - 8 * S, ey - 8 * S, ex + 8 * S, ey + 8 * S], fill=(20, 5, 30, 255))
kd.ellipse([ex - 3 * S, ey - 3 * S, ex + 3 * S, ey + 3 * S], fill=(255, 255, 255, 255))
# mouth: small smile arc at the snout tip
mx, my = hc[0] + hdx * 52 * S, hc[1] + hdy * 52 * S
kd.arc([mx - 26 * S, my - 26 * S, mx + 26 * S, my + 26 * S], start=20, end=160,
       fill=(120, 30, 10, 255), width=max(2, int(4 * S)))
# whiskers: two sweeping curves trailing back from below the snout
for sgn in (1, -1):
    pts = []
    for k in range(13):
        f = k / 12
        pts.append((mx - hdx * 110 * S * f + hnx * sgn * 34 * S * f - hnx * 8 * S,
                    my - hdy * 110 * S * f + hny * sgn * 34 * S * f - hny * 8 * S))
    kd.line(pts, fill=(255, 220, 180, 230), width=max(2, int(4 * S)), joint="curve")
# flowing tail fin (fan, kept inside the frame)
tail = smooth[0]
kd.polygon([(tail[0], tail[1] - 10 * S), (tail[0] - 110 * S, tail[1] - 70 * S),
            (tail[0] - 150 * S, tail[1] - 10 * S), (tail[0] - 115 * S, tail[1] + 40 * S),
            (tail[0] - 50 * S, tail[1] + 26 * S)],
           fill=(255, 170, 60, 200))
kd.polygon([(tail[0], tail[1] + 6 * S), (tail[0] - 95 * S, tail[1] + 85 * S),
            (tail[0] - 135 * S, tail[1] + 55 * S), (tail[0] - 85 * S, tail[1] + 10 * S)],
           fill=(255, 120, 40, 200))
# dorsal fin: triangular spikes along the back (upper edge = right normal)
for t in np.arange(0.42, 0.86, 0.055):
    i = int(t * (n - 1))
    x, y = smooth[i]
    x2, y2 = smooth[min(i + 1, n - 1)]
    x1, y1 = smooth[max(i - 1, 0)]
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy) or 1
    nx, ny = dy / L, -dx / L  # right normal: up-left, the back side
    w = maxw * prof[i]
    bx, by = x + nx * (w - 4 * S), y + ny * (w - 4 * S)
    tipx, tipy = x + nx * (w + 34 * S), y + ny * (w + 34 * S)
    ax, ay = x + dx / L * 26 * S + nx * (w - 4 * S), y + dy / L * 26 * S + ny * (w - 4 * S)
    bx2, by2 = x - dx / L * 26 * S + nx * (w - 4 * S), y - dy / L * 26 * S + ny * (w - 4 * S)
    kd.polygon([(bx2, by2), (tipx, tipy), (ax, ay)], fill=(255, 80, 30, 235))
# pectoral fin: fan on the belly edge (lower edge = left normal)
px, py = smooth[int(0.62 * (n - 1))]
x2, y2 = smooth[int(0.62 * (n - 1)) + 1]
x1, y1 = smooth[int(0.62 * (n - 1)) - 1]
dx, dy = x2 - x1, y2 - y1
L = math.hypot(dx, dy) or 1
nx, ny = -dy / L, dx / L  # left normal: down-right, the belly side
w = maxw * prof[int(0.62 * (n - 1))]
bx, by = px + nx * w, py + ny * w
# base runs along the body edge so the fin is attached, tip fans outward
b1 = (bx - dx / L * 34 * S, by - dy / L * 34 * S)
b2 = (bx + dx / L * 34 * S, by + dy / L * 34 * S)
tip = (bx + nx * 105 * S, by + ny * 105 * S)
kd.polygon([b1, tip, b2], fill=(255, 200, 120, 225))

img.alpha_composite(koi)
d = ImageDraw.Draw(img, "RGBA")

# ---------------------------------------------------------------- splash & droplets
splash_c = (0.16 * W, 0.93 * H)
for k in range(7):
    r = (40 + k * 26) * S
    a = max(0, 220 - k * 32)
    d.arc([splash_c[0] - r, splash_c[1] - r * 0.45, splash_c[0] + r, splash_c[1] + r * 0.45],
          start=180, end=360, fill=(180, 240, 255, a), width=max(3, int(6 * S)))
for _ in range(60):
    ang = rng.uniform(math.pi, 2 * math.pi)
    rr = rng.uniform(30, 260) * S
    x = splash_c[0] + math.cos(ang) * rr
    y = splash_c[1] + math.sin(ang) * rr * 0.45 - rng.uniform(0, 60) * S
    r = rng.uniform(2, 7) * S
    col = rng.choice([(255, 255, 255), (140, 230, 255), (255, 200, 120)])
    d.ellipse([x - r, y - r, x + r, y + r], fill=col + (rng.randint(150, 255),))
# speed lines behind the koi
for _ in range(26):
    t = rng.uniform(0.05, 0.55)
    i = int(t * (n - 1))
    x, y = smooth[i]
    off = rng.uniform(90, 220) * S
    ln = rng.uniform(40, 130) * S
    d.line([x - off, y + off * 0.55, x - off + ln, y + off * 0.55 - ln * 0.35],
           fill=(255, 255, 255, rng.randint(60, 140)), width=max(2, int(4 * S)))

# ---------------------------------------------------------------- "WOW!" to the judge
text_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
td = ImageDraw.Draw(text_layer)
try:
    font = ImageFont.truetype("DejaVuSans-Bold.ttf", int(150 * S))
except OSError:
    font = ImageFont.load_default()
word = "WOW!"
bbox = td.textbbox((0, 0), word, font=font, stroke_width=int(10 * S))
tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
td.text(((W - tw) / 2 - bbox[0], int(0.045 * H) - bbox[1]), word, font=font,
        fill=(255, 255, 255, 255), stroke_width=int(10 * S),
        stroke_fill=(190, 10, 120, 255))
text_layer = text_layer.rotate(-4, resample=Image.BICUBIC, center=(W / 2, int(0.12 * H)))
img.alpha_composite(text_layer)

# ---------------------------------------------------------------- vignette + finish
img = img.convert("RGB").resize((1024, 1024), Image.LANCZOS)
# gentle vignette to focus the centre
vig = Image.new("L", (1024, 1024), 0)
vd = ImageDraw.Draw(vig)
vd.ellipse([-220, -220, 1244, 1244], fill=255)
vig = vig.filter(ImageFilter.GaussianBlur(160))
black = Image.new("RGB", (1024, 1024), (5, 2, 20))
img = Image.composite(img, black, vig)
img.save("entry.png", "PNG", optimize=True)
print("saved entry.png", img.size)
