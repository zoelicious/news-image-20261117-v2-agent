#!/usr/bin/env python3
"""news-image-20261117 v2 (agent amber-puffin-51).

One image summing up the world's news of Tuesday 17 November 2026.
Drawn programmatically with Pillow (no text-to-image): every word on the
page comes from the story list below, so spelling and numbers are exact.

Layout (1024x1024, cream paper, black ink, red accent):
  kicker -> giant serif masthead -> 3-panel hero row (Kerch / Gulf / Quad)
  -> 10 numbered cards (4-13) -> world map with pins 1-13 + dots 14-43
  -> numbered briefs 14-43 -> footer with verification line + sources.

Run:  python3 main.py            (writes entry.png next to this file,
                                  or to $MAKEFUN_OUTPUT_DIR/entry.png)
Deterministic: same fonts, same draw order, same PNG bytes every run.
"""

import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
MARGIN = 28
CW = W - 2 * MARGIN  # 968 content width

# ---- palette (AD doc v2, section 5) -------------------------------------
PAPER = (247, 242, 230)   # #F7F2E6 krem gading
INK = (17, 17, 17)        # #111111
RED = (179, 39, 30)       # #B3271E
SEA = (198, 220, 232)     # pale sea blue for panels / map
SAND = (232, 214, 176)    # land sand
SAND_DK = (214, 192, 148)
SKY = (205, 226, 238)
GREY = (107, 107, 107)    # #6B6B6B global
WHITE = (255, 255, 255)
DARK_BAND = (34, 34, 34)

REGION = {  # muted accent per region, used in kickers + map pins + legend
    "EUROPE": (47, 93, 138),        # #2F5D8A
    "MIDDLE EAST": (198, 122, 46),  # #C67A2E
    "ASIA": (107, 78, 155),         # #6B4E9B
    "AFRICA": (62, 122, 78),        # #3E7A4E
    "AMERICAS": (169, 50, 38),      # #A93226
    "OCEANIA": (46, 125, 123),      # #2E7D7B
    "GLOBAL": (107, 107, 107),      # #6B6B6B
    "US": (169, 50, 38),
    "RUSSIA": (47, 93, 138),
}

# ---- fonts ---------------------------------------------------------------
def _font(names, size):
    for name in names:
        for base in ("/usr/share/fonts/truetype/", "/usr/share/fonts/"):
            for p in Path(base).rglob(name):
                try:
                    return ImageFont.truetype(str(p), size)
                except Exception:
                    continue
    return ImageFont.load_default(size)


def serif_black(size):
    return _font(["NotoSerifDisplay-Black.ttf", "DejaVuSerif-Bold.ttf",
                  "LiberationSerif-Bold.ttf"], size)


def serif_bold(size):
    return _font(["NotoSerif-Bold.ttf", "DejaVuSerif-Bold.ttf",
                  "LiberationSerif-Bold.ttf"], size)


def sans(size):
    return _font(["LiberationSans-Regular.ttf", "NotoSans-Regular.ttf",
                  "DejaVuSans.ttf"], size)


def sans_bold(size):
    return _font(["LiberationSans-Bold.ttf", "NotoSans-Bold.ttf",
                  "DejaVuSans-Bold.ttf"], size)


def sans_cond(size):
    return _font(["NotoSans-Condensed.ttf", "LiberationSans-Regular.ttf",
                  "DejaVuSans.ttf"], size)


def sans_cond_bold(size):
    return _font(["NotoSans-CondensedBold.ttf", "LiberationSans-Bold.ttf",
                  "NotoSans-Bold.ttf"], size)


# ---- text helpers --------------------------------------------------------
def text_w(draw, s, font):
    return draw.textlength(s, font=font)


def fit_font(s, fonts, max_w, draw):
    """Largest font from the list (biggest first) that fits s in max_w."""
    for f in fonts:
        if text_w(draw, s, f) <= max_w:
            return f
    return fonts[-1]


def wrap(draw, s, font, max_w):
    """Greedy word wrap; returns list of lines (never splits a word)."""
    lines, cur = [], ""
    for word in s.split(" "):
        trial = word if not cur else cur + " " + word
        if text_w(draw, trial, font) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(draw, lines, x, y, font, fill, leading):
    for ln in lines:
        draw.text((x, y), ln, font=font, fill=fill)
        y += leading
    return y


def kicker(draw, x, y, region, topic, size=11):
    """Red caps region + topic kicker, e.g. 'EUROPE · UKRAINE WAR'."""
    col = REGION.get(region, RED)
    draw.text((x, y), region, font=sans_bold(size), fill=col)
    w1 = text_w(draw, region, sans_bold(size))
    draw.text((x + w1 + 4, y), "·", font=sans_bold(size), fill=GREY)
    draw.text((x + w1 + 12, y), topic, font=sans_bold(size), fill=RED)


def num_badge(draw, cx, cy, n, r, fill):
    """Numbered circle badge (white number on region colour)."""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill,
                 outline=WHITE, width=1)
    f = sans_bold(11 if r >= 9 else 9)
    s = str(n)
    tw = text_w(draw, s, f)
    th = f.getbbox(s)[3] - f.getbbox(s)[1]
    draw.text((cx - tw / 2, cy - th / 2 - 1), s, font=f, fill=WHITE)


