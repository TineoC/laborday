#!/usr/bin/env python3
"""Render the Hershey weekend page with the enriched dataset inlined."""
import json
import re

places = json.load(open("tools/places_final.json"))
DATA = json.dumps(places, ensure_ascii=False, separators=(",", ":"))

i18n = json.load(open("tools/i18n_en.json"))
i18n.pop("_comment", None)
I18N = json.dumps(i18n, ensure_ascii=False, separators=(",", ":"))

agenda = json.load(open("tools/agenda.json"))
agenda.pop("_comment", None)
AGENDA = json.dumps(agenda, ensure_ascii=False, separators=(",", ":"))

missing = [p["n"] for p in places if p["n"] not in i18n["places"]]
if missing:
    raise SystemExit("no English copy for: " + ", ".join(missing))

# Spanish copy that would leak untranslated into the English page.
# Bare clock strings ("9am–5pm") and dashes are language-neutral and need no entry.
CLOCK = re.compile(r"^[\d:apm–\-— ]*$", re.I)
leaks = sorted(
    {
        s
        for p in places
        for s in p["sched"]
        if s not in i18n["sched"] and not CLOCK.match(s)
    }
    | {p["imgsrc"] for p in places if p["imgsrc"] and p["imgsrc"] not in i18n["imgsrc"]}
)
if leaks:
    raise SystemExit("no English for: " + " | ".join(leaks))

# The suggested agenda: every slot has to point at a place that is actually open
# that day, and every line of Spanish copy in it needs an English twin.
by_name = {p["n"]: p for p in places}
bad = []
if [d.get("d") for d in agenda["days"]] != [0, 1, 2, 3]:
    bad.append("agenda.days must be exactly d 0,1,2,3 in order")
for day in agenda["days"]:
    d = day["d"]
    for slot in day["slots"]:
        kinds = [k for k in ("n", "park", "label") if slot.get(k)]
        if len(kinds) != 1:
            bad.append(
                f"day {d} slot {slot.get('t')}: needs exactly one of n/park/label"
            )
        if slot.get("n"):
            p = by_name.get(slot["n"])
            if not p:
                bad.append(f"day {d}: no place named {slot['n']!r}")
            elif not p["days"][d]:
                bad.append(f"day {d}: {slot['n']} is closed that day")
        for key in ("label", "note"):
            s = slot.get(key)
            if s and s not in i18n["agenda"]:
                bad.append(f"no English for agenda {key}: {s}")
if bad:
    raise SystemExit("agenda.json: " + " | ".join(bad))

HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hershey — Labor Day Weekend 2026</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<style>
:root{
  --bg:#140f0d; --card:#211815; --card2:#2a1e19; --ink:#f6efe9; --dim:#a89287;
  --gold:#f0a83a; --green:#67c07a; --blue:#5eb3e4; --line:#3a2a23;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);
  font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;-webkit-text-size-adjust:100%}
.wrap{max-width:1200px;margin:0 auto;padding:0 14px}

