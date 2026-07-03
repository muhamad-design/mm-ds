# mm-ds

A Geist-based design system used as the base for all mm products - minimal, high contrast, light and dark.

**Docs site:** https://muhamad-design.github.io/mm-ds/

Token values follow Vercel's public Geist reference, published at [vercel.com/design.md](https://vercel.com/design.md) for machine consumption. mm-ds is an unofficial personal implementation and is not affiliated with or endorsed by Vercel. All documentation prose here is original. The Geist typefaces are included under the SIL Open Font License.

## What's in here

| Path | What it is |
|---|---|
| `tokens/geist.light.yaml` | **Source of truth, light theme.** Colors (scales, alpha, P3 variants), typography, spacing, rounded, component recipes |
| `tokens/geist.dark.yaml` | Source of truth, dark theme - same token names, dark values |
| `*.html` (26 pages) | The docs site, mirroring the Geist IA: Foundations (Introduction, Colors, Typography, Materials), Brands, one page per component (Avatar ... Tooltip), and Reference. Cmd+K token search, light/dark/system theme |
| `design.md` | Machine-readable spec, **light** theme - YAML frontmatter with every token value, then the rules in prose. Point AI agents here |
| `design.dark.md` | Same spec, **dark** theme values |
| `assets/tokens.css` | Every token as CSS custom properties (`:root` = light, `[data-theme="dark"]` = dark, P3 overrides via `@media (color-gamut: p3)`) |
| `assets/ds.css` / `ds.js` | The docs shell (hand-written, not generated) |
| `build.py` | The generator - rebuilds the pages, `tokens.css`, the search index, and both markdown specs |
| `fonts/` | Geist Sans 400-700 and Geist Mono 400 (woff2, OFL) |

## Workflow

```sh
# edit tokens/*.yaml, then:
python3 build.py

# preview locally
python3 -m http.server 8089   # open http://localhost:8089
```

Never edit the generated files (`*.html`, `assets/tokens.css`, `assets/search-index.js`, `design*.md`) by hand - they are overwritten on every build.

## Consuming the system

- **Web**: link `assets/tokens.css` and use the custom properties (`var(--c-gray-1000)`, `var(--c-background-100)`, `var(--rounded-sm)`, ...).
- **Anything else**: read `tokens/*.yaml` directly.
- **AI agents**: read [`design.md`](https://muhamad-design.github.io/mm-ds/design.md) (and [`design.dark.md`](https://muhamad-design.github.io/mm-ds/design.dark.md)) before styling anything; only tokens defined there are allowed - no raw hex, no raw px.

## Rules of the house

- Tokens only on surfaces - raw hex and raw px are defects.
- Color signals state (links, errors, warnings); it is never decoration.
- Both themes are first class: same token names, per-theme values, no branching designs.
- Plain hyphens in all copy (no em/en dashes).
