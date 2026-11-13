#!/usr/bin/env python3
"""World News of Friday 13 November 2026 -- make.fun news-image-01 entry.

Draws a single 1024x1024 PNG with nothing but the Python 3 standard
library (zlib for the PNG encoder). No files are read, no network is
touched, and a fixed seed makes the output byte-identical on every run.

The scene: a picture-editor front page of the day. A large globe at dusk
fills the centre, a white dove carrying an olive branch rising over it
for the day's lead story -- the Ukraine peace talks in Moscow. Around
the globe, seven gold-rimmed medallions carry the day's other stories
as plain pictorial symbols: a falling stock chart with a chip (Nvidia's
CEO resigned, shares down ~16%), a darkened envelope with a warning
mark (the global Microsoft Mail and Teams outage), a hospital cross
with a candle (the strike on a Khan Younis hospital), a storm cloud
with rain over waves (Storm Charles over Portugal), a football
(England beating Croatia into the Nations League quarter-finals), an
LNG tanker beside a sea mine (the tanker hit in the Strait of Hormuz),
and a pair of smart glasses (Google's Gemini 4 Hydrogen and its
smart-glasses preorders). Big flat shapes, a restrained palette of
deep blue night and warm gold, no text -- it has to read at a glance
and still land at ~300 px.
"""

import math
import os
import struct
import zlib
from random import Random

SIZE = 1024
SEED = 20261113

GLOBE_CX, GLOBE_CY, GLOBE_R = 512, 480, 260


# ---------------------------------------------------------------- palette
class Pal:
    SKY = [  # (stop, rgb) gradient, top -> bottom
        (0.00, (7, 10, 38)),
        (0.45, (17, 23, 64)),
        (0.75, (44, 38, 88)),
        (1.00, (96, 52, 84)),
    ]
    STAR = (235, 238, 255)
    GOLD = (232, 178, 84)
    GOLD_LT = (247, 210, 130)
    GOLD_DK = (176, 124, 46)
    GLOW = (255, 196, 110)
    OCEAN_HI = (30, 72, 132)
    OCEAN_LO = (14, 38, 84)
    LAND = (206, 172, 96)
    LAND_GREEN = (116, 158, 104)
    SHADE = (8, 18, 48)
    HIGHLIGHT = (190, 215, 245)
    DOVE = (248, 247, 242)
    DOVE_SHADE = (205, 205, 198)
    DOVE_INK = (38, 38, 44)
    BEAK = (232, 164, 60)
    LEAF = (96, 140, 74)
    MEDAL = (15, 25, 58)
    MEDAL_DK = (10, 17, 42)
    CHART_GREEN = (64, 196, 110)
    CHART_DK = (24, 90, 56)
    CHIP = (32, 40, 64)
    ENVELOPE = (96, 104, 132)
    ENVELOPE_DK = (58, 62, 88)
    WARN = (240, 170, 40)
    WARN_DK = (180, 110, 20)
    CROSS = (244, 244, 240)
    HOSPITAL_BG = (38, 84, 96)
    CANDLE = (240, 232, 210)
    FLAME = (244, 150, 52)
    FLAME_CORE = (255, 214, 110)
    CLOUD = (74, 80, 104)
    CLOUD_DK = (50, 54, 76)
    RAIN = (120, 170, 230)
    WAVE = (70, 130, 190)
    BALL = (246, 246, 240)
    BALL_INK = (30, 30, 36)
    TANKER = (52, 58, 78)
    TANKER_RED = (176, 52, 44)
    MINE = (24, 24, 30)
    BURST = (244, 120, 40)
    GLASS = (58, 74, 110)
    GLASS_LT = (150, 190, 235)


