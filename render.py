#!/usr/bin/env python3
"""Draw the 18 November 2026 world-news front page (v2) to entry.png.

One broadsheet in the shape the day's top entries use: a masthead
naming the day, three illustrated lead stories, nine small cards
with drawn icons, a dotted world map with numbered pins, thirty
numbered briefs, and a sources footer. 42 stories in all, across
six continents. Every story was checked against live news on
18 November 2026 (WIB); disputed claims are attributed, and
nothing is invented. All artwork is drawn here with Pillow.

Run: python3 render.py  ->  writes entry.png (1024x1024, < 1 MiB).
Deterministic: no randomness, no time, no network.
"""

import base64
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
OUT = Path(__file__).resolve().parent / "entry.png"

# --- palette: warm newsprint, near-black ink, restrained accents -------
PAPER = (248, 244, 236)
INK = (22, 26, 36)
NAVY = (28, 48, 84)
RED = (172, 32, 32)
GREY = (98, 102, 112)
FAINT = (214, 209, 196)
CARD = (255, 255, 255)
SEA = (206, 224, 232)
SAND = (238, 228, 205)

ACCENT = {
    "mideast": (150, 72, 32),
    "europe": (42, 92, 150),
    "asia": (176, 124, 22),
    "americas": (34, 110, 72),
    "africa": (150, 90, 20),
    "oceania": (28, 120, 118),
    "global": (96, 64, 128),
}

FONTS = "/usr/share/fonts/truetype/noto"


def load(name, size):
    return ImageFont.truetype(f"{FONTS}/{name}", size)


def masthead(size):
    return load("NotoSerifDisplay-Bold.ttf", size)


def serif(size):
    return load("NotoSerif-Bold.ttf", size)


def serif_it(size):
    return load("NotoSerif-Italic.ttf", size)


def sans(size):
    return load("NotoSans-Regular.ttf", size)


def sans_b(size):
    return load("NotoSans-Bold.ttf", size)


def sans_sb(size):
    return load("NotoSans-SemiBold.ttf", size)


def wrap_lines(d, text, fnt, max_w):
    """Greedy word wrap into lines that fit max_w pixels."""
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if d.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_lines(d, x, y, lines, fnt, fill, leading=None):
    """Draw lines top-left at (x, y); return the y below the block."""
    step = leading if leading else int(fnt.size * 1.24)
    for line in lines:
        d.text((x, y), line, font=fnt, fill=fill)
        y += step
    return y


def centre(d, cx, y, text, fnt, fill):
    d.text((cx - d.textlength(text, font=fnt) / 2, y), text, font=fnt,
           fill=fill)


# --- small drawn icons (white on a coloured chip) -----------------------