# ---- story data (AD doc v2 — facts/numbers verbatim) ----------------------
# (region, topic, headline, deck, illustration tag, caption strip)
CARDS = [
    (1, "EUROPE", "UKRAINE WAR",
     "Ukraine says a Crimean Bridge road span fell into the sea",
     "Second strike in two days; Zelensky hails an \u201cunprecedented operation\u201d. "
     "The Kremlin vows to rebuild.", "kerch",
     "KERCH STRAIT \u00b7 STRUCK FOR A SECOND DAY"),
    (2, "MIDDLE EAST", "IRAN WAR",
     "Iran sends drones at a US radar in Bahrain; US hits back",
     "Bahrain and the US say all were downed; US jets then strike Qeshm. "
     "Iran says tankers hit mines in Hormuz.", "gulf",
     "STRAIT OF HORMUZ \u00b7 DRONES DOWNED, US STRIKES"),
    (3, "ASIA", "DIPLOMACY",
     "Trump holds his first Quad summit, in Manila",
     "The four unveil critical-minerals deals; Putin reaches Shenzhen for "
     "Thursday\u2019s talks with Trump and Xi.", "quad",
     "QUAD LEADERS\u2019 SUMMIT \u00b7 MANILA"),
    (4, "AFRICA", "HEALTH",
     "Ebola cases in DR Congo top 11,000, WHO says",
     "Cases more than doubled in three months; about 5,400 have died.",
     "ebola", "DR CONGO \u00b7 EBOLA"),
    (5, "GLOBAL", "CLIMATE",
     "COP31 divided over a fossil-fuel phase-out",
     "Nations weigh the first draft; the Antalya talks end Friday.",
     "cop31", "COP31 ANTALYA \u00b7 ENDS FRI"),
    (6, "AMERICAS", "HEALTH",
     "US, Mexico and Bolivia lose measles-free status",
     "PAHO cites a year of spread; the US has 5,700+ cases in 2026.",
     "measles", "MEASLES-FREE STATUS REVOKED"),
    (7, "US", "BUSINESS",
     "Nvidia\u2019s quarterly sales double to $115.8bn",
     "Reported after the close. Earlier the Dow fell 849 points (\u22121.6%).",
     "nvidia", "NVIDIA QUARTER \u00b7 WALL STREET"),
    (8, "MIDDLE EAST", "GAZA",
     "Gaza truce at risk of collapse, UN is told",
     "Board of Peace report; UN agencies say 1.4m face acute hunger.",
     "gaza", "GAZA \u00b7 WINTER AID HELD UP"),
    (9, "ASIA", "POLITICS",
     "Mongolia\u2019s president says he will resign",
     "Kh\u00fcrels\u00fckh denies a $25m bribe claim; parliament must accept.",
     "mongolia", "ULAANBAATAR \u00b7 GRAFT CLAIM DENIED"),
    (10, "EUROPE", "POLITICS",
     "Serbia\u2019s student-led majority takes its seats",
     "Student List holds 140 of 250; Vu\u010di\u0107\u2019s party goes into opposition.",
     "serbia", "BELGRADE \u00b7 PARLIAMENT SWORN IN"),
    (11, "ASIA", "LABOUR",
     "Bangladesh police tear-gas garment workers",
     "They want Tk 30,000 a month, up from 12,500; 37 factories shut.",
     "dhaka", "DHAKA \u00b7 SAVAR \u00b7 GAZIPUR"),
    (12, "RUSSIA", "AIR CRASH",
     "Russian An-12 crash in Siberia kills all 19",
     "The air force plane came down near Kemerovo; a fault is suspected.",
     "crash", "KEMEROVO \u00b7 ALL 19 ABOARD KILLED"),
    (13, "AFRICA", "JUSTICE",
     "Mozambique puts opposition leader on trial",
     "Ven\u00e2ncio Mondlane faces 5 charges over deadly 2024 protests.",
     "trial", "MAPUTO \u00b7 SUPREME COURT"),
]

# briefs 14-43: (number, place, text) — one line each
BRIEFS = [
    (14, "Russia", "says it downed a record 1,441 drones overnight."),
    (15, "Kyiv", "missiles hit the North and South Dnipro bridges."),
    (16, "UN", "Ukraine\u2019s civilian deaths this year top all of 2025."),
    (17, "Prague", "two trains collide; 46 people injured."),
    (18, "France", "public-sector strike; 146,000 march (CGT: 500,000)."),
    (19, "Poland", "Tusk\u2019s government survives a no-confidence vote."),
    (20, "Germany", "Deutsche Bank shares fall after a huge data leak."),
    (21, "Moldova", "shuts its airspace as a drone nears Chi\u015fin\u0103u."),
    (22, "Turkey", "police seize opposition broadcaster S\u00f6zc\u00fc TV."),
    (23, "Football", "Norway win 3\u20132 in Denmark; Haaland scores twice."),
    (24, "Vatican", "Pope Leo XIV returns from South America tour."),
    (25, "UK", "sanctions 8 settlement firms and Tzav 9."),
    (26, "Israel", "Eisenkot ally Matan Kahana elected speaker, 66\u201352."),
    (27, "West Bank", "settlers kill a woman, 72, near Jericho."),
    (28, "Oman", "Iran\u2019s Aragchi holds shipping-safety talks."),
    (29, "India", "Cyclone Akvan strengthens; Odisha evacuates."),
    (30, "India", "bus falls into an Uttarakhand gorge, 8 dead."),
    (31, "Japan", "protests a Russian airspace intrusion near Fukuoka."),
    (32, "China\u2013Canada", "more tariff cuts after Carney\u2013Xi talks."),
    (33, "Malaysia", "Macron visit seals a strategic partnership."),
    (34, "Thailand", "pledges to scrap tariffs on US goods."),
    (35, "South Korea", "IMF lifts 2026 growth forecast to 3.9%."),
    (36, "Football", "India beat Pakistan 2\u20131 in SAFF final."),
    (37, "Kenya", "WFP aids 30,000 who fled Ethiopia clashes."),
    (38, "Football", "Togo beat Algeria 3\u20130 in AFCON qualifier."),
    (39, "Haiti", "Aristide\u2019s party will field no candidates."),
    (40, "US Senate", "Van Hollen challenges Schumer for leader."),
    (41, "Australia", "eases planned backpacker visa curbs."),
    (42, "Darwin", "M6.6 quake off Indonesia felt; no tsunami."),
    (43, "Apple", "Pay, iCloud and App Store outage; not a hack."),
]

# map pin locations (lon, lat) for stories 1-13 and dots for briefs 14-43
PINS = {1: (36, 45), 2: (50.5, 26.2), 3: (121, 14.6), 4: (23, -2),
        5: (29, 38), 6: (-77, 39), 7: (-122, 37), 8: (36.5, 30.5),
        9: (107, 48), 10: (20.5, 44.8), 11: (90.4, 23.8),
        12: (86, 55.4), 13: (32.6, -25.9)}
