#!/usr/bin/env python3
# Copyright (C) 2026 NYC School Zones
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Build index.html from src/template.html and the files in data/ (written by scripts/fetch_seattle.py).

Uses only the Python standard library. Run from the repo root:

    python3 scripts/build.py                         # index.html + assets/
    python3 scripts/build.py --standalone out.html   # one self-contained file that also opens offline

Steps:
  1. Load each level's attendance areas (data/elem_zones.json, ms_zones.json, hs_zones.json).
  2. Give each zone a "neighbor color" so adjacent zones differ, a label point inside the zone, and an
     approximate area.
  3. Add the option schools (data/option_schools.json) as schools without a zone, their GeoZones
     (data/geo_zones.json), each school's links (data/school_links.json) and the school results (data/results.json) when that file is there.
  4. Inline the elementary data into the template and write index.html; middle and high school go to assets/.
"""
import collections
import json
import re
import os
from html import escape

import settings

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

# GoatCounter visitor counts (https://www.goatcounter.com). Put your site code here. Leave empty to turn it off.
GOATCOUNTER_CODE = ""

SITE_URL = "https://seattle.schoolzones.org/"
SITE_NAME = "Seattle School Zones"
# The map's browser-tab title
SITE_TITLE = "Seattle School Zone Map: Elementary, Middle & High School Attendance Areas (test)"
SITE_DESCRIPTION = ("Every Seattle Public Schools elementary, middle and high school attendance area on one map. "
                    "An experiment built from the NYC School Zones code.")


def fill_settings(template):
    """Years and color ramps from scripts/settings.py into the map's placeholders."""
    def hexc(c):
        return "#%02x%02x%02x" % tuple(c)
    lo, hi = settings.TEST_STOPS[0][0], settings.TEST_STOPS[-1][0]
    rv = lambda name: f"var(--r-{name})"
    gradient = ("linear-gradient(90deg," + f"{rv(settings.TEST_STOPS[0][1])} 0%,"
                + ",".join(f"{rv(c)} {v}%" for v, c in settings.TEST_STOPS) + f",{rv(settings.TEST_STOPS[-1][1])} 100%)")
    # the ramp colors as CSS variables (--r-red ...) for each theme, for the legends
    rvars = {t: ";".join(f"--r-{k}:{hexc(c)}" for k, c in cols.items()) for t, cols in settings.RAMP_COLORS.items()}
    ramp_css = (f':root{{{rvars["light"]}}}@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{{rvars["dark"]}}}}}'
                f':root[data-theme="dark"]{{{rvars["dark"]}}}')
    ticks = "".join(f'<span style="left:{v}%">{v}{"%" if v == hi else ""}</span>' for v, _ in settings.TEST_STOPS)
    for k, v in {"__SNAPSHOT_YEAR__": settings.SNAPSHOT_YEAR, "__SNAPSHOT__": settings.SNAPSHOT_LABEL,
                 "__PREK__": settings.PREK_LABEL, "__MYSCHOOLS__": settings.MYSCHOOLS_LABEL,
                 "__CITY_GRAD__": str(settings.CITY_GRAD), "__CITY_READINESS__": str(settings.CITY_READINESS), "__BLUE_BOOK__": settings.BLUE_BOOK_LABEL,
                 "__DEMOGRAPHICS__": settings.DEMOGRAPHICS_LABEL, "__TESTS__": settings.TESTS_LABEL, "__TESTS_NOTE_SHORT__": settings.TESTS_NOTE_SHORT,
                 "__TESTS_NOTE__": settings.TESTS_NOTE,
                 "__CITY_ELA_ES__": str(settings.CITY_ELA_ES), "__CITY_MATH_ES__": str(settings.CITY_MATH_ES),
                 "__RATE_STOPS__": json.dumps(settings.RATE_STOPS, separators=(",", ":")),
                 "__TEST_STOPS__": json.dumps(settings.TEST_STOPS, separators=(",", ":")),
                 "__OUT_STOPS__": json.dumps(settings.OUT_STOPS, separators=(",", ":")),
                 "__DEMO_GROUPS__": json.dumps(settings.DEMO_GROUPS, separators=(",", ":"), ensure_ascii=False),
                 "__TEST_GRADIENT__": gradient, "__TEST_TICKS__": ticks,
                 "__RAMP_COLORS__": json.dumps(settings.RAMP_COLORS, separators=(",", ":")), "__RAMP_CSS__": ramp_css}.items():
        template = template.replace(k, v)
    return template


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)


def polys(geom):
    return geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]


def area_centroid(ring):
    a = cx = cy = 0.0
    for i in range(len(ring) - 1):
        x0, y0 = ring[i]
        x1, y1 = ring[i + 1]
        c = x0 * y1 - x1 * y0
        a += c
        cx += (x0 + x1) * c
        cy += (y0 + y1) * c
    if a == 0:
        return 0.0, tuple(ring[0])
    return a / 2, (cx / (3 * a), cy / (3 * a))


