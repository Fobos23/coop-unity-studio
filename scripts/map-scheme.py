#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Map scheme from one coordinate table: two to-scale sheets and the level-design rule checks.

    python map-scheme.py <spec.json> [--out DIR] [--strict]

Writes <name>_plan.png (ground levels, streets, buildings, story places), <name>_routes.png (routes, respite
buildings, longest sightlines, check results) and <name>_metrics.json next to the spec (or into --out).
--strict returns 1 when a rule fails. Needs Pillow only. Spec format and the rules: references/level-design.md;
example: templates/docs/map-scheme.example.json.

Coordinates are metres: x west to east, z south to north; heights are metres above the lowest ground.
The sightline check is flat and rough: a ray stops at a building, a tall blocker, the background or a ground step
of `limits.level_step`; it knows nothing of windows or of looking down from a height, and a 1 m grid lets a ray slip
past a thin fence that ends exactly at a corner (extend the fence by half a metre).
"""
import argparse
import json
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

TXT = {
    "en": dict(plan="sheet 1: ground levels, streets, buildings, places", routes="sheet 2: routes, respite, sightlines",
               levels="Ground levels", ramp="ramp (dot = top)", stairs="stairs (dot = top)", buildings="Buildings",
               door="White square on a wall = door, big = double door.", blockers="Blockers: sight and cover",
               tall="blocks sight", low="cover only", background="background: no access", places="Story places",
               squad="Squad and AI", start="start and exit", spawn="AI spawn zones", vehicle="dashed line = vehicle path",
               routes_h="Routes to the goal", walk="walk", sprint="sprint", checks="Rule checks",
               size="Size", lv="Ground levels", goal="Goal by the shortest route", overlap="Route overlap",
               refuge="To a respite door, worst spot", sight="Longest sightline outdoors", waves="Spawn zones from the start",
               limit="limit", need="need", respite="Respite", m="m", s="s",
               role=dict(goal="goal", refuge="respite: two exits", strong="stronghold at the exit", trap="one exit",
                         sleep="sleeping house: looks the same", plain="plain building")),
    "ru": dict(plan="лист 1: уровни, улицы, здания, места", routes="лист 2: пути, передышки, обзор",
               levels="Уровни земли", ramp="пандус (точка — верх)", stairs="лестница (точка — верх)", buildings="Здания",
               door="Белый квадрат на стене — дверь, большой — двойная.", blockers="Преграды: обзор и укрытие",
               tall="закрывает обзор", low="только укрытие", background="фон: недоступно", places="Места с историей",
               squad="Отряд и противник", start="высадка и выход", spawn="зоны появления", vehicle="пунктир — путь машины",
               routes_h="Пути к цели", walk="шагом", sprint="бегом", checks="Проверка правил",
               size="Размер", lv="Уровней земли", goal="До цели кратчайшим путём", overlap="Совпадение путей",
               refuge="До двери передышки, худшее место", sight="Прямая видимость, самая длинная", waves="Зоны появления от высадки",
               limit="предел", need="нужно", respite="Передышки", m="м", s="с",
               role=dict(goal="цель", refuge="передышка: два выхода", strong="опорный пункт у выхода", trap="один выход",
                         sleep="спящий дом: выглядит так же", plain="обычное здание")),
}
ROLE_COL = dict(goal=(226, 120, 104), refuge=(128, 196, 128), strong=(70, 150, 78), trap=(240, 200, 110),
                sleep=(180, 160, 220), plain=(205, 198, 188))
LEVEL_COLS = [(150, 158, 168), (222, 205, 160), (236, 232, 216), (203, 226, 190), (188, 214, 226), (226, 200, 214)]
INK, ASPHALT, PATH, BG, WALL = (40, 40, 44), (120, 125, 132), (196, 186, 160), (190, 190, 186), (70, 66, 62)
DEFAULT_LIMITS = dict(sight=40.0, refuge=25.0, overlap=0.33, goal=150.0, wave=40.0, level_step=1.65, levels=3)


def font(size, bold=False):
    names = (["arialbd.ttf", "segoeuib.ttf", "DejaVuSans-Bold.ttf"] if bold else ["arial.ttf", "segoeui.ttf", "DejaVuSans.ttf"])
    for folder in ("C:/Windows/Fonts/", "/usr/share/fonts/truetype/dejavu/", ""):
        for n in names:
            try:
                return ImageFont.truetype(folder + n, size)
            except OSError:
                pass
    return ImageFont.load_default()


class Scheme:
    def __init__(self, spec):
        self.s = spec
        self.t = TXT.get(spec.get("lang", "en"), TXT["en"])
        self.x0, self.z0, self.x1, self.z1 = spec["extent"]
        self.S = spec.get("scale", 10)
        self.M, self.PANEL = 60, 660
        self.W, self.H = int((self.x1 - self.x0) * self.S), int((self.z1 - self.z0) * self.S)
        self.lim = dict(DEFAULT_LIMITS, **spec.get("limits", {}))
        self.tall = set(spec.get("tall", []))
        self.levels = spec["levels"]
        self.decks = spec.get("decks", [])
        self.ramps = spec.get("ramps", [])
        self.blockers = spec.get("blockers", [])
        self.background = spec.get("background", [])
        self.buildings = self._place()
        self.solid = self._solid()
        self.f11, self.f12, self.f13 = font(11), font(12), font(13)
        self.b13, self.b15, self.b18, self.b26 = font(13, True), font(15, True), font(18, True), font(26, True)
        heights = sorted({r[4] for r in self.levels})
        self.lv_col = {h: LEVEL_COLS[i % len(LEVEL_COLS)] for i, h in enumerate(heights)}

    # --- geometry ---
    def _place(self):
        out = []
        cat = self.s.get("catalog", {})
        for p in self.s.get("placed", []):
            b = cat[p["key"]]
            w, d, k = b["w"], b["d"], p.get("rot", 0) % 4
            size = (w, d) if k % 2 == 0 else (d, w)
            doors = []
            for u, v, kind in b.get("doors", []):
                du, dv = [(u, v), (d - v, u), (w - u, d - v), (v, w - u)][k]
                doors.append((p["x"] + du, p["z"] + dv, kind))
            out.append(dict(id=p["id"], r=(p["x"], p["z"], p["x"] + size[0], p["z"] + size[1]), lv=b.get("lv", 1),
                            role=p.get("role", "plain"), label=p.get("label", p["id"]), doors=doors))
        return out

    @staticmethod
    def inside(r, x, z):
        return r[0] <= x <= r[2] and r[1] <= z <= r[3]

    def level_at(self, x, z, upper=True):
        for rp in self.ramps:
            r = rp["r"]
            if self.inside(r, x, z):
                t = (x - r[0]) / (r[2] - r[0]) if rp["axis"] == "x" else (z - r[1]) / (r[3] - r[1])
                return rp["h0"] + (rp["h1"] - rp["h0"]) * t
        if upper:
            for d in self.decks:
                if self.inside(d, x, z):
                    return d[4]
        for r in reversed(self.levels):
            if self.inside(r, x, z):
                return r[4]
        return self.levels[0][4]

    def _solid(self):
        grid = set()
        rects = [b["r"] for b in self.buildings] + [r[:4] for r in self.blockers if r[4] in self.tall] + self.background
        for x0, z0, x1, z1 in rects:
            thin = min(x1 - x0, z1 - z0) < 1.0
            for ix in range(int(math.floor(x0)), int(math.ceil(x1))):
                for iz in range(int(math.floor(z0)), int(math.ceil(z1))):
                    if thin or (x0 <= ix + 0.5 <= x1 and z0 <= iz + 0.5 <= z1):
                        grid.add((ix, iz))
        return grid

    def is_solid(self, x, z):
        return (int(math.floor(x)), int(math.floor(z))) in self.solid

    @staticmethod
    def length(pts):
        return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))

    @staticmethod
    def sample(pts, step=1.0):
        out = []
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            n = max(1, int(math.dist(a, b) / step))
            out += [(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n) for k in range(n)]
        return out + [tuple(pts[-1])]

    @staticmethod
    def poly_dist(p, pts):
        best = 1e9
        for i in range(len(pts) - 1):
            (ax, az), (bx, bz) = pts[i], pts[i + 1]
            dx, dz = bx - ax, bz - az
            t = 0 if dx == dz == 0 else max(0, min(1, ((p[0] - ax) * dx + (p[1] - az) * dz) / (dx * dx + dz * dz)))
            best = min(best, math.dist(p, (ax + dx * t, az + dz * t)))
        return best

    def overlap(self, a, b, near=5.0):
        sa = self.sample(a)
        return sum(1 for p in sa if self.poly_dist(p, b) <= near) / len(sa)

    def refuge_gap(self, pts):
        doors = [(d[0], d[1]) for b in self.buildings if b["role"] in ("refuge", "strong", "goal", "trap") for d in b["doors"]]
        free = self.s.get("no_ai", [])
        worst = (0.0, None)
        for p in self.sample(pts, 2.0):
            if not doors or any(self.inside(r, p[0], p[1]) for r in free):
                continue
            d = min(math.dist(p, q) for q in doors)
            if d > worst[0]:
                worst = (d, p)
        return worst

    def sightlines(self, top_n=6):
        found, step = [], self.lim["level_step"]
        for ix in range(int(self.x0) + 1, int(self.x1), 2):
            for iz in range(int(self.z0) + 1, int(self.z1), 2):
                ox, oz = ix + 0.5, iz + 0.5
                if self.is_solid(ox, oz) or any(self.inside(rp["r"], ox, oz) for rp in self.ramps):
                    continue
                on_deck = any(self.inside(d, ox, oz) for d in self.decks)
                for upper in ((True, False) if on_deck else (True,)):
                    h, best = self.level_at(ox, oz, upper), (0.0, None)
                    for a in range(0, 360, 5):
                        dx, dz, t = math.cos(math.radians(a)), math.sin(math.radians(a)), 0.0
                        while t < 200:
                            t += 0.5
                            x, z = ox + dx * t, oz + dz * t
                            if not (self.x0 < x < self.x1 and self.z0 < z < self.z1) or self.is_solid(x, z) \
                                    or abs(self.level_at(x, z, upper) - h) >= step:
                                break
                        if t > best[0]:
                            best = (t, (ox + dx * t, oz + dz * t))
                    found.append((best[0], (ox, oz), best[1], h))
        found.sort(reverse=True)
        top = []
        for f in found:
            if all(math.dist(f[1], g[1]) > 12 or math.dist(f[2], g[2]) > 12 for g in top):
                top.append(f)
            if len(top) == top_n:
                break
        return top

    def metrics(self):
        s, lim = self.s, self.lim
        speeds = s.get("speeds", {"walk": 3.4, "sprint": 6.0})
        m = {"size_m": [self.x1 - self.x0, self.z1 - self.z0], "levels_m": sorted({r[4] for r in self.levels}), "routes": {}}
        routes = s.get("routes", {})
        for k, r in routes.items():
            ln = self.length(r["pts"])
            gap, at = self.refuge_gap(r["pts"])
            m["routes"][k] = dict(length_m=round(ln, 1), walk_s=round(ln / speeds["walk"]), sprint_s=round(ln / speeds["sprint"]),
                                  refuge_gap_m=round(gap, 1), refuge_gap_at=[round(v, 1) for v in at] if at else None)
        keys = sorted(routes)
        m["overlap"] = {a + "-" + b: round(max(self.overlap(routes[a]["pts"], routes[b]["pts"]),
                                               self.overlap(routes[b]["pts"], routes[a]["pts"])), 2)
                        for i, a in enumerate(keys) for b in keys[i + 1:]}
        self.sights = self.sightlines()
        m["sight_top"] = [dict(m=round(x[0], 1), frm=[round(v, 1) for v in x[1]], to=[round(v, 1) for v in x[2]], level=x[3])
                          for x in self.sights]
        st = s.get("start")
        centre = ((st[0] + st[2]) / 2, (st[1] + st[3]) / 2) if st else None
        m["spawn_to_start_m"] = [round(math.dist((x, z), centre)) for x, z, _ in s.get("spawns", [])] if centre else []
        shortest = min((v["length_m"] for v in m["routes"].values()), default=0)
        m["checks"] = {
            "levels": len(m["levels_m"]) >= lim["levels"],
            "goal": shortest <= lim["goal"],
            "overlap": all(v <= lim["overlap"] for v in m["overlap"].values()),
            "refuge": all(v["refuge_gap_m"] <= lim["refuge"] for v in m["routes"].values()),
            "sight": (self.sights[0][0] if self.sights else 0) <= lim["sight"],
            "spawns": all(v >= lim["wave"] for v in m["spawn_to_start_m"]),
        }
        return m

    # --- drawing ---
    def px(self, x, z):
        return (self.M + (x - self.x0) * self.S, self.M + (self.z1 - z) * self.S)

    def box(self, r):
        a = self.px(max(self.x0, r[0]), min(self.z1, r[3]))
        b = self.px(min(self.x1, r[2]), max(self.z0, r[1]))
        return [a[0], a[1], b[0], b[1]]

    def label(self, d, x, z, text, f=None, fill=(30, 30, 34), bg=None):
        p, f = self.px(x, z), f or self.f12
        if bg:
            l, t, r, b = d.multiline_textbbox(p, text, font=f, anchor="mm", align="center", spacing=2)
            d.rectangle([l - 3, t - 2, r + 3, b + 2], fill=bg)
        d.multiline_text(p, text, font=f, fill=fill, anchor="mm", align="center", spacing=2)

    def dashed(self, d, pts, fill, width=3, dash=12, gap=8):
        for i in range(len(pts) - 1):
            a, b = self.px(*pts[i]), self.px(*pts[i + 1])
            ln, t = math.dist(a, b), 0
            while t < ln:
                e = min(ln, t + dash)
                d.line([(a[0] + (b[0] - a[0]) * t / ln, a[1] + (b[1] - a[1]) * t / ln),
                        (a[0] + (b[0] - a[0]) * e / ln, a[1] + (b[1] - a[1]) * e / ln)], fill=fill, width=width)
                t += dash + gap

    def blocker_col(self, kind):
        custom = self.s.get("colors", {})
        if kind in custom:
            return tuple(custom[kind])
        return (78, 66, 60) if kind in self.tall else (150, 140, 132)

    def base(self, d):
        for r in self.levels:
            d.rectangle(self.box(r), fill=self.lv_col[r[4]])
        for r in self.s.get("paths", []):
            d.rectangle(self.box(r), fill=PATH)
        for r in self.s.get("asphalt", []):
            d.rectangle(self.box(r), fill=ASPHALT)
        for a, b in self.s.get("walls", []):
            d.line([self.px(*a), self.px(*b)], fill=WALL, width=4)
        for rp in self.ramps:
            r = rp["r"]
            stairs = rp.get("kind") == "stairs"
            d.rectangle(self.box(r), fill=(168, 160, 150) if stairs else (136, 140, 146), outline=WALL)
            for i in range(1, 7 if stairs else 4):
                t = i / (7 if stairs else 4)
                if rp["axis"] == "x":
                    x = r[0] + (r[2] - r[0]) * t
                    d.line([self.px(x, r[1]), self.px(x, r[3])], fill=WALL, width=1)
                else:
                    z = r[1] + (r[3] - r[1]) * t
                    d.line([self.px(r[0], z), self.px(r[2], z)], fill=WALL, width=1)
            up = 1 if rp["h1"] > rp["h0"] else -1
            cx, cz = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
            a, b = ((cx - up * 1.6, cz), (cx + up * 1.6, cz)) if rp["axis"] == "x" else ((cx, cz - up * 1.6), (cx, cz + up * 1.6))
            d.line([self.px(*a), self.px(*b)], fill=(255, 255, 255), width=3)
            bx, by = self.px(*b)
            d.ellipse([bx - 4, by - 4, bx + 4, by + 4], fill=(255, 255, 255))
        for dk in self.decks:
            d.rectangle(self.box(dk[:4]), outline=(30, 30, 34), width=4)
        for r in self.background:
            b = self.box(r)
            d.rectangle(b, fill=BG)
            for i in range(int(b[0]) - int(b[3] - b[1]), int(b[2]), 14):
                x0, y0, x1, y1 = i, b[3], i + (b[3] - b[1]), b[1]
                if x0 < b[0]:
                    y0 -= (b[0] - x0); x0 = b[0]
                if x1 > b[2]:
                    y1 += (x1 - b[2]); x1 = b[2]
                if x0 < x1:
                    d.line([x0, y0, x1, y1], fill=(170, 170, 166), width=1)
        for x0, z0, x1, z1, kind in self.blockers:
            thin = min(x1 - x0, z1 - z0) < 1.0
            d.rectangle(self.box((x0, z0, x1, z1)), fill=self.blocker_col(kind), outline=None if thin else (30, 30, 30))
        for line in self.s.get("lines", []):  # pipes, cables: [[x,z],[x,z],[r,g,b]]
            d.line([self.px(*line[0]), self.px(*line[1])], fill=tuple(line[2]) if len(line) > 2 else (150, 80, 50), width=5)

    def buildings_layer(self, d, roles=None, names=True):
        for b in self.buildings:
            if roles and b["role"] not in roles:
                continue
            d.rectangle(self.box(b["r"]), fill=ROLE_COL.get(b["role"], ROLE_COL["plain"]), outline=INK, width=3)
            for dx, dz, kind in b["doors"]:
                x, y = self.px(dx, dz)
                s = 9 if kind == "dd" else 6
                d.rectangle([x - s, y - s, x + s, y + s], fill=(255, 255, 255), outline=(20, 20, 20), width=2)
            if names:
                r = b["r"]
                self.label(d, (r[0] + r[2]) / 2, (r[1] + r[3]) / 2, b["label"] + ("\n%d" % b["lv"] if b["lv"] > 1 else ""))

    def overlays(self, d):
        st = self.s.get("start")
        if st:
            self.dashed(d, [(st[0], st[1]), (st[2], st[1]), (st[2], st[3]), (st[0], st[3]), (st[0], st[1])], (250, 215, 40), 4)
        if self.s.get("vehicle_path"):
            self.dashed(d, self.s["vehicle_path"], (255, 255, 255), 2, 8, 6)
        for x, z, name in self.s.get("spawns", []):
            p = self.px(max(self.x0 + 2.2, min(self.x1 - 2.2, x)), max(self.z0 + 2.2, min(self.z1 - 2.2, z)))
            d.rectangle([p[0] - 20, p[1] - 20, p[0] + 20, p[1] + 20], fill=(200, 50, 50), outline=(90, 10, 10), width=2)
            d.text(p, name, font=self.b13, fill=(255, 255, 255), anchor="mm")
        for x, z, name in self.s.get("landmarks", []):
            p = self.px(x, z)
            d.polygon([(p[0], p[1] - 12), (p[0] - 9, p[1] + 8), (p[0] + 9, p[1] + 8)], fill=(200, 40, 40), outline=(20, 20, 20))
            d.text((p[0], p[1] + 12), name, font=self.f11, fill=INK, anchor="mt")
        for x, z, text in self.s.get("labels", []):
            self.label(d, x, z, text, self.f11, bg=(255, 255, 255))

    def scenes(self, d):
        for n, x, z, _ in self.s.get("scenes", []):
            p = self.px(x, z)
            d.ellipse([p[0] - 13, p[1] - 13, p[0] + 13, p[1] + 13], fill=(255, 235, 90), outline=(20, 20, 20), width=2)
            d.text(p, str(n), font=self.b13, fill=(20, 20, 20), anchor="mm")

    def frame(self, d, sub):
        d.rectangle([self.M, self.M, self.M + self.W, self.M + self.H], outline=INK, width=3)
        d.text((self.M, 8), self.s.get("title", "Map") + " — " + sub, font=self.b26, fill=INK)
        for x in range(int(math.ceil(self.x0 / 10) * 10), int(self.x1) + 1, 10):
            p = self.px(x, self.z0)
            d.line([p[0], p[1], p[0], p[1] + 6], fill=INK)
            d.text((p[0], p[1] + 8), str(x), font=self.f11, fill=(90, 90, 90), anchor="mt")
        for z in range(int(math.ceil(self.z0 / 10) * 10), int(self.z1) + 1, 10):
            p = self.px(self.x0, z)
            d.line([p[0] - 6, p[1], p[0], p[1]], fill=INK)
            d.text((p[0] - 9, p[1]), str(z), font=self.f11, fill=(90, 90, 90), anchor="rm")

    def panel(self, d, lines):
        x, y = self.M + self.W + 40, self.M
        for kind, text in lines:
            if kind == "h":
                y += 8
                d.text((x, y), text, font=self.b18, fill=INK); y += 28
            elif kind in ("sw", "ln"):
                col, t = text
                if kind == "sw":
                    d.rectangle([x, y + 1, x + 26, y + 15], fill=tuple(col), outline=INK)
                else:
                    d.line([x, y + 8, x + 26, y + 8], fill=tuple(col), width=5)
                d.text((x + 36, y), t, font=self.f13, fill=INK); y += 21
            else:
                for part in text.split("\n"):
                    d.text((x, y), part, font=self.b13 if kind == "b" else self.f13, fill=INK); y += 19

    def sheet(self):
        img = Image.new("RGB", (self.M * 2 + self.W + self.PANEL, self.M * 2 + self.H), (250, 249, 245))
        return img, ImageDraw.Draw(img)

    def render(self, out, name, m):
        t, lim = self.t, self.lim
        img, d = self.sheet()
        self.base(d)
        self.buildings_layer(d)
        self.overlays(d)
        self.scenes(d)
        self.frame(d, t["plan"])
        lines = [("h", t["levels"])] + [("sw", (self.lv_col[h], "%+.1f %s" % (h, t["m"]))) for h in sorted(self.lv_col)]
        lines += [("sw", ((136, 140, 146), t["ramp"])), ("sw", ((168, 160, 150), t["stairs"])), ("h", t["buildings"])]
        used = {b["role"] for b in self.buildings}
        lines += [("sw", (ROLE_COL[r], t["role"][r])) for r in ("goal", "refuge", "strong", "trap", "sleep", "plain") if r in used]
        lines += [("t", t["door"]), ("h", t["blockers"])]
        for kind in sorted({r[4] for r in self.blockers}):
            lines.append(("sw", (self.blocker_col(kind), "%s — %s" % (kind, t["tall"] if kind in self.tall else t["low"]))))
        lines += [("sw", (BG, t["background"])), ("h", t["places"])]
        lines += [("t", "%2d  %s" % (n, title)) for n, _, _, title in self.s.get("scenes", [])]
        lines += [("h", t["squad"]), ("sw", ((250, 215, 40), t["start"])), ("sw", ((200, 50, 50), t["spawn"])), ("t", t["vehicle"])]
        self.panel(d, lines)
        img.save(os.path.join(out, name + "_plan.png"))

        img, d = self.sheet()
        self.base(d)
        veil = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(veil).rectangle([self.M, self.M, self.M + self.W, self.M + self.H], fill=(250, 249, 245, 120))
        img.paste(veil, (0, 0), veil)
        d = ImageDraw.Draw(img)
        self.buildings_layer(d, roles=("goal", "refuge", "strong", "trap", "sleep"), names=False)
        self.overlays(d)
        for x in self.sights[:3]:
            d.line([self.px(*x[1]), self.px(*x[2])], fill=(200, 30, 30), width=2)
            self.label(d, (x[1][0] + x[2][0]) / 2, (x[1][1] + x[2][1]) / 2, "%.0f %s" % (x[0], t["m"]), self.f11, (160, 20, 20), (255, 255, 255))
        routes = self.s.get("routes", {})
        for k in sorted(routes, reverse=True):
            pts = [self.px(*p) for p in routes[k]["pts"]]
            d.line(pts, fill=(255, 255, 255), width=11, joint="curve")
            d.line(pts, fill=tuple(routes[k]["color"]), width=6, joint="curve")
        self.scenes(d)
        self.frame(d, t["routes"])
        ok = lambda key: "OK  " if m["checks"][key] else "FAIL"
        lines = [("h", t["routes_h"])]
        for k in sorted(routes):
            r = m["routes"][k]
            lines.append(("ln", (routes[k]["color"], routes[k].get("name", k))))
            lines.append(("t", "      %.0f %s · %s %d %s · %s %d %s" % (r["length_m"], t["m"], t["walk"], r["walk_s"], t["s"],
                                                                       t["sprint"], r["sprint_s"], t["s"])))
        lines += [("h", t["checks"]),
                  ("t", "%s: %.0f × %.0f %s" % (t["size"], m["size_m"][0], m["size_m"][1], t["m"])),
                  ("t", "%s %s: %d (%s ≥ %d)" % (ok("levels"), t["lv"], len(m["levels_m"]), t["need"], lim["levels"])),
                  ("t", "%s %s: %.0f %s (%s %.0f)" % (ok("goal"), t["goal"], min((v["length_m"] for v in m["routes"].values()), default=0),
                                                       t["m"], t["limit"], lim["goal"])),
                  ("t", "%s %s (%s %d %%): %s" % (ok("overlap"), t["overlap"], t["limit"], lim["overlap"] * 100,
                                                    ", ".join("%s %d %%" % (k, v * 100) for k, v in m["overlap"].items()))),
                  ("t", "%s %s (%s %.0f %s):\n        %s" % (ok("refuge"), t["refuge"], t["limit"], lim["refuge"], t["m"],
                                                              " · ".join("%s %.0f" % (k, v["refuge_gap_m"]) for k, v in m["routes"].items()))),
                  ("t", "%s %s (%s %.0f %s):\n        %s" % (ok("sight"), t["sight"], t["limit"], lim["sight"], t["m"],
                                                              ", ".join("%.0f" % x[0] for x in self.sights[:3]))),
                  ("t", "%s %s: %s %s (%s ≥ %.0f)" % (ok("spawns"), t["waves"], ", ".join(str(v) for v in m["spawn_to_start_m"]),
                                                       t["m"], t["need"], lim["wave"])),
                  ("h", t["respite"])]
        lines += [("sw", (ROLE_COL[r], t["role"][r])) for r in ("refuge", "strong", "sleep", "trap") if r in used]
        self.panel(d, lines)
        img.save(os.path.join(out, name + "_routes.png"))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("spec")
    ap.add_argument("--out")
    ap.add_argument("--strict", action="store_true", help="exit 1 when a rule fails")
    a = ap.parse_args()
    with open(a.spec, encoding="utf-8") as f:
        spec = json.load(f)
    out = a.out or os.path.dirname(os.path.abspath(a.spec))
    os.makedirs(out, exist_ok=True)
    name = spec.get("name") or os.path.splitext(os.path.basename(a.spec))[0]
    sch = Scheme(spec)
    m = sch.metrics()
    sch.render(out, name, m)
    with open(os.path.join(out, name + "_metrics.json"), "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=1)
    for key, good in m["checks"].items():
        print("%s %s" % ("OK  " if good else "FAIL", key))
    print("routes:", ", ".join("%s %.0f m" % (k, v["length_m"]) for k, v in m["routes"].items()),
          "| sight top:", ", ".join("%.0f" % s["m"] for s in m["sight_top"][:3]))
    return 1 if a.strict and not all(m["checks"].values()) else 0


if __name__ == "__main__":
    sys.exit(main())