DOTS = {14: (37, 55.7), 15: (30.5, 50.4), 16: (33, 49), 17: (14.4, 50),
        18: (2.3, 48.9), 19: (21, 52.2), 20: (8.7, 50.1), 21: (28.8, 47),
        22: (29, 41), 23: (12.6, 55.7), 24: (12.45, 41.9), 25: (-0.1, 51.5),
        26: (35.2, 31.8), 27: (35.5, 31.9), 28: (58.4, 23.6),
        29: (85, 20), 30: (79, 30), 31: (130.4, 33.6), 32: (116.4, 39.9),
        33: (101.7, 3.1), 34: (100.5, 13.8), 35: (127, 37.5),
        36: (77.2, 28.6), 37: (36.8, -1.3), 38: (1.2, 6.1),
        39: (-72.3, 18.5), 40: (-77, 38.9), 41: (149.1, -35.3),
        42: (130.8, -12.5), 43: (-122, 37.3)}
DOT_REGION = {14: "RUSSIA", 15: "EUROPE", 16: "GLOBAL", 17: "EUROPE",
              18: "EUROPE", 19: "EUROPE", 20: "EUROPE", 21: "EUROPE",
              22: "MIDDLE EAST", 23: "EUROPE", 24: "EUROPE",
              25: "EUROPE", 26: "MIDDLE EAST", 27: "MIDDLE EAST",
              28: "MIDDLE EAST", 29: "ASIA", 30: "ASIA", 31: "ASIA",
              32: "ASIA", 33: "ASIA", 34: "ASIA", 35: "ASIA", 36: "ASIA",
              37: "AFRICA", 38: "AFRICA", 39: "AMERICAS", 40: "AMERICAS",
              41: "OCEANIA", 42: "OCEANIA", 43: "AMERICAS"}


# ---- flat illustrations --------------------------------------------------
def _flag(draw, x, y, w, h, kind):
    """Tiny flat flag: us / india / japan / australia / mongolia / serbia /
    bangladesh / mexico / bolivia / drcongo."""
    if kind == "us":
        for i in range(7):
            draw.rectangle([x, y + i * h / 7, x + w, y + (i + 1) * h / 7],
                           fill=RED if i % 2 == 0 else WHITE)
        draw.rectangle([x, y, x + w * 0.4, y + h * 4 / 7], fill=(47, 93, 138))
    elif kind == "india":
        draw.rectangle([x, y, x + w, y + h / 3], fill=(255, 153, 51))
        draw.rectangle([x, y + h / 3, x + w, y + 2 * h / 3], fill=WHITE)
        draw.rectangle([x, y + 2 * h / 3, x + w, y + h], fill=(19, 136, 8))
        draw.ellipse([x + w / 2 - h / 8, y + h / 2 - h / 8,
                      x + w / 2 + h / 8, y + h / 2 + h / 8],
                     outline=(0, 56, 147), width=1)
    elif kind == "japan":
        draw.rectangle([x, y, x + w, y + h], fill=WHITE)
        draw.ellipse([x + w / 2 - h / 5, y + h / 2 - h / 5,
                      x + w / 2 + h / 5, y + h / 2 + h / 5], fill=(188, 0, 45))
    elif kind == "australia":
        draw.rectangle([x, y, x + w, y + h], fill=(0, 40, 104))
        draw.rectangle([x, y, x + w * 0.5, y + h * 0.5], fill=(0, 40, 104))
        draw.line([x, y, x + w * 0.5, y + h * 0.5], fill=WHITE, width=1)
        draw.line([x + w * 0.5, y, x, y + h * 0.5], fill=WHITE, width=1)
        for sx, sy in ((0.72, 0.25), (0.82, 0.6), (0.65, 0.7)):
            draw.ellipse([x + w * sx - 1, y + h * sy - 1,
                          x + w * sx + 1, y + h * sy + 1], fill=WHITE)
    elif kind == "mongolia":
        draw.rectangle([x, y, x + w / 3, y + h], fill=RED)
        draw.rectangle([x + w / 3, y, x + 2 * w / 3, y + h], fill=(0, 102, 179))
        draw.rectangle([x + 2 * w / 3, y, x + w, y + h], fill=RED)
    elif kind == "serbia":
        draw.rectangle([x, y, x + w, y + h / 3], fill=RED)
        draw.rectangle([x, y + h / 3, x + w, y + 2 * h / 3], fill=(0, 56, 147))
        draw.rectangle([x, y + 2 * h / 3, x + w, y + h], fill=WHITE)
    elif kind == "bangladesh":
        draw.rectangle([x, y, x + w, y + h], fill=(0, 106, 78))
        draw.ellipse([x + w * 0.4 - h / 4, y + h / 2 - h / 4,
                      x + w * 0.4 + h / 4, y + h / 2 + h / 4], fill=RED)
    elif kind == "mexico":
        draw.rectangle([x, y, x + w / 3, y + h], fill=(0, 104, 71))
        draw.rectangle([x + w / 3, y, x + 2 * w / 3, y + h], fill=WHITE)
        draw.rectangle([x + 2 * w / 3, y, x + w, y + h], fill=(206, 17, 38))
    elif kind == "bolivia":
        draw.rectangle([x, y, x + w, y + h / 3], fill=RED)
        draw.rectangle([x, y + h / 3, x + w, y + 2 * h / 3], fill=(247, 219, 0))
        draw.rectangle([x, y + 2 * h / 3, x + w, y + h], fill=(0, 122, 61))
    elif kind == "drcongo":
        draw.rectangle([x, y, x + w, y + h], fill=(0, 114, 206))
        draw.polygon([(x, y + h), (x + w * 0.55, y), (x + w, y),
                      (x + w * 0.45, y + h)], fill=RED)
        draw.line([x, y + h, x + w * 0.55, y], fill=(247, 219, 0), width=2)
        draw.line([x + w * 0.45, y + h, x + w, y], fill=(247, 219, 0), width=2)


