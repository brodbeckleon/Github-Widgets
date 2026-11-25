#!/usr/bin/env python3
"""Generates the looping pixel-art Shinkansen banner (Series 0 on a viaduct below Mt Fuji).

    python3 scripts/train.py   ->  resources/svg/train_dark.svg, resources/svg/train_light.svg

Everything is drawn on a 280x80 pixel grid and scaled 3x. The train stands still;
the scenery scrolls at different speeds (parallax) and each scrolling layer is a seamless tile.
light = dusk (pink-lit snow cap, lavender clouds), dark = moonlit night with lit windows.
No third-party packages needed.
"""
import math
import random
from pathlib import Path

GW, GH, SCALE = 280, 80, 3
TOP = 36                   # train roof row; the body is 16 rows tall
BOT = 52                   # bogie row
RAIL = 53                  # parapet in front of the wheels
DECK = 54                  # viaduct deck surface
GROUND = 71                # ground line under the viaduct
WIRE = 31                  # contact wire
MAST = 70                  # catenary mast spacing

PALETTES = {
    "light": dict(
        sky=["#3c5494", "#455e9c", "#5069a5", "#5d73ab", "#6c7db0", "#7d86b3",
             "#908db4", "#a294b3", "#b39bb1", "#c2a2ae", "#cfa9ac"],
        # snow: lit, lit gully, shade, shade gully / rock: same order, then two haze tones
        snow=["#fff1df", "#f7cfb6", "#cfa6c0", "#ab90ba"],
        rock=["#6b669f", "#5e5b95", "#504f88", "#47477e", "#7275a8", "#8083b0"],
        cloud=dict(rim="#f6bd98", lit="#dda5a6", mid="#ab8fb0", sh="#8479a8", dk="#69649b"),
        streak=["#8a7fb0", "#a394b8", "#d3a3a4", "#746fa6"],
        hill=["#3f3f74", "#363a62", "#74506a", "#2e3350"],
        tower="#8d8fae", tower2="#62658a", pole="#5e5648", pole2="#93876c", wire="#39395a",
        body="#f1ecde", body2="#d9d2c2", roof="#c3c5cc", roof2="#7d8090", blue="#2462b6",
        blue2="#17437f", glass="#2c3654", cabglass="#1e2436", door="#d3ccbc", hi="#fffdf6",
        head="#a3abbe", glint="#e3e7f0", gap="#3a3a48", panto="#2f2f3a", under="#1c2a4c",
        bogie="#22242e", wheel="#666c80",
        rail_hi="#d9b6ac", rail_lo="#a98b88", deck="#9b8b7c", face="#3c2e28",
        shadow="#241c18", hazard="#e0a040", wall="#563a20", wall2="#4a3019",
        pier="#7e6c4a", pier2="#685838", pier3="#93805c", fence="#c9a39d", mesh="#6a4a36",
        board="#6e4e30", board2="#5a3e24", red="#bf3a2c", red2="#922c22", white="#e8e2d6",
        white2="#c8c0b2", bottle="#4e7050", bottle2="#90b088", panel="#2a2626", label="#e6833a",
        bin="#d8d2c4", cone="#e0682c", cone2="#f2e6d8", booth="#8b7656", booth2="#6f5c40",
        win="#3d3b6c", sign="#ece6da", ground="#3a2e24",
        meadow=["#93a060", "#7f8f52", "#6b7c46", "#d2b84e"],            # far, mid, near, rapeseed
        tree=["#3f5c46", "#2e4638", "#6a8450", "#4e3c30"],              # lit, shade, rim, trunk
        water=["#7586b8", "#d3aab4", "#55669a"], house=["#d6cbb6", "#56464e", "#3d3b6c"],
        grass=["#836a3c", "#6e5832", "#a08a54", "#5a482a", "#b49c62"],
    ),
    "dark": dict(
        sky=["#070b20", "#090d25", "#0b102a", "#0d1330", "#0f1635", "#11193b",
             "#131c41", "#151f47", "#17224c", "#192551", "#1b2856"],
        snow=["#f1f5ff", "#cdd7f0", "#919dca", "#7582b4"],
        rock=["#333e70", "#2c3666", "#222b58", "#1d254e", "#2c3768", "#303b6e"],
        cloud=dict(rim="#8e9cc8", lit="#5c6a9c", mid="#3a4677", sh="#2b3564", dk="#222b55"),
        streak=["#2a3462", "#36407a", "#4a5488", "#222a56"],
        hill=["#141a38", "#11172c", "#1f2140", "#0d1224"],
        tower="#4b5274", tower2="#343a58", pole="#2c2a2c", pole2="#48443e", wire="#56608a",
        body="#c9cdd8", body2="#aeb2c0", roof="#9a9eac", roof2="#5e6274", blue="#2a56ae",
        blue2="#1c3a80", glass="#ffd877", cabglass="#a58c58", door="#aeb2c0", hi="#e9edf6",
        head="#fff6cc", glint="#fffdf0", gap="#262a38", panto="#1c1f28", under="#141c36",
        bogie="#16181e", wheel="#4a4e5a",
        rail_hi="#7a6a78", rail_lo="#5a4e5c", deck="#4a4450", face="#1c1820",
        shadow="#100d12", hazard="#9a7030", wall="#24180e", wall2="#1c130b",
        pier="#3e3830", pier2="#322c24", pier3="#4a4238", fence="#6e5c62", mesh="#2e221c",
        board="#33261a", board2="#281d13", red="#e04a38", red2="#a8352a", white="#f4f0e2",
        white2="#d8d2c2", bottle="#9be08a", bottle2="#e8ffd8", panel="#3a3434", label="#ff9a4a",
        bin="#7a766c", cone="#9a4a24", cone2="#b8aca0", booth="#3e3428", booth2="#2e261c",
        win="#ffd36b", sign="#d8d2c0", ground="#16120e",
        meadow=["#2a3833", "#24312d", "#1d2927", "#444a30"],
        tree=["#1a292a", "#111c1e", "#2a3d3a", "#18130f"],
        water=["#1d2b54", "#7f93c8", "#141f42"], house=["#4c4c5c", "#20202c", "#ffd36b"],
        grass=["#3a3220", "#2e2819", "#4a4028", "#241f14", "#55492e"],
    ),
}


