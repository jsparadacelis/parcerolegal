# Parcero Legal — Design System v1 · «Cielo Andino»

> Sistema de diseño para el frontend de **parcerolegal**. Reemplaza la identidad terracota por una paleta azul + oro (guiño a Colombia sin bandera literal), un logo de wordmark + destello, y una respuesta de chat con jerarquía clara.
>
> **Combo aprobado:** logo `1b` + paleta `1c` + respuesta `1e`.
> **Stack objetivo:** Next.js (App Router) + Tailwind CSS v4 (`@theme` en `globals.css`).

---

## 0. Cómo usar este documento

Este archivo es la **fuente de verdad** del rediseño. Está pensado para implementarse directamente en el repo `frontend/`. Los cambios se agrupan en tres capas:

1. **Tokens** → `frontend/app/globals.css` (bloque `@theme`) + fuentes en `layout.tsx`.
2. **Marca** → nuevo componente `Logo` + `icon.tsx` / `apple-icon.tsx`.
3. **Componentes** → `SearchBox`, `ResultPanel`, `SourceCard`, `Disclaimer`, navbar en `page.tsx`.

En la carpeta `code/` de este handoff hay versiones **listas para pegar** de cada archivo. Este `.md` documenta el *por qué* y las specs exactas.

---

## 1. Marca

### Logo (wordmark + destello)

- Wordmark `parcerolegal` en **Bricolage Grotesque 800**, todo minúscula, `letter-spacing: -0.03em`.
- `parcero` en `--color-ink`; `legal` en `--color-primary`.
- **Destello** a la derecha del texto (reemplaza la balanza): una cruz `+` en `--color-primary` con una chispa diagonal pequeña en `--color-gold`. Es el único elemento gráfico de la marca.
- Ya **no** existe el ícono de casita/flecha.

**Proporciones del destello** (relativas a la altura de la x del wordmark):
- Contenedor cuadrado ≈ 0.5× del tamaño de fuente del wordmark.
- Cruz: dos barras de `~2.8px` con `border-radius: 3px`.
- Chispa: barra de `~2.4px × 7px`, `--color-gold`, `rotate(45deg)`, esquina superior derecha.

### Monograma / favicon
- Cuadrado con `border-radius: 15px` (a 54px) — escala proporcional.
- Fondo `--color-ink` (o `--color-primary`), letra `p` en Bricolage 800 blanca, con un punto de `--color-gold` (o `--color-primary`) en la esquina superior derecha.

### Variantes
- **Sobre oscuro:** `parcero` blanco, `legal` en `#7FA0F0` (primary aclarado), destello igual.
- **Clearspace mínimo:** la altura de la «p» a cada lado.

### Evitar
- Estirar, cambiar peso o usar mayúsculas.
- Separar el destello del texto.
- Recolorear fuera de los tokens.

---

## 2. Color — paleta «Cielo Andino»

Azul confiable como primario, oro marigold **solo como acento** (nunca texto largo ni fondo de bloques de contenido). Tintas neutras frías (reemplazan las cálidas marrones anteriores).

| Rol | Token | Hex | Uso |
|---|---|---|---|
| Primario | `--color-primary` | `#2457D6` | Acciones, enlaces, ícono activo, `legal` del logo |
| Primario hover | `--color-primary-hover` | `#1D46AD` | Hover de botones/links |
| Primario tint | `--color-primary-tint` | `#ECF1FB` | Fondos de bloque «EN CORTO», íconos de fuente, chips |
| Primario pale | `--color-primary-pale` | `#F5F8FE` | Fondo sutil del panel de respuesta (opcional) |
| Primario borde | `--color-primary-border` | `rgba(36,87,214,0.16)` | Bordes de tarjetas de fuente / focus ring |
| Oro (acento) | `--color-gold` | `#FFC53D` | Chispa del logo, badge «destacado». Solo acento. |
| Oro tint | `--color-gold-tint` | `#FFF6DF` | Fondo de ícono de sentencia, badge suave |
| Oro tinta | `--color-gold-ink` | `#8A6206` | Texto sobre oro tint |
| Tinta | `--color-ink` | `#14161C` | Texto principal, titulares |
| Tinta 2 | `--color-ink-2` | `#3A3F49` | Cuerpo de párrafo |
| Tinta 3 | `--color-ink-3` | `#6A7180` | Metadatos, placeholders, pies |
| Superficie | `--color-surface` | `#FFFFFF` | Tarjetas, panel de respuesta, navbar |
| Papel | `--color-surface-2` | `#F5F7FA` | Fondo de página |
| Superficie 3 | `--color-surface-3` | `#EEF1F6` | Skeletons, divisores suaves |
| Borde | `--color-border` | `#E4E8EF` | Bordes por defecto |
| OK | `--color-ok` / `--color-ok-tint` | `#15803D` / `#DCFCE7` | Estado «vigente», éxito |
| Aviso | `--color-warn` | `#B45309` | Advertencias |
| Error | `--color-error` / `--color-error-tint` | `#B91C1C` / `#FEE2E2` | Estado de error |