def _smoke(draw, cx, cy, r, col=(120, 120, 120)):
    for dx, dy, rr in ((-r, 0, r * 0.7), (0, -r * 0.6, r * 0.85),
                      (r * 0.9, -r * 0.1, r * 0.65), (r * 0.2, r * 0.4, r * 0.6)):
        draw.ellipse([cx + dx - rr, cy + dy - rr, cx + dx + rr, cy + dy + rr],
                     fill=col)


def draw_hero(draw, tag, x, y, w, h):
    """Flat diagram illustration for a hero panel (x,y,w,h)."""
    if tag == "kerch":
        draw.rectangle([x, y, x + w, y + h], fill=SKY)
        draw.rectangle([x, y + h * 0.55, x + w, y + h], fill=SEA)
        for i in range(6):  # wave ticks
            wx = x + 12 + i * (w - 24) / 5
            draw.arc([wx - 8, y + h * 0.62, wx + 8, y + h * 0.78],
                     200, 340, fill=(120, 170, 200), width=2)
        # bridge deck: left span standing, middle span collapsed
        dy = y + h * 0.42
        draw.rectangle([x, y + h * 0.42, x + w * 0.42, dy + 7], fill=INK)
        draw.rectangle([x + w * 0.62, y + h * 0.42, x + w, dy + 7], fill=INK)
        for px in (0.08, 0.2, 0.32, 0.7, 0.82, 0.93):  # pillars
            draw.rectangle([x + w * px, dy + 7, x + w * px + 5,
                            y + h * 0.62], fill=INK)
        draw.line([x + w * 0.42, dy + 4, x + w * 0.58, y + h * 0.66],
                  fill=INK, width=7)  # fallen span
        _smoke(draw, x + w * 0.52, y + h * 0.3, 13)
        draw.polygon([(x + w * 0.52, y + h * 0.36), (x + w * 0.52 + 8, y + h * 0.3),
                      (x + w * 0.52 + 14, y + h * 0.36)], fill=(255, 170, 0))
        for jx, jy in ((0.12, 0.16), (0.3, 0.1), (0.88, 0.14)):  # jets
            draw.polygon([(x + w * jx, y + h * jy),
                          (x + w * jx - 12, y + h * jy + 4),
                          (x + w * jx - 4, y + h * jy + 7)], fill=INK)
        f = sans_bold(10)
        draw.text((x + 8, y + 8), "CRIMEA", font=f, fill=INK)
        draw.rectangle([x + w * 0.58, y + 6, x + w * 0.58 + 86, y + 20],
                       fill=RED)
        draw.text((x + w * 0.58 + 4, y + 8), "ROAD SPAN DOWN",
                  font=sans_bold(9), fill=WHITE)
        draw.text((x + w - 52, y + h - 18), "RUSSIA", font=f, fill=INK)
    elif tag == "gulf":
        draw.rectangle([x, y, x + w, y + h], fill=SAND)
        # sea band across the middle, pinched into the Strait of Hormuz
        draw.polygon([(x, y + h * 0.42), (x + w * 0.55, y + h * 0.42),
                      (x + w * 0.68, y + h * 0.5), (x + w, y + h * 0.5),
                      (x + w, y + h * 0.86), (x, y + h * 0.86)], fill=SEA)
        # Qeshm island (sand) in the strait
        draw.ellipse([x + w * 0.66, y + h * 0.56, x + w * 0.8, y + h * 0.68],
                     fill=SAND, outline=SAND_DK)
        # Bahrain island (sand dot) in the sea
        draw.ellipse([x + w * 0.2, y + h * 0.58, x + w * 0.27, y + h * 0.66],
                     fill=SAND, outline=SAND_DK)
        f = sans_bold(10)
        draw.text((x + w * 0.42, y + 8), "IRAN", font=f, fill=INK)
        draw.text((x + w * 0.08, y + h * 0.68), "BAHRAIN", font=f, fill=INK)
        draw.text((x + w * 0.62, y + h * 0.42), "QESHM", font=f, fill=INK)
        draw.text((x + w * 0.8, y + h * 0.88), "HORMUZ", font=f, fill=INK)
        # drone path (dashed) Bahrain -> Qeshm, intercepted mid-way
        for t in range(0, 11):
            px = x + w * (0.27 + 0.042 * t)
            py = y + h * (0.62 - 0.008 * t)
            draw.ellipse([px - 1, py - 1, px + 1, py + 1], fill=RED)
        xx, xy = x + w * 0.44, y + h * 0.56
        draw.line([xx - 5, xy - 5, xx + 5, xy + 5], fill=RED, width=3)
        draw.line([xx - 5, xy + 5, xx + 5, xy - 5], fill=RED, width=3)
        draw.rectangle([x + w * 0.3, y + h * 0.24, x + w * 0.3 + 92,
                        y + h * 0.24 + 14], fill=RED)
        draw.text((x + w * 0.3 + 4, y + h * 0.24 + 2), "DRONES DOWNED",
                  font=sans_bold(9), fill=WHITE)
        # jet strike on Qeshm
        draw.polygon([(x + w * 0.6, y + h * 0.6), (x + w * 0.6 - 12, y + h * 0.6 + 4),
                      (x + w * 0.6 - 4, y + h * 0.6 + 7)], fill=INK)
        _smoke(draw, x + w * 0.8, y + h * 0.58, 5)
        draw.rectangle([x + w * 0.52, y + h * 0.74, x + w * 0.52 + 74,
                        y + h * 0.74 + 14], fill=(47, 93, 138))
        draw.text((x + w * 0.52 + 4, y + h * 0.74 + 2), "US STRIKES",
                  font=sans_bold(9), fill=WHITE)
        # tanker with smoke, bottom right in the sea
        draw.rectangle([x + w * 0.84, y + h * 0.7, x + w * 0.95, y + h * 0.78],
                       fill=INK)
        draw.rectangle([x + w * 0.88, y + h * 0.65, x + w * 0.91, y + h * 0.7],
                       fill=INK)
        _smoke(draw, x + w * 0.9, y + h * 0.6, 4, col=(90, 90, 90))
    elif tag == "quad":
        draw.rectangle([x, y, x + w, y + h], fill=(232, 226, 244))
        draw.rectangle([x, y, x + w, y + 24], fill=(107, 78, 155))
        draw.text((x + 10, y + 6), "QUAD LEADERS\u2019 SUMMIT \u00b7 MANILA",
                  font=sans_bold(11), fill=WHITE)
        # table
        ty = y + h * 0.72
        draw.rectangle([x + 14, ty, x + w - 14, ty + 8], fill=(122, 84, 48))
        draw.rectangle([x + 20, ty + 8, x + 28, y + h - 20], fill=(122, 84, 48))
        draw.rectangle([x + w - 28, ty + 8, x + w - 20, y + h - 20],
                       fill=(122, 84, 48))
        flags = [("us", "US"), ("india", "INDIA"), ("japan", "JAPAN"),
                 ("australia", "AUSTRALIA")]
        fw, fh = 44, 28
        gap = (w - 4 * fw - 28) / 3
        for i, (kind, name) in enumerate(flags):
            fx = x + 14 + i * (fw + gap)
            fy = y + 34
            _flag(draw, fx, fy, fw, fh, kind)
            draw.rectangle([fx + fw / 2 - 1, fy + fh, fx + fw / 2 + 1, ty],
                           fill=INK)
            f = sans_bold(9)
            tw = text_w(draw, name, f)
            draw.text((fx + fw / 2 - tw / 2, fy + fh + 4), name, font=f,
                      fill=INK)
        draw.rectangle([x, y + h - 18, x + w, y + h], fill=(107, 78, 155))
        draw.text((x + 10, y + h - 15), "NEW CRITICAL-MINERALS DEALS",
                  font=sans_bold(9), fill=WHITE)


