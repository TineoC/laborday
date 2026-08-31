#!/usr/bin/env python3
"""Enrich Hershey-area place list: real driving distance/time (OSRM) + Wikipedia image."""
import json, time, urllib.parse, urllib.request

ORIGIN = (40.28736, -76.65803)  # Hersheypark main entrance
UA = {"User-Agent": "hershey-trip-planner/1.0 (personal trip planning)"}

def get(url, timeout=20):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)

def route(lat, lng):
    """Real driving distance (mi) and duration (min) from Hersheypark via OSRM."""
    url = (f"https://router.project-osrm.org/route/v1/driving/"
           f"{ORIGIN[1]},{ORIGIN[0]};{lng},{lat}?overview=false")
    try:
        d = get(url)
        if d.get("code") != "Ok":
            return None, None
        r = d["routes"][0]
        return round(r["distance"] / 1609.344, 1), round(r["duration"] / 60)
    except Exception as e:
        print("  route fail:", e)
        return None, None

def wiki_img(title):
    if not title:
        return ""
    url = ("https://en.wikipedia.org/api/rest_v1/page/summary/"
           + urllib.parse.quote(title.replace(" ", "_")))
    try:
        d = get(url)
        src = (d.get("originalimage") or d.get("thumbnail") or {}).get("source", "")
        return src.split("?")[0]
    except Exception:
        return ""

places = json.load(open("tools/places_seed.json"))
for p in places:
    dist, mins = route(p["lat"], p["lng"])
    p["mi"], p["min"] = dist, mins
    p["img"] = wiki_img(p.get("wiki", ""))
    print(f"{p['n'][:38]:40} {dist} mi  {mins} min  img={'Y' if p['img'] else '-'}")
    time.sleep(0.35)

json.dump(places, open("tools/places_final.json", "w"), indent=1, ensure_ascii=False)
print("\nwrote /tmp/places_out.json", len(places), "places")