def point_in_ring(pt, ring):
    x, y = pt
    inside = False
    for i in range(len(ring) - 1):
        x0, y0 = ring[i]
        x1, y1 = ring[i + 1]
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
            inside = not inside
    return inside


DIRECTIONS = {"N", "S", "E", "W", "NORTH", "SOUTH", "EAST", "WEST"}

def prepare_zones(d):
    feats = d["features"]

    # Zones are neighbors if they share boundary vertices.
    owner = collections.defaultdict(set)
    for i, f in enumerate(feats):
        for p in polys(f["geometry"]):
            for ring in p:
                for c in ring[::2]:
                    owner[(round(c[0], 4), round(c[1], 4))].add(i)
    adj = collections.defaultdict(set)
    for s in owner.values():
        for a in s:
            adj[a] |= s - {a}

    # Greedy coloring, most-connected zones first.
    color = {}
    for i in sorted(range(len(feats)), key=lambda i: -len(adj[i])):
        used = {color[j] for j in adj[i] if j in color}
        color[i] = next(c for c in range(10) if c not in used)

    for i, f in enumerate(feats):
        largest = max(polys(f["geometry"]), key=lambda p: abs(area_centroid(p[0])[0]))
        _, c = area_centroid(largest[0])
        if not point_in_ring(c, largest[0]):
            # Centroid fell outside (odd shapes): scan across for an inside point.
            xs = [pt[0] for pt in largest[0]]
            found = None
            for k in range(1, 200):
                x = min(xs) + (max(xs) - min(xs)) * k / 200
                if point_in_ring((x, c[1]), largest[0]):
                    found = (x, c[1])
                    break
            c = found or largest[0][0]
        props = f["properties"]
        props["c"] = color[i]
        props["lp"] = [round(c[1], 5), round(c[0], 5)]
        props["ar"] = round(sum(abs(area_centroid(p[0])[0]) for p in polys(f["geometry"])) * 1e6, 1)
    return max(color.values()) + 1


def head_tags():
    title, desc, url = escape(SITE_NAME), escape(SITE_DESCRIPTION), SITE_URL
    img = SITE_URL + "preview.png"
    return (
        f'<meta name="description" content="{desc}">\n'
        # a test build: keep it out of search results until it has a home of its own
        '<meta name="robots" content="noindex">\n'
        '<link rel="icon" href="favicon.svg" type="image/svg+xml">\n'
        # Home-screen app: opens full screen when added from Safari's Share menu or Chrome's Install
        '<link rel="manifest" href="site.webmanifest">\n'
        '<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">\n'
        '<meta name="apple-mobile-web-app-capable" content="yes">\n'
        '<meta name="mobile-web-app-capable" content="yes">\n'
        '<meta name="apple-mobile-web-app-title" content="School Zones">\n'
        '<meta name="apple-mobile-web-app-status-bar-style" content="default">\n'
        '<meta name="theme-color" content="#f3f4f1" media="(prefers-color-scheme: light)">\n'
        '<meta name="theme-color" content="#141917" media="(prefers-color-scheme: dark)">\n'
        '<meta property="og:type" content="website">\n'
        f'<meta property="og:site_name" content="{title}">\n'
        f'<meta property="og:title" content="{title}">\n'
        f'<meta property="og:description" content="{desc}">\n'
        f'<meta property="og:url" content="{url}">\n'
        f'<meta property="og:image" content="{img}">\n'
        '<meta property="og:image:width" content="1200">\n'
        '<meta property="og:image:height" content="630">\n'
        '<meta name="twitter:card" content="summary_large_image">\n'
        f'<meta name="twitter:title" content="{title}">\n'
        f'<meta name="twitter:description" content="{desc}">\n'
        f'<meta name="twitter:image" content="{img}">\n'
    )


def goatcounter_tag():
    code = GOATCOUNTER_CODE.strip()
    if not code:
        return ""
    return (f'\n<script data-goatcounter="https://{code}.goatcounter.com/count" '
            'async src="https://gc.zgo.at/count.js"></script>')


def option_rows(rows):
    """Option schools as the map's rows for schools without a zone: [id, name, address, lat, lon, priority
    districts (none here), district residents only (0), programs (none), kind flag (1 = highly capable)]."""
    return [[r[0], r[1], r[2], r[3], r[4], [], 0, [], 1 if r[5] == "highly capable" else 0] for r in rows]


def level(name, option, results):
    z = load(name)
    prepare_zones(z)
    out = {"schools": z["schools"], "features": z["features"], "NZ": option_rows(option)}
    ids = set(z["schools"]) | {r[0] for r in option}
    out["T"] = {k: results[k] for k in sorted(ids) if k in results}
    return out, z


