#!/usr/bin/env python3
"""Harvest several real photos per place from its own official site (+ Wikipedia fallback)."""
import json, re, html, time, urllib.parse, urllib.request, urllib.error
import concurrent.futures as cf

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
      "Accept-Language": "en-US,en;q=0.9"}

def get(url, timeout=22, limit=1_200_000):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
            return r.read(limit).decode("utf-8", "ignore"), r.geturl()
    except Exception:
        return "", url

BAD = re.compile(r'(logo|icon|sprite|favicon|placeholder|avatar|badge|button|arrow|spacer|'
                 r'pixel|blank|loading|thumb-?nail-?default|social|facebook|twitter|instagram|'
                 r'yelp|tripadvisor|footer|header-bg|pattern|texture|swatch|1x1|banner-ad)', re.I)
OK_EXT = re.compile(r'\.(jpe?g|png|webp)(\?|$)', re.I)

def extract(doc, base):
    urls = []
    def add(u):
        if not u: return
        u = html.unescape(u.strip()).split(" ")[0]
        if u.startswith("data:"): return
        if u.startswith("//"): u = "https:" + u
        if not u.startswith("http"): u = urllib.parse.urljoin(base, u)
        urls.append(u)

    for m in re.finditer(r'<meta[^>]+(?:property|name)=["\'](?:og:image|twitter:image)(?::secure_url)?["\']'
                         r'[^>]+content=["\']([^"\']+)', doc, re.I):
        add(m.group(1))
    for m in re.finditer(r'<img[^>]+src=["\']([^"\']+)', doc, re.I):
        add(m.group(1))
    for m in re.finditer(r'<img[^>]+data-src=["\']([^"\']+)', doc, re.I):
        add(m.group(1))
    for m in re.finditer(r'srcset=["\']([^"\']+)', doc, re.I):
        # take the largest candidate in each srcset
        cands = [c.strip().split(" ")[0] for c in m.group(1).split(",") if c.strip()]
        if cands: add(cands[-1])
    for m in re.finditer(r'background-image\s*:\s*url\((["\']?)([^)"\']+)\1\)', doc, re.I):
        add(m.group(2))

    seen, out = set(), []
    for u in urls:
        key = u.split("?")[0].lower()
        if key in seen: continue
        seen.add(key)
        if BAD.search(u): continue
        if not OK_EXT.search(u.split("?")[0]): continue
        out.append(u)
    return out

def verify(u):
    """Keep only URLs that really return a reasonably large image."""
    try:
        req = urllib.request.Request(u, headers=UA, method="GET")
        with urllib.request.urlopen(req, timeout=15) as r:
            ct = (r.headers.get("content-type") or "").lower()
            if not ct.startswith("image/"): return 0
            cl = r.headers.get("content-length")
            if cl and int(cl) < 18000: return 0          # too small = icon
            chunk = r.read(90_000)
            if len(chunk) < 18000 and not cl: return 0
            return int(cl) if cl else len(chunk)
    except Exception:
        return 0

def wiki_images(title, want=4):
    """Lead image + page images from a Wikipedia article."""
    out = []
    if not title: return out
    t = urllib.parse.quote(title.replace(" ", "_"))
    try:
        d = json.load(urllib.request.urlopen(urllib.request.Request(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{t}", headers=UA), timeout=20))
        src = (d.get("originalimage") or d.get("thumbnail") or {}).get("source")
        if src: out.append(src.split("?")[0])
    except Exception:
        pass
    try:
        u = ("https://en.wikipedia.org/w/api.php?action=query&format=json&prop=images"
             f"&titles={t}&imlimit=25")
        d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=20))
        names = []
        for p in ((d.get("query") or {}).get("pages") or {}).values():
            for im in p.get("images", []):
                n = im.get("title", "")
                if n.lower().endswith((".jpg", ".jpeg", ".png")) and not BAD.search(n):
                    names.append(n)
        if names:
            u2 = ("https://en.wikipedia.org/w/api.php?action=query&format=json&prop=imageinfo"
                  "&iiprop=url&iiurlwidth=900&titles=" + urllib.parse.quote("|".join(names[:12])))
            d2 = json.load(urllib.request.urlopen(urllib.request.Request(u2, headers=UA), timeout=25))
            for p in ((d2.get("query") or {}).get("pages") or {}).values():
                th = (p.get("imageinfo") or [{}])[0].get("thumburl")
                if th: out.append(th)
    except Exception:
        pass
    seen, res = set(), []
    for u in out:
        if u in seen: continue
        seen.add(u); res.append(u)
    return res[:want]

SITES = json.load(open("tools/site_map.json"))
WIKI  = json.load(open("tools/wiki_map.json"))

def work(p):
    name = p["n"]
    found = []
    site = SITES.get(name) or p.get("site") or ""
    pages = []
    if site:
        pages.append(site)
        for sub in ("gallery", "photos", "about", "visit", "plan-your-visit"):
            pages.append(urllib.parse.urljoin(site, sub))
    for pg in pages[:4]:
        doc, base = get(pg)
        if not doc: continue
        found += extract(doc, base)
        if len(found) >= 14: break
    # dedupe preserving order
    seen, cand = set(), []
    for u in found:
        k = u.split("?")[0].lower()
        if k in seen: continue
        seen.add(k); cand.append(u)

    good = []
    for u in cand[:22]:
        if verify(u):
            good.append(u)
        if len(good) >= 5: break

    if len(good) < 2:
        for u in wiki_images(WIKI.get(name, ""), 4):
            if u not in good and verify(u):
                good.append(u)
            if len(good) >= 4: break
    return name, good[:5], ("sitio oficial" if site and good else "Wikipedia")

places = json.load(open("tools/places_final.json"))
with cf.ThreadPoolExecutor(max_workers=6) as ex:
    results = dict()
    for name, imgs, src in ex.map(work, places):
        results[name] = {"imgs": imgs, "src": src}
        print(f"{name[:32]:34} {len(imgs)} fotos  ({src})")

json.dump(results, open("tools/img_harvest.json", "w"), indent=1)
tot = sum(len(v["imgs"]) for v in results.values())
zero = [k for k, v in results.items() if not v["imgs"]]
print(f"\ntotal {tot} fotos · sin foto: {len(zero)}")
for z in zero: print("   -", z)
