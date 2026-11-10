#!/usr/bin/env python3
"""Download Seattle Public Schools' attendance areas, option-school GeoZones and school sites (the district's own
ArcGIS services, no key) and write them in the shapes scripts/build.py reads:

  data/elem_zones.json, ms_zones.json, hs_zones.json
      {"source", "year", "schools": {id: {"n", "a", "lat", "lon", "g"}},
       "features": [{"properties": {"dbns": [id], "label", "boro", "dist", "remarks"}, "geometry"}]}
  data/option_schools.json
      {"es" / "ms" / "hs": [[id, name, address, lat, lon, kind]]}   schools without an attendance area
  data/geo_zones.json
      {"es" / "hs": [{"properties": {"id", "name"}, "geometry"}]}   the area with priority at an option school
  data/results.json
      {"year", "schools": {id: [ELA tested, ELA met standard, math tested, math met standard]}}
      Smarter Balanced results, all grades, from the state's Report Card data (data.wa.gov, no key)

School ids are the district's own numbers ("201"); the code calls them dbns, the name left from the NYC site.

    python3 scripts/fetch_seattle.py
"""
import json
import os
import re
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
BASE = "https://services2.arcgis.com/I7NQBinfvOmxQbXs/arcgis/rest/services/"
YEAR = "2025-26"
SCHOOLS = "dbo_vw_schools_2025"
# level: (service, the field with the school's id)
ZONES = {"elem": ("sps_attendance_area_ES_2025_2026", "es_sch"),
         "ms": ("sps_attendance_area_MS_2025_2026", "ms_sch"),
         "hs": ("sps_attendance_area_HS_2025_2026", "HS_SCH")}
GEO_ZONES = {"es": "sps_geo_zone_ES_2025_2026", "hs": "sps_geo_zone_HS_2025_2026"}
# the sites file's "status" for schools without an attendance area, and what the map calls them
OPTION = {"Option ELEM": "option", "Option HS": "option", "Option K-12": "option", "HC": "highly capable"}
# Washington State Report Card assessment data for RESULTS_YEAR (data.wa.gov; each school year is its own dataset)
RESULTS = "https://data.wa.gov/resource/fusr-6kv7.json"
RESULTS_YEAR = "2025-26"
# state names the district's sites file words differently: state name (after name_key) -> sites name (after name_key)
ALIASES = {"frantz coe": "coe", "edmonds s meany": "meany", "stephen decatur": "decatur"}
GRADES = ["PK", "0K"] + [f"{n:02d}" for n in range(1, 13)]


def layer(name):
    q = urllib.parse.urlencode({"where": "1=1", "outFields": "*", "outSR": 4326, "f": "geojson"})
    with urllib.request.urlopen(f"{BASE}{name}/FeatureServer/0/query?{q}", timeout=120) as r:
        d = json.load(r)
    if d.get("exceededTransferLimit"):
        raise SystemExit(f"{name}: more rows than one request returns; page it")
    return d["features"]


def tidy(geom):
    """Coordinates to 5 decimals (about a metre), without the repeats rounding leaves."""
    def ring(r):
        out = []
        for x, y, *_ in r:
            p = [round(x, 5), round(y, 5)]
            if not out or out[-1] != p:
                out.append(p)
        return out
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    polys = [[r2 for r in p if len(r2 := ring(r)) >= 4] for p in polys]
    polys = [p for p in polys if p]
    return {"type": "MultiPolygon", "coordinates": polys} if len(polys) > 1 else {"type": "Polygon", "coordinates": polys[0]}


def grade_list(span):
    """'K-5' -> 'PK,0K,01,...' the way the map's grades() reads it."""
    a, _, b = span.replace("PreK", "PK").replace("P-", "PK-").partition("-")
    key = lambda g: GRADES.index("0K" if g.strip() == "K" else g.strip() if g.strip() == "PK" else f"{int(g):02d}")
    try:
        i, j = key(a), key(b or a)
    except ValueError:
        return ""
    return ",".join(GRADES[i:j + 1])


def name_key(n, level=False):
    """A school's name without the words the district and the state add differently. level=True keeps
    "elementary", "middle" and "high", for the names that differ only by them (West Seattle)."""
    n = n.lower().replace("int'l", "international").replace("&", "and")
    n = re.sub(r"[^a-z0-9 ]", " ", n)
    drop = {"school", "k", "5", "8", "12", "international", "stem", "at", "the", "pk", "ms", "hs"}
    if not level:
        drop |= {"elementary", "middle", "high"}
    return " ".join(w for w in n.split() if w not in drop)