# small flat illustration for a grid card (x,y,w,h)
def draw_mini(draw, tag, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=SKY)
    if tag == "ebola":
        draw.rectangle([x, y + h * 0.55, x + w, y + h], fill=SAND)
        draw.polygon([(x + w * 0.18, y + h * 0.6), (x + w * 0.5, y + h * 0.22),
                      (x + w * 0.82, y + h * 0.6)], fill=WHITE)
        draw.rectangle([x + w * 0.46, y + h * 0.34, x + w * 0.54, y + h * 0.5],
                       fill=RED)
        draw.rectangle([x + w * 0.42, y + h * 0.4, x + w * 0.58, y + h * 0.46],
                       fill=RED)
        tf = sans_bold(8)
        tstr = "11,000+ CASES"
        tw = text_w(draw, tstr, tf)
        draw.rectangle([x + w - tw - 12, y + 6, x + w - 6, y + 20], fill=RED)
        draw.text((x + w - tw - 8, y + 8), tstr, font=tf, fill=WHITE)
        for dx, dy in ((0.1, 0.3), (0.9, 0.35)):
            draw.ellipse([x + w * dx - 4, y + h * dy - 4, x + w * dx + 4,
                          y + h * dy + 4], fill=RED)
    elif tag == "cop31":
        cx, cy, r = x + w * 0.24, y + h * 0.5, h * 0.36
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(120, 190, 120),
                     outline=(47, 93, 138), width=2)
        draw.arc([cx - r * 0.45, cy - r, cx + r * 0.45, cy + r], 270, 90,
                 fill=(47, 93, 138), width=1)
        draw.arc([cx - r * 0.45, cy - r, cx + r * 0.45, cy + r], 90, 270,
                 fill=(47, 93, 138), width=1)
        draw.line([cx - r, cy, cx + r, cy], fill=(47, 93, 138), width=1)
        draw.rectangle([x + w * 0.62, y + h * 0.45, x + w * 0.7, y + h * 0.85],
                       fill=WHITE, outline=INK)
        draw.rectangle([x + w * 0.62, y + h * 0.62, x + w * 0.7, y + h * 0.85],
                       fill=RED)
        draw.ellipse([x + w * 0.58, y + h * 0.78, x + w * 0.74, y + h * 0.97],
                     fill=RED)
        tf = sans_bold(8)
        t1 = "DRAFT: PHASE-OUT"
        tw = text_w(draw, t1, tf)
        draw.rectangle([x + w - tw - 12, y + 4, x + w - 6, y + 18],
                       fill=(47, 93, 138))
        draw.text((x + w - tw - 8, y + 6), t1, font=tf, fill=WHITE)
    elif tag == "measles":
        for i, kind in enumerate(("us", "mexico", "bolivia")):
            _flag(draw, x + 8 + i * 52, y + 8, 44, 26, kind)
        for dx, dy in ((0.15, 0.65), (0.5, 0.7), (0.85, 0.62)):
            draw.ellipse([x + w * dx - 5, y + h * dy - 5, x + w * dx + 5,
                          y + h * dy + 5], fill=RED)
            for a in range(8):
                import math
                ax = x + w * dx + 8 * math.cos(a * math.pi / 4)
                ay = y + h * dy + 8 * math.sin(a * math.pi / 4)
                draw.line([x + w * dx, y + h * dy, ax, ay], fill=RED, width=1)
        draw.rectangle([x, y + h - 15, x + w, y + h], fill=RED)
        draw.text((x + 6, y + h - 13), "MEASLES-FREE STATUS LOST",
                  font=sans_bold(8), fill=WHITE)
    elif tag == "nvidia":
        draw.rectangle([x, y, x + w, y + h], fill=(16, 24, 16))
        draw.rectangle([x + 10, y + 12, x + 40, y + 42], fill=(20, 60, 20),
                       outline=(118, 185, 0), width=2)
        draw.text((x + 16, y + 20), "AI", font=sans_bold(14),
                  fill=(118, 185, 0))
        for i, bh in enumerate((8, 16, 24, 34)):
            draw.rectangle([x + 52 + i * 14, y + h - 10 - bh,
                            x + 62 + i * 14, y + h - 10], fill=(118, 185, 0))
        draw.text((x + 110, y + 6), "$115.8BN", font=sans_bold(13),
                  fill=(118, 185, 0))
        draw.text((x + 110, y + 22), "DOW \u2212849", font=sans_bold(10),
                  fill=RED)
    elif tag == "gaza":
        draw.rectangle([x, y + h * 0.6, x + w, y + h], fill=SAND)
        for i, cx in enumerate((0.25, 0.55, 0.82)):
            draw.polygon([(x + w * cx - 22, y + h * 0.62),
                          (x + w * cx, y + h * 0.3),
                          (x + w * cx + 22, y + h * 0.62)], fill=WHITE)
        draw.rectangle([x + w * 0.66, y + h * 0.74, x + w - 8, y + h * 0.9],
                       fill=WHITE, outline=INK)
        draw.text((x + w * 0.66 + 4, y + h * 0.77), "AID",
                  font=sans_bold(9), fill=RED)
        tf = sans_bold(8)
        tstr = "1.4M FACE ACUTE HUNGER"
        tw = text_w(draw, tstr, tf)
        draw.rectangle([x + w - tw - 12, y + 4, x + w - 6, y + 18], fill=RED)
        draw.text((x + w - tw - 8, y + 6), tstr, font=tf, fill=WHITE)
    elif tag == "mongolia":
        _flag(draw, x + 10, y + 8, 40, 26, "mongolia")
        draw.rectangle([x + 60, y + 10, x + w - 10, y + h - 10], fill=WHITE,
                       outline=INK)
        draw.text((x + 66, y + 14), "RESIGNATION", font=sans_bold(9), fill=INK)
        for i in range(3):
            draw.line([x + 66, y + 28 + i * 7, x + w - 16, y + 28 + i * 7],
                      fill=GREY, width=1)
        draw.line([x + 66, y + h - 18, x + w - 40, y + h - 18], fill=INK, width=1)
    elif tag == "serbia":
        import math
        ccx, ccy, rr = x + w * 0.5, y + h * 0.92, h * 0.62
        for i in range(9):  # hemicycle arc, red students vs blue bloc
            a = math.pi * (0.08 + 0.84 * i / 8)
            sx = ccx + rr * math.cos(a)
            sy = ccy - rr * math.sin(a) * 0.75
            draw.ellipse([sx - 5, sy - 5, sx + 5, sy + 5],
                         fill=RED if i < 5 else (47, 93, 138))
        draw.text((x + 8, y + 4), "STUDENTS 140", font=sans_bold(10), fill=RED)
        tw = text_w(draw, "VU\u010cI\u0106 103", sans_bold(10))
        draw.text((x + w - tw - 8, y + 4), "VU\u010cI\u0106 103",
                  font=sans_bold(10), fill=(47, 93, 138))
    elif tag == "dhaka":
        draw.rectangle([x, y + h * 0.5, x + w, y + h], fill=SAND)
        draw.rectangle([x + 10, y + h * 0.3, x + 60, y + h * 0.62], fill=GREY)
        draw.rectangle([x + 66, y + h * 0.42, x + 96, y + h * 0.62], fill=GREY)
        draw.rectangle([x + 20, y + h * 0.18, x + 26, y + h * 0.3], fill=GREY)
        for i in range(4):  # workers
            wx = x + 112 + i * 16
            draw.ellipse([wx - 4, y + h * 0.52, wx + 4, y + h * 0.6], fill=INK)
            draw.rectangle([wx - 4, y + h * 0.6, wx + 4, y + h * 0.82], fill=INK)
        draw.rectangle([x + w - 74, y + 6, x + w - 6, y + 22], fill=WHITE,
                       outline=INK)
        draw.text((x + w - 70, y + 9), "TK 30,000", font=sans_bold(9), fill=INK)
        draw.text((x + w - 70, y + 9 + 10), "MINIMUM", font=sans_bold(8),
                  fill=RED)
    elif tag == "crash":
        # An-12 silhouette, nose-down over mountains
        draw.polygon([(x + 14, y + h * 0.34), (x + 20, y + h * 0.28),
                      (x + w * 0.6, y + h * 0.3), (x + w * 0.6, y + h * 0.38),
                      (x + 20, y + h * 0.4)], fill=GREY)
        draw.polygon([(x + w * 0.56, y + h * 0.3), (x + w * 0.72, y + h * 0.16),
                      (x + w * 0.76, y + h * 0.32)], fill=GREY)
        draw.polygon([(x + w * 0.3, y + h * 0.3), (x + w * 0.38, y + h * 0.16),
                      (x + w * 0.44, y + h * 0.3)], fill=GREY)
        _smoke(draw, x + w * 0.78, y + h * 0.42, 8)
        draw.polygon([(x, y + h), (x + w * 0.25, y + h * 0.72),
                      (x + w * 0.5, y + h), (x + w * 0.75, y + h * 0.78),
                      (x + w, y + h)], fill=(150, 160, 150))
        tf = sans_bold(8)
        tstr = "ALL 19 ABOARD KILLED"
        tw = text_w(draw, tstr, tf)
        draw.rectangle([x + w - tw - 12, y + 6, x + w - 6, y + 20], fill=INK)
        draw.text((x + w - tw - 8, y + 8), tstr, font=tf, fill=WHITE)
    elif tag == "trial":
        # gavel: diagonal handle + head, over a sound block
        draw.line([x + w * 0.3, y + h * 0.7, x + w * 0.62, y + h * 0.3],
                  fill=(122, 84, 48), width=6)
        draw.line([x + w * 0.56, y + h * 0.16, x + w * 0.78, y + h * 0.34],
                  fill=(122, 84, 48), width=10)
        draw.rectangle([x + w * 0.2, y + h * 0.74, x + w * 0.44, y + h * 0.82],
                       fill=(122, 84, 48))
        tf = sans_bold(9)
        tstr = "5 CHARGES"
        tw = text_w(draw, tstr, tf)
        draw.rectangle([x + w - tw - 12, y + 6, x + w - 6, y + 20], fill=RED)
        draw.text((x + w - tw - 8, y + 8), tstr, font=tf, fill=WHITE)