def hsh(*a):
    """Deterministic hash of ints -> [0, 1)."""
    v = 2166136261
    for x in a:
        v = ((v ^ (int(x) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
        v ^= v >> 13
    return (v & 0xFFFFFF) / float(1 << 24)


class Layer:
    def __init__(self, tile=None):
        self.tile = tile
        self.px = {}

    def set(self, x, y, c):
        if c is None or not (0 <= y < GH):
            return
        if self.tile:
            x %= self.tile
        elif not (0 <= x < GW):
            return
        self.px[(x, y)] = c

    def rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, c)

    def svg(self):
        rows = {}
        for (x, y), c in self.px.items():
            rows.setdefault(y, {})[x] = c
        paths = {}
        for y, cols in sorted(rows.items()):
            xs = sorted(cols)
            i = 0
            while i < len(xs):
                x0, c = xs[i], cols[xs[i]]
                j = i
                while j + 1 < len(xs) and xs[j + 1] == xs[j] + 1 and cols[xs[j + 1]] == c:
                    j += 1
                w = xs[j] - x0 + 1
                paths.setdefault(c, []).append(f"M{x0} {y}h{w}v1h-{w}z")
                i = j + 1
        return "".join(f'<path fill="{c}" d="{"".join(d)}"/>' for c, d in paths.items())


# ---------------------------------------------------------------- sky & far scenery

def sky_svg(p):
    """Horizontal bands, each fading into the next through one checkerboard row."""
    cols = p["sky"]
    step = DECK / len(cols)
    out = []
    for i, c in enumerate(cols):
        y0 = round(i * step)
        y1 = round((i + 1) * step) if i < len(cols) - 1 else GH
        out.append(f'<rect x="0" y="{y0}" width="{GW}" height="{y1 - y0}" fill="{c}"/>')
    for i in range(1, len(cols)):
        y0 = round(i * step)
        out.append(f'<path d="M{i % 2} {y0 - 1}.5H{GW}" stroke="{cols[i]}" stroke-dasharray="1 1"/>')
    return "".join(out)


FUJI_X, FUJI_Y = 100, 3


def fuji_layer(p, moonlit=False):
    """Static: far enough away that it does not move during the loop.

    Seen from the south like from the Tokaido line: flat crater rim, concave flanks that
    flare out towards the base, Mt Hoei as a shoulder on the right flank, and a snow cap
    that runs down the gullies in streaks. Lit from the left at dusk, from the moon (right) at night.
    """
    L = Layer()
    snow, rock = p["snow"], p["rock"]
    H, FLARE, RIM, RIDGES = 60.0, 90.0, 6.0, 34

    def half(dy):
        return RIM + -FLARE * math.log(1 - (dy + 0.6) / H)

    for y in range(FUJI_Y, TOP + 10):
        dy = y - FUJI_Y
        w = half(dy)
        hoei = 3.2 * math.exp(-((dy - 17) / 2.4) ** 2)            # shoulder on the right flank
        for x in range(int(FUJI_X - w), int(FUJI_X + w + hoei) + 1):
            if dy == 0 and x - FUJI_X in (-3, -2, -1, 0, 4, 5):    # notches in the crater rim
                continue
            n = (x - FUJI_X) / w                                   # -1 .. 1 across the cone
            q = (n + 1) * RIDGES / 2
            k, fr = int(q), q - int(q)
            side = -n if moonlit else n
            shade = side > 0.22 + 0.3 * (hsh(k, 1) - 0.5)
            gully = (fr < 0.45) if moonlit else (fr > 0.55)        # far side of each ridge
            tone = (2 if shade else 0) + (1 if gully and hsh(k, 5) < 0.6 else 0)
            line = 10 + 6 * hsh(k, 2)                              # snow line of this ridge
            if 0.3 < fr < 0.75 and hsh(k, 3) > 0.5:
                line += 2 + 5 * hsh(k, 4)                          # snow stays longer in gullies
            if n > 1:                                              # Mt Hoei: bare rock, crater in shade
                c = rock[3] if dy < 17 else rock[2]
            elif dy < line:
                c = snow[tone]
            elif dy < line + 1.2 and not gully:
                c = snow[3] if shade else snow[2]                  # thin dusting below the cap
            elif dy > 24 + 6 * hsh(x // 2, y):
                c = rock[5] if dy > 31 + 4 * hsh(x // 3, y, 1) else rock[4]   # haze at the base
            else:
                c = rock[tone]
            L.set(x, y, c)
    return L


def clouds_layer(p):
    """Cloud belt around the foot of the mountain: lit puffs in loose groups with a flat base."""
    T = 560
    L = Layer(T)
    c = p["cloud"]
    rnd = random.Random(21)
    puffs = []
    x = 0
    while x < T:
        dens = 0.5 + 0.5 * math.sin(2 * math.pi * (3 * x / T) + 2.4)
        if dens > 0.3:
            r = rnd.randint(3, 4 + round(4 * dens))
            puffs.append((x, 37 - r + rnd.randint(0, 3), r))
        x += rnd.randint(4, 9)
    puffs.sort(key=lambda q: q[1])
    for cx, cy, r in puffs:
        for dy in range(-r, r + 1):
            y = cy + dy
            if y > 38:
                continue
            for dx in range(-int(r * 1.35), int(r * 1.35) + 1):
                nx, ny = dx / (r * 1.35), dy / r
                d = math.hypot(nx, ny)
                if d > 1:
                    continue
                b = -0.45 * nx - 0.9 * ny
                if d > 0.8 and b > 0.35:
                    col = c["rim"]
                elif b > 0.3:
                    col = c["lit"]
                elif b > -0.15:
                    col = c["mid"]
                elif b > -0.55:
                    col = c["sh"]
                else:
                    col = c["dk"]
                L.set(cx + dx, y, col)
    for x in range(T):                             # flat dark base under each group
        if any((x, y) in L.px for y in range(34, 39)):
            L.set(x, 38, c["dk"])
            L.set(x, 39, c["dk"])
            if hsh(x // 3, 5) < 0.6:
                L.set(x, 40, c["dk"])
    return L


def streaks_layer(p):
    """Thin stratus lines below the cloud belt, like in a dusk sky."""
    T = 560
    L = Layer(T)
    rnd = random.Random(4)
    s = p["streak"]
    for y in range(39, 47):
        x = rnd.randrange(T)
        for _ in range(3):
            n = rnd.randint(25, 120)
            col = s[2] if rnd.random() < 0.2 else rnd.choice((s[0], s[1], s[3]))
            for i in range(n):
                L.set(x + i, y, col)
            x += n + rnd.randint(20, 110)
    return L


def hills_layer(p):
    """Foothills on the horizon; dark enough that the cream nose stands out against them."""
    T = 560
    L = Layer(T)
    h = p["hill"]
    for x in range(T):
        top = int(45.5 - 2.5 * math.sin(2 * math.pi * x / T + 0.6) - 1.5 * math.sin(2 * math.pi * x / 140 + 1)
                  - 0.8 * math.sin(2 * math.pi * x / 40))
        for y in range(top, DECK):
            if y > 51:
                col = h[3]
            elif y - top < 3 and (x + 3 * y) % 41 < 9:
                col = h[2]                         # last light catching the ridge
            elif (x * 7 + y * 3) % 11 == 0 or y > 49:
                col = h[1]
            else:
                col = h[0]
            L.set(x, y, col)
    return L


# ---------------------------------------------------------------- railway

def poles_layer(p):
    """Catenary masts with the sagging messenger wire, and pylons; same speed as the viaduct."""
    T = 560
    L = Layer(T)
    for tx in (38, 318):                           # power pylons further back
        for y in range(21, DECK):
            L.set(tx, y, p["tower"])
            L.set(tx + 2, y, p["tower2"])
            L.set(tx + 1, y, p["tower"] if (y % 4) in (0, 1) else None)
        L.rect(tx - 2, 23, 7, 1, p["tower2"])
        L.rect(tx - 1, 27, 5, 1, p["tower2"])
    for x in range(T):                             # messenger wire hangs between the masts
        u = ((x - 10) % MAST) / MAST * 2 - 1
        L.set(x, WIRE - 4 + round(2.4 * (1 - u * u)), p["wire"])
    for mx in range(10, T, MAST):
        L.rect(mx, 25, 1, DECK - 25, p["pole"])
        L.rect(mx + 1, 25, 1, DECK - 25, p["pole2"])
        L.rect(mx - 1, 27, 8, 1, p["pole"])        # cantilever
        L.set(mx + 6, 28, p["pole"])
        for i in range(1, 4):                      # stay
            L.set(mx + 1 + i, 27 + i, p["pole"])
        L.set(mx + 5, WIRE - 1, p["pole"])         # steady arm down to the contact wire
    return L


# Head of the Series 0, drawn facing left (tip in column 0) and mirrored when stamped.
# Rows run from two above the roof (horn) to one below the skirt (pilot).
#   h lit top edge of the hood   w ivory   s ivory in shade   B blue   D dark blue
#   g cab glass (raked 45 degrees, unframed)   L lamp disc   i glint on the lamp   e E crew door edge on ivory / on blue
NOSE = [
    "                    www   ",
    "                    w     ",
    "              wwwwwwwwwwww",
    "             ggggggwwwwwww",
    "            gggggggwwwwwww",
    "           ggggggggwweweww",
    "        hhhwwwwwwwwwBEBEBB",
    "    hhhhwwwwwwwwwBBBBEgEBB",
    "  hhwwwwwwwwwwwBBBBBBEgEBB",
    " hwwwwwwwwwwwwwBBBBBBEBEBB",
    "hwwLiwwwwwwwwwwwwBBBBEBEBB",
    "wwwLLwwwwwwwwwwwwwwwweweww",
    "wwwwwwwwwwwwwwwwwwwwweweww",
    " swwwwwwwwwwwwwwwwwwweweww",
    "  sssssssssssssssssssesess",
    "  BBBBBBBBBBBBBBBBBBBBBBBB",
    " BBBBBBBBBBBBBBBBBBBBBBBBB",
    " DDDDDDDDDDDDDDDDDDDDDDDDD",
    "  BBBBBBB                 ",
]
NOSE = [row[::-1] for row in NOSE]
SIDE = "rrwwBBBBBwwwsBBD"                          # one column of the car body, roof to skirt
HEAD_X = 216                                       # tip of the nose
CAR = 100                                          # car length
LAMP_Y = TOP + 8                                   # lamp rows: LAMP_Y, LAMP_Y + 1


def draw_train(p):
    L = Layer()
    key = dict(r="roof", h="hi", w="body", s="body2", B="blue", D="blue2", g="cabglass",
               L="head", i="glint", e="door", E="blue2")
    nose_x = HEAD_X - len(NOSE[0]) + 1
    joints = [HEAD_X - CAR, HEAD_X - 2 * CAR]      # the tail runs off-screen to the left

    for x in range(0, nose_x):
        for r, ch in enumerate(SIDE):
            L.set(x, TOP + r, p[key[ch]])
    for r, row in enumerate(NOSE):
        assert len(row) == len(NOSE[0]), row
        for i, ch in enumerate(row):
            if ch != " ":
                L.set(nose_x + i, TOP - 2 + r, p[key[ch]])

    def door(d):
        for dx in (0, 2):
            L.rect(d + dx, TOP + 3, 1, 1, p["door"])
            L.rect(d + dx, TOP + 4, 1, 5, p["blue2"])
            L.rect(d + dx, TOP + 9, 1, 4, p["door"])
        L.rect(d + 1, TOP + 5, 1, 2, p["glass"])

    # cars: (first column, last column, is it the head car)
    cars = [(joints[0] + 1, nose_x - 1, True), (joints[1] + 1, joints[0] - 1, False), (-CAR, joints[1] - 1, False)]
    for a, b, head in cars:
        door(a + 4)
        door(b - 3 if head else b - 6)
        last = b - 6 if head else b - 10
        x = a + 10
        while x + 2 <= last:                       # dark, almost square side windows
            L.rect(x, TOP + 5, 3, 3, p["glass"])
            x += 5
        x = a + 9
        while x + 7 <= last:                       # louvres of the roof units
            for i in (0, 2, 4, 6):
                L.set(x + i, TOP + 1, p["roof2"])
            x += 12
        bogies = (a + 9, b - 18 if head else b - 24)
        for bx in bogies:
            L.rect(bx, BOT, 15, 1, p["bogie"])
            for wx in (bx + 2, bx + 10):
                L.rect(wx, BOT, 3, 1, p["wheel"])
        x = bogies[0] + 19                         # underfloor boxes between the bogies
        while x + 8 <= bogies[1] - 3:
            L.rect(x, BOT, 8, 1, p["under"])
            x += 11
    for g in joints:
        for y in range(TOP, TOP + 16):
            L.px.pop((g, y), None)
        L.rect(g, TOP + 1, 1, 14, p["gap"])
        for gx in (g - 1, g + 1):                  # car ends in shade
            L.rect(gx, TOP + 2, 1, 2, p["body2"])
            L.rect(gx, TOP + 9, 1, 3, p["body2"])

    # pantograph on the second car, reaching the contact wire
    px = joints[0] - 30
    L.rect(px - 3, TOP - 1, 9, 1, p["panto"])
    for i in range(3):
        L.set(px + i, TOP - 2 - i, p["panto"])
        L.set(px + 2 - i, TOP - 2 - i, p["panto"])
    L.rect(px - 2, WIRE + 1, 7, 1, p["panto"])
    return L


def field_layer(p, moonlit=False):
    """Meadows, fields, farmhouses and trees behind the viaduct; seen through its open spans."""
    T = 560
    L = Layer(T)
    m, t, hs = p["meadow"], p["tree"], p["house"]
    for x in range(T):
        top = 57 - round(1.5 * math.sin(2 * math.pi * 4 * x / T + 1) + 1.2 * math.sin(2 * math.pi * 11 * x / T)
                         + 1.5 * hsh(x // 3, 2))
        for y in range(top, 61):                   # wood at the far end of the fields
            L.set(x, y, t[2] if y == top and hsh(x, 3) < 0.35 else t[0] if y - top < 2 else t[1])
        for y in range(61, GROUND + 1):
            c = m[0] if y < 63 else m[1] if y < 67 else m[2]
            if y in (63, 67) and (x + y) % 2:
                c = m[0] if y == 63 else m[1]
            L.set(x, y, c)
    for a, b, y0 in ((36, 104, 64), (176, 262, 63), (318, 396, 65), (452, 536, 63)):
        for y in (y0, y0 + 1):                     # rapeseed strips
            for x in range(a - 3 * (y - y0), b - 3 * (y - y0)):
                L.set(x, y, m[3] if (x // 9 + y) % 4 else m[1])

    def house(x):
        for i, w in enumerate((5, 9, 13)):
            L.rect(x + 6 - w // 2, 58 + i, w, 1, hs[1])
        L.rect(x + 1, 61, 11, 4, hs[0])
        L.rect(x + 9, 61, 3, 4, hs[1] if moonlit else t[3])
        L.rect(x + 3, 62, 2, 2, hs[2])
        L.rect(x + 6, 62, 2, 2, hs[2])

    def broadleaf(cx, base, r):
        L.rect(cx, base - 3, 1, 4, t[3])
        cy = base - 2 - r
        for dy in range(-r, r + 1):
            for dx in range(-int(r * 1.25), int(r * 1.25) + 1):
                nx, ny = dx / (r * 1.25), dy / r
                if nx * nx + ny * ny > 1:
                    continue
                lit = (0.6 if moonlit else -0.6) * nx - 0.8 * ny
                c = t[2] if lit > 0.5 and hsh(cx + dx, dy) < 0.7 else t[0] if lit > -0.15 else t[1]
                L.set(cx + dx, cy + dy, c)

    def cedar(cx, base, h):
        L.rect(cx, base - 1, 1, 2, t[3])
        for i in range(h):
            w = min(i // 3 + (1 if i % 3 == 2 else 0), 4)
            for dx in range(-w, w + 1):
                far = dx > 0 if not moonlit else dx < 0
                rim = (dx == -w if not moonlit else dx == w) and i % 3 == 2
                L.set(cx + dx, base - 1 - h + i, t[2] if rim else t[1] if far else t[0])

    for hx in (118, 296, 468):
        house(hx)
    rnd = random.Random(33)
    trees = []
    x = 6
    while x < T - 8:
        for _ in range(rnd.choice((1, 1, 2, 3))):
            trees.append((rnd.randint(63, 69), x, rnd.random() < 0.4))
            x += rnd.randint(5, 9)
        x += rnd.randint(14, 44)
    for base, cx, conifer in sorted(trees):        # far ones first
        if conifer:
            cedar(cx, base, 9 + (base - 63))
        else:
            broadleaf(cx, base, 3 + (base - 63) // 2)
    return L


def viaduct_layer(p):
    """Parapet and deck, carried in turn by a walled-in stretch (vending machines, fence, booth),
    open spans on T-piers and an arch bridge over a river."""
    T = 560
    L = Layer(T)

    def walled(x):
        return x >= 430 or x < 96

    def concrete(x, y, edge=False):
        return p["pier3"] if edge else p["pier2"] if hsh(x, y // 2) < 0.3 else p["pier"]

    for x in range(T):
        # low parapet in front of the wheels, with a joint every few pixels
        L.set(x, RAIL, p["rail_lo"] if x % 7 == 0 else p["rail_hi"])
        # deck
        L.set(x, DECK, p["deck"])
        L.rect(x, DECK + 1, 1, 2, p["face"])
        L.set(x, DECK + 3, p["shadow"])
        if walled(x):                              # back wall in the shade of the deck
            for y in range(DECK + 4, GROUND):
                L.set(x, y, p["wall2"] if y < DECK + 7 or hsh(x // 3, y // 4) < 0.25 else p["wall"])
            L.set(x, GROUND, p["ground"])
    for x in range(140, 222):                      # hazard stripes on the girder over the lane
        if x % 5 < 2:
            L.set(x, DECK + 3, p["hazard"])

    for px in (0, 490):                            # pilasters in the wall
        for x in range(px, px + 14):
            for y in range(DECK + 4, GROUND):
                L.set(x, y, concrete(x, y, x == px))
    for px in (92, 430):                           # where the wall ends
        for x in range(px, px + 4):
            for y in range(DECK + 4, GROUND + 1):
                L.set(x, y, concrete(x, y, x == px))
    for px in (140, 210):                          # T-piers of the open spans
        for x in range(px - 4, px + 14):
            L.set(x, DECK + 4, concrete(x, DECK + 4, x == px - 4))
        for x in range(px - 2, px + 12):
            L.set(x, DECK + 5, concrete(x, DECK + 5, x == px - 2))
        for x in range(px, px + 10):
            for y in range(DECK + 6, GROUND + 1):
                L.set(x, y, p["pier2"] if x >= px + 8 else concrete(x, y, x == px))

    # arch bridge: two spans over the river
    w = p["water"]
    for a in (290, 360):
        for x in range(a, a + 60):
            u = (x - a - 29.5) / 30
            crown = max(DECK + 5, 69 - round(10 * math.sqrt(max(0.0, 1 - u * u))))
            for y in range(DECK + 4, crown):
                L.set(x, y, concrete(x, y, y == crown - 1))
            if hsh(x // 2, 61) < 0.5:
                L.set(x, 61, p["tree"][1])         # far bank
            L.set(x, 62, p["tree"][1])
            for y in range(max(crown, 63), GROUND + 1):
                glint = hsh(x // 4 + 31 * y, 7) < 0.13 and y > 64
                L.set(x, y, w[2] if y == 63 else w[1] if glint else w[0])
    for px in (280, 350, 420):
        for x in range(px, px + 10):
            for y in range(DECK + 4, GROUND + 1):
                L.set(x, y, p["pier2"] if x >= px + 8 else concrete(x, y, x == px))

    def fence(x0, x1):
        for x in range(x0, x1):
            L.set(x, 61, p["fence"])
            for y in range(62, 67):
                L.set(x, y, p["mesh"] if (x + y) % 2 == 0 else None)
            for y in range(67, GROUND):
                L.set(x, y, p["board2"] if x % 4 == 0 else p["board"])
            if x % 8 == 0:
                L.rect(x, 60, 1, GROUND - 60, p["fence"])

    for a, b in [(15, 56), (434, 462)]:
        fence(a, b)

    def vending(x, body, body2):
        L.rect(x, 59, 8, 12, body)
        L.rect(x + 7, 59, 1, 12, body2)
        L.rect(x, 59, 8, 1, p["panel"])
        for r in range(3):
            for i in range(6):
                L.set(x + 1 + i, 61 + r * 2, p["bottle"] if i % 2 == 0 else p["bottle2"])
        L.rect(x + 1, 67, 3, 1, p["label"])
        L.rect(x + 5, 66, 1, 2, p["panel"])
        L.rect(x + 1, 69, 6, 1, p["panel"])

    vending(60, p["red"], p["red2"])
    vending(70, p["white"], p["white2"])
    L.rect(79, 67, 4, 4, p["bin"])
    vending(464, p["white"], p["white2"])
    vending(474, p["red"], p["red2"])
    L.rect(483, 67, 4, 4, p["bin"])
    L.rect(85, 63, 6, 8, p["white2"])              # switch box
    L.rect(86, 64, 4, 1, p["panel"])

    def cone(x):
        L.set(x + 1, 66, p["cone"])
        L.rect(x + 1, 67, 1, 1, p["cone2"])
        L.rect(x, 68, 3, 2, p["cone"])
        L.rect(x - 1, 70, 5, 1, p["cone"])

    for cx in (100, 107, 224, 231):
        cone(cx)
    # small booth with a window
    L.rect(508, 60, 40, 11, p["booth"])
    L.rect(508, 60, 40, 1, p["booth2"])
    L.rect(514, 62, 14, 7, p["win"])
    L.rect(532, 62, 3, 5, p["sign"])
    L.rect(538, 63, 6, 8, p["booth2"])
    return L


def glow_layer(p):
    """Night only: light pools in front of the vending machines and the booth window."""
    T = 560
    L = Layer(T)
    for cx, w in ((70, 26), (474, 26), (521, 22)):
        for x in range(cx - w // 2, cx + w // 2):
            for y in range(58, GROUND + 4):
                if abs(x - cx) / (w / 2) + abs(y - 66) / 9 < 1:
                    L.set(x, y, "#fff0b8")
    return L


def grass_layer(p):
    T = 280
    L = Layer(T)
    g = p["grass"]
    rnd = random.Random(8)
    for x in range(T):
        for y in range(GROUND + 1, GH):
            r = rnd.random()
            L.set(x, y, g[1] if r < 0.25 else g[3] if r < 0.32 else g[2] if r < 0.42 else g[0])
        if rnd.random() < 0.55:                    # blades poking up in front of the viaduct
            hgt = rnd.randint(1, 4)
            col = g[4] if rnd.random() < 0.4 else g[2]
            for y in range(GROUND + 1 - hgt, GROUND + 1):
                L.set(x, y, col)
    return L


# ---------------------------------------------------------------- compose

def build(theme):
    p = PALETTES[theme]
    night = theme == "dark"
    out = []
    W, H = GW * SCALE, GH * SCALE
    out.append(f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
               f'width="{W}" height="{H}" viewBox="0 0 {GW} {GH}" shape-rendering="crispEdges">')

    layers = {  # name: (layer, seconds per tile)
        "clouds": (clouds_layer(p), 360),
        "streaks": (streaks_layer(p), 200),
        "hills": (hills_layer(p), 90),
        "field": (field_layer(p, moonlit=night), 14),
        "poles": (poles_layer(p), 8),
        "viaduct": (viaduct_layer(p), 8),
        "glow": (glow_layer(p), 8),
        "grass": (grass_layer(p), 3.6),
    }
    css = []
    for name, (layer, secs) in layers.items():
        if name == "glow" and not night:
            continue
        css.append(f".{name}{{animation:{name} {secs}s linear infinite}}"
                   f"@keyframes {name}{{to{{transform:translateX(-{layer.tile}px)}}}}")
    css.append("@keyframes tw{50%{opacity:.25}}"
               ".tw1{animation:tw 3s steps(2) infinite}.tw2{animation:tw 4.4s steps(2) infinite 1s}"
               ".beam{animation:beam 2.6s steps(3) infinite}@keyframes beam{50%{opacity:.6}}"
               "@media (prefers-reduced-motion:reduce){*{animation:none!important}}")
    out.append(f"<style>{''.join(css)}</style>")

    out.append(sky_svg(p))

    if night:
        rnd = random.Random(9)
        for k in (1, 2):
            s = Layer()
            for _ in range(24):
                s.set(rnd.randrange(GW), rnd.randrange(0, 30), "#e9edff" if rnd.random() < 0.7 else "#9fb2ff")
            out.append(f'<g class="tw{k}">{s.svg()}</g>')
        moon = Layer()
        cx, cy, r = 244, 9, 5
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r + 1:
                    moon.set(x, y, "#d9d5b8" if (x - cx, y - cy) in [(-2, -1), (1, 2), (2, -2)] else "#f2efd6")
        out.append(moon.svg())

    def scrolling(name, opacity=None):
        layer = layers[name][0]
        copies = math.ceil(GW / layer.tile) + 1
        uses = "".join(f'<use xlink:href="#{name}T" href="#{name}T" x="{layer.tile * i}"/>' for i in range(1, copies))
        op = f' opacity="{opacity}"' if opacity else ""
        return f'<g class="{name}"{op}><g id="{name}T">{layer.svg()}</g>{uses}</g>'

    out.append(fuji_layer(p, moonlit=night).svg())
    out.append(scrolling("clouds"))
    out.append(scrolling("streaks"))
    out.append(scrolling("hills"))
    out.append(scrolling("field"))
    out.append(scrolling("poles"))
    # contact wire (static, it is continuous)
    out.append(f'<rect x="0" y="{WIRE}" width="{GW}" height="1" fill="{p["wire"]}"/>')
    train = draw_train(p)
    out.append(train.svg())
    if night:                                      # beam starts at the lamp and passes over the cap
        parts = []
        for k, op in enumerate((".32", ".2", ".11", ".05")):
            beam = Layer()
            for i in range(k * 9, k * 9 + 9):
                for y in range(LAMP_Y - i // 14, LAMP_Y + 2 + i // 8):
                    if (HEAD_X - 4 + i, y) not in train.px:
                        beam.set(HEAD_X - 4 + i, y, p["head"])
            parts.append(f'<g opacity="{op}">{beam.svg()}</g>')
        out.append(f'<g class="beam">{"".join(parts)}</g>')
    out.append(scrolling("viaduct"))
    if night:
        out.append(scrolling("glow", ".14"))
    out.append(scrolling("grass"))
    out.append("</svg>")
    return "".join(out)


if __name__ == "__main__":
    dest = Path(__file__).resolve().parent.parent / "resources" / "svg"
    dest.mkdir(parents=True, exist_ok=True)
    for theme in ("light", "dark"):
        f = dest / f"train_{theme}.svg"
        f.write_text(build(theme))
        print(f"{f.name}: {f.stat().st_size / 1024:.1f} KB")