# ---------------------------------------------------------------- canvas
class Canvas:
    """A flat RGB buffer with a few scanline drawing primitives."""

    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)

    def hline(self, y, x0, x1, rgb):
        if y < 0 or y >= self.h:
            return
        x0 = max(0, int(x0))
        x1 = min(self.w - 1, int(x1))
        if x1 < x0:
            return
        n = x1 - x0 + 1
        i = (y * self.w + x0) * 3
        self.px[i:i + 3 * n] = bytes(rgb) * n

    def hline_alpha(self, y, x0, x1, rgb, alpha):
        if y < 0 or y >= self.h or alpha <= 0.0:
            return
        if alpha >= 1.0:
            self.hline(y, x0, x1, rgb)
            return
        x0 = max(0, int(x0))
        x1 = min(self.w - 1, int(x1))
        if x1 < x0:
            return
        a = int(alpha * 256)
        ia = 256 - a
        r, g, b = rgb
        i = (y * self.w + x0) * 3
        for _ in range(x1 - x0 + 1):
            self.px[i] = (r * a + self.px[i] * ia) >> 8
            self.px[i + 1] = (g * a + self.px[i + 1] * ia) >> 8
            self.px[i + 2] = (b * a + self.px[i + 2] * ia) >> 8
            i += 3

    def dot(self, x, y, rgb, alpha=1.0):
        if 0 <= x < self.w and 0 <= y < self.h and alpha > 0.0:
            a = int(alpha * 256)
            ia = 256 - a
            i = (y * self.w + x) * 3
            self.px[i] = (rgb[0] * a + self.px[i] * ia) >> 8
            self.px[i + 1] = (rgb[1] * a + self.px[i + 1] * ia) >> 8
            self.px[i + 2] = (rgb[2] * a + self.px[i + 2] * ia) >> 8

    def disc(self, cx, cy, r, rgb, alpha=1.0):
        r = int(r)
        for y in range(max(0, cy - r), min(self.h - 1, cy + r) + 1):
            dy = y - cy
            dx = int(math.sqrt(max(0, r * r - dy * dy)))
            self.hline_alpha(y, cx - dx, cx + dx, rgb, alpha)

    def ellipse(self, cx, cy, rx, ry, rgb, alpha=1.0):
        rx, ry = int(rx), int(ry)
        for y in range(max(0, cy - ry), min(self.h - 1, cy + ry) + 1):
            t = (y - cy) / ry
            dx = int(rx * math.sqrt(max(0.0, 1.0 - t * t)))
            self.hline_alpha(y, cx - dx, cx + dx, rgb, alpha)

    def poly(self, pts, rgb, alpha=1.0):
        """Scanline polygon fill."""
        edges = []
        n = len(pts)
        for i in range(n):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % n]
            if y0 != y1:
                edges.append((y0, y1, x0, x1))
        ymin = max(0, int(min(p[1] for p in pts)))
        ymax = min(self.h - 1, int(max(p[1] for p in pts)))
        for y in range(ymin, ymax + 1):
            xs = []
            for y0, y1, x0, x1 in edges:
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) / (y1 - y0) * (x1 - x0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.hline_alpha(y, math.ceil(xs[i]), math.floor(xs[i + 1]),
                                 rgb, alpha)

    def glow(self, cx, cy, r, rgb, peak):
        """Soft radial glow, quadratic falloff."""
        r2 = r * r
        R, G, B = rgb
        for y in range(max(0, cy - r), min(self.h - 1, cy + r) + 1):
            dy = y - cy
            dy2 = dy * dy
            span = int(math.sqrt(max(0, r2 - dy2)))
            for x in range(max(0, cx - span), min(self.w - 1, cx + span) + 1):
                dx = x - cx
                f = 1.0 - (dx * dx + dy2) / r2
                if f <= 0.0:
                    continue
                a = int(peak * f * f * 256)
                if a <= 0:
                    continue
                ia = 256 - a
                i = (y * self.w + x) * 3
                self.px[i] = (R * a + self.px[i] * ia) >> 8
                self.px[i + 1] = (G * a + self.px[i + 1] * ia) >> 8
                self.px[i + 2] = (B * a + self.px[i + 2] * ia) >> 8

    def thick_polyline(self, pts, radius, rgb, alpha=1.0):
        for x, y in pts:
            self.disc(x, y, radius, rgb, alpha)

    def ring(self, cx, cy, r, thick, rgb, alpha=1.0):
        pts = []
        for k in range(360):
            th = 2 * math.pi * k / 360
            pts.append((int(cx + r * math.cos(th)), int(cy + r * math.sin(th))))
        self.thick_polyline(pts, thick, rgb, alpha)


def quad_bezier(p0, p1, p2, steps):
    pts = []
    for i in range(steps + 1):
        t = i / steps
        u = 1.0 - t
        pts.append((
            int(u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0]),
            int(u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]),
        ))
    return pts


def lerp_stops(stops, t):
    for i in range(len(stops) - 1):
        t0, c0 = stops[i]
        t1, c1 = stops[i + 1]
        if t <= t1:
            f = 0.0 if t1 == t0 else (t - t0) / (t1 - t0)
            return tuple(int(c0[k] + (c1[k] - c0[k]) * f) for k in range(3))
    return stops[-1][1]


