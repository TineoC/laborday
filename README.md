# Labor Day Weekend 2026 — Hershey, PA

Guía de actividades fuera de Hersheypark para el fin de semana de Labor Day
(viernes 4 – lunes 7 de septiembre de 2026).

**En vivo:** https://laborday.tineochristopher.com

## Qué incluye

32 lugares alrededor de Hershey: miradores, parques estatales, museos,
cervecerías, aventura al aire libre y los eventos especiales de ese fin de semana.

Cada lugar trae:

- Foto, calificación de Google y precio de la experiencia
- **Distancia y tiempo reales manejando** desde la entrada de Hersheypark
- **Horario día por día** del fin de semana (viernes a lunes), incluyendo horarios especiales de feriado
- Eventos específicos de ese fin de semana (Kipona, Duryea Day, Jazz at the Barnyard, etc.)
- Enlaces directos a Google Maps y a cómo llegar

Filtros por categoría y por día, y orden por cercanía, calificación o precio.

## Fuentes de los datos

| Dato | Fuente |
|---|---|
| Distancias y tiempos de manejo | [OSRM](https://project-osrm.org/) sobre datos de OpenStreetMap |
| Mapa | Leaflet + tiles de CARTO / OpenStreetMap |
| Horarios | Sitio oficial de cada lugar (los verificados se marcan ✓ en la página) |
| Eventos del fin de semana | Sitios y calendarios oficiales |
| Fotos | `og:image` del sitio oficial, o Wikimedia Commons |
| Estrellas | Google Maps — de referencia; cada tarjeta enlaza a las reseñas en vivo |

Los horarios marcados ⚠ son estimados: confírmenlos antes de manejar.
Los precios pueden cambiar.

## Estructura

Un solo archivo, `index.html`, sin build ni dependencias que instalar.
Leaflet se carga desde CDN. Ábrelo directo en el navegador.

## Enlaces compartibles

Los filtros viven en la URL, así que cualquier vista se puede mandar por chat:

| Parámetro | Valores | Ejemplo |
|---|---|---|
| `cat` | `recomendados`, `miradores`, `parques`, `conocer`, `agua`, `eventos`, `cervezas` | `?cat=miradores` |
| `dia` | `vie`, `sab`, `dom`, `lun` | `?dia=lun` |
| `orden` | `cerca`, `estrellas`, `gratis` | `?orden=gratis` |
| `evento` | `1` | `?evento=1` |

Se combinan:

```
https://laborday.tineochristopher.com/?cat=recomendados&dia=lun&orden=estrellas
```

La página trae botones de vistas rápidas arriba del mapa y un botón para copiar
el link de la vista actual. Un parámetro inválido se ignora y cae al valor por
defecto.