def icon_chart(d, x, y, s, c):
    d.line([(x + s * .18, y + s * .78), (x + s * .40, y + s * .52),
            (x + s * .58, y + s * .64), (x + s * .84, y + s * .22)],
           fill=c, width=max(3, s // 11))
    d.polygon([(x + s * .84, y + s * .22), (x + s * .70, y + s * .22),
               (x + s * .84, y + s * .36)], fill=c)


def icon_chart_down(d, x, y, s, c):
    d.line([(x + s * .16, y + s * .24), (x + s * .40, y + s * .48),
            (x + s * .58, y + s * .38), (x + s * .84, y + s * .78)],
           fill=c, width=max(3, s // 11))
    d.polygon([(x + s * .84, y + s * .78), (x + s * .70, y + s * .78),
               (x + s * .84, y + s * .64)], fill=c)


def icon_dome(d, x, y, s, c):
    d.rectangle([x + s * .16, y + s * .68, x + s * .84, y + s * .76], fill=c)
    for i in range(4):
        bx = x + s * (.22 + i * .16)
        d.rectangle([bx, y + s * .50, bx + s * .08, y + s * .68], fill=c)
    d.pieslice([x + s * .30, y + s * .14, x + s * .70, y + s * .54],
               180, 360, fill=c)
    d.rectangle([x + s * .47, y + s * .06, x + s * .53, y + s * .16], fill=c)


def icon_parliament(d, x, y, s, c):
    d.rectangle([x + s * .14, y + s * .74, x + s * .86, y + s * .82], fill=c)
    d.polygon([(x + s * .12, y + s * .42), (x + s * .88, y + s * .42),
               (x + s * .50, y + s * .16)], fill=c)
    for i in range(4):
        bx = x + s * (.20 + i * .17)
        d.rectangle([bx, y + s * .44, bx + s * .09, y + s * .74], fill=c)


def icon_spiral(d, x, y, s, c):
    for i, r in enumerate((0.40, 0.28, 0.16)):
        box = [x + s * (0.5 - r), y + s * (0.5 - r),
               x + s * (0.5 + r), y + s * (0.5 + r)]
        d.arc(box, 210 + i * 130, 210 + i * 130 + 250, fill=c,
              width=max(3, s // 12))
    d.ellipse([x + s * .44, y + s * .44, x + s * .56, y + s * .56], fill=c)


def icon_coin(d, x, y, s, c):
    d.ellipse([x + s * .12, y + s * .12, x + s * .88, y + s * .88],
              outline=c, width=max(3, s // 11))
    d.text((x + s * .30, y + s * .22), "\u20ac", font=sans_b(int(s * .52)),
           fill=c)


def icon_olive(d, x, y, s, c):
    # Olive branch: diagonal stem with paired leaves.
    d.line([(x + s * .18, y + s * .82), (x + s * .82, y + s * .18)],
           fill=c, width=max(3, s // 12))
    for t in (.28, .50, .72):
        px = x + s * (.18 + t * .64)
        py = y + s * (.82 - t * .64)
        d.ellipse([px - s * .13, py - s * .05, px + s * .02, py + s * .10],
                  fill=c)
        d.ellipse([px - s * .02, py - s * .13, px + s * .13, py + s * .02],
                  fill=c)


def icon_virus(d, x, y, s, c):
    d.ellipse([x + s * .30, y + s * .30, x + s * .70, y + s * .70], fill=c)
    for ang in range(0, 360, 45):
        import math
        a = math.radians(ang)
        x1 = x + s * .5 + math.cos(a) * s * .34
        y1 = y + s * .5 + math.sin(a) * s * .34
        x2 = x + s * .5 + math.cos(a) * s * .46
        y2 = y + s * .5 + math.sin(a) * s * .46
        d.line([(x1, y1), (x2, y2)], fill=c, width=max(3, s // 12))


def icon_chip(d, x, y, s, c):
    d.rectangle([x + s * .22, y + s * .22, x + s * .78, y + s * .78],
                outline=c, width=max(3, s // 11))
    d.line([(x + s * .22, y + s * .42), (x + s * .08, y + s * .42)],
           fill=c, width=max(2, s // 16))
    d.line([(x + s * .22, y + s * .58), (x + s * .08, y + s * .58)],
           fill=c, width=max(2, s // 16))
    d.line([(x + s * .78, y + s * .42), (x + s * .92, y + s * .42)],
           fill=c, width=max(2, s // 16))
    d.line([(x + s * .78, y + s * .58), (x + s * .92, y + s * .58)],
           fill=c, width=max(2, s // 16))
    d.line([(x + s * .42, y + s * .22), (x + s * .42, y + s * .08)],
           fill=c, width=max(2, s // 16))
    d.line([(x + s * .58, y + s * .22), (x + s * .58, y + s * .08)],
           fill=c, width=max(2, s // 16))
    d.line([(x + s * .42, y + s * .78), (x + s * .42, y + s * .92)],
           fill=c, width=max(2, s // 16))
    d.line([(x + s * .58, y + s * .78), (x + s * .58, y + s * .92)],
           fill=c, width=max(2, s // 16))


ICONS = {
    "chart": icon_chart,
    "chart_down": icon_chart_down,
    "dome": icon_dome,
    "parliament": icon_parliament,
    "spiral": icon_spiral,
    "coin": icon_coin,
    "olive": icon_olive,
    "virus": icon_virus,
    "chip": icon_chip,
}


# --- lead scenes (original flat drawings) -------------------------------

def scene_gulf(d, x, y, w, h):
    """Strait of Hormuz sketch: sea, two shores, Qeshm and Bahrain."""
    d.rectangle([x, y, x + w, y + h], fill=SEA)
    # Northern shore (Iran) and southern shore (Arabia).
    d.polygon([(x, y), (x + w, y), (x + w, y + h * .30),
               (x + w * .62, y + h * .42), (x + w * .30, y + h * .30),
               (x, y + h * .38)], fill=SAND)
    d.polygon([(x, y + h), (x + w, y + h), (x + w, y + h * .72),
               (x + w * .55, y + h * .62), (x + w * .28, y + h * .78),
               (x, y + h * .68)], fill=(226, 212, 178))
    # Qeshm island.
    d.polygon([(x + w * .52, y + h * .46), (x + w * .78, y + h * .40),
               (x + w * .86, y + h * .52), (x + w * .60, y + h * .58)],
              fill=(196, 178, 138))
    # Bahrain islet.
    d.ellipse([x + w * .16, y + h * .56, x + w * .24, y + h * .64],
              fill=(196, 178, 138))
    # Drone flight paths (dashed red).
    for t in range(0, 10):
        px = x + w * (.30 + t * .035)
        py = y + h * (.62 - t * .012)
        d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=RED)
    for t in range(0, 8):
        px = x + w * (.60 - t * .030)
        py = y + h * (.30 + t * .014)
        d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=RED)
    # Strike markers.
    for cx, cy in ((.68, .47), (.20, .60)):
        px, py = x + w * cx, y + h * cy
        d.ellipse([px - 9, py - 9, px + 9, py + 9], outline=RED, width=3)
        d.line([(px - 12, py), (px + 12, py)], fill=RED, width=2)
        d.line([(px, py - 12), (px, py + 12)], fill=RED, width=2)
    # Labels.
    d.text((x + 10, y + 8), "IRAN", font=sans_b(13), fill=(90, 80, 60))
    d.text((x + w - 58, y + h - 22), "HORMUZ", font=sans_b(13),
           fill=(90, 80, 60))
    d.text((x + w * .66, y + h * .14), "QESHM", font=sans_b(12),
           fill=(90, 80, 60))
    d.text((x + w * .10, y + h * .66), "BAHRAIN", font=sans_b(12),
           fill=(90, 80, 60))


def scene_bridge(d, x, y, w, h):
    """Kerch Strait: a bridge deck with a collapsed span, smoke, sea."""
    d.rectangle([x, y, x + w, y + h], fill=(196, 214, 226))
    # Sky band.
    d.rectangle([x, y, x + w, y + h * .34], fill=(226, 232, 236))
    # Sun haze.
    d.ellipse([x + w * .80, y + h * .06, x + w * .80 + 34, y + h * .06 + 34],
              fill=(240, 214, 140))
    # Sea.
    d.rectangle([x, y + h * .52, x + w, y + h], fill=(120, 164, 196))
    for i in range(5):
        wy = y + h * (.60 + i * .08)
        d.line([(x + 12, wy), (x + w - 12, wy)], fill=(170, 205, 225),
               width=2)
    # Bridge deck, left and right of the gap.
    deck_y = y + h * .46
    d.rectangle([x, deck_y, x + w * .38, deck_y + 9], fill=(70, 74, 82))
    d.rectangle([x + w * .62, deck_y, x + w, deck_y + 9], fill=(70, 74, 82))
    # Fallen span, tilted into the water.
    d.polygon([(x + w * .40, deck_y + 4), (x + w * .58, deck_y + 4),
               (x + w * .54, y + h * .78), (x + w * .44, y + h * .78)],
              fill=(96, 100, 110))
    # Arches and piers.
    for px in (.10, .30, .70, .90):
        d.rectangle([x + w * px, deck_y + 9, x + w * px + 7, y + h * .86],
                    fill=(70, 74, 82))
    d.arc([x + w * .06, deck_y - 26, x + w * .36, deck_y + 8], 180, 360,
          fill=(70, 74, 82), width=5)
    d.arc([x + w * .64, deck_y - 26, x + w * .94, deck_y + 8], 180, 360,
          fill=(70, 74, 82), width=5)
    # Smoke over the gap.
    for cx, cy, r in ((.50, .30, 16), (.55, .22, 20), (.46, .20, 13)):
        d.ellipse([x + w * cx - r, y + h * cy - r,
                   x + w * cx + r, y + h * cy + r], fill=(120, 122, 128))
    d.text((x + 10, y + h - 22), "KERCH STRAIT  ·  19 KM CROSSING",
           font=sans_b(12), fill=(255, 255, 255))


def scene_manila(d, x, y, w, h):
    """Manila at dusk: warm sky, skyline, four Quad flags, one jet."""
    for i in range(h):
        t = i / h
        r = int(38 + (238 - 38) * t)
        g = int(58 + (150 - 58) * t)
        b = int(96 + (92 - 96) * t)
        d.line([(x, y + i), (x + w, y + i)], fill=(r, g, b))
    # Sun.
    sx, sy, sr = x + w * .78, y + h * .30, 30
    d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(240, 168, 54))
    # Skyline.
    towers = [(0.00, .52, .09, .90), (.08, .38, .08, .90), (.15, .56, .10, .90),
              (.24, .32, .08, .90), (.31, .46, .09, .90), (.39, .26, .09, .90),
              (.47, .52, .09, .90), (.55, .40, .09, .90), (.63, .58, .09, .90),
              (.71, .44, .08, .90), (.78, .54, .08, .90), (.85, .42, .07, .90),
              (.91, .56, .09, .90)]
    for bx, by, bw, bh in towers:
        d.rectangle([x + w * bx, y + h * by, x + w * (bx + bw),
                     y + h * bh], fill=(18, 24, 42))
        for wy in (.18, .38, .58, .78):
            for wx in (.28, .68):
                wxp = x + w * (bx + bw * wx)
                wyp = y + h * (by + (bh - by) * wy)
                d.rectangle([wxp - 2, wyp - 3, wxp + 2, wyp + 3],
                            fill=(240, 200, 110))
    # Bay strip.
    d.rectangle([x, y + h * .90, x + w, y + h], fill=(16, 50, 84))
    # Four flags on poles.
    def flag_us(fx, fy, fw, fh):
        for i in range(7):
            d.rectangle([fx, fy + i * fh / 7, fx + fw, fy + (i + 1) * fh / 7],
                        fill=RED if i % 2 == 0 else (255, 255, 255))
        d.rectangle([fx, fy, fx + fw * .42, fy + fh * .55], fill=NAVY)

    def flag_india(fx, fy, fw, fh):
        d.rectangle([fx, fy, fx + fw, fy + fh / 3], fill=(255, 153, 51))
        d.rectangle([fx, fy + fh / 3, fx + fw, fy + 2 * fh / 3],
                    fill=(255, 255, 255))
        d.rectangle([fx, fy + 2 * fh / 3, fx + fw, fy + fh], fill=(19, 136, 8))

    def flag_japan(fx, fy, fw, fh):
        d.rectangle([fx, fy, fx + fw, fy + fh], fill=(255, 255, 255))
        cx, cy, r = fx + fw / 2, fy + fh / 2, fh * .30
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(188, 0, 45))

    def flag_australia(fx, fy, fw, fh):
        d.rectangle([fx, fy, fx + fw, fy + fh], fill=(0, 40, 104))
        d.line([(fx, fy), (fx + fw * .5, fy + fh * .5)],
               fill=(255, 255, 255), width=2)
        d.line([(fx + fw * .5, fy), (fx, fy + fh * .5)],
               fill=(255, 255, 255), width=2)
        for sx2, sy2 in ((.72, .28), (.85, .55), (.68, .72)):
            d.ellipse([fx + fw * sx2 - 2, fy + fh * sy2 - 2,
                       fx + fw * sx2 + 2, fy + fh * sy2 + 2],
                      fill=(255, 255, 255))

    fw, fh = 42, 28
    for i, fn in enumerate((flag_us, flag_india, flag_japan, flag_australia)):
        fx = x + 16 + i * 74
        fy = y + h * .90 - fh - 24
        d.line([(fx + 2, fy - 8), (fx + 2, y + h * .90)],
               fill=(240, 240, 240), width=3)
        fn(fx + 4, fy, fw, fh)
    # Jet crossing the sun.
    px, py = x + w * .34, y + h * .16
    d.polygon([(px, py), (px + 52, py + 3), (px, py + 6), (px - 9, py + 3)],
              fill=(255, 255, 255))
    d.polygon([(px + 12, py - 1), (px + 25, py - 14), (px + 30, py - 1)],
              fill=(255, 255, 255))
    d.polygon([(px + 12, py + 4), (px + 23, py + 14), (px + 28, py + 4)],
              fill=(255, 255, 255))
    d.text((x + 10, y + h - 22), "MANILA  ·  FIRST QUAD IN TWO YEARS",
           font=sans_b(12), fill=(255, 255, 255))


# --- dotted world map ----------------------------------------------------
# Hand-drawn land mask, 72 cols (5 deg each, -180..180) x 32 rows
# (~4.7 deg each, 90..-60). '#' is land.
LAND = [
    "....................#####...............................................",
    "........###.......#########............................................",
    "......#######.......########..............................#######.....",
    "...#####......................######................################",
    "..#######..........#############....####....###########################",
    "..######..........#################..####...##########################",
    ".......##################...#......#######..#########################.",
    ".......################...##......#######...########################..",
    "........###############...#.......##########..####################....",
    ".........#############...........###########..#################......",
    ".........############............###########...###############.......",
    "..........###########..###.....##########......#############.........",
    "..........##########...........#############....##########..........",
    "..........########..............############....########...........",
    "...........#####................############....######.............",
    "............####................###########......#####.............",
    "..............###...#####........##########.......####..............",
    "...............###..#####.........#########.......####..............",
    ".................#####...........########........#######...........",
    "..................#######.........#######.........#########........",
    "..................########........#######.........########.........",
    "...................########.......#######.........######...........",
    "...................########.......#######..##......#...............",
    "...................#######........######...##......#######.........",
    "...................######.........######..........########.........",
    "....................#####.........#####...........########.........",
    "....................####..........####............#######..........",
    "....................###...........................######..##.......",
    "....................###...............................##..........",
    "....................##................................................",
    "....................##................................................",
    "....................##................................................",
]

# (lon, lat) of each featured story's pin.
PINS = [
    (50.5, 26.0),    # 1 Gulf / Bahrain
    (36.5, 45.3),    # 2 Kerch Bridge
    (121.0, 14.6),   # 3 Manila
    (-122.0, 37.4),  # 4 Nvidia, California
    (-150.0, 64.0),  # 5 Alaska
    (35.2, 31.8),    # 6 Jerusalem
    (80.0, 16.0),    # 7 Andhra Pradesh
    (-74.0, 40.7),   # 8 New York
    (4.4, 50.8),     # 9 Brussels
    (34.5, 31.5),    # 10 Gaza
    (23.0, -2.0),    # 11 DR Congo
    (-160.0, -15.0), # 12 Cook Islands
]

PIN_COLOUR = [
    ACCENT["mideast"], ACCENT["europe"], ACCENT["asia"],
    ACCENT["americas"], ACCENT["americas"], ACCENT["asia"],
    ACCENT["asia"], ACCENT["americas"], ACCENT["europe"],
    ACCENT["mideast"], ACCENT["africa"], ACCENT["oceania"],
]

# --- the day's stories ----------------------------------------------------
# (number, region tag, beat, headline, deck, icon key, accent key)

LEADS = [
    (1, "MIDDLE EAST", "WAR",
     "US and Iran trade fire over the Gulf",
     "US jets hit an Iranian missile site on Qeshm after "
     "drones hit a US radar in Bahrain; Iran also fired at "
     "Kuwait.",
     "gulf", "mideast"),
    (2, "EUROPE", "UKRAINE WAR",
     "Crimea bridge span falls into the sea",
     "Kyiv says a second strike destroyed the road arch; "
     "Moscow says it downed 1,441 drones. Trains resumed "
     "on one track.",
     "bridge", "europe"),
    (3, "ASIA", "DIPLOMACY",
     "Trump meets Marcos, then flies to Shenzhen",
     "Talks and lunch in Manila after the first Quad in two "
     "years. APEC opens in Shenzhen; a Xi\u2013Putin\u2013Trump "
     "trilateral follows.",
     "manila", "asia"),
]

SCENES = {"gulf": scene_gulf, "bridge": scene_bridge, "manila": scene_manila}

CARDS = [
    (4, "UNITED STATES", "BUSINESS",
     "Nvidia's revenue doubles to $115.8bn",
     "Sales rose 103% as data-centre demand held. The board "
     "will not bring back Huang.",
     "chart", "americas"),
    (5, "UNITED STATES", "POLITICS",
     "Peltola wins Alaska; Senate now 56\u201344",
     "AP calls it: the first Alaska Native senator, and the "
     "first Democrat to win the seat since 2008.",
     "dome", "americas"),
    (6, "ISRAEL", "POLITICS",
     "Knesset elects Kahana as speaker, 66\u201352",
     "Kahana, an ally of Gadi Eisenkot, replaces Amir Ohana "
     "after a seven-hour debate.",
     "parliament", "asia"),
    (7, "SOUTH ASIA", "WEATHER",
     "Cyclone Akvan bears down on Andhra Pradesh",
     "Landfall is forecast for Friday, gusts to 110 km/h. "
     "Odisha is moving people from the coast.",
     "spiral", "asia"),
    (8, "UNITED STATES", "MARKETS",
     "Wall Street slides as the Dow drops 849",
     "The S&P 500 closed at its lowest since July. An NSA "
     "outage was blamed on maintenance.",
     "chart_down", "americas"),
    (9, "EUROPE", "UKRAINE",
     "EU proposes a \u20ac45bn loan for Ukraine",
     "It would cover about two-thirds of Kyiv's 2027 gap, "
     "repaid only if Russia pays reparations.",
     "coin", "europe"),
    (10, "MIDDLE EAST", "GAZA",
     "Board of Peace warns Gaza truce may collapse",
     "Its report to the UN warns of \u201canother winter in tents "
     "and rubble\u201d for the displaced.",
     "olive", "mideast"),
    (11, "AFRICA", "HEALTH",
     "Ebola in Congo passes 11,000 cases",
     "The outbreak has more than doubled in three months, the "
     "WHO says; 5,400 have died.",
     "virus", "africa"),
    (12, "OCEANIA", "WEATHER",
     "Cyclone Xavier reaches Category 5",
     "Winds of 220 km/h by the Northern Cook Islands; gale "
     "warnings for Pukapuka, Nassau.",
     "spiral", "oceania"),
]

BRIEFS = [
    (13, "Measles", "US loses status held since 2000"),
    (14, "An-12 crash", "19 killed in Siberia"),
    (15, "Dhoni retires", "Ends IPL career; CSK mentor"),
    (16, "Amazon", "$7bn for Indian renewables"),
    (17, "Canada\u2013China", "Extend trade deals"),
    (18, "Anthropic", "Prices IPO; ANT trades Thursday"),
    (19, "Voyager 1", "First craft one light-day out"),
    (20, "GTA VI", "Midnight launch begins in NZ"),
    (21, "Sudan", "2,230 civilian deaths in 10 months"),
    (22, "Tokyo", "Jets scrambled at Russian planes"),
    (23, "Papua New Guinea", "6.0 quake strikes"),
    (24, "Romania", "5.3 quake in Vrancea"),
    (25, "Waymo", "Halts driverless freeway rides"),
    (26, "UK sanctions", "8 settlement firms listed"),
    (27, "Australia sanctions", "Lists 7, incl. settler Weiss"),
    (28, "COP31", "Talks stall on finance, fuels"),
    (29, "Senegal", "First into AFCON 2027"),
    (30, "India beat Pakistan", "2\u20131, SAFF final, 10th title"),
    (31, "Nations League", "N. Ireland, Austria, Sweden up"),
    (32, "Estonia", "To shut Russia border on 1 Dec"),
    (33, "Thailand", "Trump signs reciprocal trade deal"),
    (34, "Guinea", "224 jailed over illegal mining"),
    (35, "Costa Rica", "Journalist shot dead in drug probe"),
    (36, "Bulgaria", "Gas tanker sinks; 19 rescued"),
    (37, "Fishermen sue US", "16 sue over drone strike"),
    (38, "Telegram", "Jordan and Iraq block the app"),
    (39, "Optimizely", "Hack hits code used by 178 firms"),
    (40, "Peru", "M5.9 quake, no damage reported"),
    (41, "Indonesia", "Prabowo sorry over haze; 16 died"),
    (42, "South Africa", "Inflation 5.2%, a 2-year high"),
]

FOOTER = ("Every story was reported on Wednesday 18 November 2026; "
          "disputed claims are attributed. Sources: Reuters, AP, AFP, "
          "BBC, Al Jazeera, UN News, IMD and others. Original drawings.")


# --- page sections ---------------------------------------------------------

def draw_masthead(d):
    mx = 26
    centre(d, W // 2, 10, "T H E   D A Y   I N   W O R L D   N E W S",
           sans_b(13), GREY)
    right = "42 STORIES  \u00b7  6 CONTINENTS  \u00b7  ONE DAY"
    d.text((W - mx - d.textlength(right, font=sans_b(13)), 10), right,
           font=sans_b(13), fill=RED)
    centre(d, W // 2, 28, "Wednesday 18 November 2026",
           masthead(62), INK)
    centre(d, W // 2, 100,
           "Every story on this page happened, or was first reported, "
           "on this day.",
           serif_it(16), GREY)
    # Double rule with coloured segments.
    d.line([(mx, 126), (W - mx, 126)], fill=INK, width=3)
    d.line([(mx, 131), (W - mx, 131)], fill=INK, width=1)
    seg_w = (W - 2 * mx) / 6
    cols = [ACCENT["mideast"], ACCENT["europe"], ACCENT["asia"],
            ACCENT["americas"], ACCENT["africa"], ACCENT["oceania"]]
    for i, c in enumerate(cols):
        d.rectangle([mx + i * seg_w, 136, mx + (i + 1) * seg_w, 140],
                    fill=c)


def draw_lead(d, x, y, w, h, num, region, beat, head, deck, scene, accent):
    d.rounded_rectangle([x, y, x + w, y + h], radius=8, fill=CARD,
                        outline=FAINT, width=1)
    sh = 110
    SCENES[scene](d, x + 1, y + 1, w - 2, sh)
    ty = y + sh + 8
    # Numbered badge + kicker.
    d.ellipse([x + 12, ty, x + 34, ty + 22], fill=ACCENT[accent])
    num_s = str(num)
    d.text((x + 23 - d.textlength(num_s, font=sans_b(13)) / 2, ty + 3),
           num_s, font=sans_b(13), fill=(255, 255, 255))
    d.text((x + 42, ty + 3), f"{region}  \u00b7  {beat}",
           font=sans_b(13), fill=ACCENT[accent])
    hl = wrap_lines(d, head, serif(24), w - 24)
    yy = draw_lines(d, x + 12, ty + 28, hl, serif(24), INK, leading=27)
    dl = wrap_lines(d, deck, sans(13), w - 24)
    draw_lines(d, x + 12, yy + 4, dl, sans(13), (58, 62, 74), leading=17)


def draw_card(d, x, y, w, h, num, region, beat, head, deck, icon, accent):
    c = ACCENT[accent]
    d.rounded_rectangle([x, y, x + w, y + h], radius=8, fill=CARD,
                        outline=FAINT, width=1)
    d.rectangle([x, y + 8, x + 5, y + h - 8], fill=c)
    # Icon chip, top right.
    s = 44
    ix, iy = x + w - s - 10, y + 10
    d.rounded_rectangle([ix, iy, ix + s, iy + s], radius=7, fill=c)
    ICONS[icon](d, ix, iy, s, (255, 255, 255))
    tx = x + 16
    tw = w - 16 - s - 18
    d.text((tx, y + 9), f"{num}  {region}  \u00b7  {beat}",
           font=sans_b(11), fill=c)
    hl = wrap_lines(d, head, sans_b(18), tw)
    yy = draw_lines(d, tx, y + 26, hl, sans_b(18), INK, leading=20)
    dl = wrap_lines(d, deck, sans(13), w - 28)
    draw_lines(d, tx, yy + 4, dl, sans(13), (58, 62, 74), leading=15)


def draw_map(d, x, y, w, h):
    d.text((x, y), "WHERE IT HAPPENED", font=sans_b(13), fill=RED)
    my = y + 20
    mh = h - 48
    d.rounded_rectangle([x, my, x + w, my + mh], radius=6, fill=(232, 240, 242),
                        outline=FAINT, width=1)
    rows, cols = len(LAND), len(LAND[0])
    dx = w / cols
    dy = mh / rows
    for r, row in enumerate(LAND):
        for cix, ch in enumerate(row[:cols]):
            if ch == '#':
                cx = x + (cix + 0.5) * dx
                cy = my + (r + 0.5) * dy
                d.ellipse([cx - 1.6, cy - 1.6, cx + 1.6, cy + 1.6],
                          fill=(120, 140, 150))
    # Numbered pins.
    for i, (lon, lat) in enumerate(PINS):
        gx = (lon + 180) / 360 * cols
        gy = (90 - lat) / 150 * rows
        px = x + gx * dx
        py = my + gy * dy
        # Nudge the Gaza pin off Jerusalem's so both read.
        if i == 9:
            px -= 7
            py += 7
            d.line([(x + gx * dx, my + gy * dy), (px, py)], fill=GREY,
                   width=1)
        d.ellipse([px - 8, py - 8, px + 8, py + 8],
                  fill=PIN_COLOUR[i], outline=(255, 255, 255), width=1)
        s = str(i + 1)
        d.text((px - d.textlength(s, font=sans_b(9)) / 2, py - 5), s,
               font=sans_b(9), fill=(255, 255, 255))
    ly = my + mh + 8
    d.text((x, ly), "Numbered pins: stories 1\u201312 above.",
           font=sans(11), fill=GREY)


def draw_briefs(d, x, y, w, h):
    d.text((x, y), "ALSO ON WEDNESDAY 18 NOVEMBER \u2014 30 MORE STORIES",
           font=sans_b(13), fill=RED)
    d.line([(x, y + 20), (x + w, y + 20)], fill=INK, width=2)
    col_w = (w - 18) // 2
    fnt = sans(11)
    fnt_b = sans_b(11)
    for i, (num, place, text) in enumerate(BRIEFS):
        col = i // 15
        row = i % 15
        bx = x + col * (col_w + 18)
        by = y + 28 + row * 15
        d.text((bx, by), f"{num}.", font=fnt_b, fill=RED)
        d.text((bx + 26, by), place, font=fnt_b, fill=INK)
        rest = f" \u2014 {text}"
        d.text((bx + 26 + d.textlength(place, font=fnt_b), by), rest,
               font=fnt, fill=(58, 62, 74))


def render():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    mx = 26

    draw_masthead(d)

    # Three leads.
    ly, lh, gap = 146, 244, 12
    lw = (W - 2 * mx - 2 * gap) // 3
    for i, (num, region, beat, head, deck, scene, accent) in enumerate(LEADS):
        draw_lead(d, mx + i * (lw + gap), ly, lw, lh, num, region, beat,
                  head, deck, scene, accent)

    # Nine cards, 3 x 3.
    cy, ch = 400, 100
    cw = lw
    for i, (num, region, beat, head, deck, icon, accent) in enumerate(CARDS):
        cx = mx + (i % 3) * (cw + gap)
        cyy = cy + (i // 3) * (ch + 10)
        draw_card(d, cx, cyy, cw, ch, num, region, beat, head, deck,
                  icon, accent)

    # Bottom: map left, briefs right.
    by = 730
    draw_map(d, mx, by, 330, 260)
    draw_briefs(d, mx + 330 + 16, by, W - mx - (mx + 330 + 16), 260)

    # Footer.
    fl = wrap_lines(d, FOOTER, sans(11), W - 2 * mx)
    draw_lines(d, mx, 996, fl, sans(11), GREY, leading=14)

    img.save(OUT, optimize=True)
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")


def write_b64():
    data = OUT.read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    target = Path(__file__).resolve().parent / "entry.png.b64"
    target.write_text(b64 + "\n", encoding="ascii")
    print(f"wrote {target} ({target.stat().st_size} bytes, "
          f"image {len(data)} bytes)")


if __name__ == "__main__":
    render()
    write_b64()
