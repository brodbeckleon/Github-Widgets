#!/usr/bin/env python3
"""Generates the looping pixel-art Shinkansen banner (Series 0 on a viaduct below Mt Fuji).

    python3 scripts/train.py   ->  resources/svg/train_dark.svg, resources/svg/train_light.svg

Everything is drawn on a 280x80 pixel grid and scaled 3x. The train stands still;
the scenery scrolls at different speeds (parallax) and each scrolling layer is a seamless tile.
light = dusk (pink-lit Fuji, lavender clouds), dark = moonlit night with lit windows.
No third-party packages needed.
"""
import math
import random
from pathlib import Path

GW, GH, SCALE = 280, 80, 3
TOP, BOT = 42, 53          # train roof / wheel row
DECK = 54                  # viaduct deck surface
GROUND = 71                # ground line under the viaduct

PALETTES = {
    "light": dict(
        sky=["#5c79b2", "#5b74ac", "#5a6ea6", "#58689f", "#556198", "#525a92", "#4e538b"],
        fuji=["#efdcc0", "#e6c6ae", "#d9a9a0", "#c4949e", "#a98aa4", "#94809f", "#7f7499"],
        cloud=dict(rim="#f4b48e", lit="#d8a0a0", mid="#a58aac", sh="#7d74a3", dk="#625e96"),
        streak=["#7a72a8", "#9488b4", "#c79a9c", "#666aa0"],
        hill=["#45457a", "#3b4160", "#6f4c5c", "#33384f"],
        tower="#8d8fae", tower2="#62658a", pole="#6e6448", pole2="#9c8f6c", wire="#3e3e5e",
        body="#ece7dc", body2="#d6d0c4", roof="#c4beb3", blue="#1d48a0", blue2="#163a84",
        glass="#8fa3bd", door="#e2ddd2", cap="#fbf9f2", head="#fff1b8", gap="#4b4a57",
        panto="#34343e", skirt="#8c8c96", bogie="#2e2e36",
        rail_hi="#d4b0a8", rail_lo="#a88a88", post="#c8a49e", deck="#9b8b7c", face="#3c2e28",
        shadow="#241c18", hazard="#e0a040", wall="#563a20", wall2="#4a3019",
        pier="#7e6c4a", pier2="#685838", pier3="#93805c", fence="#c9a39d", mesh="#6a4a36",
        board="#6e4e30", board2="#5a3e24", red="#bf3a2c", red2="#922c22", white="#e8e2d6",
        white2="#c8c0b2", bottle="#4e7050", bottle2="#90b088", panel="#2a2626", label="#e6833a",
        bin="#d8d2c4", cone="#e0682c", cone2="#f2e6d8", booth="#8b7656", booth2="#6f5c40",
        win="#3d3b6c", sign="#ece6da", ground="#3a2e24",
        grass=["#836a3c", "#6e5832", "#a08a54", "#5a482a", "#b49c62"],
    ),
    "dark": dict(
        sky=["#080c22", "#0a0f28", "#0d132f", "#101736", "#121b3e", "#152046", "#18244e"],
        fuji=["#c9d3ea", "#b3bfdc", "#9aa7cc", "#8592bc", "#6b77a3", "#5c6894", "#4c5784"],
        cloud=dict(rim="#8e9cc8", lit="#5c6a9c", mid="#3a4677", sh="#2b3564", dk="#222b55"),
        streak=["#2a3462", "#36407a", "#4a5488", "#222a56"],
        hill=["#161c3a", "#141a2e", "#22223e", "#0f1426"],
        tower="#4b5274", tower2="#343a58", pole="#3a3426", pole2="#4e4634", wire="#5a6488",
        body="#c6cad4", body2="#aeb2be", roof="#9da1ad", blue="#2a50aa", blue2="#1f3e88",
        glass="#ffd877", door="#b9bdc8", cap="#eef2ff", head="#fff6cc", gap="#2e3240",
        panto="#22252e", skirt="#555a66", bogie="#1c1e24",
        rail_hi="#7a6a78", rail_lo="#5a4e5c", post="#6e606c", deck="#4a4450", face="#1c1820",
        shadow="#100d12", hazard="#9a7030", wall="#24180e", wall2="#1c130b",
        pier="#3e3830", pier2="#322c24", pier3="#4a4238", fence="#6e5c62", mesh="#2e221c",
        board="#33261a", board2="#281d13", red="#e04a38", red2="#a8352a", white="#f4f0e2",
        white2="#d8d2c2", bottle="#9be08a", bottle2="#e8ffd8", panel="#3a3434", label="#ff9a4a",
        bin="#7a766c", cone="#9a4a24", cone2="#b8aca0", booth="#3e3428", booth2="#2e261c",
        win="#ffd36b", sign="#d8d2c0", ground="#16120e",
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


def wrapdist(a, b, t):
    d = abs(a - b) % t
    return min(d, t - d)


# ---------------------------------------------------------------- sky & far scenery

def fuji_layer(p):
    """Static: far enough away that it does not move during the loop."""
    L = Layer()
    f = p["fuji"]
    fx, fy = 78, 1
    for y in range(fy, 47):
        dy = y - fy
        w = 2 + 2.4 * dy + 0.04 * dy * dy
        for x in range(int(fx - w), int(fx + w) + 1):
            if dy < 2:
                L.set(x, y, f[0])
                continue
            u = (x - fx) / dy                      # constant along ridges radiating from the peak
            ridge = int((u + 6) * 7)
            v = 0.55 * hsh(ridge) + 0.35 * hsh(ridge, y // 3) + dy / 70
            if u > 0.55:                           # shadow side of the ridge
                c = f[3] if v < 0.45 else f[4] if v < 0.7 else f[5] if v < 0.95 else f[6]
            else:
                c = f[0] if v < 0.35 else f[1] if v < 0.55 else f[2] if v < 0.78 else f[3] if v < 1.0 else f[4]
            L.set(x, y, c)
    return L


def clouds_layer(p):
    """Cumulus bank: overlapping lit puffs, painted back (high) to front (low)."""
    T = 560
    L = Layer(T)
    c = p["cloud"]
    rnd = random.Random(21)
    puffs = []
    x = 0
    while x < T:
        r = rnd.randint(3, 8)
        puffs.append((x, rnd.randint(31, 38), r))
        x += rnd.randint(5, 11)
    puffs.sort(key=lambda q: q[1])
    for cx, cy, r in puffs:
        for dy in range(-r, r + 1):
            y = cy + dy
            if y > 42:
                continue
            for dx in range(-int(r * 1.35), int(r * 1.35) + 1):
                nx, ny = dx / (r * 1.35), dy / r
                d = math.hypot(nx, ny)
                if d > 1:
                    continue
                b = -0.45 * nx - 0.9 * ny
                if d > 0.82 and b > 0.35:
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
    for x in range(T):                             # flat dark base of the bank
        for y in range(39, 43):
            if (x, y) not in L.px or y >= 41:
                L.set(x, y, c["dk"] if y < 42 or hsh(x, 3) < 0.7 else c["sh"])
    return L


def streaks_layer(p):
    """Thin stratus lines in front of the cloud base, like in a dusk sky."""
    T = 560
    L = Layer(T)
    rnd = random.Random(4)
    s = p["streak"]
    for y in range(42, 50):
        x = rnd.randrange(T)
        for _ in range(3):
            n = rnd.randint(25, 140)
            col = s[2] if rnd.random() < 0.15 else rnd.choice((s[0], s[1], s[3]))
            for i in range(n):
                L.set(x + i, y, col)
            x += n + rnd.randint(15, 90)
    return L


def hills_layer(p):
    T = 560
    L = Layer(T)
    h = p["hill"]
    for x in range(T):
        top = int(49 - 3 * math.sin(2 * math.pi * x / T) - 1.5 * math.sin(2 * math.pi * x / 140 + 1))
        for y in range(top, DECK + 3):
            if y > 52:
                col = h[3]
            elif y - top < 4 and (x + 3 * y) % 41 < 9:
                col = h[2]                         # last light catching the ridge
            elif (x * 7 + y * 3) % 11 == 0 or y > 50:
                col = h[1]
            else:
                col = h[0]
            L.set(x, y, col)
    return L


# ---------------------------------------------------------------- railway

def poles_layer(p):
    """Catenary masts and lattice towers behind the train; same speed as the viaduct."""
    T = 560
    L = Layer(T)
    for mx in range(10, T, 70):
        L.rect(mx, 33, 1, DECK - 33, p["pole"])
        L.rect(mx + 1, 33, 1, DECK - 33, p["pole2"])
        L.rect(mx - 1, 35, 7, 1, p["pole"])
        L.set(mx + 5, 36, p["pole"])
    for tx in (45, 325):
        for y in range(26, DECK):
            L.set(tx, y, p["tower"])
            L.set(tx + 2, y, p["tower2"])
            L.set(tx + 1, y, p["tower"] if (y % 4) in (0, 1) else None)
        L.rect(tx - 2, 28, 7, 1, p["tower2"])
    return L


def nose_profile(t):
    """Bullet nose of the Series 0: rows cut from the roof / from the skirt, t = 0 at the cab, 1 at the tip."""
    s = math.sqrt(max(0.0, 1 - t * t))
    return round(7 * (1 - s)), round(3 * (1 - s))


def draw_train(p):
    L = Layer()
    xh, nose = 214, 22                             # head (tip) and nose length
    gaps = [142, 70]                               # car joints; the tail runs off-screen left

    def col(x):
        if x > xh - nose:
            a, b = nose_profile((x - (xh - nose)) / nose)
            return TOP + a, BOT - 1 - b
        return TOP, BOT - 1

    for x in range(0, xh + 1):
        ct, cb = col(x)
        for y in range(ct, cb + 1):
            L.set(x, y, p["roof"] if y == ct and ct == TOP else p["body2"] if y >= 49 else p["body"])
        # blue window band (follows the nose down to the tip)
        b0 = 44 if ct < 44 else ct + 1
        for y in range(b0, min(b0 + 4, cb)):
            L.set(x, y, p["blue"])
        # skirt stripe
        if cb - 1 >= 50:
            L.set(x, cb - 1, p["blue2"])
        L.set(x, cb, p["skirt"])

    # side windows inside the band, small and square like the original 0 series
    for x in range(2, xh - nose - 1):
        if any(abs(x - g) <= 5 for g in gaps) or abs(x - (xh - nose - 5)) <= 2:
            continue
        if x % 4 in (0, 1):
            L.rect(x, 45, 1, 2, p["glass"])
    # doors at the car ends
    for g in gaps:
        for dx in (-4, 3):
            L.rect(g + dx, 44, 2, 6, p["door"])
            L.rect(g + dx, 45, 2, 1, p["glass"])
    L.rect(xh - nose - 6, 44, 2, 6, p["door"])
    L.rect(xh - nose - 6, 45, 2, 1, p["glass"])
    # cab windshield on the nose slope
    for x in range(xh - nose + 2, xh - nose + 13):
        ct, _ = col(x)
        if x == xh - nose + 7:
            continue                               # centre pillar
        for y in range(ct + 1, min(ct + 3, 44)):
            L.set(x, y, p["glass"])
    # round nose cap and headlight
    L.rect(xh - 1, 48, 2, 2, p["cap"])
    L.set(xh - 2, 49, p["cap"])
    L.rect(xh - 3, 50, 2, 1, p["head"])
    # car joints
    for g in gaps:
        L.rect(g, TOP + 1, 1, BOT - TOP - 2, p["gap"])
    # bogies and wheels
    for cx in (20, 52, 92, 124, 164, 196):
        L.rect(cx - 6, BOT, 13, 1, p["bogie"])
    # pantograph on the middle car, reaching the contact wire at y=37
    px = 106
    L.rect(px - 2, TOP - 1, 6, 1, p["panto"])
    for i in range(4):
        L.set(px + i // 2, TOP - 2 - i, p["panto"])
        L.set(px + 2 - i // 2, TOP - 2 - i, p["panto"])
    L.rect(px - 2, 37, 7, 1, p["panto"])
    return L


def viaduct_layer(p):
    """Railing, deck and everything under the viaduct (vending machines, fence, cones, booth)."""
    T = 560
    L = Layer(T)
    piers = [0, 140, 280, 420]
    for x in range(T):
        # railing in front of the train
        L.set(x, 50, p["rail_hi"])
        L.set(x, 52, p["rail_lo"])
        if x % 7 == 0:
            L.rect(x, 50, 1, 4, p["post"])
        # deck
        L.set(x, DECK, p["deck"])
        L.rect(x, DECK + 1, 1, 2, p["face"])
        L.set(x, DECK + 3, p["shadow"])
        # back wall in the shade of the deck
        for y in range(DECK + 4, GROUND):
            L.set(x, y, p["wall2"] if y < DECK + 7 or hsh(x // 3, y // 4) < 0.25 else p["wall"])
        L.set(x, GROUND, p["ground"])
    for x in range(160, 272):                      # hazard stripes under the bridge section
        if x % 5 < 2:
            L.set(x, DECK + 3, p["hazard"])
    for px in piers:
        for x in range(px, px + 14):
            for y in range(DECK + 4, GROUND):
                c = p["pier3"] if x == px else p["pier2"] if hsh(x, y // 2) < 0.3 else p["pier"]
                L.set(x, y, c)

    def fence(x0, x1):
        for x in range(x0, x1):
            L.set(x, 61, p["fence"])
            for y in range(62, 67):
                L.set(x, y, p["mesh"] if (x + y) % 2 == 0 else None)
            for y in range(67, GROUND):
                L.set(x, y, p["board2"] if x % 4 == 0 else p["board"])
            if x % 8 == 0:
                L.rect(x, 60, 1, GROUND - 60, p["fence"])

    for a, b in [(15, 56), (88, 138), (300, 368), (392, 418), (500, 558)]:
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
    vending(372, p["white"], p["white2"])
    vending(382, p["red"], p["red2"])
    L.rect(176, 63, 7, 8, p["white2"])
    L.rect(177, 64, 5, 1, p["panel"])

    def cone(x):
        L.set(x + 1, 66, p["cone"])
        L.rect(x + 1, 67, 1, 1, p["cone2"])
        L.rect(x, 68, 3, 2, p["cone"])
        L.rect(x - 1, 70, 5, 1, p["cone"])

    for cx in (200, 207, 466, 473, 480):
        cone(cx)
    # small booth with a window
    L.rect(226, 60, 40, 11, p["booth"])
    L.rect(226, 60, 40, 1, p["booth2"])
    L.rect(232, 62, 14, 7, p["win"])
    L.rect(250, 62, 3, 5, p["sign"])
    L.rect(256, 63, 6, 8, p["booth2"])
    return L


def glow_layer(p):
    """Night only: light pools in front of the vending machines and the booth window."""
    T = 560
    L = Layer(T)
    for cx, w in ((70, 26), (239, 22), (382, 26)):
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

    # sky bands
    edges = [0, 8, 16, 24, 32, 40, 48, GH]
    for i, c in enumerate(p["sky"]):
        out.append(f'<rect x="0" y="{edges[i]}" width="{GW}" height="{edges[i + 1] - edges[i]}" fill="{c}"/>')

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

    out.append(fuji_layer(p).svg())
    out.append(scrolling("clouds"))
    out.append(scrolling("streaks"))
    out.append(scrolling("hills"))
    out.append(scrolling("poles"))
    # catenary: messenger and contact wire (static, they are continuous)
    out.append(f'<rect x="0" y="35" width="{GW}" height="1" fill="{p["wire"]}"/>')
    out.append(f'<rect x="0" y="37" width="{GW}" height="1" fill="{p["wire"]}"/>')
    out.append(draw_train(p).svg())
    if night:
        parts = []
        for k, op in enumerate((".45", ".28", ".14", ".06")):
            beam = Layer()
            for i in range(k * 12, k * 12 + 12):
                for y in range(50 - i // 10, 51 + i // 14):
                    beam.set(215 + i, y, p["head"])
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
