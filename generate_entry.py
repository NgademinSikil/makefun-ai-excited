#!/usr/bin/env python3
"""Rebuild entry.png for make.fun bounty ai-excited-01 (recorded rebuild).

The artwork — "WOW! Koi", a luminous koi leaping out of a neon ocean
toward a blazing synthwave sun — is painted procedurally with Pillow and
numpy. Every random draw comes from one seed, so the picture is fully
reproducible: running this script twice writes byte-identical PNGs.

Run:  python3 generate_entry.py  ->  entry.png (1024x1024, < 1 MiB)
"""
import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# --- fixed configuration -------------------------------------------------
SCALE = 2            # supersampling: paint at 2048, downscale to 1024
CANVAS = 1024 * SCALE
SEED = 20261116
SEA_LINE = int(0.60 * CANVAS)

# One shared random source for the whole picture. The order in which the
# stages below draw from it is part of the artwork: do not reorder stages.
dice = random.Random(SEED)
np.random.default_rng(SEED)  # reserved; numpy draws use fixed arrays instead


def blend(c0, c1, f):
    """Linear blend of two RGB triples, truncated to integers."""
    return tuple(int(c0[i] + (c1[i] - c0[i]) * f) for i in range(3))


def vertical_gradient(width, height, stops):
    """Image filled with a vertical gradient through [(pos, rgb), ...]."""
    ramp = np.linspace(0, 1, height)
    buf = np.zeros((height, width, 3), dtype=np.uint8)
    for row in range(height):
        t = ramp[row]
        for j in range(len(stops) - 1):
            (p0, col0), (p1, col1) = stops[j], stops[j + 1]
            if p0 <= t <= p1:
                f = 0 if p1 == p0 else (t - p0) / (p1 - p0)
                buf[row, :, :] = blend(col0, col1, f)
                break
        else:
            buf[row, :, :] = stops[-1][1]
    return Image.fromarray(buf, "RGB")


def fresh_draw(canvas, mode="RGBA"):
    if mode is None:
        return ImageDraw.Draw(canvas)
    return ImageDraw.Draw(canvas, mode)