**Reglas:** el oro es solo acento (nunca cuerpo de texto ni fondo de un bloque de contenido). El azul es acción/enlace. El texto largo siempre en tintas neutras.

---

## 3. Tipografía

Tres familias. La **jerarquía** es lo que arregla el «todo se ve igual / pegado».

| Familia | Token | Uso | Pesos |
|---|---|---|---|
| Bricolage Grotesque | `--font-display` | Logo, H1–H2 | 500–800 |
| Instrument Sans | `--font-sans` | Cuerpo, UI | 400–600 |
| Space Mono | `--font-mono` | Etiquetas, códigos de sentencia, datos | 400 / 700 |

### Escala

| Nivel | Tamaño / interlínea / peso | Familia | Color | Uso |
|---|---|---|---|---|
| H1 | 34 / 1.1 / 800 | display | ink | «tu derecho, claro.» |
| H2 | 22 / 1.2 / 700 | display | ink | Títulos de sección |
| Lead / TL;DR | 16 / 1.5 / 500 | sans | ink | Bloque «EN CORTO» |
| Cuerpo | 15 / 1.7 / 400 | sans | ink-2 | Párrafos de la respuesta |
| Small | 13 / 1.5 / 400 | sans | ink-3 | Metadatos, pies |
| Label | 10.5 / — / 700, `letter-spacing:.12em`, UPPER | mono | primary o ink-3 | «EN CORTO», «FUENTES», «PUNTOS CLAVE» |

> En móvil, el cuerpo puede bajar a 14.5px; nunca menos.

---

## 4. Fundamentos

- **Espacio:** base 4px → `4 · 8 · 12 · 16 · 24 · 32 · 48 · 64`. **Entre bloques de la respuesta: 18–22px** (el aire que faltaba).
- **Radios:** `sm 6` · `md 8` (botones) · `lg 12` (input, tarjetas) · `xl 16` (panel de respuesta) · `full` (chips/badges).
- **Elevación:** bordes primero, sombras suaves y bajas.
  - `sm`: `0 1px 3px rgba(20,22,28,.08)` — tarjetas.
  - `lg`: `0 8px 30px -18px rgba(20,22,28,.35)` — flotantes.

---

## 5. Componentes

### 5.1 Navbar
- `flex justify-between`, `padding: 14px 20px`, fondo `surface`, borde inferior `border`.
- Izquierda: `<Logo />` (wordmark + destello) como botón de reset.
- Derecha: badge «No reemplaza un abogado» — `surface-2`, borde `border`, texto `ink-3` 11px, `rounded-full`, `padding: 5px 11px`.

### 5.2 Botones
- **Primario:** fondo `primary`, texto blanco, `700 13px`, `padding: 11px 18px`, `radius md`. Hover → `primary-hover`. Active → `ink`.
- **Secundario:** fondo `surface`, borde `1.5px primary`, texto `primary 600`.
- **Texto:** `primary 600` + flecha `→`.
- Focus ring: `ring-2 ring-primary ring-offset-2`.
- Altura mínima táctil **44px**.

### 5.3 Chips / badges
- `rounded-full`, `padding: 6px 12px`, `600 12px`.
- Categoría (azul): `primary-tint` / `primary`. Destacado (oro): `gold-tint` / `gold-ink`. Vigente (verde): `ok-tint` / `ok`. Código mono: `surface-2` + borde, `Space Mono`.

### 5.4 SearchBox
- Contenedor `flex items-center gap-3`, fondo `surface`, borde `1.5px`, `radius lg`, `padding: 12px 14px`, `min-height 52px`.
- Reposo: borde `border`, ícono lupa en `primary`, placeholder `ink-3`.
- Hover / focus: borde `primary` + `box-shadow: 0 0 0 3px primary-tint` (reemplaza el `ring terra-light`).
- Botón «Preguntar» primario a la derecha, `min-height 44px`.

### 5.5 ResultPanel — **patrón clave (respuesta del chat)**

Este es el componente que se rediseña. Se lee como una **conversación con jerarquía**:

```
[1] Pregunta del usuario   → burbuja azul, alineada a la derecha
[2] EN CORTO (TL;DR)       → bloque sobre primary-tint, lead 16px
[3] Cuerpo + Puntos clave  → párrafos 15/1.7, bullets con check; 18–22px de aire entre bloques
[4] Fuentes                → tarjetas clicables (§ / C) con flecha →
[5] Disclaimer             → pie fino con borde superior + ícono ⓘ
```

**Layout:**
- Panel exterior: `surface-2`, `radius xl`, `padding 24px`.
- Pregunta: burbuja `primary` blanca, `radius 14px 14px 3px 14px`, `max-width 78%`, alineada a la derecha, margen inferior 20px.
- Respuesta: fila `flex gap-3` con avatar (34px, `radius 10px`, `primary`, letra `p` blanca + punto oro) + burbuja `surface`, borde `border`, `radius 4px 16px 16px 16px`, `padding: 22px 24px`.

**Bloque EN CORTO:** fondo `primary-tint`, `radius 11px`, `padding: 14px 16px`. Label mono `primary`. Texto lead 16/1.5/500 en `ink`.