def rotated_ellipse_pts(cx, cy, rx, ry, angle_deg, n=36):
    ang = math.radians(angle_deg)
    ca, sa = math.cos(ang), math.sin(ang)
    pts = []
    for k in range(n):
        th = 2 * math.pi * k / n
        ex, ey = rx * math.cos(th), ry * math.sin(th)
        pts.append((int(cx + ex * ca - ey * sa),
                    int(cy + ex * sa + ey * ca)))
    return pts


# ---------------------------------------------------------------- scene
def paint_sky(cv):
    for y in range(SIZE):
        cv.hline(y, 0, SIZE - 1, lerp_stops(Pal.SKY, y / SIZE))


def paint_stars(cv, rng):
    for _ in range(150):
        x = rng.randrange(0, SIZE)
        y = rng.randrange(0, 980)
        # keep stars out of the globe and the dove
        if (x - GLOBE_CX) ** 2 + (y - GLOBE_CY) ** 2 < 300 ** 2:
            continue
        if 380 < x < 660 and 30 < y < 250:
            continue
        b = rng.choice([150, 180, 210, 235, 255])
        cv.disc(x, y, rng.choice([1, 1, 1, 2]),
                (b, b, min(255, b + 15)), rng.uniform(0.35, 0.9))


# ------------------------------------------------------------ the globe
CONTINENTS = [
    # North America
    [(-218, -92), (-186, -148), (-128, -166), (-78, -142), (-58, -96),
     (-92, -62), (-138, -46), (-192, -50)],
    # Greenland
    [(-108, -196), (-82, -200), (-72, -182), (-92, -172)],
    # South America
    [(-152, 28), (-122, 8), (-86, 24), (-80, 88), (-104, 150),
     (-140, 142), (-162, 82)],
    # Africa
    [(8, -62), (58, -82), (96, -42), (86, 28), (46, 92), (4, 72), (-16, 2)],
    # Eurasia
    [(58, -142), (128, -172), (208, -142), (226, -82), (182, -58),
     (140, -94), (94, -112)],
    # Australia
    [(148, 88), (198, 82), (216, 118), (172, 142), (144, 118)],
]


def paint_globe(cv):
    cv.glow(GLOBE_CX, GLOBE_CY + 30, 420, Pal.GLOW, 0.16)
    # ocean, darker toward the bottom
    for y in range(GLOBE_CY - GLOBE_R, GLOBE_CY + GLOBE_R + 1):
        dy = y - GLOBE_CY
        dx = int(math.sqrt(max(0, GLOBE_R * GLOBE_R - dy * dy)))
        t = (y - (GLOBE_CY - GLOBE_R)) / (2 * GLOBE_R)
        c = tuple(int(Pal.OCEAN_HI[k] + (Pal.OCEAN_LO[k] - Pal.OCEAN_HI[k]) * t)
                  for k in range(3))
        cv.hline(y, GLOBE_CX - dx, GLOBE_CX + dx, c)
    # sphere shading: dusk shadow on the lower right, light on the upper left
    cv.ellipse(GLOBE_CX + 120, GLOBE_CY + 110, 190, 160, Pal.SHADE, 0.20)
    cv.ellipse(GLOBE_CX - 110, GLOBE_CY - 110, 150, 110, Pal.HIGHLIGHT, 0.10)
    # continents (drawn loose; the clip pass trims them to the disc)
    for pts in CONTINENTS:
        cv.poly([(GLOBE_CX + x, GLOBE_CY + y) for x, y in pts], Pal.LAND)
    # a touch of green on two landmasses
    cv.ellipse(GLOBE_CX + 40, GLOBE_CY + 10, 26, 18, Pal.LAND_GREEN, 0.85)
    cv.ellipse(GLOBE_CX + 150, GLOBE_CY - 110, 34, 16, Pal.LAND_GREEN, 0.8)
    # clip pass: repaint sky over anything outside the disc
    for y in range(GLOBE_CY - GLOBE_R - 2, GLOBE_CY + GLOBE_R + 3):
        dy = y - GLOBE_CY
        if abs(dy) > GLOBE_R:
            continue
        dx = int(math.sqrt(max(0, GLOBE_R * GLOBE_R - dy * dy)))
        sky = lerp_stops(Pal.SKY, y / SIZE)
        cv.hline(y, GLOBE_CX - GLOBE_R - 2, GLOBE_CX - dx - 1, sky)
        cv.hline(y, GLOBE_CX + dx + 1, GLOBE_CX + GLOBE_R + 2, sky)
    cv.ring(GLOBE_CX, GLOBE_CY, GLOBE_R, 4, Pal.GOLD, 0.95)