def main(standalone_path=None):
    import datetime
    option = load("option_schools.json")
    # results.json (optional): {school id: [ELA tested, ELA met standard, math tested, math met standard]}
    results = load("results.json")["schools"] if os.path.exists(os.path.join(DATA, "results.json")) else {}
    d, z = level("elem_zones.json", option["es"], results)
    d["MS"], _ = level("ms_zones.json", option["ms"], results)
    d["HS"], _ = level("hs_zones.json", option["hs"], results)
    # grades for the schools the zone files don't carry (the option schools)
    d["G"] = {r[0]: r[6] for rows in option.values() for r in rows}
    d["ST"], d["LS"], d["DIST"] = [], {"n": [], "l": []}, {}
    # LK: links for each school on the map, {school id: [its page under the district's school directory, the
    # state's id for its report card]} (data/school_links.json)
    link = load("school_links.json") if os.path.exists(os.path.join(DATA, "school_links.json")) else {}
    names = {r[0]: r[1] for rows in option.values() for r in rows}
    for x in (d, d["MS"], d["HS"]):
        names.update({k: v["n"] for k, v in x["schools"].items()})
    on_map = set(d["schools"]) | set(d["MS"]["schools"]) | set(d["HS"]["schools"]) | set(d["G"])
    d["LK"] = {k: [v["page"], v["state"]] for k, v in link.items() if k in on_map}
    print("no school page link: " + (", ".join(sorted(names.get(k, k) for k in on_map - set(link))) or "none"))
    # GZ: option schools' GeoZones, {school id: [polygon, ...]}, for every level (a K-8's is the same at both)
    gz = load("geo_zones.json") if os.path.exists(os.path.join(DATA, "geo_zones.json")) else {}
    known = {r[0] for rows in option.values() for r in rows}
    d["GZ"] = {}
    for f in (f for fs in gz.values() for f in fs):
        sid = f["properties"]["id"]
        if sid not in known:
            print(f"GeoZone {sid} ({f['properties']['name']}) has no option school on the map; left out")
            continue
        d["GZ"][sid] = polys(f["geometry"])

    with open(os.path.join(ROOT, "src", "template.html"), encoding="utf-8") as f:
        template = f.read()
    template = template.replace("__UPDATED__", datetime.date.today().strftime("%b %Y"))
    with open(os.path.join(ROOT, "VERSION"), encoding="utf-8") as f:
        template = template.replace("__VERSION__", f.read().strip())
    template = template.replace("__ZONES_DATE__", z["year"])
    template = template.replace("__ES_ZONES__", str(len(d["features"])))
    template = fill_settings(template)

    full = dict(d)
    # Middle and high school load on demand from assets/. The standalone file keeps everything inline.
    assets = {}
    os.makedirs(os.path.join(ROOT, "assets"), exist_ok=True)
    for key, obj in {"ms": d.pop("MS"), "hs": d.pop("HS")}.items():
        # A .js file that sets window.NYCSZ[key], loaded with a script tag so it also works from file://
        rel = f"assets/{key}.js"
        with open(os.path.join(ROOT, rel), "w", encoding="utf-8") as f:
            f.write(f"(window.NYCSZ=window.NYCSZ||{{}})[{json.dumps(key)}]=")
            json.dump(obj, f, separators=(",", ":"))
            f.write(";\n")
        assets[key] = rel
    d["ASSETS"] = assets

    if standalone_path:
        write_page(template, full, standalone_path)
        print(f"wrote {standalone_path} ({os.path.getsize(standalone_path) / 1e6:.2f} MB, everything inline)")
    out = os.path.join(ROOT, "index.html")
    write_page(template, d, out)
    print(f"{len(full['GZ'])} option school GeoZones")
    for lv, x in (("elementary", full), ("middle", full["MS"]), ("high", full["HS"])):
        print(f"{lv}: {len(x['features'])} zones, {len(x['NZ'])} schools without a zone, {len(x['T'])} with results")
    print(f"wrote {out} ({os.path.getsize(out) / 1e6:.2f} MB) + " +
          ", ".join(f"{p} ({os.path.getsize(os.path.join(ROOT, p)) / 1e6:.2f} MB)" for p in assets.values()))


def write_page(template, d, out):
    payload = json.dumps(d, separators=(",", ":")).replace("</", "<\\/")
    page = template.replace("__DATA__", payload)

    # The template is an HTML fragment; wrap it as a full document.
    cut = page.index("</style>") + len("</style>")
    html = (
        "<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
        + head_tags()
        + page[:cut].replace(
            "<style>",
            "<style>\n*,*::before,*::after{box-sizing:border-box}\nbody{margin:0}\n[hidden]{display:none!important}\n",
            1,
        )
        + "\n</head>\n<body>"
        + page[cut:]
        + goatcounter_tag()
        + "\n</body>\n</html>\n"
    )
    html = re.sub(r"<title>.*?</title>", lambda m: f"<title>{escape(SITE_TITLE)}</title>", html, count=1)
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)


if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    main(args[args.index("--standalone") + 1] if "--standalone" in args else None)
