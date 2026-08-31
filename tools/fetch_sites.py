#!/usr/bin/env python3
"""Fetch each place's official site: real og:image photo + Labor Day weekend events."""
import json, re, time, urllib.parse, urllib.request, urllib.error, html, concurrent.futures as cf

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
      "Accept-Language": "en-US,en;q=0.9"}

# official sites, incl. ones missing from the dataset
SITES = {
 "Tröegs Independent Brewing": "https://www.troegs.com/",
 "The Hershey Story Museum": "https://hersheystory.org/",
 "Hershey Gardens": "https://www.hersheygardens.org/",
 "Hershey's Chocolate World": "https://www.chocolateworld.com/",
 "AACA Automobile Museum": "https://www.aacamuseum.org/",
 "Pennsylvania State Capitol": "https://www.pacapitol.com/",
 "Indian Echo Caverns": "https://indianechocaverns.com/",
 "Cocoa Kayak Rentals": "https://cocoakayak.com/",
 "Mt. Gretna Lake & Beach": "https://mtgretnalake.com/",
 "The Vineyard at Hershey": "https://www.thevineyardathershey.com/",
 "Jazz at the Barnyard": "https://hersheyhistory.org/",
 "Through the Lens of Hershey": "https://hersheyhistory.org/",
 "Hidden Still Spirits": "https://hiddenstill.com/",
 "Kipona Festival": "https://harrisburgpa.gov/kipona/",
 "ZooAmerica": "https://zooamerica.com/",
 "Fort Hunter Mansion & Park": "https://forthunter.org/",
 "Cornwall Iron Furnace": "https://www.cornwallironfurnace.org/",
 "Swatara State Park": "https://www.dcnr.pa.gov/StateParks/FindAPark/SwataraStatePark/",
 "Memorial Lake State Park": "https://www.dcnr.pa.gov/StateParks/FindAPark/MemorialLakeStatePark/",
 "Rubber Soul Brewing": "https://www.rubbersoulbrewing.com/",
 "Snitz Creek Brewery": "https://www.snitzcreekbrewery.com/",
 "YAH Brew": "https://www.yahbrew.com/",
 "Rotunda Brew Pub": "https://www.hersheylodge.com/dining/rotunda-brew-pub/",
 "Downtown Lititz": "https://www.lititzpa.com/",
 "Wildwood Park": "https://www.dauphincounty.gov/departments/parks-and-recreation/parks/wildwood-park",
 "Boyd Big Tree Preserve": "https://www.dcnr.pa.gov/StateParks/FindAPark/BoydBigTreePreserveConservationArea/",
 "Coleman Memorial Park": "https://www.lebanonpa.org/coleman-memorial-park/",
 "Reservoir Park": "https://harrisburgpa.gov/parks-recreation/",
 "Governor Dick Observation Tower": "https://www.parksandtrails.org/",
 "Second Mountain Hawk Watch": "https://www.hawkcount.org/",
 "Waggoner's Gap Hawk Watch": "https://waggonersgap.org/",
 "Hawk Rock Overlook": "https://www.appalachiantrail.org/",
}

def fetch(url, timeout=25):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read(900_000)
            return raw.decode("utf-8", "ignore"), r.geturl()
    except Exception as e:
        return "", str(e)

def og_image(doc, base):
    for pat in (r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',
                r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
                r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)'):
        m = re.search(pat, doc, re.I)
        if m:
            u = html.unescape(m.group(1)).strip()
            if u.startswith("//"): u = "https:" + u
            if u.startswith("/"):  u = urllib.parse.urljoin(base, u)
            if u.lower().endswith((".svg",)) or "logo" in u.lower(): continue
            return u
    return ""

# Labor Day weekend 2026 = Sep 4 (Fri) .. Sep 7 (Mon)
DATE_PATS = [
 r'\bSept?(?:ember)?\.?\s*[4-7]\b', r'\b9/[4-7]\b', r'\b2026-09-0[4-7]\b',
 r'\bLabor\s*Day\b', r'\bSept?(?:ember)?\.?\s*4\s*[-–]\s*7\b',
]
EVENT_WORDS = r'(festival|live music|concert|tour|tasting|workshop|special|hours|closed|open|event|celebration|weekend|market|class)'

def scan_events(doc):
    txt = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', doc, flags=re.S|re.I)
    txt = html.unescape(re.sub(r'<[^>]+>', ' ', txt))
    txt = re.sub(r'\s+', ' ', txt)
    hits = []
    for pat in DATE_PATS:
        for m in re.finditer(pat, txt, re.I):
            s = max(0, m.start()-130); e = min(len(txt), m.end()+180)
            snip = txt[s:e].strip()
            if re.search(EVENT_WORDS, snip, re.I):
                hits.append(snip)
    # dedupe
    seen, out = set(), []
    for h_ in hits:
        k = h_[:70].lower()
        if k in seen: continue
        seen.add(k); out.append(h_)
    return out[:6]

def work(item):
    name, url = item
    doc, final = fetch(url)
    res = {"name": name, "url": url, "ok": bool(doc), "img": "", "events": [], "err": ""}
    if not doc:
        res["err"] = final[:90]; return res
    res["img"] = og_image(doc, final if final.startswith("http") else url)
    res["events"] = scan_events(doc)
    # also try an events/calendar subpage
    for sub in ("events", "calendar", "events/", "whats-happening", "plan-your-visit", "hours"):
        u2 = urllib.parse.urljoin(final if final.startswith("http") else url, sub)
        d2, f2 = fetch(u2, 18)
        if d2 and len(d2) > 2000:
            ev = scan_events(d2)
            if ev:
                res["events"] = (res["events"] + ev)[:8]
                res["events_url"] = u2
                break
    return res

with cf.ThreadPoolExecutor(max_workers=6) as ex:
    results = list(ex.map(work, SITES.items()))

json.dump(results, open("tools/site_scan.json", "w"), indent=1, ensure_ascii=False)
for r in results:
    flag = "IMG" if r["img"] else "---"
    print(f'{r["name"][:30]:32} {flag}  ev={len(r["events"])}  {r["err"][:40]}')
print("\nsaved /tmp/site_scan.json")
