#!/usr/bin/env python3
"""Render the Hershey weekend page with the enriched dataset inlined."""
import json

places = json.load(open("tools/places_final.json"))
DATA = json.dumps(places, ensure_ascii=False, separators=(",", ":"))

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
  <h1>🍫 Hershey — Fin de Semana de Labor Day</h1>
  <div class="dates">Vie 4 · Sáb 5 · Dom 6 · Lun 7 de septiembre 2026</div>
  <div class="origin">Todas las distancias y tiempos son manejando desde la entrada de Hersheypark</div>
</div></header>

<div class="wrap">

  <div class="note">
    <b>⏰ Happy Hours Ticket:</b> entra al parque de <b>5:00 pm al cierre</b>.
    Las tardes-noches ya están tomadas — todo esto va <b>en la mañana o temprano en la tarde</b>.
    Bonus: con ese boleto <b>ZooAmerica es gratis</b> entrando desde adentro del parque.
  </div>

  <div class="note warn">
    <b>Horarios:</b> los marcados <span style="color:#67c07a">✓ confirmado</span> los saqué del sitio oficial
    del lugar. Los <span style="color:#f0916f">⚠ confirmar</span> son estimados — llamen o revisen Google Maps.
    <b>⭐ Las estrellas son de referencia</b>; el botón "Maps + reviews" abre Google Maps con las reales.
  </div>

  <div class="quick">
    <span>Vistas rápidas:</span>
    <a href="?cat=recomendados">⭐ Recomendados</a>
    <a href="?evento=1">🎉 Con evento ese finde</a>
    <a href="?orden=gratis">💵 Gratis primero</a>
    <a href="?cat=miradores">🏔️ Miradores</a>
    <a href="?dia=lun">🇺🇸 Abierto el lunes</a>
  </div>

  <div id="map"></div>

  <div class="bar" id="bar"></div>
  <div class="count" id="count"></div>
  <div id="cards"></div>

  <footer>
    <div class="fnote">
      Distancias y tiempos de manejo calculados con OSRM sobre datos de OpenStreetMap ·
      mapa &copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> ·
      horarios y eventos del sitio oficial de cada lugar · estrellas de Google Maps (referencia).
      Fotos del sitio oficial de cada lugar o de Wikimedia/Wikipedia — desliza sobre la imagen para ver más.
    </div>
    <div class="flinks">
      <a href="https://github.com/TineoC/laborday" target="_blank" rel="noopener">Código en GitHub</a>
      <a href="https://github.com/TineoC/laborday/blob/main/CONTRIBUTING.md" target="_blank" rel="noopener">Cómo contribuir</a>
      <a href="https://github.com/TineoC/laborday/blob/main/AGENTS.md" target="_blank" rel="noopener">AGENTS.md</a>
      <a href="https://github.com/TineoC/laborday/blob/main/.github/CODEOWNERS" target="_blank" rel="noopener">CODEOWNERS</a>
      <a href="https://github.com/TineoC/laborday/issues/new" target="_blank" rel="noopener">Reportar un dato incorrecto</a>
    </div>
    <div class="copy">
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
const DAYS = ["Vie","Sáb","Dom","Lun"];
const CATS = ["Todos","⭐ Recomendados","Miradores","Parques","Conocer","Agua & Aventura","Eventos","Cervezas"];
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

/* ---------- map ---------- */
const map = L.map('map',{scrollWheelZoom:false}).setView([40.29,-76.70], 10);
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',
  {attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
   maxZoom:19}).addTo(map);

L.circleMarker(HP,{radius:11,color:"#fff",weight:3,fillColor:"#e0483a",fillOpacity:1})
 .addTo(map).bindPopup("<b>🎢 Hersheypark</b><br>Punto de partida<br>Happy Hours: 5pm → cierre");

const markers = PLACES.map(p => {
  const m = L.circleMarker([p.lat,p.lng],{
    radius: p.rec ? 10 : 7, color:"#140f0d", weight:2,
    fillColor: COLOR[p.cat] || "#f0a83a", fillOpacity:.95
  }).bindPopup(
    `<b>${esc(p.n)}</b>${p.rec?' ⭐':''}<br>${esc(p.town)}<br>
     ⭐ ${p.stars} Google · <b>${p.mi} mi · ${p.min} min</b><br>
     💵 ${esc(p.price)}<br>
     <a href="${gmaps(p)}" target="_blank" rel="noopener">Reviews y horario →</a> ·
     <a href="${gdir(p)}" target="_blank" rel="noopener">Cómo llegar →</a>`
  );
  m.__p = p;
  return m.addTo(map);
});
map.fitBounds(L.featureGroup(markers).getBounds().pad(0.12));