def results(sites):
    q = urllib.parse.urlencode({"$where": "districtcode='17001' AND organizationlevel='School' AND studentgroup='All Students' "
                                          "AND gradelevel='All Grades' AND testadministration='SBAC'", "$limit": 5000})
    with urllib.request.urlopen(f"{RESULTS}?{q}", timeout=120) as r:
        rows = json.load(r)
    by_name = {}
    for sid, s in sites.items():
        by_name.setdefault(name_key(s["n"]), set()).add(sid)
        by_name.setdefault(name_key(s["n"], True), set()).add(sid)
    out, missed = {}, set()
    for r in rows:
        if r["schoolyear"] != RESULTS_YEAR:
            raise SystemExit(f"results are for {r['schoolyear']}, not {RESULTS_YEAR}: point RESULTS at that year's dataset")
        k = name_key(r["schoolname"])
        ids = by_name.get(ALIASES.get(k, k), [])
        if len(ids) != 1:
            ids = by_name.get(name_key(r["schoolname"], True), [])
        if len(ids) != 1:
            missed.add(r["schoolname"])
            continue
        try:
            tested, met = int(r["count_of_students_tested"]), int(r["count_consistent_grade_level"])
        except (KeyError, ValueError):
            continue  # numbers the state holds back for small groups
        row = out.setdefault(min(ids), [None] * 4)
        i = {"ELA": 0, "Math": 2}[r["testsubject"]]
        row[i], row[i + 1] = tested, met
    out = {k: v for k, v in sorted(out.items()) if None not in v}
    if missed:
        print(f"results: no single school in the sites file for {len(missed)}: " + "; ".join(sorted(missed)))
    return out


def save(name, obj):
    path = os.path.join(DATA, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, separators=(",", ":"), ensure_ascii=False)
    print(f"wrote data/{name} ({os.path.getsize(path) / 1e3:.0f} KB)")


def main():
    os.makedirs(DATA, exist_ok=True)
    sites = {}
    for f in layer(SCHOOLS):
        p, (lon, lat) = f["properties"], f["geometry"]["coordinates"][:2]
        sites[str(p["school_ID"])] = {"n": p["school_name"].strip(), "a": f"{p['address'].strip()}, Seattle, WA {p['zip']}",
                                      "lat": round(lat, 6), "lon": round(lon, 6), "g": grade_list(p["grades"] or ""),
                                      "status": p["status"], "span": p["grades"]}
    card = lambda s: {k: s[k] for k in ("n", "a", "lat", "lon", "g")}

    zoned = {}
    for lv, (name, field) in ZONES.items():
        feats, schools = [], {}
        for f in layer(name):
            sid = str(f["properties"][field])
            if sid not in sites:
                print(f"{lv}: zone for school {sid} ({f['properties']}) has no row in the sites file; left without a school")
                ids = []
            else:
                ids = [sid]
                schools[sid] = card(sites[sid])
            feats.append({"type": "Feature", "properties": {"dbns": ids, "label": None, "boro": "", "dist": None, "remarks": None},
                          "geometry": tidy(f["geometry"])})
        zoned[lv] = set(schools)
        save(f"{lv}_zones.json", {"type": "FeatureCollection", "source": "Seattle Public Schools", "year": YEAR,
                                  "schools": schools, "features": feats})

    # schools without an attendance area, on each level's map their grades reach
    opt = {"es": [], "ms": [], "hs": []}
    spans = {"es": {"0K", "01", "02", "03", "04", "05"}, "ms": {"06", "07", "08"}, "hs": {"09", "10", "11", "12"}}
    for sid, s in sorted(sites.items(), key=lambda kv: kv[1]["n"]):
        if s["status"] not in OPTION:
            continue
        for lv, gs in spans.items():
            if gs & set(s["g"].split(",")) and sid not in zoned["elem" if lv == "es" else lv]:
                opt[lv].append([sid, s["n"], s["a"], s["lat"], s["lon"], OPTION[s["status"]], s["g"]])
    save("option_schools.json", opt)
    left = sorted(f"{s['n']} ({s['status']}, {s['span']})" for sid, s in sites.items()
                  if s["status"] not in OPTION and not any(sid in z for z in zoned.values()))
    print(f"not on the map ({len(left)}): " + "; ".join(left))

    res = results(sites)
    save("results.json", {"year": RESULTS_YEAR, "source": "Washington State Report Card (OSPI)", "schools": res})
    on_map = set().union(*zoned.values()) | {r[0] for rows in opt.values() for r in rows}
    print("on the map without results: " + "; ".join(sorted(sites[k]["n"] for k in on_map - set(res))))

    save("geo_zones.json", {lv: [{"type": "Feature", "properties": {"id": str(f["properties"]["GEO_ID"]), "name": f["properties"]["GEOZONE"]},
                                  "geometry": tidy(f["geometry"])} for f in layer(name)] for lv, name in GEO_ZONES.items()})


if __name__ == "__main__":
    main()