# ---- world map (simplified equirectangular continents) --------------------
CONTINENTS = {
    "north_america": [(-168, 66), (-140, 70), (-125, 72), (-110, 73),
                      (-95, 80), (-85, 80), (-75, 73), (-65, 62), (-55, 52),
                      (-60, 47), (-70, 42), (-75, 35), (-80, 26), (-85, 30),
                      (-90, 21), (-95, 19), (-105, 20), (-115, 28),
                      (-125, 40), (-125, 49), (-140, 60), (-155, 58)],
    "greenland": [(-58, 64), (-45, 60), (-30, 68), (-22, 70), (-30, 76),
                  (-55, 76), (-58, 70)],
    "south_america": [(-80, 10), (-75, 11), (-70, 12), (-62, 10), (-52, 5),
                      (-50, 0), (-44, -3), (-35, -8), (-39, -15), (-41, -23),
                      (-48, -28), (-58, -35), (-65, -41), (-70, -50),
                      (-74, -53), (-70, -45), (-73, -37), (-72, -20),
                      (-77, -12), (-81, -5), (-80, 2)],
    "africa": [(-17, 15), (-10, 31), (-5, 35), (10, 37), (20, 32), (30, 31),
               (35, 28), (43, 12), (51, 11), (48, 0), (40, -10), (35, -18),
               (32, -26), (28, -33), (20, -35), (15, -27), (12, -18),
               (9, -1), (9, 4), (-8, 4), (-13, 8)],
    "europe": [(-10, 36), (-9, 43), (-2, 44), (-1, 46), (-4, 48), (0, 50),
               (3, 52), (8, 55), (8, 58), (12, 56), (18, 56), (21, 55),
               (24, 58), (24, 60), (30, 60), (28, 62), (24, 65), (20, 70),
               (15, 70), (10, 68), (5, 60), (5, 58), (-2, 55), (-5, 50),
               (-10, 43)],
    "uk": [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (0, 53),
           (1, 51), (-3, 50)],
    "asia": [(28, 41), (33, 42), (36, 36), (39, 36), (43, 39), (47, 39),
             (50, 40), (54, 38), (57, 37), (60, 25), (62, 25), (66, 25),
             (70, 23), (72, 20), (75, 15), (77, 8), (80, 7), (80, 13),
             (84, 19), (88, 22), (91, 22), (93, 17), (95, 15), (97, 10),
             (99, 8), (101, 6), (103, 2), (104, 8), (106, 10), (109, 13),
             (108, 18), (106, 21), (110, 20), (113, 22), (117, 23),
             (120, 25), (121, 28), (120, 31), (122, 32), (121, 37),
             (120, 39), (124, 40), (127, 40), (129, 42), (131, 43),
             (135, 44), (137, 46), (140, 48), (142, 50), (142, 54),
             (141, 59), (137, 60), (136, 61), (139, 65), (142, 71),
             (150, 71), (158, 69), (162, 66), (170, 67), (178, 66),
             (178, 62), (170, 61), (163, 60), (160, 56), (158, 52),
             (156, 51), (154, 59), (150, 59), (142, 59), (141, 55),
             (140, 50), (138, 46), (135, 44), (132, 43), (130, 42),
             (127, 40), (124, 39), (120, 35), (120, 31), (117, 30),
             (114, 28), (110, 25), (108, 20), (105, 18), (103, 10),
             (100, 8), (98, 12), (96, 16), (93, 20), (91, 22), (89, 22),
             (86, 20), (83, 17), (80, 13), (77, 8), (74, 12), (72, 20),
             (69, 22), (66, 25), (63, 25), (60, 25), (57, 27), (54, 27),
             (52, 28), (50, 29), (48, 30), (45, 29), (43, 29), (40, 31),
             (37, 36), (34, 36), (31, 36), (28, 38)],
    "japan": [(130, 31), (132, 33), (134, 34), (137, 35), (139, 37),
              (141, 39), (141, 42), (143, 43), (145, 44), (142, 44),
              (140, 40), (138, 36), (136, 34), (133, 34), (131, 32)],
    "australia": [(113, -22), (114, -30), (115, -35), (120, -34),
                  (124, -33), (129, -32), (132, -32), (136, -35),
                  (140, -38), (145, -38), (150, -37), (153, -32),
                  (153, -27), (150, -23), (146, -19), (142, -15),
                  (142, -11), (137, -12), (135, -15), (132, -12),
                  (130, -13), (126, -14), (122, -17), (118, -20)],
    "new_zealand": [(167, -45), (170, -42), (174, -38), (177, -38),
                    (175, -40), (172, -43), (168, -46)],
}