/* ---------- cards ---------- */
function cardHTML(p){
  const gal = (p.imgs && p.imgs.length)
    ? `<div class="gal">${p.imgs.map((u,i)=>
         `<img src="${u}" alt="${esc(p.n)} — foto ${i+1}" loading="lazy" decoding="async"
               onerror="this.remove()">`).join('')}</div>
       ${p.imgs.length>1?`<div class="galn">1 / ${p.imgs.length} · desliza →</div>`:''}`
    : `<div class="noimg" style="background:linear-gradient(140deg,${COLOR[p.cat]}33,#2a1e19)">${EMOJI[p.cat]||'📍'}</div>`;
  const sched = p.sched.map((s,i)=>{
    const off = /^(—|Cerrad|No abre|Solo el parque)/i.test(s);
    return `<tr class="${off?'off':''}${i===3?' lastday':''}">
              <th>${DAYS[i]} ${4+i}</th><td>${esc(s)}</td></tr>`;
  }).join('');
  return `
  <div class="card">
    <div class="thumb">
      ${gal}
      <div class="badges">
        <span class="pill stars">⭐ ${p.stars}</span>
        ${p.rec ? '<span class="pill rec">RECOMENDADO</span>'
                : (isFree(p) ? '<span class="pill free">GRATIS</span>' : '')}
      </div>
    </div>
    <div class="body">
      <h3>${esc(p.n)}</h3>
      <div class="town">${EMOJI[p.cat]||''} ${esc(p.town)}</div>
      ${p.event?`<div class="event">${esc(p.event)}</div>`:''}
      <dl class="facts">
        <dt>Distancia</dt><dd><b>${p.mi} mi</b> · ${p.min} min manejando</dd>
        <dt>Precio</dt><dd class="price">${esc(p.price)}</dd>
      </dl>
      <div class="schedhead">
        Horario del fin de semana
        <span class="vb ${p.ver?'ok':'chk'}">${p.ver?'✓ confirmado':'⚠ confirmar'}</span>
      </div>
      <table class="sched">${sched}</table>
      <p class="why">${esc(p.why)}</p>
      <div class="tip">💡 ${esc(p.tip)}</div>
      <div class="links">
        <a class="primary" href="${gmaps(p)}" target="_blank" rel="noopener">⭐ Maps + reviews</a>
        <a href="${gdir(p)}" target="_blank" rel="noopener">🧭 Cómo llegar</a>
        ${p.site?`<a href="${p.site}" target="_blank" rel="noopener">Web</a>`:''}
      </div>
      ${p.imgsrc?`<div class="credit">${p.imgs.length} foto${p.imgs.length>1?'s':''} · ${esc(p.imgsrc)}</div>`:''}
    </div>
  </div>`;
}

let curCat = "Todos", curSort = "mi", curDay = -1, onlyEvents = false;

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
  const c = (q.get("cat")||"").toLowerCase();
  if(UNSLUG[c]) curCat = UNSLUG[c];
  const d = DAYSLUG.indexOf((q.get("dia")||"").toLowerCase());
  if(d >= 0) curDay = d;
  const s = (q.get("orden")||"").toLowerCase();
  if(UNSORT[s]) curSort = UNSORT[s];
  if(q.get("evento") === "1") onlyEvents = true;
}

function writeURL(){
  const q = new URLSearchParams();
  if(curCat !== "Todos")  q.set("cat", SLUG[curCat]);
  if(curDay >= 0)         q.set("dia", DAYSLUG[curDay]);
  if(curSort !== "mi")    q.set("orden", SORTSLUG[curSort]);
  if(onlyEvents)          q.set("evento", "1");
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
    `${list.length} lugares · ${list.filter(isFree).length} gratis · ${list.filter(p=>p.event).length} con evento ese finde`;
  document.getElementById('cards').innerHTML =
    `<div class="grid">${list.map(cardHTML).join('')}</div>`;
  writeURL();

  const keep = new Set(list.map(p=>p.n));
  markers.forEach(m => keep.has(m.__p.n) ? m.addTo(map) : map.removeLayer(m));
}

document.getElementById('bar').innerHTML =
  CATS.map(c=>`<button data-c="${c}">${c}</button>`).join('') +
  `<span class="spacer"></span>
   <select id="dsel">
     <option value="-1">Cualquier día</option>
     ${DAYS.map((d,i)=>`<option value="${i}">${d} ${4+i} sept</option>`).join('')}
   </select>
   <button id="evb" class="evtoggle">🎉 Solo con evento</button>
   <button id="share" class="sharebtn">🔗 Copiar link de esta vista</button>
   <select id="ssel">
     <option value="mi">Más cerca primero</option>
     <option value="stars">Mejor calificado</option>
     <option value="free">Gratis primero</option>
   </select>`;

document.getElementById('bar').addEventListener('click', e=>{
  if(e.target.tagName!=='BUTTON' || !e.target.dataset.c) return;
  document.querySelectorAll('#bar button').forEach(b=>b.classList.remove('on'));
  e.target.classList.add('on');
  curCat = e.target.dataset.c;
  render();
});
document.getElementById('evb').onclick = e => {
  onlyEvents = !onlyEvents;
  e.target.classList.toggle('on', onlyEvents);
  render();
};
document.getElementById('dsel').onchange = e => { curDay = +e.target.value; render(); };
document.getElementById('ssel').onchange = e => { curSort = e.target.value; render(); };

readURL();
syncControls();
render();

addEventListener('popstate', () => { readURL(); syncControls(); render(); });

// "copiar link de esta vista" button
document.getElementById('share').onclick = async e => {
  const btn = e.currentTarget;
  try{
    await navigator.clipboard.writeText(location.href);
    btn.textContent = '✓ Link copiado';
  }catch{
    btn.textContent = location.href;
  }
  setTimeout(()=>{ btn.textContent = '🔗 Copiar link de esta vista'; }, 2200);
};

setTimeout(()=>map.invalidateSize(),150);
</script>
</body>
</html>
"""

out = HTML.replace("__DATA__", DATA)
open("index.html", "w").write(out)
print("wrote page:", len(out), "bytes,", len(places), "places")
print("free:", sum(1 for p in places if "GRATIS" in p["price"]))