# ------------------------------------------------------------ the dove
def paint_dove(cv):
    # Tail feathers fanning left, behind the body
    for dx, dy, ln in [(-58, 26, 66), (-66, 8, 74), (-58, -10, 62)]:
        tip = (452 + dx, 168 + dy)
        cv.poly([(452, 158), (452, 178), tip], Pal.DOVE_SHADE, 0.95)
    # Raised wing sweeping up-left
    cv.poly([(468, 152), (404, 42), (358, 56), (396, 124), (448, 170)],
            Pal.DOVE, 0.97)
    cv.poly([(450, 158), (412, 74), (386, 70), (420, 126)], Pal.DOVE_SHADE,
            0.5)
    # Body: long ellipse tilted up to the right
    cv.poly(rotated_ellipse_pts(520, 158, 92, 40, -14), Pal.DOVE)
    # Lower wing folded along the body
    cv.poly([(486, 168), (566, 138), (600, 150), (540, 192), (492, 188)],
            Pal.DOVE_SHADE, 0.9)
    # Head and beak
    cv.disc(606, 122, 24, Pal.DOVE)
    cv.poly([(624, 112), (652, 120), (624, 130)], Pal.BEAK)
    cv.disc(612, 116, 4, Pal.DOVE_INK)
    cv.disc(614, 114, 1, (255, 255, 255))
    # Olive branch in the beak, trailing right and down
    stem = quad_bezier((648, 122), (690, 132), (724, 168), 16)
    cv.thick_polyline(stem, 3, Pal.LEAF, 0.95)
    for lx, ly, ang in [(672, 128, -30), (688, 142, 25), (700, 152, -35),
                        (714, 160, 20)]:
        cv.poly(rotated_ellipse_pts(lx, ly, 16, 6, ang), Pal.LEAF)
    # A few soft motion feathers under the dove
    for x, y, r in [(470, 210, 5), (500, 224, 4), (540, 214, 5)]:
        cv.disc(x, y, r, Pal.DOVE, 0.55)


# ------------------------------------------------------------ medallions
def medallion(cv, cx, cy, r=76):
    cv.disc(cx, cy, r, Pal.GOLD)
    cv.disc(cx, cy, r - 5, Pal.MEDAL)
    cv.disc(cx, cy, r - 5, Pal.MEDAL_DK, 0.25)


def paint_chart(cv, cx, cy):
    # falling green stock line with a chip -- Nvidia
    cv.poly([(cx - 52, cy + 38), (cx + 52, cy + 38), (cx + 52, cy + 52),
             (cx - 52, cy + 52)], Pal.CHART_DK)
    line = quad_bezier((cx - 50, cy - 44), (cx - 8, cy - 30),
                       (cx + 50, cy + 26), 24)
    cv.thick_polyline(line, 5, Pal.CHART_GREEN)
    cv.poly([(cx + 50, cy + 26), (cx + 34, cy + 14), (cx + 46, cy + 34)],
            Pal.CHART_GREEN)
    # chip, lower left
    cv.poly([(cx - 52, cy - 6), (cx - 14, cy - 6), (cx - 14, cy + 30),
             (cx - 52, cy + 30)], Pal.CHIP)
    cv.poly([(cx - 44, cy + 2), (cx - 22, cy + 2), (cx - 22, cy + 22),
             (cx - 44, cy + 22)], Pal.CHART_GREEN)
    for px in (cx - 48, cx - 38, cx - 28, cx - 18):
        cv.hline(cy - 12, px, px + 4, Pal.GOLD)
        cv.hline(cy + 36, px, px + 4, Pal.GOLD)


def paint_envelope(cv, cx, cy):
    # darkened envelope with a warning mark -- Microsoft outage
    cv.poly([(cx - 50, cy - 30), (cx + 50, cy - 30), (cx + 50, cy + 34),
             (cx - 50, cy + 34)], Pal.ENVELOPE)
    cv.poly([(cx - 50, cy - 30), (cx, cy + 2), (cx + 50, cy - 30)],
            Pal.ENVELOPE_DK)
    cv.poly([(cx - 50, cy + 34), (cx - 8, cy + 2), (cx + 8, cy + 2),
             (cx + 50, cy + 34)], Pal.ENVELOPE_DK, 0.6)
    # warning triangle, lower right, overlapping the envelope
    cv.poly([(cx + 8, cy + 44), (cx + 34, cy - 2), (cx + 60, cy + 44)],
            Pal.WARN)
    cv.poly([(cx + 14, cy + 38), (cx + 34, cy + 6), (cx + 54, cy + 38)],
            Pal.WARN_DK)
    cv.hline(cy + 14, cx + 32, cx + 36, Pal.WARN)
    cv.hline(cy + 16, cx + 32, cx + 36, Pal.WARN)
    cv.hline(cy + 18, cx + 32, cx + 36, Pal.WARN)
    cv.hline(cy + 20, cx + 32, cx + 36, Pal.WARN)
    cv.hline(cy + 22, cx + 32, cx + 36, Pal.WARN)
    cv.disc(cx + 34, cy + 30, 3, Pal.WARN)