header{background:linear-gradient(160deg,#3a1f10,#140f0d);border-bottom:1px solid var(--line);padding:26px 0 20px}
h1{margin:0 0 6px;font-size:clamp(22px,5vw,32px);letter-spacing:-.6px}
.dates{color:var(--gold);font-weight:600;font-size:15px}
.langbar{display:flex;gap:6px;align-items:center;justify-content:flex-end;margin-bottom:10px;font-size:12px}
.langbar span{color:var(--dim)}
.langbar button{background:var(--card);color:var(--dim);border:1px solid var(--line);
  padding:4px 10px;border-radius:99px;font-size:12px;cursor:pointer}
.langbar button.on{background:var(--gold);color:#2a1a08;border-color:var(--gold);font-weight:700}
.origin{color:var(--dim);font-size:13px;margin-top:5px}

.note{background:var(--card2);border:1px solid var(--line);border-left:3px solid var(--gold);
  padding:12px 14px;border-radius:10px;font-size:14px;margin:14px 0}
.note.warn{border-left-color:#e0644a}

.leaflet-tile-pane{filter:invert(1) hue-rotate(180deg) brightness(.72) contrast(1.05) saturate(.7)}
.leaflet-container{background:#0d0a09}
#map{height:min(58vh,460px);border-radius:14px;margin:14px 0;border:1px solid var(--line);background:#0d0a09}

.bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:14px 0 6px;
  position:sticky;top:0;z-index:500;background:var(--bg);padding:10px 0;border-bottom:1px solid var(--line)}
.bar button{background:var(--card);color:var(--ink);border:1px solid var(--line);
  padding:7px 13px;border-radius:99px;font-size:14px;cursor:pointer;white-space:nowrap}
.bar button.on{background:var(--gold);color:#2a1a08;border-color:var(--gold);font-weight:700}
.bar .spacer{flex:1}
.bar button.sharebtn{background:#2a1e19;color:var(--dim);border-style:dashed}
.bar button.sharebtn:hover{color:var(--gold);border-color:var(--gold)}
.bar select{background:var(--card);color:var(--ink);border:1px solid var(--line);
  border-radius:8px;padding:7px 10px;font-size:14px}
.count{color:var(--dim);font-size:13px;padding:6px 0}
.quick{display:flex;flex-wrap:wrap;gap:7px;align-items:center;margin:14px 0 0;font-size:13px}
.quick span{color:var(--dim)}
.quick a{color:var(--gold);text-decoration:none;padding:5px 11px;border-radius:99px;
  border:1px solid var(--line);background:var(--card)}
.quick a:hover{border-color:var(--gold)}

.grid{display:grid;gap:14px;grid-template-columns:repeat(auto-fill,minmax(310px,1fr));margin-bottom:26px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;overflow:hidden;
  display:flex;flex-direction:column;transition:transform .12s,border-color .12s}
.card:hover{transform:translateY(-2px);border-color:#5a4034}
.thumb{height:150px;background-size:cover;background-position:center;position:relative;
  background-color:#2a1e19;display:flex;align-items:center;justify-content:center;font-size:46px}
.thumb{padding:0}
.gal{display:flex;height:100%;overflow-x:auto;scroll-snap-type:x mandatory;
  scrollbar-width:none;-webkit-overflow-scrolling:touch}
.gal::-webkit-scrollbar{display:none}
.gal img{flex:0 0 100%;width:100%;height:100%;object-fit:cover;scroll-snap-align:center;
  background:#2a1e19}
.galn{position:absolute;bottom:7px;right:8px;background:rgba(12,8,6,.8);color:#e8dcd3;
  font-size:10.5px;padding:2px 8px;border-radius:99px;pointer-events:none}
.noimg{width:100%;height:100%;display:flex;align-items:center;justify-content:center;font-size:46px}
.thumb .badges{position:absolute;top:8px;left:8px;right:8px;display:flex;justify-content:space-between;gap:6px}
.pill{background:rgba(12,8,6,.82);backdrop-filter:blur(4px);color:var(--ink);font-size:12px;
  padding:4px 9px;border-radius:99px;font-weight:600;white-space:nowrap}
.pill.stars{color:var(--gold)}
.pill.rec{background:var(--gold);color:#2a1a08}
.pill.free{background:rgba(103,192,122,.9);color:#0d2412}
.body{padding:13px 14px 14px;display:flex;flex-direction:column;flex:1}
.card h3{margin:0 0 2px;font-size:17px;line-height:1.25}
.town{color:var(--dim);font-size:13px;margin-bottom:9px}
.facts{display:grid;grid-template-columns:auto 1fr;gap:3px 10px;font-size:13.5px;margin-bottom:9px}
.facts dt{color:var(--dim)}
.facts dd{margin:0}
.price{color:var(--green);font-weight:600}
.why{font-size:14px;margin:0 0 8px}
.tip{font-size:13px;background:#2f2119;border-left:2px solid var(--gold);padding:7px 10px;
  border-radius:0 7px 7px 0;color:#e4d3c6;margin-bottom:10px}
.days{display:flex;gap:5px;margin-bottom:11px}
.day{font-size:11px;padding:2px 8px;border-radius:6px;background:#191210;color:#6b5a51;border:1px solid var(--line)}
.day.hit{background:var(--gold);color:#2a1a08;font-weight:700;border-color:var(--gold)}
.links{display:flex;gap:7px;flex-wrap:wrap;margin-top:auto}
.links a{font-size:13px;text-decoration:none;padding:7px 11px;border-radius:8px;
  background:#33231d;color:var(--gold);border:1px solid var(--line);white-space:nowrap}
.links a.primary{background:var(--gold);color:#2a1a08;font-weight:700;border-color:var(--gold)}
.event{background:linear-gradient(90deg,#4a2a12,#33231d);border:1px solid #6b4520;
  color:#ffd9a0;font-size:13px;padding:9px 11px;border-radius:9px;margin-bottom:10px;line-height:1.45}
.schedhead{font-size:11px;text-transform:uppercase;letter-spacing:.9px;color:var(--dim);
  margin:2px 0 6px;display:flex;justify-content:space-between;align-items:center;gap:8px}
.vb{font-size:10px;letter-spacing:0;text-transform:none;padding:2px 7px;border-radius:99px;font-weight:700}
.vb.ok{background:rgba(103,192,122,.18);color:var(--green);border:1px solid rgba(103,192,122,.4)}
.vb.chk{background:rgba(224,100,74,.16);color:#f0916f;border:1px solid rgba(224,100,74,.4)}
table.sched{width:100%;border-collapse:collapse;font-size:13px;margin-bottom:10px}
table.sched th{text-align:left;font-weight:700;color:var(--gold);width:64px;padding:3px 0;vertical-align:top}
table.sched td{padding:3px 0;color:#e8dcd3}
table.sched tr.off th{color:#6b5a51}
table.sched tr.off td{color:#6b5a51}
table.sched tr.lastday th::after{content:" 🇺🇸";font-size:9px}
.credit{font-size:10px;color:#6b5a51;margin-top:8px}
.credit a{color:#6b5a51}

h2.sec{font-size:14px;text-transform:uppercase;letter-spacing:1.3px;color:var(--dim);
  margin:26px 0 12px;border-bottom:1px solid var(--line);padding-bottom:7px}

/* ---------- agendas (suggested + build-your-own) ---------- */
.secsub{color:var(--dim);font-size:13px;margin:-6px 0 12px}
.agdays{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(240px,1fr))}
.agday{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 13px}
.agday h3{margin:0 0 9px;font-size:15px;color:var(--gold);letter-spacing:-.2px}
.aslot{display:flex;gap:9px;padding:7px 0;border-top:1px solid var(--line);font-size:13.5px}
.agday .aslot:first-of-type{border-top:0}
.aslot .at{color:var(--gold);font-weight:700;flex:0 0 62px;font-variant-numeric:tabular-nums}
#plan-days .aslot .at{flex:0 0 20px}   /* "1." needs far less room than "11:30am" */
.aslot .an{flex:1;min-width:0}
.aslot .an a{color:var(--ink);text-decoration:none;border-bottom:1px dotted #5a4034}
.aslot .an a:hover{color:var(--gold)}
.aslot .ameta{color:var(--dim);font-size:12px;margin-top:2px}
.aslot .anote{color:#e4d3c6;font-size:12px;margin-top:3px;border-left:2px solid var(--gold);padding-left:7px}
.aslot.park{background:linear-gradient(90deg,#4a2a12,#33231d);border-radius:8px;padding:8px 9px;
  border-top:0;margin-top:7px}
.aslot.park .an{color:#ffd9a0;font-weight:600}
.aslot.opt{opacity:.72}
.aslot .aopt{font-size:10.5px;text-transform:uppercase;letter-spacing:.7px;color:var(--dim)}
.agempty{color:#6b5a51;font-size:13px;padding:6px 0}
.planbtns{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 12px}
.planbtns button{background:var(--card);color:var(--ink);border:1px solid var(--line);
  padding:7px 13px;border-radius:99px;font-size:13.5px;cursor:pointer}
.planbtns button:hover{border-color:var(--gold);color:var(--gold)}
.planbtns button.primary{background:var(--gold);color:#2a1a08;border-color:var(--gold);font-weight:700}
.aslot .arrow{display:flex;gap:4px;align-items:flex-start}
.aslot .arrow button{background:none;border:1px solid var(--line);color:var(--dim);border-radius:6px;
  width:22px;height:22px;line-height:1;font-size:12px;cursor:pointer;padding:0}
.aslot .arrow button:hover{color:var(--gold);border-color:var(--gold)}
.daytog{display:flex;flex-wrap:wrap;gap:5px;align-items:center;margin-bottom:11px}
.daytog .lab{font-size:11px;text-transform:uppercase;letter-spacing:.9px;color:var(--dim)}
.daytog button{background:#191210;color:var(--dim);border:1px solid var(--line);
  font-size:11.5px;padding:3px 9px;border-radius:6px;cursor:pointer}
.daytog button:hover{border-color:var(--gold);color:var(--gold)}
.daytog button.on{background:var(--gold);color:#2a1a08;font-weight:700;border-color:var(--gold)}
footer{color:var(--dim);font-size:12.5px;padding:22px 0 50px;border-top:1px solid var(--line);margin-top:20px}
.fnote{margin-bottom:12px;line-height:1.6}
.flinks{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px}
.flinks a{color:var(--gold);text-decoration:none;font-size:12.5px;padding:5px 11px;
  border:1px solid var(--line);border-radius:99px;background:var(--card)}
.flinks a:hover{border-color:var(--gold)}
.copy{font-size:12px;line-height:1.6;color:#8b776c}
footer a{color:var(--gold)}
.leaflet-popup-content-wrapper{background:#241916;color:#f6efe9;border-radius:10px}
.leaflet-popup-tip{background:#241916}
.leaflet-popup-content{margin:11px 13px;font:13.5px/1.45 -apple-system,sans-serif}
.leaflet-popup-content a{color:var(--gold)}
@media(max-width:600px){.grid{grid-template-columns:1fr}.thumb{height:135px}}
</style>
</head>
<body>

<header><div class="wrap">
  <div class="langbar"><span id="langlabel"></span>
    <button data-l="es">Español</button><button data-l="en">English</button>
  </div>
  <h1 id="t-h1">🍫 Hershey — Fin de Semana de Labor Day</h1>
  <div class="dates" id="t-dates">Vie 4 · Sáb 5 · Dom 6 · Lun 7 de septiembre 2026</div>
  <div class="origin" id="t-origin">Todas las distancias y tiempos son manejando desde la entrada de Hersheypark</div>
</div></header>

<div class="wrap">

  <div class="note" id="t-note1">
    <b>⏰ Happy Hours Ticket:</b> el parque es <b>el sábado, de 5:00 pm al cierre</b>.
    Ese día todo lo demás va <b>en la mañana o temprano en la tarde</b>.
    El viernes es de llegada y algo social; el domingo y el lunes las tardes quedan libres.
    Bonus: con ese boleto <b>ZooAmerica es gratis</b> entrando desde adentro del parque.
  </div>

  <div class="note warn" id="t-note2">
    <b>Horarios:</b> los marcados <span style="color:#67c07a">✓ confirmado</span> los saqué del sitio oficial
    del lugar. Los <span style="color:#f0916f">⚠ confirmar</span> son estimados — llamen o revisen Google Maps.
    <b>⭐ Las estrellas son de referencia</b>; el botón "Maps + reviews" abre Google Maps con las reales.
  </div>

  <section id="agenda">
    <h2 class="sec" id="t-agenda-h">Agenda sugerida</h2>
    <div class="secsub" id="t-agenda-sub"></div>
    <div class="agdays" id="agenda-days"></div>
  </section>

  <section id="myplan">
    <h2 class="sec" id="t-plan-h">Arma tu propia agenda</h2>
    <div class="secsub" id="t-plan-sub"></div>
    <div class="planbtns" id="plan-btns"></div>
    <div class="agdays" id="plan-days"></div>
  </section>

  <div class="quick" id="quick"></div>

  <div id="map"></div>

  <div class="bar" id="bar"></div>
  <div class="count" id="count"></div>
  <div id="cards"></div>

  <footer>
    <div class="fnote" id="t-fnote">
      Distancias y tiempos de manejo calculados con OSRM sobre datos de OpenStreetMap ·
      mapa &copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> ·
      horarios y eventos del sitio oficial de cada lugar · estrellas de Google Maps (referencia).
      Fotos del sitio oficial de cada lugar o de Wikimedia/Wikipedia — desliza sobre la imagen para ver más.
    </div>
    <div class="flinks">
      <a href="https://github.com/TineoC/laborday" target="_blank" rel="noopener" id="t-fcode">Código en GitHub</a>
      <a href="https://github.com/TineoC/laborday/blob/main/CONTRIBUTING.md" target="_blank" rel="noopener" id="t-fcontrib">Cómo contribuir</a>
      <a href="https://github.com/TineoC/laborday/blob/main/AGENTS.md" target="_blank" rel="noopener">AGENTS.md</a>
      <a href="https://github.com/TineoC/laborday/blob/main/.github/CODEOWNERS" target="_blank" rel="noopener">CODEOWNERS</a>
      <a href="https://github.com/TineoC/laborday/issues/new" target="_blank" rel="noopener" id="t-fissue">Reportar un dato incorrecto</a>
    </div>
    <div class="copy" id="t-fcopy">
      &copy; 2026 Christopher Tineo. Publicado bajo
      <a href="https://github.com/TineoC/laborday/blob/main/LICENSE" target="_blank" rel="noopener">licencia MIT</a>.
      Guía informativa hecha para un viaje familiar — no está afiliada a Hersheypark,
      The Hershey Company ni a ninguno de los lugares listados.
      Verifiquen horarios y precios antes de salir.
    </div>
  </footer>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const PLACES = __DATA__;
const I18N = __I18N__;
const AGENDA = __AGENDA__;
const DAYS_ES = ["Vie","Sáb","Dom","Lun"];
const CATS = ["Todos","⭐ Recomendados","Miradores","Parques","Conocer","Agua & Aventura","Eventos","Cervezas"];

/* ---------- language ---------- */
const UI_ES = {
  htmlLang:"es",
  title:"Hershey — Labor Day Weekend 2026",
  h1:"🍫 Hershey — Fin de Semana de Labor Day",
  dates:"Vie 4 · Sáb 5 · Dom 6 · Lun 7 de septiembre 2026",
  origin:"Todas las distancias y tiempos son manejando desde la entrada de Hersheypark",
  noteTicket:'<b>⏰ Happy Hours Ticket:</b> el parque es <b>el sábado, de 5:00 pm al cierre</b>. '+
    'Ese día todo lo demás va <b>en la mañana o temprano en la tarde</b>. El viernes es de llegada '+
    'y algo social; el domingo y el lunes las tardes quedan libres. '+
    'Bonus: con ese boleto <b>ZooAmerica es gratis</b> entrando desde adentro del parque.',
  noteHours:'<b>Horarios:</b> los marcados <span style="color:#67c07a">✓ confirmado</span> los saqué del sitio '+
    'oficial del lugar. Los <span style="color:#f0916f">⚠ confirmar</span> son estimados — llamen o revisen '+
    'Google Maps. <b>⭐ Las estrellas son de referencia</b>; el botón "Maps + reviews" abre Google Maps con las reales.',
  quickLabel:"Vistas rápidas:",
  quickRec:"⭐ Recomendados", quickEvent:"🎉 Con evento ese finde", quickFree:"💵 Gratis primero",
  quickLookouts:"🏔️ Miradores", quickMonday:"🇺🇸 Abierto el lunes",
  anyDay:"Cualquier día", onlyEvents:"🎉 Solo con evento",
  share:"🔗 Copiar link de esta vista", shareOk:"✓ Link copiado",
  sortMi:"Más cerca primero", sortStars:"Mejor calificado", sortFree:"Gratis primero",
  countPlaces:"lugares", countFree:"gratis", countEvents:"con evento ese finde",
  distance:"Distancia", price:"Precio", driving:"min manejando",
  schedHead:"Horario del fin de semana", verOk:"✓ confirmado", verChk:"⚠ confirmar",
  recommended:"RECOMENDADO", free:"GRATIS",
  linkMaps:"⭐ Maps + reviews", linkDir:"🧭 Cómo llegar", linkSite:"Web",
  photo:"foto", photos:"fotos", swipe:"desliza →",
  popupStart:"Punto de partida", popupHappy:"Happy Hours: sábado 5pm → cierre",
  popupReviews:"Reviews y horario →", popupDir:"Cómo llegar →",
  footNote:'Distancias y tiempos de manejo calculados con OSRM sobre datos de OpenStreetMap · '+
    'mapa &copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> · '+
    'horarios y eventos del sitio oficial de cada lugar · estrellas de Google Maps (referencia). '+
    'Fotos del sitio oficial de cada lugar o de Wikimedia/Wikipedia — desliza sobre la imagen para ver más.',
  footCode:"Código en GitHub", footContrib:"Cómo contribuir", footIssue:"Reportar un dato incorrecto",
  footCopy:'&copy; 2026 Christopher Tineo. Publicado bajo '+
    '<a href="https://github.com/TineoC/laborday/blob/main/LICENSE" target="_blank" rel="noopener">licencia MIT</a>. '+
    'Guía informativa hecha para un viaje familiar — no está afiliada a Hersheypark, The Hershey Company '+
    'ni a ninguno de los lugares listados. Verifiquen horarios y precios antes de salir.',
  langLabel:"Idioma / Language",
  agendaTitle:"Agenda sugerida",
  agendaSub:"Un plan por día: viernes de llegada, el sábado gira alrededor del Happy Hours ticket y el lunes termina de regreso a Newark. Nada de esto está reservado — cambien lo que quieran.",
  agendaPark:"🎢 Hersheypark — Happy Hours (5pm → cierre)",
  agendaOpt:"opcional",
  planTitle:"Arma tu propia agenda",
  planSub:"Toca un día en cualquier tarjeta para agregarlo aquí. El link de esta sección se lleva tu plan — mándaselo a quien quieras.",
  planEmpty:"Nada todavía. Toca un día en cualquier tarjeta de abajo.",
  planCopy:"🔗 Copiar mi agenda",
  planCopyOk:"✓ Link copiado",
  planClear:"🗑️ Vaciar",
  planUseSuggested:"⭐ Partir de la agenda sugerida",
  planRemove:"quitar",
  planUp:"subir",
  planDown:"bajar",
  planAdd:"Agregar a:"
};

/* system default: first browser language that is en or es, else es */
function systemLang(){
  const prefs = navigator.languages && navigator.languages.length
    ? navigator.languages : [navigator.language || "es"];
  for(const l of prefs){
    const two = String(l).slice(0,2).toLowerCase();
    if(two === "en" || two === "es") return two;
  }
  return "es";
}
let LANG = systemLang(), langExplicit = false;

const T   = () => LANG === "en" ? I18N.ui : UI_ES;
const DAYS = () => LANG === "en" ? I18N.days : DAYS_ES;
const catLabel = c => LANG === "en" ? (I18N.cats[c] || c) : c;
/* place field with English override; falls back to the Spanish original */
const tp  = (p,k) => (LANG === "en" && I18N.places[p.n] && I18N.places[p.n][k]) || p[k];
const tsched  = s => LANG === "en" ? (I18N.sched[s]  || s) : s;
const tnote   = s => LANG === "en" ? (I18N.agenda[s] || s) : s;
const timgsrc = s => LANG === "en" ? (I18N.imgsrc[s] || s) : s;
const COLOR = {"Miradores":"#f0a83a","Parques":"#67c07a","Conocer":"#c98ae0",
               "Agua & Aventura":"#5eb3e4","Eventos":"#ef7d5a","Cervezas":"#d99a4e"};
const EMOJI = {"Miradores":"🏔️","Parques":"🌳","Conocer":"🏛️",
               "Agua & Aventura":"🛶","Eventos":"🎉","Cervezas":"🍺"};

const HP = [40.28736,-76.65803];
const gmaps = p => "https://www.google.com/maps/search/?api=1&query=" + encodeURIComponent(p.q);
const gdir  = p => "https://www.google.com/maps/dir/?api=1&origin=" + HP.join(",") +
                   "&destination=" + p.lat + "," + p.lng + "&travelmode=driving";
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const isFree = p => /GRATIS/i.test(p.price);

/* slugs come from the name, not the array index — a shared plan has to survive
   places being added, removed or reordered in the dataset */
const slug = n => n.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g,"")
  .replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"");
const BY_SLUG = Object.fromEntries(PLACES.map(p => [slug(p.n), p]));

/* ---------- map ---------- */
const map = L.map('map',{scrollWheelZoom:false}).setView([40.29,-76.70], 10);
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',
  {attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
   maxZoom:19}).addTo(map);

const hpMarker = L.circleMarker(HP,{radius:11,color:"#fff",weight:3,fillColor:"#e0483a",fillOpacity:1})
 .addTo(map).bindPopup("");

const popupHTML = p =>
  `<b>${esc(p.n)}</b>${p.rec?' ⭐':''}<br>${esc(tp(p,'town'))}<br>
   ⭐ ${p.stars} Google · <b>${p.mi} mi · ${p.min} min</b><br>
   💵 ${esc(tp(p,'price'))}<br>
   <a href="${gmaps(p)}" target="_blank" rel="noopener">${T().popupReviews}</a> ·
   <a href="${gdir(p)}" target="_blank" rel="noopener">${T().popupDir}</a>`;

const markers = PLACES.map(p => {
  const m = L.circleMarker([p.lat,p.lng],{
    radius: p.rec ? 10 : 7, color:"#140f0d", weight:2,
    fillColor: COLOR[p.cat] || "#f0a83a", fillOpacity:.95
  }).bindPopup("");
  m.__p = p;
  return m.addTo(map);
});

function refreshPopups(){
  hpMarker.setPopupContent(`<b>🎢 Hersheypark</b><br>${T().popupStart}<br>${T().popupHappy}`);
  markers.forEach(m => m.setPopupContent(popupHTML(m.__p)));
}
map.fitBounds(L.featureGroup(markers).getBounds().pad(0.12));

/* ---------- cards ---------- */
function cardHTML(p){
  const gal = (p.imgs && p.imgs.length)
    ? `<div class="gal">${p.imgs.map((u,i)=>
         `<img src="${u}" alt="${esc(p.n)} — ${T().photo} ${i+1}" loading="lazy" decoding="async"
               onerror="this.remove()">`).join('')}</div>
       ${p.imgs.length>1?`<div class="galn">1 / ${p.imgs.length} · ${T().swipe}</div>`:''}`
    : `<div class="noimg" style="background:linear-gradient(140deg,${COLOR[p.cat]}33,#2a1e19)">${EMOJI[p.cat]||'📍'}</div>`;
  const sched = p.sched.map((s,i)=>{
    const off = /^(—|Cerrad|No abre|Solo el parque)/i.test(s);
    return `<tr class="${off?'off':''}${i===3?' lastday':''}">
              <th>${DAYS()[i]} ${4+i}</th><td>${esc(tsched(s))}</td></tr>`;
  }).join('');
  return `
  <div class="card">
    <div class="thumb">
      ${gal}
      <div class="badges">
        <span class="pill stars">⭐ ${p.stars}</span>
        ${p.rec ? `<span class="pill rec">${T().recommended}</span>`
                : (isFree(p) ? `<span class="pill free">${T().free}</span>` : '')}
      </div>
    </div>
    <div class="body">
      <h3>${esc(p.n)}</h3>
      <div class="town">${EMOJI[p.cat]||''} ${esc(tp(p,'town'))}</div>
      ${p.event?`<div class="event">${esc(tp(p,'event'))}</div>`:''}
      <dl class="facts">
        <dt>${T().distance}</dt><dd><b>${p.mi} mi</b> · ${p.min} ${T().driving}</dd>
        <dt>${T().price}</dt><dd class="price">${esc(tp(p,'price'))}</dd>
      </dl>
      <div class="schedhead">
        ${T().schedHead}
        <span class="vb ${p.ver?'ok':'chk'}">${p.ver?T().verOk:T().verChk}</span>
      </div>
      <table class="sched">${sched}</table>
      <div class="daytog">
        <span class="lab">${T().planAdd}</span>
        ${p.days.map((open,i)=> open
          ? `<button data-s="${slug(p.n)}" data-d="${i}"
               class="${myPlan[i].includes(slug(p.n))?'on':''}">${DAYS()[i]} ${4+i}</button>`
          : '').join('')}
      </div>
      <p class="why">${esc(tp(p,'why'))}</p>
      <div class="tip">💡 ${esc(tp(p,'tip'))}</div>
      <div class="links">
        <a class="primary" href="${gmaps(p)}" target="_blank" rel="noopener">${T().linkMaps}</a>
        <a href="${gdir(p)}" target="_blank" rel="noopener">${T().linkDir}</a>
        ${p.site?`<a href="${p.site}" target="_blank" rel="noopener">${T().linkSite}</a>`:''}
      </div>
      ${p.imgsrc?`<div class="credit">${p.imgs.length} ${p.imgs.length>1?T().photos:T().photo} · ${esc(timgsrc(p.imgsrc))}</div>`:''}
    </div>
  </div>`;
}

/* ---------- photo galleries advance on their own every 3s ---------- */
const GAL_MS = 3000;
const GAL_HOLD = 8000;          /* pause after the visitor touches a gallery */
const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)');

/* live count, not p.imgs.length — broken images remove themselves onerror */
const galIndex = g => g.clientWidth ? Math.round(g.scrollLeft / g.clientWidth) : 0;

function updateCounter(g){
  const c = g.parentElement.querySelector('.galn');
  if(!c) return;
  const n = g.children.length;
  if(n < 2){ c.remove(); return; }
  c.textContent = `${galIndex(g)+1} / ${n} · ${T().swipe}`;
}

function advance(g){
  const n = g.children.length;
  if(n < 2 || !g.clientWidth) return;
  g.scrollTo({left: ((galIndex(g)+1) % n) * g.clientWidth, behavior:"smooth"});
}

const onScreen = el => {
  const r = el.getBoundingClientRect();
  return r.bottom > 0 && r.top < innerHeight;
};

let galTimer = null;
function initGalleries(){
  document.querySelectorAll('.gal').forEach(g => {
    updateCounter(g);
    g.addEventListener('scroll', () => {
      clearTimeout(g.__t);
      g.__t = setTimeout(() => updateCounter(g), 120);
    }, {passive:true});
    /* someone swiping or hovering is reading this card — back off, then resume */
    ['pointerenter','pointerdown','touchstart'].forEach(ev =>
      g.addEventListener(ev, () => { g.__hold = Date.now() + GAL_HOLD; }, {passive:true}));
  });
  /* auto-advance is movement; leave it off when the visitor asked for less of it */
  if(galTimer || reduceMotion.matches) return;
  galTimer = setInterval(() => {
    if(document.hidden) return;
    const now = Date.now();
    document.querySelectorAll('.gal').forEach(g => {
      if(!(g.__hold > now) && onScreen(g)) advance(g);
    });
  }, GAL_MS);
}

/* ---------- suggested agenda ---------- */
const DATENUM = i => 4 + i;   /* Fri Sep 4 … Mon Sep 7 */

function slotHTML(s){
  const cls = "aslot" + (s.park ? " park" : "") + (s.opt ? " opt" : "");
  const opt = s.opt ? ` <span class="aopt">${T().agendaOpt}</span>` : "";
  const note = s.note ? `<div class="anote">${esc(tnote(s.note))}</div>` : "";
  let main;
  if(s.park){
    main = `${T().agendaPark}${opt}`;
  }else if(s.label){
    main = `${esc(tnote(s.label))}${opt}`;
  }else{
    const p = BY_SLUG[slug(s.n)];
    if(!p) return "";
    main = `<a href="${gmaps(p)}" target="_blank" rel="noopener">${esc(p.n)}</a>${opt}
            <div class="ameta">${esc(tp(p,'town'))} · ${p.min} ${T().driving}</div>`;
  }
  return `<div class="${cls}"><div class="at">${esc(s.t)}</div>
            <div class="an">${main}${note}</div></div>`;
}

function renderAgenda(){
  document.getElementById('t-agenda-h').textContent   = T().agendaTitle;
  document.getElementById('t-agenda-sub').textContent = T().agendaSub;
  document.getElementById('agenda-days').innerHTML = AGENDA.days.map(day =>
    `<div class="agday">
       <h3>${DAYS()[day.d]} ${DATENUM(day.d)}</h3>
       ${day.slots.map(slotHTML).join('')}
     </div>`).join('');
}

/* ---------- build-your-own agenda ---------- */
/* the Happy Hours ticket is Saturday only, so that is the one day with a
   fixed 5pm anchor; the other three evenings are the family's to spend */
const PARK_DAY = AGENDA.days.findIndex(d => d.slots.some(s => s.park));
const PLAN_KEY = "laborday.plan";
let myPlan = [[],[],[],[]];

function savePlan(){
  try{ localStorage.setItem(PLAN_KEY, JSON.stringify(myPlan)); }catch{}
}
function loadPlan(){
  try{
    const raw = JSON.parse(localStorage.getItem(PLAN_KEY) || "null");
    if(Array.isArray(raw) && raw.length === 4) myPlan = raw.map(cleanDay);
  }catch{}
}
/* whatever comes in from a link or from storage, keep only real, open places */
const cleanDay = (arr, d) => (Array.isArray(arr) ? arr : [])
  .filter(s => BY_SLUG[s] && BY_SLUG[s].days[d])
  .filter((s,i,a) => a.indexOf(s) === i);

const planEmpty = () => myPlan.every(d => !d.length);

function togglePlan(s, d){
  const at = myPlan[d].indexOf(s);
  if(at >= 0) myPlan[d].splice(at,1); else myPlan[d].push(s);
  afterPlanChange();
}
function movePlan(s, d, by){
  const at = myPlan[d].indexOf(s), to = at + by;
  if(at < 0 || to < 0 || to >= myPlan[d].length) return;
  myPlan[d].splice(to, 0, myPlan[d].splice(at,1)[0]);
  afterPlanChange();
}
function afterPlanChange(){
  savePlan();
  renderMyPlan();
  render();                     /* card day-toggles reflect the plan */
}

function planRowHTML(s, d, i, len){
  const p = BY_SLUG[s];
  return `<div class="aslot">
    <div class="at">${i+1}.</div>
    <div class="an">
      <a href="${gmaps(p)}" target="_blank" rel="noopener">${esc(p.n)}</a>
      <div class="ameta">${esc(tp(p,'town'))} · ${p.min} ${T().driving} · ${esc(tsched(p.sched[d]))}</div>
    </div>
    <div class="arrow">
      <button data-mv="-1" data-s="${s}" data-d="${d}" title="${T().planUp}" ${i===0?'disabled':''}>↑</button>
      <button data-mv="1"  data-s="${s}" data-d="${d}" title="${T().planDown}" ${i===len-1?'disabled':''}>↓</button>
      <button data-rm="1"  data-s="${s}" data-d="${d}" title="${T().planRemove}">×</button>
    </div>
  </div>`;
}

function renderMyPlan(){
  document.getElementById('t-plan-h').textContent   = T().planTitle;
  document.getElementById('t-plan-sub').textContent = T().planSub;
  document.getElementById('plan-btns').innerHTML =
    `<button id="plancopy" class="primary">${T().planCopy}</button>
     <button id="planseed">${T().planUseSuggested}</button>
     <button id="planclear">${T().planClear}</button>`;

  document.getElementById('plan-days').innerHTML = myPlan.map((day,d) =>
    `<div class="agday">
       <h3>${DAYS()[d]} ${DATENUM(d)}</h3>
       ${day.length
          ? day.map((s,i)=>planRowHTML(s,d,i,day.length)).join('')
          : `<div class="agempty">${T().planEmpty}</div>`}
       ${day.length && d === PARK_DAY ? `<div class="aslot park"><div class="at">5pm</div>
                        <div class="an">${T().agendaPark}</div></div>` : ''}
     </div>`).join('');

  document.getElementById('plancopy').onclick = async e => {
    const btn = e.currentTarget;
    try{
      await navigator.clipboard.writeText(location.href);
      btn.textContent = T().planCopyOk;
    }catch{
      btn.textContent = location.href;
    }
    setTimeout(()=>{ btn.textContent = T().planCopy; }, 2200);
  };
  document.getElementById('planclear').onclick = () => { myPlan = [[],[],[],[]]; afterPlanChange(); };
  document.getElementById('planseed').onclick = () => {
    myPlan = AGENDA.days.map(day => cleanDay(
      day.slots.filter(s => s.n).map(s => slug(s.n)), day.d));
    afterPlanChange();
  };
  writeURL();
}

document.getElementById('plan-days').addEventListener('click', e => {
  const b = e.target.closest('button');
  if(!b) return;
  const s = b.dataset.s, d = +b.dataset.d;
  if(b.dataset.rm) togglePlan(s, d);
  else if(b.dataset.mv) movePlan(s, d, +b.dataset.mv);
});

/* the cards are re-rendered wholesale, so the handler lives on the container */
document.getElementById('cards').addEventListener('click', e => {
  const b = e.target.closest('.daytog button');
  if(!b) return;
  togglePlan(b.dataset.s, +b.dataset.d);
});

const DEFAULT_CAT = "⭐ Recomendados";
let curCat = DEFAULT_CAT, curSort = "mi", curDay = -1, onlyEvents = false;

/* --- shareable URLs: ?cat=recomendados&dia=sab&orden=estrellas&evento=1 --- */
const SLUG = {"Todos":"todos","⭐ Recomendados":"recomendados","Miradores":"miradores",
  "Parques":"parques","Conocer":"conocer","Agua & Aventura":"agua","Eventos":"eventos",
  "Cervezas":"cervezas"};
const UNSLUG = Object.fromEntries(Object.entries(SLUG).map(([k,v])=>[v,k]));
const DAYSLUG = ["vie","sab","dom","lun"];
const SORTSLUG = {mi:"cerca", stars:"estrellas", free:"gratis"};
const UNSORT = Object.fromEntries(Object.entries(SORTSLUG).map(([k,v])=>[v,k]));

function readURL(){
  const q = new URLSearchParams(location.search);
  const l = (q.get("lang")||"").slice(0,2).toLowerCase();
  if(l === "en" || l === "es"){ LANG = l; langExplicit = true; }
  const c = (q.get("cat")||"").toLowerCase();
  if(UNSLUG[c]) curCat = UNSLUG[c];
  const d = DAYSLUG.indexOf((q.get("dia")||"").toLowerCase());
  if(d >= 0) curDay = d;
  const s = (q.get("orden")||"").toLowerCase();
  if(UNSORT[s]) curSort = UNSORT[s];
  if(q.get("evento") === "1") onlyEvents = true;

  /* a shared plan wins over whatever this browser had saved, and sticks */
  if(DAYSLUG.some(k => q.has(k))){
    myPlan = DAYSLUG.map((k,d) => cleanDay((q.get(k)||"").split(",").filter(Boolean), d));
    savePlan();
  }else{
    loadPlan();
  }
}

function writeURL(){
  const q = new URLSearchParams();
  if(langExplicit)          q.set("lang", LANG);
  if(curCat !== DEFAULT_CAT) q.set("cat", SLUG[curCat]);
  if(curDay >= 0)           q.set("dia", DAYSLUG[curDay]);
  if(curSort !== "mi")      q.set("orden", SORTSLUG[curSort]);
  if(onlyEvents)            q.set("evento", "1");
  myPlan.forEach((day,d) => { if(day.length) q.set(DAYSLUG[d], day.join(",")); });
  const qs = q.toString();
  history.replaceState(null, "", qs ? location.pathname + "?" + qs : location.pathname);
}

function syncControls(){
  document.querySelectorAll('#bar button[data-c]').forEach(b =>
    b.classList.toggle('on', b.dataset.c === curCat));
  document.getElementById('dsel').value = String(curDay);
  document.getElementById('ssel').value = curSort;
  document.getElementById('evb').classList.toggle('on', onlyEvents);
}

function render(){
  let list = PLACES.slice();
  if(curCat === "⭐ Recomendados") list = list.filter(p=>p.rec);
  else if(curCat !== "Todos")      list = list.filter(p=>p.cat===curCat);
  if(curDay >= 0) list = list.filter(p=>p.days[curDay]);
  if(onlyEvents)  list = list.filter(p=>p.event);

  if(curSort==="mi")     list.sort((a,b)=>a.mi-b.mi);
  if(curSort==="stars")  list.sort((a,b)=>b.stars-a.stars);
  if(curSort==="free")   list.sort((a,b)=>(isFree(b)-isFree(a)) || a.mi-b.mi);

  document.getElementById('count').textContent =
    `${list.length} ${T().countPlaces} · ${list.filter(isFree).length} ${T().countFree} · ` +
    `${list.filter(p=>p.event).length} ${T().countEvents}`;
  document.getElementById('cards').innerHTML =
    `<div class="grid">${list.map(cardHTML).join('')}</div>`;
  initGalleries();
  writeURL();

  const keep = new Set(list.map(p=>p.n));
  markers.forEach(m => keep.has(m.__p.n) ? m.addTo(map) : map.removeLayer(m));
}

function buildBar(){
  const mon = LANG === "en" ? "Sep" : "sept";
  document.getElementById('bar').innerHTML =
    CATS.map(c=>`<button data-c="${c}">${catLabel(c)}</button>`).join('') +
    `<span class="spacer"></span>
     <select id="dsel">
       <option value="-1">${T().anyDay}</option>
       ${DAYS().map((d,i)=>`<option value="${i}">${d} ${4+i} ${mon}</option>`).join('')}
     </select>
     <button id="evb" class="evtoggle">${T().onlyEvents}</button>
     <button id="share" class="sharebtn">${T().share}</button>
     <select id="ssel">
       <option value="mi">${T().sortMi}</option>
       <option value="stars">${T().sortStars}</option>
       <option value="free">${T().sortFree}</option>
     </select>`;

  document.getElementById('evb').onclick = e => {
    onlyEvents = !onlyEvents;
    e.target.classList.toggle('on', onlyEvents);
    render();
  };
  document.getElementById('dsel').onchange = e => { curDay = +e.target.value; render(); };
  document.getElementById('ssel').onchange = e => { curSort = e.target.value; render(); };
  document.getElementById('share').onclick = async e => {
    const btn = e.currentTarget;
    try{
      await navigator.clipboard.writeText(location.href);
      btn.textContent = T().shareOk;
    }catch{
      btn.textContent = location.href;
    }
    setTimeout(()=>{ btn.textContent = T().share; }, 2200);
  };
}

/* quick views keep the current language in the link */
function buildQuick(){
  const qp = extra => "?" + (langExplicit ? "lang=" + LANG + "&" : "") + extra;
  document.getElementById('quick').innerHTML =
    `<span>${T().quickLabel}</span>
     <a href="${qp("cat=recomendados")}">${T().quickRec}</a>
     <a href="${qp("evento=1")}">${T().quickEvent}</a>
     <a href="${qp("orden=gratis")}">${T().quickFree}</a>
     <a href="${qp("cat=miradores")}">${T().quickLookouts}</a>
     <a href="${qp("dia=lun")}">${T().quickMonday}</a>`;
}

function applyLang(){
  const t = T();
  document.documentElement.lang = t.htmlLang;
  document.title = t.title;
  document.getElementById('t-h1').textContent      = t.h1;
  document.getElementById('t-dates').textContent   = t.dates;
  document.getElementById('t-origin').textContent  = t.origin;
  document.getElementById('t-note1').innerHTML     = t.noteTicket;
  document.getElementById('t-note2').innerHTML     = t.noteHours;
  document.getElementById('t-fnote').innerHTML     = t.footNote;
  document.getElementById('t-fcopy').innerHTML     = t.footCopy;
  document.getElementById('t-fcode').textContent   = t.footCode;
  document.getElementById('t-fcontrib').textContent= t.footContrib;
  document.getElementById('t-fissue').textContent  = t.footIssue;
  document.getElementById('langlabel').textContent = t.langLabel;
  document.querySelectorAll('.langbar button').forEach(b =>
    b.classList.toggle('on', b.dataset.l === LANG));
  buildQuick();
  renderAgenda();
  renderMyPlan();
  buildBar();
  refreshPopups();
  syncControls();
}

document.querySelector('.langbar').addEventListener('click', e => {
  if(e.target.tagName !== 'BUTTON') return;
  LANG = e.target.dataset.l;
  langExplicit = true;
  applyLang();
  render();
});

document.getElementById('bar').addEventListener('click', e=>{
  if(e.target.tagName!=='BUTTON' || !e.target.dataset.c) return;
  document.querySelectorAll('#bar button').forEach(b=>b.classList.remove('on'));
  e.target.classList.add('on');
  curCat = e.target.dataset.c;
  render();
});
readURL();
applyLang();
render();

addEventListener('popstate', () => { readURL(); applyLang(); render(); });

setTimeout(()=>map.invalidateSize(),150);
</script>
</body>
</html>
"""

out = (
    HTML.replace("__DATA__", DATA)
    .replace("__I18N__", I18N)
    .replace("__AGENDA__", AGENDA)
)
open("index.html", "w").write(out)
print("wrote page:", len(out), "bytes,", len(places), "places")
print("free:", sum(1 for p in places if "GRATIS" in p["price"]))