def draw_map(draw, x, y, w, h):
    """World map: pale sea, sand continents, numbered pins 1-13, dots 14-43."""
    draw.rectangle([x, y, x + w, y + h], fill=SEA)
    draw.rectangle([x, y, x + w, y + h], outline=GREY, width=1)

    def proj(lon, lat):
        lat = max(-58, min(84, lat))
        px = x + (lon + 180) / 360.0 * w
        py = y + (84 - lat) / 142.0 * h
        return (px, py)

    for poly in CONTINENTS.values():
        draw.polygon([proj(lon, lat) for lon, lat in poly], fill=SAND,
                     outline=SAND_DK)
    # dots first (under pins), then numbered pins
    for n, (lon, lat) in DOTS.items():
        px, py = proj(lon, lat)
        col = REGION[DOT_REGION[n]]
        draw.ellipse([px - 3, py - 3, px + 3, py + 3], fill=col,
                     outline=WHITE, width=1)
    for n, (lon, lat) in PINS.items():
        px, py = proj(lon, lat)
        region = CARDS[n - 1][1]
        num_badge(draw, px, py, n, 8, REGION[region])


def draw_legend(draw, x, y):
    items = [("Americas", "AMERICAS"), ("Europe", "EUROPE"),
             ("Middle East", "MIDDLE EAST"), ("Asia", "ASIA"),
             ("Africa", "AFRICA"), ("Oceania", "OCEANIA"),
             ("Global", "GLOBAL")]
    f = sans(10)
    cx = x
    for name, reg in items:
        col = REGION[reg]
        draw.ellipse([cx, y + 1, cx + 8, y + 9], fill=col)
        draw.text((cx + 11, y), name, font=f, fill=INK)
        cx += 11 + text_w(draw, name, f) + 12
    draw.text((cx + 2, y), "Pins: stories 1\u201313 \u00b7 dots: 14\u201343",
              font=f, fill=GREY)