**Cuerpo:** `p` = 15/1.7/400 `ink-2`, margen inferior 18px. `strong` = 600 `ink`.

**Puntos clave:** label mono `ink-3`. Cada item: `flex gap-11px`, check en círculo 20px `primary-tint`/`primary`, texto 14.5/1.55. Gap entre items 12px.

**Fuentes:** ver 5.6.

**Disclaimer:** ver 5.7.

> **Nota de implementación (`react-markdown`):** el `answer` llega como markdown. Renderizar el **primer párrafo** como bloque «EN CORTO» (lead) y el resto como cuerpo. Mapear `ul/li` a la lista de puntos clave con check. Ver `code/components/ResultPanel.tsx`.
>
> **Recomendación backend (opcional, mejor a futuro):** que la API devuelva `tl_dr: string` y `key_points: string[]` aparte del `answer`, para no depender de heurística sobre el markdown.

### 5.6 SourceCard — clicable, diferencia Constitución vs Sentencia
- De **chip** a **tarjeta**: `flex items-center gap-3`, borde `primary-border`, `surface`, `radius 10px`, `padding: 11px 13px`. Es un `<a>` (target `_blank`).
- Ícono 30–32px `radius 8px`:
  - `source_type === 'constitucion'` → fondo `primary-tint`, glifo `§` en `primary` (Bricolage).
  - `source_type === 'sentencia'` → fondo `gold-tint`, letra `C` en `gold-ink` (Space Mono).
- Título 13–13.5px `600 ink`; subtítulo 11.5px `ink-3` (título II / corte).
- Flecha `→` `primary` a la derecha (señal de clicable). Hover: `opacity .8` o borde más fuerte.

### 5.7 Disclaimer — integrado
- Ya **no** es bloque amarillo. Es un **pie fino**: `flex gap-2`, `border-top: 1px solid border`, `padding-top 16px`, `margin-top 20px`.
- Ícono `ⓘ` en `ink-3`. Texto 12/1.5 `ink-3`.
- Copy: «Esto es orientativo y no reemplaza a un abogado. Para tu caso puntual, consulta a un profesional.»

### 5.8 Estados
- **Cargando (skeleton):** barras `surface-3`, `radius 6px`, anchos 90% / 100% / 70%, gap 9px. Animación de pulso suave (opcional).
- **Error:** ícono `!` en círculo `error-tint`/`error`, texto 13.5/1.5 `ink-2` + link «Intenta de nuevo →» en `primary`.
- **Vacío / hero:** H1 «tu derecho, claro.» + subtítulo `ink-2` + SearchBox + link de ejemplo en `ink-3` (hover `primary`).

---

## 6. Voz — tono parcero 50/50

Cercano y en lenguaje normal, pero preciso y respaldado en la fuente. Se tutea, se evita la jerga, cada afirmación jurídica va con su fuente.

**Sí:**
- «Sí, te pueden despedir sin justa causa, pero te deben pagar una indemnización.»
- «En corto: tienes 36 horas.»
- Tutear · frases cortas · «según el Artículo 30…».

**No:**
- «De conformidad con lo preceptuado en el ordenamiento jurídico vigente…»
- Prometer resultados o dar consejo definitivo.
- Afirmar sin citar la fuente · exceso de emojis.

---

## 7. Tokens — `globals.css` (Tailwind v4)

Ver archivo listo en `code/globals.css`. Reemplaza el bloque `@theme` actual. Renombrado principal: **`terra → primary`** (buscar y reemplazar en el código). Los nombres siguen la convención de Tailwind v4, por lo que generan utilidades `bg-primary`, `text-ink-2`, `rounded-lg`, etc.

## 8. Fuentes — `layout.tsx`

Reemplazar el `<link>` de Plus Jakarta Sans por:

```
https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,600;12..96,700;12..96,800&family=Instrument+Sans:ital,wght@0,400;0,500;0,600;1,400&family=Space+Mono:wght@400;700&display=swap
```

---

## 9. Checklist de implementación

- [ ] `globals.css`: reemplazar `@theme` (tokens Cielo Andino) — `code/globals.css`.
- [ ] `layout.tsx`: cambiar fuentes de Google.
- [ ] Crear `components/Logo.tsx` (wordmark + destello) — `code/components/Logo.tsx`.
- [ ] `page.tsx`: usar `<Logo />` en navbar; ajustar clases `terra → primary`.
- [ ] `SearchBox.tsx`: focus con `primary` + `box-shadow` primary-tint.
- [ ] `ResultPanel.tsx`: nueva anatomía (burbuja, EN CORTO, puntos clave, aire).
- [ ] `SourceCard.tsx`: tarjeta con ícono según `source_type` + flecha.
- [ ] `Disclaimer.tsx`: pie fino integrado.
- [ ] `icon.tsx` / `apple-icon.tsx`: monograma `p` + punto (adiós casita).
- [ ] `opengraph-image.tsx`: actualizar colores/logo si aplica.
- [ ] Buscar y reemplazar restos de `terra` en todo `frontend/`.

---

*Referencia visual completa: el prototipo HTML `Parcero Legal — Design System` de esta sesión. Este `.md` es autosuficiente para implementar sin él.*
