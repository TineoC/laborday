# Cómo contribuir

Esta es una guía de actividades para el fin de semana de Labor Day 2026 cerca
de Hersheypark. Lo más útil que puedes aportar no es código: es **corregir un
dato que está mal**.

## Reportar un dato incorrecto

Abre un [issue](https://github.com/TineoC/laborday/issues/new) e incluye:

- El nombre del lugar
- Qué está mal (horario, precio, distancia, foto, evento)
- El dato correcto y **de dónde lo sacaste** (link al sitio oficial, captura de
  Google Maps, o "llamé y me dijeron")

Los horarios marcados ⚠ en la página son estimados. Si confirmas uno con el
lugar, dilo en el issue y lo pasamos a ✓.

## Prioridades

Por orden de utilidad:

1. **Horarios equivocados** — alguien maneja 30 millas y encuentra cerrado
2. **Precios desactualizados**
3. **Fotos que no son del lugar** — ver la nota de abajo, esto ya pasó bastante
4. Lugares nuevos que valga la pena agregar
5. Mejoras de la página

## Cambiar los datos

Los 32 lugares viven en `tools/places_seed.json`. Editas ahí y regeneras:

```bash
python3 tools/build_page.py
```

Eso reescribe `index.html`. No edites `index.html` a mano — se sobreescribe.

Lee [`AGENTS.md`](AGENTS.md) antes de tocar el pipeline. Explica de dónde sale
cada dato y qué fuentes ya se probaron y fallaron.

## Reglas sobre las fotos

**Solo se publica una foto si es verificablemente del lugar.** Esto no es
opcional.

Buscar fotos automáticamente por coordenadas o por nombre produce mucha basura.
En la primera versión de este repo la búsqueda automática asignó una foto de un
gato a una cervecería, parques de Minnesota a un mirador de Pensilvania, y fotos
del waterpark de un hotel a un brewpub.

Si no encuentras una foto que claramente sea del lugar, deja el tile de color
con el ícono de categoría. Un placeholder honesto es mejor que una foto
equivocada.

Fuentes aceptables, en orden:

1. El sitio oficial del lugar (`og:image` o su galería)
2. Wikimedia Commons / Wikipedia, cuando el artículo es del lugar mismo
3. Una foto del pueblo o del área inmediata, **si la tarjeta dice de dónde salió**

No subas fotos con copyright de terceros al repo. La página enlaza las
imágenes, no las hospeda.

## Estilo

- El texto base es **español informal**. Mantenlo así.
- La página es bilingüe. El inglés vive en `tools/i18n_en.json` y es una
  **traducción** del español, no una fuente nueva de datos. Si agregas o
  cambias un lugar, actualiza también su bloque en ese archivo — el build falla
  si falta.
- Los nombres propios de lugares van en inglés, como aparecen en Google Maps.
- Nada de dependencias nuevas. La página es un archivo HTML con Leaflet desde
  CDN, y así se queda.

## Pull requests

- Una PR por tema
- Di qué verificaste y cómo
- Si cambias datos, corre `python3 tools/build_page.py` e incluye el
  `index.html` regenerado en el mismo commit

@TineoC revisa todas las PRs (ver [`.github/CODEOWNERS`](.github/CODEOWNERS)).

## Despliegue

`main` se publica solo en https://laborday.tineochristopher.com vía GitHub
Pages. Si tu PR se mergea, está en vivo en un par de minutos.