# ---- page composition ----------------------------------------------------
def render():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # kicker row
    d.text((MARGIN, 8), "THE WORLD\u2019S NEWS IN ONE PICTURE",
           font=sans_bold(11), fill=RED)
    right = "43 STORIES \u00b7 6 CONTINENTS \u00b7 ALL FROM TUESDAY"
    d.text((W - MARGIN - text_w(d, right, sans_bold(11)), 8), right,
           font=sans_bold(11), fill=INK)

    # masthead
    mast = "Tuesday 17 November 2026"
    mf = fit_font(mast, [serif_black(68), serif_black(64), serif_black(60)],
                  CW, d)
    d.text((MARGIN, 24), mast, font=mf, fill=INK)
    d.rectangle([MARGIN, 96, W - MARGIN, 99], fill=INK)
    d.rectangle([MARGIN, 102, W - MARGIN, 103], fill=INK)

    # hero row: 3 panels
    gap = 10
    pw = (CW - 2 * gap) // 3
    hy, hh = 110, 114          # illustration band
    strip_h = 16
    hy_text = hy + hh + strip_h + 6
    for i, card in enumerate(CARDS[:3]):
        n, region, topic, head, deck, tag, strip = card
        px = MARGIN + i * (pw + gap)
        draw_hero(d, tag, px, hy, pw, hh)
        d.rectangle([px, hy + hh, px + pw, hy + hh + strip_h], fill=DARK_BAND)
        sf = sans_bold(9)
        d.text((px + 6, hy + hh + 3), strip, font=sf, fill=WHITE)
        num_badge(d, px + 9, hy_text + 6, n, 9, REGION[region])
        kicker(d, px + 20, hy_text, region, topic, size=11)
        hl = wrap(d, head, serif_bold(18), pw)
        y = draw_wrapped(d, hl[:2], px, hy_text + 15, serif_bold(18), INK, 21)
        dl = wrap(d, deck, sans(12), pw)
        draw_wrapped(d, dl[:2], px, y + 2, sans(12), INK, 15)

    d.line([MARGIN, 336, W - MARGIN, 336], fill=INK, width=1)

    # grid: 10 cards, 5 cols x 2 rows
    gw = (CW - 4 * 8) // 5
    gh = 136
    gy0 = 344
    for idx, card in enumerate(CARDS[3:]):
        n, region, topic, head, deck, tag, strip = card
        row, col = divmod(idx, 5)
        gx = MARGIN + col * (gw + 8)
        gy = gy0 + row * (gh + 6)
        draw_mini(d, tag, gx, gy, gw, 46)
        d.rectangle([gx, gy + 46, gx + gw, gy + 59], fill=DARK_BAND)
        d.text((gx + 5, gy + 49), strip, font=sans_bold(8), fill=WHITE)
        num_badge(d, gx + 8, gy + 68, n, 8, REGION[region])
        kicker(d, gx + 19, gy + 63, region, topic, size=10)
        hl = wrap(d, head, serif_bold(15), gw)
        y = draw_wrapped(d, hl[:2], gx, gy + 77, serif_bold(15), INK, 17)
        dl = wrap(d, deck, sans(11), gw)
        draw_wrapped(d, dl[:2], gx, y + 1, sans(11), INK, 13)

    d.line([MARGIN, 628, W - MARGIN, 628], fill=INK, width=1)

    # bottom zone: map (left) + briefs (right)
    by = 636
    d.text((MARGIN, by), "WHERE IT HAPPENED", font=sans_bold(13), fill=RED)
    bx = MARGIN + 508
    d.text((bx, by), "ALSO ON TUESDAY 17 NOVEMBER", font=sans_bold(13),
           fill=RED)
    map_w, map_h = 440, 272
    draw_map(d, MARGIN, by + 22, map_w, map_h)
    draw_legend(d, MARGIN, by + 22 + map_h + 8)

    # briefs, two columns of 15
    bf = sans_cond(10)
    bfb = sans_cond_bold(10)
    col_w = (CW - map_w - 16 - 12) // 2
    for i, (n, place, txt) in enumerate(BRIEFS):
        col, row = divmod(i, 15)
        bx2 = MARGIN + map_w + 16 + col * (col_w + 12)
        by2 = by + 24 + row * 18
        num_badge(d, bx2 + 7, by2 + 6, n, 7, REGION[DOT_REGION[n]])
        line = f"{place}: {txt}"
        d.text((bx2 + 17, by2), line, font=bf, fill=INK)

    # footer
    d.line([MARGIN, 948, W - MARGIN, 948], fill=INK, width=1)
    ver = ("Every story here happened or was first reported on Tuesday "
           "17 November 2026. Disputed claims are attributed.")
    src = "Sources: Reuters, AP, AFP, BBC, Al Jazeera, WHO, UN."
    d.text((MARGIN, 956), ver, font=sans(11), fill=INK)
    d.text((W - MARGIN - text_w(d, src, sans(11)), 956), src,
           font=sans(11), fill=INK)
    d.text((MARGIN, 974), "Original drawings. 43 stories \u00b7 6 continents "
           "\u00b7 one day.", font=sans(10), fill=GREY)
    d.text((W - MARGIN - text_w(d, "Tuesday 17 November 2026", sans_bold(10)),
            974), "Tuesday 17 November 2026", font=sans_bold(10), fill=GREY)
    return img


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if not out_dir:
        out_dir = "/output" if os.path.isdir("/output") else str(
            Path(__file__).resolve().parent)
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    img = render()
    img.save(Path(out_dir) / "entry.png", format="PNG", optimize=True)
    print(f"wrote {Path(out_dir) / 'entry.png'} ({img.size[0]}x{img.size[1]})")


if __name__ == "__main__":
    main()
