#!/usr/bin/env python3
"""Merge verified per-day hours, weekend events, and official-site photos into the dataset."""
import json

places = {p["n"]: p for p in json.load(open("tools/places_final.json"))}
scan = {r["name"]: r for r in json.load(open("tools/site_scan.json"))}

C = "✓"   # verified from official site
W = "⚠"   # needs confirming

# sched = [Fri, Sat, Sun, Mon(Labor Day)]; ver=True means scraped from the official site today
HOURS = {
 "Tröegs Independent Brewing": (["11am–10pm","11am–10pm","11am–9pm","11:30am–9pm"], True),
 "The Hershey Story Museum":   (["9am–5pm","9am–5pm","9am–5pm","9am–5pm"], True),
 "Hershey Gardens":            (["9am–6pm","9am–6pm","9am–6pm","9am–6pm"], True),
 "Indian Echo Caverns":        (["9am–5pm","9am–5pm","9am–5pm","9am–5pm"], True),
 "AACA Automobile Museum":     (["9am–5pm","9am–5pm","9am–5pm","9am–5pm"], True),
 "Hidden Still Spirits":       (["11am–11pm","11am–11pm","12pm–9pm","11am–10pm"], True),
 "Rubber Soul Brewing":        (["11:30am–11pm","11:30am–11pm","12pm–9pm","11:30am–9pm"], True),
 "Snitz Creek Brewery":        (["11:30am–10pm","11:30am–10pm","11:30am–9pm","11:30am–9pm"], True),
 "Fort Hunter Mansion & Park": (["Parque amanecer–anochecer · Mansión 10am–4:30pm",
                                 "Parque amanecer–anochecer · Mansión 10am–4:30pm",
                                 "Parque amanecer–anochecer · Mansión 12pm–4:30pm",
                                 "Solo el parque (mansión cierra lunes)"], True),
 "Kipona Festival":            (["No abre viernes","11am–7pm","11am–8pm + fuegos artificiales","11am–6pm"], True),
 "Jazz at the Barnyard":       (["Portones 6pm · música 7–9pm","—","—","—"], True),
 "Through the Lens of Hershey":(["6pm–9pm (durante el Jazz)","10am–3pm (Gallery Day)","—","—"], True),
 "Hershey History Center":     (["6pm–9pm (noche de Jazz)","10am–3pm","Cerrado","Cerrado"], True),
 "ZooAmerica":                 (["10am–7pm","10am–7pm","10am–7pm","10am–7pm"], False),
 "Hershey's Chocolate World":  (["9am–9pm","9am–9pm","9am–9pm","9am–9pm"], False),
 "Pennsylvania State Capitol": (["Tours 8:30am–4pm","Tours 9am–4pm","Tours 9am–4pm","Feriado — probablemente cerrado"], False),
 "Cornwall Iron Furnace":      (["9am–5pm","9am–5pm","12pm–5pm","Cerrado (feriado)"], False),
 "Mt. Gretna Lake & Beach":    (["11am–7pm","11am–7pm","11am–7pm","ÚLTIMO DÍA de temporada"], False),
 "The Vineyard at Hershey":    (["12pm–9pm","12pm–9pm","12pm–7pm","12pm–6pm"], False),
 "Cocoa Kayak Rentals":        (["9am–5pm (con reserva)","9am–5pm (con reserva)","9am–5pm (con reserva)","9am–5pm (con reserva)"], False),
 "YAH Brew":                   (["3pm–10pm","12pm–10pm","12pm–8pm","12pm–8pm"], False),
 "Rotunda Brew Pub":           (["11am–11pm","11am–11pm","11am–10pm","11am–10pm"], False),
 "Downtown Lititz":            (["Tiendas 10am–6pm","Tiendas 10am–5pm","Muchas tiendas cerradas","Varía — feriado"], False),
}
DAWN = (["Amanecer–anochecer"]*4, True)
for n in ("Swatara State Park","Memorial Lake State Park","Wildwood Park","Boyd Big Tree Preserve",
          "Coleman Memorial Park","Reservoir Park","Governor Dick Observation Tower",
          "Second Mountain Hawk Watch","Waggoner's Gap Hawk Watch","Hawk Rock Overlook"):
    HOURS[n] = DAWN

# weekend-specific happenings found on the official sites
EVENTS = {
 "Kipona Festival": "🎉 110º Kipona · Family Fun Zone, Giant Puppet Parade, Keystone Dock Dogs, "
                    "Art in the Park, food trucks, beer/wine garden. FUEGOS ARTIFICIALES el domingo. "
                    "Parqueo con parquímetro GRATIS domingo y lunes; $5 en River Street Garage el sábado 8am–5pm.",
 "AACA Automobile Museum": "🚗 SÁBADO 5: Duryea Day (show de autos antiguos, 9am–3pm) + Ollie Day (9am–5pm) "
                           "+ charla 'Board Tracks: Speed, Spectacle & Risk in Early Auto Racing'.",
 "Hershey Gardens": "🎨 Vie 4 a Dom 6: Hershey Area Art Association Show & Sale ('Blooming Art'), 9am–6pm. "
                    "Viernes 12–12:30pm: alimentación en vivo en el Zoology Zone.",
 "Jazz at the Barnyard": "🎷 VIERNES 4: concierto de la banda Third Stream, 7–9pm. Portones y exhibición de fotos abren 6pm.",
 "Through the Lens of Hershey": "📸 Fotografía de John Martin. Vie 4 noche de preview (6–9pm, durante el Jazz) "
                                "y Sáb 5 Gallery Day (10am–3pm).",
 "Downtown Lititz": "🛍️ Vie 4 y Sáb 5: 'Thanks for the Love Party' en Bunyaad Marketplace — 20% de descuento en todo.",
 "Tröegs Independent Brewing": "🍺 Abierto el lunes de Labor Day con horario especial (11:30am–9pm).",
 "Mt. Gretna Lake & Beach": "🏖️ El lunes de Labor Day suele ser el ÚLTIMO día de la temporada. Llamen antes.",
}

# real photos pulled from each place's own website (og:image)
for name, r in scan.items():
    if r.get("img") and name in places:
        places[name]["img"] = r["img"]
        places[name]["credit"] = r["url"]
        places[name]["imgsrc"] = "sitio oficial"

for n, p in places.items():
    sched, ver = HOURS.get(n, (["Confirmar"]*4, False))
    p["sched"] = sched
    p["ver"] = ver
    p["event"] = EVENTS.get(n, "")
    if p.get("img") and p.get("imgsrc") != "sitio oficial":
        p["imgsrc"] = "Wikimedia Commons"
    # a place is "available" on a day if its schedule isn't a dash/closed marker
    p["days"] = [0 if (s in ("—",) or "cerrad" in s.lower() or "no abre" in s.lower()) else 1
                 for s in sched]

out = sorted(places.values(), key=lambda p: p["mi"])
json.dump(out, open("tools/places_final.json", "w"), indent=1, ensure_ascii=False)
print("places:", len(out))
print("horario verificado en sitio oficial:", sum(1 for p in out if p["ver"]))
print("con evento del finde:", sum(1 for p in out if p["event"]))
print("fotos:", sum(1 for p in out if p["img"]),
      "(oficiales:", sum(1 for p in out if p.get("imgsrc") == "sitio oficial"), ")")