def paint_hospital(cv, cx, cy):
    # hospital cross with a candle -- Khan Younis
    cv.poly([(cx - 52, cy - 34), (cx + 6, cy - 34), (cx + 6, cy + 34),
             (cx - 52, cy + 34)], Pal.HOSPITAL_BG)
    cv.poly([(cx - 40, cy - 14), (cx - 22, cy - 14), (cx - 22, cy + 14),
             (cx - 40, cy + 14)], Pal.CROSS)
    cv.poly([(cx - 49, cy - 5), (cx - 13, cy - 5), (cx - 13, cy + 5),
             (cx - 49, cy + 5)], Pal.CROSS)
    # candle, right side
    cv.poly([(cx + 26, cy + 2), (cx + 42, cy + 2), (cx + 42, cy + 36),
             (cx + 26, cy + 36)], Pal.CANDLE)
    cv.hline(cy - 4, cx + 33, cx + 35, Pal.DOVE_INK)
    cv.poly([(cx + 34, cy - 26), (cx + 42, cy - 10), (cx + 26, cy - 10)],
            Pal.FLAME)
    cv.poly([(cx + 34, cy - 20), (cx + 39, cy - 10), (cx + 29, cy - 10)],
            Pal.FLAME_CORE)


def paint_storm(cv, cx, cy):
    # storm cloud, rain, waves -- Storm Charles
    for dx, dy, r in [(-28, -18, 26), (0, -28, 32), (28, -16, 26),
                      (-12, -8, 26), (14, -8, 26)]:
        cv.disc(cx + dx, cy + dy, r, Pal.CLOUD)
    cv.disc(cx - 28, cy - 18, 26, Pal.CLOUD_DK, 0.35)
    cv.ellipse(cx, cy + 2, 52, 14, Pal.CLOUD_DK, 0.55)
    for i, x in enumerate((cx - 40, cx - 20, cx, cx + 20, cx + 40)):
        y0 = cy + 16 + (i % 2) * 4
        cv.thick_polyline([(x, y0), (x - 6, y0 + 18)], 3, Pal.RAIN, 0.85)
    for y, a in [(cy + 44, 0.9), (cy + 56, 0.6)]:
        cv.thick_polyline(quad_bezier((cx - 50, y), (cx - 25, y - 8),
                                      (cx, y), 10), 3, Pal.WAVE, a)
        cv.thick_polyline(quad_bezier((cx, y), (cx + 25, y - 8),
                                      (cx + 50, y), 10), 3, Pal.WAVE, a)


def paint_football(cv, cx, cy):
    # football -- England's win over Croatia
    cv.disc(cx, cy, 46, Pal.BALL)
    cv.disc(cx, cy, 46, Pal.BALL_INK, 0.08)
    pent = []
    for k in range(5):
        th = -math.pi / 2 + 2 * math.pi * k / 5
        pent.append((int(cx + 15 * math.cos(th)), int(cy + 15 * math.sin(th))))
    cv.poly(pent, Pal.BALL_INK)
    for k in range(5):
        th = -math.pi / 2 + 2 * math.pi * k / 5
        px, py = cx + 15 * math.cos(th), cy + 15 * math.sin(th)
        ex, ey = cx + 40 * math.cos(th), cy + 40 * math.sin(th)
        cv.thick_polyline([(int(px), int(py)), (int(ex), int(ey))], 2,
                          Pal.BALL_INK, 0.8)
        cv.disc(int(ex), int(ey), 6, Pal.BALL_INK, 0.85)
    cv.ring(cx, cy, 46, 2, Pal.BALL_INK, 0.5)


