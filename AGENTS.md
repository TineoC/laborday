# AGENTS.md

Instructions for AI coding agents working in this repository.

## What this is

A single-page guide to things to do outside Hersheypark over Labor Day weekend
2026 (Fri Sep 4 – Mon Sep 7), built for one family trip. Live at
https://laborday.tineochristopher.com, served by GitHub Pages from `main`.

The whole site is **one file**: `index.html`. It is generated — do not hand-edit
it.

## Layout

```
index.html                  generated output; never edit directly
CNAME                       custom domain for GitHub Pages
tools/places_seed.json      the 32 places: name, category, coords, price, copy
tools/places_final.json     enriched dataset the page is built from
tools/i18n_en.json          English translation of the UI and of every place
tools/img_harvest.json      photo URLs per place
tools/build_page.py         renders places_final.json -> index.html
tools/enrich_distances.py   OSRM driving distance/time from Hersheypark
tools/fetch_sites.py        scrapes official sites for hours, events, photos
tools/harvest_imgs.py       collects several photos per place
tools/merge.py              merges hours + events + photos -> places_final.json
```

Rebuild after any data change:

```bash
python3 tools/build_page.py
```

## Hard rules

**Never invent a fact.** Every hour, price, distance and photo on this page is
either scraped from a real source or explicitly marked as unverified in the UI.
A plausible-looking guess is worse than an honest ⚠ badge, because someone
drives 30 miles on it.

**The ✓/⚠ badge is load-bearing.** `ver: true` means the hours came from that
venue's own website. If you add a place and you did not scrape its hours, set
`ver: false`. Do not set it to `true` to make the page look tidier.

**Only ship a photo that is verifiably of the subject.** See the failure log
below. When in doubt, no photo — the card falls back to a coloured tile with a
category emoji, which is fine.

**No new dependencies.** Leaflet from CDN is the only runtime dependency and it
stays that way. No build step, no bundler, no framework.

**Page copy is informal Spanish, and Spanish is the source of truth.** Place
names stay in English as they appear on Google Maps.

**The page is bilingual (es/en).** English lives in `tools/i18n_en.json` and is
a *translation layer only* — never put a fact there that is not already in the
Spanish copy. `build_page.py` refuses to build if a place, a schedule phrase or
a photo credit has no English entry. The language is picked from
`navigator.languages` (first entry that is `en` or `es`, otherwise Spanish), and
can be forced with `?lang=en` / `?lang=es` or the toggle in the header. Once
forced, `lang` rides along in every shareable URL.

## Data sources that work

| Data | Source | Key needed |
|---|---|---|
| Driving distance & time | OSRM `router.project-osrm.org` | No |
| Map tiles | `tile.openstreetmap.org` | No |
| Hours, events, photos | each venue's own website, via `curl` | No |
| Fallback photos | Wikipedia REST API / Wikimedia Commons | No |

Distances are real driving routes from the Hersheypark entrance
(`40.28736, -76.65803`), not straight lines.

## Sources that do NOT work — do not retry these

- **Google ratings and hours cannot be scraped.** `google.com/search` returns a
  JS-only shell with no rating markup. The stars in the dataset are reference
  values, clearly labelled as such in the UI, and every card links to live
  Google Maps. Getting real ratings requires a Google Places API key.
- **Google Images is not available** for the same reason. Use the venue's own
  `og:image` instead — it is usually the same hero photo Google surfaces.
- **CARTO basemap tiles now demand an API key.** The map used
  `basemaps.cartocdn.com` and started rendering "API KEY REQUIRED" watermarks
  across every tile. Replaced with plain OpenStreetMap tiles darkened via a CSS
  filter applied to `.leaflet-tile-pane` only, so markers and popups keep their
  colour. Do not reintroduce CARTO.
- **Wikimedia Commons geosearch is useless here.** Searching by coordinates
  returned a photo of a cat for a brewery and a Bowie knife for a park. Commons
  *category* listings and Wikipedia *article* images are acceptable; geosearch
  is not.
- **Commons file pages carry no coordinates**, so images cannot be
  geo-verified programmatically.

## Photo sourcing failure log

Automatic image search assigned, in earlier passes:

- Minnesota state parks (Afton, Bear Head Lake) to Governor Dick Observation
  Tower — `parksandtrails.org` is a Minnesota organisation, not the PA one
- Hawk Mountain Sanctuary photos to Second Mountain Hawk Watch — different place
- Hershey Lodge waterpark and roller-coaster shots to Rotunda Brew Pub
- A generic county-commissioners portrait to Wildwood Park
- A file literally named `Wanda.png` to Reservoir Park and Kipona Festival

All were purged by hostname and filename blacklist in `harvest_imgs.py`. If you
extend the harvester, extend the blacklist too, and **eyeball the filenames
before committing** — the automated relevance gate catches maybe 60% of bad
matches.

One bug worth remembering: an early filename filter included the token `wiki`,
which silently discarded every `upload.wikimedia.org` URL and made it look like
Wikipedia had no images for anything. Match blacklists against the **filename**,
not the whole URL.

## Verified weekend facts

Already confirmed from official sites and baked into the dataset. Do not
re-scrape these:

- **Kipona Festival** is Sep 5–7, not Friday. Sat 11am–7pm, Sun 11am–8pm with
  fireworks, Mon 11am–6pm. Free metered parking Sun and Mon.
- **AACA Museum, Sat Sep 5:** Duryea Day car show 9am–3pm, Ollie Day 9am–5pm.
- **Hershey Gardens, Sep 4–6:** Art Association Show & Sale 9am–6pm.
- **Jazz at the Barnyard:** Fri Sep 4, gates 6pm, music 7–9pm.
- **Tröegs:** Fri/Sat 11am–10pm, Sun 11am–9pm, Labor Day 11:30am–9pm.

22 of 32 places have officially confirmed hours; 10 are estimates flagged ⚠.

Two flagged on the page as worth a phone call: **Mt. Gretna Lake** (season
normally ends on Labor Day) and **PA State Capitol** (holiday Monday tours may
not run).

## Context that shapes the content

The family holds a **Happy Hours ticket** — park entry from 5pm to close. So
every suggestion is a morning or early-afternoon activity, and the page says so
up top. Keep that framing if you add places.

## Deployment

Push to `main`. GitHub Pages rebuilds automatically. DNS is a `CNAME` record
`laborday` → `tineoc.github.io` in Cloudflare, deliberately **not proxied**, so
GitHub can complete its Let's Encrypt challenge. If you turn the Cloudflare
proxy on, set SSL mode to Full or the cert will break.

## Review

@TineoC owns everything — see [`.github/CODEOWNERS`](.github/CODEOWNERS).
Contribution guidelines are in [`CONTRIBUTING.md`](CONTRIBUTING.md).