def paint_sky():
    """Indigo-to-magenta dusk sky with soft nebula blobs and stars."""
    sky = vertical_gradient(CANVAS, CANVAS, [
        (0.00, (8, 8, 46)),      # deep indigo
        (0.30, (48, 16, 96)),    # violet
        (0.48, (150, 24, 122)),  # magenta dusk
        (0.60, (255, 90, 40)),   # burning orange at the horizon
        (1.00, (16, 6, 40)),     # deep sea below (overpainted later)
    ]).convert("RGBA")

    haze = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    hd = fresh_draw(haze)
    for (fx, fy, fr, colour, alpha) in [
        (0.22, 0.16, 0.20, (0, 220, 255), 46),
        (0.82, 0.12, 0.16, (255, 60, 180), 50),
        (0.68, 0.30, 0.13, (255, 180, 60), 34),
        (0.12, 0.38, 0.12, (120, 80, 255), 40),
    ]:
        hd.ellipse([fx * CANVAS - fr * CANVAS, fy * CANVAS - fr * CANVAS,
                    fx * CANVAS + fr * CANVAS, fy * CANVAS + fr * CANVAS],
                   fill=colour + (alpha,))
    haze = haze.filter(ImageFilter.GaussianBlur(90 * SCALE))
    sky.alpha_composite(haze)

    pen = fresh_draw(sky)
    for _ in range(260):
        x = dice.uniform(0, CANVAS)
        y = dice.uniform(0, SEA_LINE * 0.75)
        r = dice.uniform(0.8, 2.6) * SCALE
        a = dice.randint(140, 255)
        pen.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, a))
        if dice.random() < 0.12:  # cross sparkle
            arm = r * 4
            pen.line([x - arm, y, x + arm, y], fill=(255, 255, 255, a // 2),
                     width=max(1, int(SCALE)))
            pen.line([x, y - arm, x, y + arm], fill=(255, 255, 255, a // 2),
                     width=max(1, int(SCALE)))
    return sky


def paint_sun(canvas):
    """Blazing synthwave sun with glow, gradient disc and dark slats."""
    cx, cy = 512 * SCALE, 490 * SCALE
    radius = 200 * SCALE

    halo = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    hd = fresh_draw(halo)
    hd.ellipse([cx - radius * 1.45, cy - radius * 1.45,
                cx + radius * 1.45, cy + radius * 1.45],
               fill=(255, 120, 40, 90))
    halo = halo.filter(ImageFilter.GaussianBlur(60 * SCALE))
    canvas.alpha_composite(halo)

    side = radius * 2
    disc = np.zeros((side, side, 4), dtype=np.uint8)
    yy, xx = np.mgrid[0:side, 0:side]
    dist = np.sqrt((xx - radius) ** 2 + (yy - radius) ** 2) / radius
    inside = dist <= 1.0
    up = np.clip(1 - yy / side, 0, 1)  # 1 at top -> 0 at bottom
    warm_top = np.array([255, 240, 120], dtype=float)
    warm_mid = np.array([255, 140, 40], dtype=float)
    warm_bot = np.array([255, 40, 110], dtype=float)
    shade = np.where((up > 0.5)[..., None],
                     warm_top + (warm_mid - warm_top) * (1 - up)[..., None] * 2,
                     warm_mid + (warm_bot - warm_mid) * (0.5 - up)[..., None] * 2)
    disc[..., :3] = shade.astype(np.uint8)
    disc[..., 3] = np.where(inside, 255, 0).astype(np.uint8)
    canvas.alpha_composite(Image.fromarray(disc, "RGBA"), (cx - radius, cy - radius))

    pen = fresh_draw(canvas)
    for (y0, thick) in [(0.55, 0.012), (0.63, 0.017), (0.72, 0.024), (0.82, 0.032)]:
        y = cy - radius + int(y0 * 2 * radius)
        half = int(math.sqrt(max(0, radius ** 2 - (y - cy) ** 2)))
        pen.rectangle([cx - half, y, cx + half, y + int(thick * CANVAS)],
                      fill=(16, 6, 40, 255))
    return canvas


def paint_mountains(canvas):
    """Two dark ridgelines silhouetted against the sunset."""
    pen = fresh_draw(canvas)

    def ridge(base_y, amp, colour, seed):
        local = random.Random(seed)
        pts = [(0, CANVAS)]
        x, y = 0, base_y
        while x < CANVAS:
            pts.append((x, y))
            x += local.randint(60, 150) * SCALE
            y = base_y + local.randint(-amp, amp) * SCALE
        pts += [(CANVAS, CANVAS), (CANVAS, base_y)]
        pen.polygon(pts, fill=colour)

    ridge(int(0.585 * CANVAS), 26, (52, 14, 88, 255), 7)
    ridge(int(0.605 * CANVAS), 18, (30, 8, 58, 255), 21)
    return canvas


def paint_ocean(canvas):
    """Dark sea with a shimmering sun-reflection column."""
    sea = vertical_gradient(CANVAS, CANVAS - SEA_LINE, [
        (0.00, (64, 16, 90)),
        (0.25, (24, 10, 70)),
        (1.00, (6, 4, 34)),
    ])
    canvas.paste(sea, (0, SEA_LINE))

    sun_x = 512 * SCALE
    refl = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    rd = fresh_draw(refl)
    for i in range(42):
        y = SEA_LINE + int(i * (CANVAS - SEA_LINE) / 42) + dice.randint(-3, 3) * SCALE
        wob = dice.uniform(-1, 1)
        half = (26 + i * 2.6) * SCALE
        mid = sun_x + wob * half * 0.35
        a = max(0, 170 - i * 4)
        col = (255, 150 + i, 60, a) if i < 22 else (255, 110, 150, a // 2)
        rd.line([mid - half, y, mid + half, y], fill=col, width=max(3, int(5 * SCALE)))
    refl = refl.filter(ImageFilter.GaussianBlur(6 * SCALE))
    canvas.alpha_composite(refl)

    pen = fresh_draw(canvas)
    for _ in range(70):
        y = dice.uniform(SEA_LINE + 10, CANVAS - 20)
        x = dice.uniform(0, CANVAS)
        ln = dice.uniform(20, 160) * SCALE
        col = dice.choice([(0, 220, 255), (255, 120, 200), (255, 220, 120)])
        pen.line([x, y, x + ln, y], fill=col + (dice.randint(40, 130),),
                 width=max(1, int(2 * SCALE)))
    return canvas


def smooth_spine(points, samples=24):
    """Catmull-Rom spline through the control points."""
    padded = [points[0]] + points + [points[-1]]
    out = []
    for i in range(len(padded) - 3):
        p0, p1, p2, p3 = padded[i], padded[i + 1], padded[i + 2], padded[i + 3]
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


def paint_koi(canvas):
    """The hero koi: glowing body, gradient belly, head, fins and tail."""
    # Spine from tail (lower-left, in the water) to head (upper-right).
    spine = [(x * CANVAS, y * CANVAS) for x, y in [
        (0.16, 0.94), (0.24, 0.88), (0.34, 0.79), (0.46, 0.69),
        (0.58, 0.59), (0.69, 0.50), (0.78, 0.43), (0.84, 0.38),
    ]]
    # Half-widths at 1024 scale (kept for reference; the profile below rules).
    _widths = [w * SCALE for w in [26, 44, 62, 74, 78, 70, 56, 40]]

    smooth = smooth_spine(spine)
    n = len(smooth)
    # Width profile: taper at both ends, fat in the middle.
    prof = [math.sin(math.pi * (0.12 + 0.76 * i / (n - 1))) ** 0.9
            for i in range(n)]
    maxw = 108 * SCALE
    left, right = [], []
    for i, (x, y) in enumerate(smooth):
        x2, y2 = smooth[min(i + 1, n - 1)]
        x1, y1 = smooth[max(i - 1, 0)]
        dx, dy = x2 - x1, y2 - y1
        length = math.hypot(dx, dy) or 1
        nx, ny = -dy / length, dx / length
        w = maxw * prof[i]
        left.append((x + nx * w, y + ny * w))
        right.append((x - nx * w, y - ny * w))
    body_poly = left + right[::-1]

    koi = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    kd = fresh_draw(koi)
    kd.polygon(body_poly, fill=(255, 120, 40, 255))
    canvas.alpha_composite(koi.filter(ImageFilter.GaussianBlur(26 * SCALE)))

    # Body fill: vertical gradient, orange back -> pale belly.
    grad = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    ga = np.zeros((CANVAS, CANVAS, 4), dtype=np.uint8)
    c_top = np.array([255, 90, 20], dtype=float)
    c_mid = np.array([255, 190, 80], dtype=float)
    c_bot = np.array([255, 250, 230], dtype=float)
    band_top, band_bot = 0.30 * CANVAS, 0.99 * CANVAS
    f = np.clip((np.arange(CANVAS)[:, None] - band_top) / (band_bot - band_top), 0, 1)
    col = np.where((f < 0.5)[..., None],
                   c_top + (c_mid - c_top) * (f * 2)[..., None],
                   c_mid + (c_bot - c_mid) * ((f - 0.5) * 2)[..., None])
    ga[..., :3] = np.repeat(col.astype(np.uint8), CANVAS, axis=1)
    mask = Image.new("L", (CANVAS, CANVAS), 0)
    md = fresh_draw(mask, None)
    md.polygon(body_poly, fill=255)
    ga[..., 3] = np.array(mask)
    koi.alpha_composite(Image.fromarray(ga, "RGBA"))

    kd = fresh_draw(koi)
    kd.line(left + [left[0]], fill=(40, 8, 40, 255),
            width=max(3, int(5 * SCALE)), joint="curve")
    kd.line(right + [right[0]], fill=(40, 8, 40, 255),
            width=max(3, int(5 * SCALE)), joint="curve")
    # Back patches along the top edge only.
    for t, r in [(0.38, 0.035), (0.55, 0.042), (0.70, 0.032)]:
        i = int(t * (n - 1))
        x, y = smooth[i]
        kd.ellipse([x - r * CANVAS, y - r * CANVAS * 0.5,
                    x + r * CANVAS, y + r * CANVAS * 0.5],
                   fill=(214, 40, 20, 235))
    # Scale arcs.
    for t in np.arange(0.25, 0.9, 0.07):
        i = int(t * (n - 1))
        x, y = smooth[i]
        r = maxw * prof[i] * 0.55
        kd.arc([x - r, y - r * 0.6, x + r, y + r * 0.6], start=200, end=340,
               fill=(180, 40, 10, 160), width=max(2, int(3 * SCALE)))

    # --- rounded head cap, oriented along the spine ---
    hx, hy = smooth[-1]
    px0, py0 = smooth[-6]
    hdx, hdy = hx - px0, hy - py0
    hL = math.hypot(hdx, hdy) or 1
    hdx, hdy = hdx / hL, hdy / hL          # head direction (up-right)
    hnx, hny = -hdy, hdx                  # left normal (up-left, visible side)
    hc = (hx + hdx * 34 * SCALE, hy + hdy * 34 * SCALE)
    head_layer = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    hd = fresh_draw(head_layer)
    hd.ellipse([hc[0] - 62 * SCALE, hc[1] - 52 * SCALE,
                hc[0] + 62 * SCALE, hc[1] + 52 * SCALE],
               fill=(255, 165, 60, 255))
    hd.ellipse([hc[0] - 62 * SCALE, hc[1] + 2 * SCALE,
                hc[0] + 62 * SCALE, hc[1] + 52 * SCALE],
               fill=(255, 235, 200, 255))
    ang = -math.degrees(math.atan2(hdy, hdx))
    head_layer = head_layer.rotate(ang, resample=Image.BICUBIC, center=hc)
    koi.alpha_composite(head_layer)

    kd = fresh_draw(koi)
    # Eye, on the upper (back) side of the head.
    ex = hc[0] - hnx * 20 * SCALE + hdx * 14 * SCALE
    ey = hc[1] - hny * 20 * SCALE + hdy * 14 * SCALE
    kd.ellipse([ex - 14 * SCALE, ey - 14 * SCALE, ex + 14 * SCALE, ey + 14 * SCALE],
               fill=(255, 255, 255, 255))
    kd.ellipse([ex - 8 * SCALE, ey - 8 * SCALE, ex + 8 * SCALE, ey + 8 * SCALE],
               fill=(20, 5, 30, 255))
    kd.ellipse([ex - 3 * SCALE, ey - 3 * SCALE, ex + 3 * SCALE, ey + 3 * SCALE],
               fill=(255, 255, 255, 255))
    # Mouth: small smile arc at the snout tip.
    mx, my = hc[0] + hdx * 52 * SCALE, hc[1] + hdy * 52 * SCALE
    kd.arc([mx - 26 * SCALE, my - 26 * SCALE, mx + 26 * SCALE, my + 26 * SCALE],
           start=20, end=160, fill=(120, 30, 10, 255), width=max(2, int(4 * SCALE)))
    # Whiskers: two sweeping curves trailing back from below the snout.
    for sgn in (1, -1):
        pts = []
        for k in range(13):
            f = k / 12
            pts.append((mx - hdx * 110 * SCALE * f + hnx * sgn * 34 * SCALE * f - hnx * 8 * SCALE,
                        my - hdy * 110 * SCALE * f + hny * sgn * 34 * SCALE * f - hny * 8 * SCALE))
        kd.line(pts, fill=(255, 220, 180, 230), width=max(2, int(4 * SCALE)),
                joint="curve")
    # Flowing tail fin (fan, kept inside the frame).
    tail = smooth[0]
    kd.polygon([(tail[0], tail[1] - 10 * SCALE),
                (tail[0] - 110 * SCALE, tail[1] - 70 * SCALE),
                (tail[0] - 150 * SCALE, tail[1] - 10 * SCALE),
                (tail[0] - 115 * SCALE, tail[1] + 40 * SCALE),
                (tail[0] - 50 * SCALE, tail[1] + 26 * SCALE)],
               fill=(255, 170, 60, 200))
    kd.polygon([(tail[0], tail[1] + 6 * SCALE),
                (tail[0] - 95 * SCALE, tail[1] + 85 * SCALE),
                (tail[0] - 135 * SCALE, tail[1] + 55 * SCALE),
                (tail[0] - 85 * SCALE, tail[1] + 10 * SCALE)],
               fill=(255, 120, 40, 200))
    # Dorsal fin: triangular spikes along the back (right normal = up-left).
    for t in np.arange(0.42, 0.86, 0.055):
        i = int(t * (n - 1))
        x, y = smooth[i]
        x2, y2 = smooth[min(i + 1, n - 1)]
        x1, y1 = smooth[max(i - 1, 0)]
        dx, dy = x2 - x1, y2 - y1
        length = math.hypot(dx, dy) or 1
        nx, ny = dy / length, -dx / length
        w = maxw * prof[i]
        bx, by = x + nx * (w - 4 * SCALE), y + ny * (w - 4 * SCALE)
        tipx, tipy = x + nx * (w + 34 * SCALE), y + ny * (w + 34 * SCALE)
        ax, ay = (x + dx / length * 26 * SCALE + nx * (w - 4 * SCALE),
                  y + dy / length * 26 * SCALE + ny * (w - 4 * SCALE))
        bx2, by2 = (x - dx / length * 26 * SCALE + nx * (w - 4 * SCALE),
                    y - dy / length * 26 * SCALE + ny * (w - 4 * SCALE))
        kd.polygon([(bx2, by2), (tipx, tipy), (ax, ay)], fill=(255, 80, 30, 235))
    # Pectoral fin: fan on the belly edge (left normal = down-right).
    j = int(0.62 * (n - 1))
    px, py = smooth[j]
    x2, y2 = smooth[j + 1]
    x1, y1 = smooth[j - 1]
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy) or 1
    nx, ny = -dy / length, dx / length
    w = maxw * prof[j]
    bx, by = px + nx * w, py + ny * w
    b1 = (bx - dx / length * 34 * SCALE, by - dy / length * 34 * SCALE)
    b2 = (bx + dx / length * 34 * SCALE, by + dy / length * 34 * SCALE)
    tip = (bx + nx * 105 * SCALE, by + ny * 105 * SCALE)
    kd.polygon([b1, tip, b2], fill=(255, 200, 120, 225))

    canvas.alpha_composite(koi)
    return canvas, smooth, n


def paint_splash(canvas, smooth, n):
    """Splash rings, droplets and speed lines around the leaping koi."""
    pen = fresh_draw(canvas)
    splash_c = (0.16 * CANVAS, 0.93 * CANVAS)
    for k in range(7):
        r = (40 + k * 26) * SCALE
        a = max(0, 220 - k * 32)
        pen.arc([splash_c[0] - r, splash_c[1] - r * 0.45,
                 splash_c[0] + r, splash_c[1] + r * 0.45],
                start=180, end=360, fill=(180, 240, 255, a),
                width=max(3, int(6 * SCALE)))
    for _ in range(60):
        ang = dice.uniform(math.pi, 2 * math.pi)
        rr = dice.uniform(30, 260) * SCALE
        x = splash_c[0] + math.cos(ang) * rr
        y = splash_c[1] + math.sin(ang) * rr * 0.45 - dice.uniform(0, 60) * SCALE
        r = dice.uniform(2, 7) * SCALE
        col = dice.choice([(255, 255, 255), (140, 230, 255), (255, 200, 120)])
        pen.ellipse([x - r, y - r, x + r, y + r],
                    fill=col + (dice.randint(150, 255),))
    for _ in range(26):
        t = dice.uniform(0.05, 0.55)
        i = int(t * (n - 1))
        x, y = smooth[i]
        off = dice.uniform(90, 220) * SCALE
        ln = dice.uniform(40, 130) * SCALE
        pen.line([x - off, y + off * 0.55, x - off + ln, y + off * 0.55 - ln * 0.35],
                 fill=(255, 255, 255, dice.randint(60, 140)),
                 width=max(2, int(4 * SCALE)))
    return canvas


def paint_title(canvas):
    """Big tilted WOW! for the judge, top centre."""
    text_layer = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    td = fresh_draw(text_layer)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", int(150 * SCALE))
    except OSError:
        font = ImageFont.load_default()
    word = "WOW!"
    bbox = td.textbbox((0, 0), word, font=font, stroke_width=int(10 * SCALE))
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    td.text(((CANVAS - tw) / 2 - bbox[0], int(0.045 * CANVAS) - bbox[1]), word,
            font=font, fill=(255, 255, 255, 255), stroke_width=int(10 * SCALE),
            stroke_fill=(190, 10, 120, 255))
    text_layer = text_layer.rotate(-4, resample=Image.BICUBIC,
                                   center=(CANVAS / 2, int(0.12 * CANVAS)))
    canvas.alpha_composite(text_layer)
    return canvas


def finish(canvas):
    """Downscale to 1024, add a gentle vignette, save as entry.png."""
    img = canvas.convert("RGB").resize((1024, 1024), Image.LANCZOS)
    vig = Image.new("L", (1024, 1024), 0)
    vd = ImageDraw.Draw(vig)
    vd.ellipse([-220, -220, 1244, 1244], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(160))
    black = Image.new("RGB", (1024, 1024), (5, 2, 20))
    img = Image.composite(img, black, vig)
    img.save("entry.png", "PNG", optimize=True)
    print("saved entry.png", img.size)


def main():
    canvas = paint_sky()
    canvas = paint_sun(canvas)
    canvas = paint_mountains(canvas)
    canvas = paint_ocean(canvas)
    canvas, smooth, n = paint_koi(canvas)
    canvas = paint_splash(canvas, smooth, n)
    canvas = paint_title(canvas)
    finish(canvas)


if __name__ == "__main__":
    main()