def paint_tanker(cv, cx, cy):
    # LNG tanker beside a sea mine -- Strait of Hormuz
    cv.poly([(cx - 52, cy - 6), (cx + 52, cy - 6), (cx + 44, cy + 26),
             (cx - 44, cy + 26)], Pal.TANKER)
    cv.poly([(cx - 52, cy - 6), (cx + 52, cy - 6), (cx + 52, cy + 2),
             (cx - 52, cy + 2)], Pal.TANKER_RED)
    for x in (cx - 40, cx - 14, cx + 12):
        cv.poly([(x, cy - 30), (x + 20, cy - 30), (x + 20, cy - 6),
                 (x, cy - 6)], Pal.CHIP)
    cv.poly([(cx + 34, cy - 34), (cx + 44, cy - 34), (cx + 44, cy - 6),
             (cx + 34, cy - 6)], Pal.TANKER)
    # sea mine, upper right
    mx, my = cx + 34, cy - 40
    for ang in range(0, 360, 45):
        th = math.radians(ang)
        cv.thick_polyline(
            [(int(mx + 10 * math.cos(th)), int(my + 10 * math.sin(th))),
             (int(mx + 18 * math.cos(th)), int(my + 18 * math.sin(th)))],
            2, Pal.MINE)
    cv.disc(mx, my, 11, Pal.MINE)
    # burst star between mine and tanker
    bx, by = cx + 12, cy - 44
    for ang in range(0, 360, 45):
        th = math.radians(ang)
        cv.thick_polyline(
            [(bx, by),
             (int(bx + 14 * math.cos(th)), int(by + 14 * math.sin(th)))],
            2, Pal.BURST)
    cv.disc(bx, by, 4, Pal.BURST)
    # waves under the hull
    cv.thick_polyline(quad_bezier((cx - 52, cy + 40), (cx - 25, cy + 32),
                                  (cx, cy + 40), 10), 3, Pal.WAVE, 0.9)
    cv.thick_polyline(quad_bezier((cx, cy + 40), (cx + 25, cy + 32),
                                  (cx + 52, cy + 40), 10), 3, Pal.WAVE, 0.9)


def paint_glasses(cv, cx, cy):
    # smart glasses -- Google's Gemini 4 Hydrogen and glasses preorders
    cv.poly([(cx - 52, cy - 22), (cx - 8, cy - 22), (cx - 8, cy + 18),
             (cx - 52, cy + 18)], Pal.GLASS)
    cv.poly([(cx + 8, cy - 22), (cx + 52, cy - 22), (cx + 52, cy + 18),
             (cx + 8, cy + 18)], Pal.GLASS)
    cv.poly([(cx - 44, cy - 14), (cx - 16, cy - 14), (cx - 16, cy + 10),
             (cx - 44, cy + 10)], Pal.GLASS_LT, 0.85)
    cv.poly([(cx + 16, cy - 14), (cx + 44, cy - 14), (cx + 44, cy + 10),
             (cx + 16, cy + 10)], Pal.GLASS_LT, 0.85)
    cv.hline(cy - 8, cx - 8, cx + 8, Pal.GOLD)
    cv.hline(cy - 6, cx - 8, cx + 8, Pal.GOLD)
    cv.hline(cy - 2, cx - 52, cx - 60, Pal.GOLD)
    cv.hline(cy - 2, cx + 52, cx + 60, Pal.GOLD)
    # sparkle above the right lens
    sx, sy = cx + 30, cy - 40
    cv.poly([(sx, sy - 12), (sx + 3, sy - 3), (sx + 12, sy), (sx + 3, sy + 3),
             (sx, sy + 12), (sx - 3, sy + 3), (sx - 12, sy),
             (sx - 3, sy - 3)], Pal.GOLD_LT)


# ---------------------------------------------------------------- PNG out
def encode_png(cv):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)  # filter: none
        raw += cv.px[y * cv.w * 3:(y + 1) * cv.w * 3]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        return out + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    return png


def main():
    rng = Random(SEED)
    cv = Canvas(SIZE, SIZE)
    paint_sky(cv)
    paint_stars(cv, rng)
    paint_globe(cv)
    paint_dove(cv)

    medallions = [
        (138, 168, paint_chart),
        (886, 168, paint_envelope),
        (118, 500, paint_hospital),
        (906, 500, paint_storm),
        (168, 856, paint_football),
        (856, 856, paint_tanker),
        (512, 908, paint_glasses),
    ]
    for cx, cy, fn in medallions:
        medallion(cv, cx, cy)
        fn(cv, cx, cy)

    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", ".")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    data = encode_png(cv)
    with open(path, "wb") as f:
        f.write(data)
    print(f"wrote {path} ({len(data)} bytes)")


if __name__ == "__main__":
    main()
