#!/usr/bin/env python3
"""
mm-ds build - generates the docs site + machine-readable specs from tokens/.

  Inputs : tokens/geist.light.yaml, tokens/geist.dark.yaml
           (Geist token data - colors incl. P3, typography, spacing, rounded,
            components - as published in Vercel's public design.md)
  Output : HTML pages (foundations + brands + one page per component),
           assets/tokens.css, assets/search-index.js,
           design.md, design.dark.md, .nojekyll

Site IA mirrors vercel.com/geist: Foundations (Introduction, Colors,
Typography, Materials), Brands, Components, plus a Reference group for the
machine-readable specs. Layout/shapes/motion/voice rules live in design.md
only, same as the reference.

Hand-written, never generated: assets/ds.css, assets/ds.js.
Run: python3 build.py
"""
import html
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_URL = "https://github.com/muhamad-design/mm-ds"
PAGES_URL = "https://muhamad-design.github.io/mm-ds"


# ---- tiny ordered YAML-subset parser (nested maps + scalars, comments) --------
def parse_yaml(relpath):
    root = {}
    stack = [(-1, root)]  # (indent of the key that opened the dict, dict)
    with open(os.path.join(HERE, relpath), encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            indent = len(line) - len(line.lstrip(" "))
            key, _, val = s.partition(":")
            key, val = key.strip(), val.strip()
            while stack and indent <= stack[-1][0]:
                stack.pop()
            cur = stack[-1][1]
            if val == "":
                child = {}
                cur[key] = child
                stack.append((indent, child))
            else:
                if val.startswith('"') and val.endswith('"'):
                    val = val[1:-1]
                cur[key] = val
    return root


L = parse_yaml("tokens/geist.light.yaml")
D = parse_yaml("tokens/geist.dark.yaml")
LC, DC = L["colors"], D["colors"]
TY = L["typography"]
SP = L["spacing"]
RD = L["rounded"]
CO = L["components"]

# ---- values documented in the reference prose (not in the frontmatter) --------
SHADOWS = {
    "light": {
        "card": "0 2px 2px rgba(0, 0, 0, 0.04)",
        "menu": "0 1px 1px rgba(0, 0, 0, 0.02), 0 4px 8px -4px rgba(0, 0, 0, 0.04), 0 16px 24px -8px rgba(0, 0, 0, 0.06)",
        "modal": "0 1px 1px rgba(0, 0, 0, 0.02), 0 8px 16px -4px rgba(0, 0, 0, 0.04), 0 24px 32px -8px rgba(0, 0, 0, 0.06)",
    },
    "dark": {
        "card": "0 1px 2px rgba(0, 0, 0, 0.16)",
        "menu": "0 1px 1px rgba(0, 0, 0, 0.02), 0 4px 8px -4px rgba(0, 0, 0, 0.04), 0 16px 24px -8px rgba(0, 0, 0, 0.06)",
        "modal": "0 1px 1px rgba(0, 0, 0, 0.02), 0 8px 16px -4px rgba(0, 0, 0, 0.04), 0 24px 32px -8px rgba(0, 0, 0, 0.06)",
    },
}
FOCUS = {"light": ("#ffffff", "#006bff", "blue-700"), "dark": ("#000000", "#47a8ff", "blue-900")}
BREAKPOINTS = [("sm", "401px"), ("md", "601px"), ("lg", "961px"), ("xl", "1200px"), ("2xl", "1400px")]
EASING = "cubic-bezier(0.175, 0.885, 0.32, 1.1)"

STEPS = [str(n) for n in range(100, 1100, 100)]
ACCENTS = ["blue", "red", "amber", "green", "teal", "purple", "pink"]
STEP_ROLES = [
    ("100", "Default background"), ("200", "Hover background"), ("300", "Active background"),
    ("400", "Default border"), ("500", "Hover border"), ("600", "Active border"),
    ("700", "Solid fill, high contrast"), ("800", "Solid fill, hover"),
    ("900", "Secondary text and icons"), ("1000", "Primary text and icons"),
]


def esc(s):
    return html.escape(str(s), quote=True)


def copyb(v):
    return f'<button class="copy" type="button" data-copy="{esc(v)}">{esc(v)}</button>'


def swpair(lh, dh):
    return (f'<span class="sw-pair"><span class="sw on-light"><span style="background:{esc(lh)}"></span></span>'
            f'<span class="sw on-dark"><span style="background:{esc(dh)}"></span></span></span>')


def tbl(headers, rows):
    th = "".join(f"<th>{h}</th>" for h in headers)
    return (f'<div class="tbl-wrap"><table class="tbl"><thead><tr>{th}</tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>')


def color_rows(names):
    rows = []
    for n in names:
        rows.append(f'<tr><td>{swpair(LC[n], DC[n])}</td><td class="mono"><code class="tok">{esc(n)}</code></td>'
                    f'<td class="mono">{copyb(LC[n])}</td><td class="mono">{copyb(DC[n])}</td></tr>')
    return rows


def color_table(names):
    return tbl(["", "Token", "Light", "Dark"], color_rows(names))


def callout(title, items):
    lis = "".join(f"<li>{i}</li>" for i in items)
    return f'<div class="callout"><h4>{esc(title)}</h4><ul>{lis}</ul></div>'


def demo(inner, extra=""):
    return f'<div class="demo-panel{(" " + extra) if extra else ""}">{inner}</div>'


def var_c(name):
    return f"var(--c-{name})"


# ---- foundations ----------------------------------------------------------------
def sec_index():
    ramp = "".join(f'<span style="background:{var_c("blue-" + s)}"></span>' for s in STEPS)
    cards = (
        '<div class="bento">'
        f'<a class="bcard" href="colors.html"><span class="bprev"><span class="bramp">{ramp}</span></span>'
        '<span class="btitle">Colors</span><p>A high-contrast, accessible color system in light and dark.</p></a>'
        '<a class="bcard" href="typography.html"><span class="bprev"><span class="btype">Ag</span>'
        '<span class="btype btype-mono">Ag</span></span>'
        '<span class="btitle">Typeface</span><p>Geist Sans and Geist Mono, with every style as a token.</p></a>'
        '<a class="bcard" href="materials.html"><span class="bprev"><span class="bmat"></span></span>'
        '<span class="btitle">Materials</span><p>Presets for radii, fills, strokes, and shadows.</p></a>'
        '<a class="bcard" href="button.html"><span class="bprev"><span class="gbtn gbtn-primary">Deploy Project</span></span>'
        '<span class="btitle">Components</span><p>Token-driven building blocks, live in both themes.</p></a>'
        '<a class="bcard" href="brands.html"><span class="bprev"><span class="brand-mark bprev-mark" aria-hidden="true">m</span></span>'
        '<span class="btitle">Brand</span><p>The mm-ds mark, wordmark, and usage rules.</p></a>'
        '<a class="bcard" href="ai.html"><span class="bprev"><code class="tok">design.md</code></span>'
        '<span class="btitle">AI &amp; agents</span><p>The whole system as machine-readable specs.</p></a>'
        '</div>')
    attribution = (
        '<p>Token values follow Vercel\'s public Geist reference, published at '
        '<a href="https://vercel.com/design.md">vercel.com/design.md</a> for reuse by tools and agents. '
        'mm-ds is an unofficial personal implementation and is not affiliated with or endorsed by Vercel. '
        'The Geist typefaces are used under the SIL Open Font License.</p>')
    return [
        ("explore", "", cards),
        ("attribution", "", attribution),
    ]


def sec_colors():
    scales = [("Backgrounds", ["background-100", "background-200"]),
              ("Gray", [f"gray-{s}" for s in STEPS]),
              ("Gray alpha", [f"gray-alpha-{s}" for s in STEPS])]
    scales += [(a.capitalize(), [f"{a}-{s}" for s in STEPS]) for a in ACCENTS]
    rows = []
    for label, names in scales:
        cells = []
        for n in names:
            cells.append(
                f'<button class="scale-swatch" type="button" style="background:{var_c(n)}" '
                f'title="{esc(n)}" aria-label="{esc(n)}" data-copy="{esc(n)}" '
                f'data-raw-light="{esc(LC[n])}" data-raw-dark="{esc(DC[n])}"></button>')
        rows.append(f'<div class="scale-row"><span class="scale-label">{esc(label)}</span>'
                    f'<div class="scale-strip">{"".join(cells)}</div></div>')
    return [
        ("scales", "Scales", (
            '<p>There are 10 color scales in the system. P3 colors are used on supported browsers and '
            'displays.</p>'
            f'<div class="scales">{"".join(rows)}</div>')),
    ]


TYPE_NOTES = {
    "heading-72": "Marketing heroes.", "heading-64": "Large marketing headings.",
    "heading-56": "Marketing headings.", "heading-48": "Large page titles.",
    "heading-40": "Page titles.", "heading-32": "Large section titles.",
    "heading-24": "Section titles.", "heading-20": "Subsection titles.",
    "heading-16": "Card and row titles.", "heading-14": "Dense UI titles.",
    "button-16": "Large buttons.", "button-14": "Default buttons.", "button-12": "Compact buttons.",
    "label-20": "Prominent single-line text.", "label-18": "Large form labels.",
    "label-16": "Form labels and rows.", "label-14": "Default UI text.",
    "label-14-mono": "UI data and paths.", "label-13": "Dense metadata.",
    "label-13-mono": "Dense data.", "label-12": "Fine print.", "label-12-mono": "Fine data.",
    "copy-24": "Prominent body text.", "copy-20": "Lead paragraphs.", "copy-18": "Large body text.",
    "copy-16": "Default prose.", "copy-14": "Default UI copy.", "copy-14-mono": "Inline code in copy.",
    "copy-13": "Dense copy.", "copy-13-mono": "Dense code.",
}


def ts_rows(keys):
    rows = []
    for k in keys:
        t = TY[k]
        ff = "var(--font-mono)" if t["fontFamily"] == "Geist Mono" else "var(--font-sans)"
        ls = t.get("letterSpacing", "")
        style = (f"font-family:{ff};font-size:{t['fontSize']};font-weight:{t['fontWeight']};"
                 f"line-height:{t['lineHeight']};letter-spacing:{ls or 'normal'}")
        disp = " ".join(p.capitalize() for p in k.split("-"))
        rows.append(f'<div class="ts-row"><span class="ts-sample" style="{style}">{esc(disp)}</span>'
                    f'<span class="ts-name">{esc(k)}</span>'
                    f'<span class="ts-note">{esc(TYPE_NOTES.get(k, ""))}</span></div>')
    return f'<div class="ts-list">{"".join(rows)}</div>'


def sec_typography():
    keys = list(TY.keys())
    g = {
        "headings": [k for k in keys if k.startswith("heading-")],
        "buttons": [k for k in keys if k.startswith("button-")],
        "label": [k for k in keys if k.startswith("label-")],
        "copy": [k for k in keys if k.startswith("copy-")],
    }
    return [
        ("usage", "Usage", (
            '<p>Every text style ships as a token carrying family, size, weight, line height, and letter '
            'spacing. <b>Geist Sans</b> sets interface text and prose; <b>Geist Mono</b> sets code and data. '
            'Both are open source under the SIL Open Font License. The specimens below render live from the '
            'token values; agents read the same values from <a href="design.md">design.md</a>.</p>')),
        ("headings", "Headings", (
            '<p>Used to introduce pages and sections. Letter spacing tightens as the size grows.</p>'
            + ts_rows(g["headings"]))),
        ("buttons", "Buttons", (
            '<p>Medium-weight labels for buttons and compact controls.</p>' + ts_rows(g["buttons"]))),
        ("label", "Label", (
            '<p>Single-line text that gets scanned, not read: navigation, form labels, table headers, '
            'metadata. The <code class="tok">-mono</code> variants keep the same metrics in Geist Mono.</p>'
            + ts_rows(g["label"]))),
        ("copy", "Copy", (
            '<p>Multi-line body text with taller line heights. <code class="tok">copy-14</code> and '
            '<code class="tok">label-14</code> cover most interface text.</p>' + ts_rows(g["copy"]))),
    ]


def mat_tiles(tiers):
    cells = []
    for name, radius, shadow, note in tiers:
        sh = "none" if shadow is None else f"var(--shadow-{shadow})"
        recipe = f"rounded-{radius}" + (f" · shadow-{shadow}" if shadow else " · gray-alpha-400")
        cells.append(
            f'<div><div class="mat-stage"><div class="mat-sample" '
            f'style="border-radius:var(--rounded-{radius});box-shadow:{sh}"></div></div>'
            f'<div class="demo-head"><code class="tok">material-{esc(name)}</code>'
            f'<span class="demo-val">{esc(recipe)}</span></div>'
            f'<div class="demo-desc">{esc(note)}</div></div>')
    return f'<div class="mat-grid">{"".join(cells)}</div>'


def sec_materials():
    surface = mat_tiles([
        ("base", "sm", None, "The resting material: a translucent border, no shadow."),
        ("small", "sm", "card", "Raised cards and subtle lifts."),
        ("medium", "sm", "menu", "Emphasized surfaces that stay in the page flow."),
        ("large", "md", "modal", "The strongest on-page emphasis."),
    ])
    floating = mat_tiles([
        ("tooltip", "sm", "card", "Tooltips take the lightest floating material."),
        ("menu", "md", "menu", "Popovers, dropdowns, and other transient surfaces."),
        ("modal", "md", "modal", "Modals and dialogs above a scrim."),
        ("fullscreen", "lg", "modal", "Sheets and fullscreen surfaces."),
    ])
    lf, df = FOCUS["light"], FOCUS["dark"]
    focus_demo = demo(
        '<button class="gbtn gbtn-secondary" type="button" style="box-shadow:var(--focus-ring)">Focused</button>'
        '<button class="gbtn gbtn-secondary" type="button">Tab to me</button>')
    return [
        ("surface", "Surface", "<p>On the page.</p>" + surface),
        ("floating", "Floating", "<p>Above the page.</p>" + floating),
        ("focus", "Focus ring", (
            '<p>Focus is a two-layer ring: a 2px gap in the surface color, then a 2px blue ring. It shows on '
            'every interactive element at <code class="tok">:focus-visible</code>.</p>'
            + focus_demo
            + callout("Values", [
                f'Light: <code class="tok">box-shadow: 0 0 0 2px {lf[0]}, 0 0 0 4px {lf[1]}</code> ({lf[2]}).',
                f'Dark: <code class="tok">box-shadow: 0 0 0 2px {df[0]}, 0 0 0 4px {df[1]}</code> ({df[2]}).',
            ]))),
        ("best-practices", "Best Practices", callout("Choosing a material", [
            "Match the material to the layer: surface materials stay in the page flow, floating materials sit "
            "above it.",
            "Depth comes from borders and tonal surfaces first; shadows stay quiet.",
            "Tooltips always take the lightest floating material.",
            "Pair modal and fullscreen materials with a scrim behind them.",
        ])),
    ]


def sec_brands():
    band_light = ('<div class="brand-band on-light-band"><span class="brand-mark band-mark" aria-hidden="true">m</span>'
                  '<span class="band-word">mm-ds</span></div>')
    band_dark = ('<div class="brand-band on-dark-band"><span class="brand-mark band-mark inverse" aria-hidden="true">m</span>'
                 '<span class="band-word inverse">mm-ds</span></div>')
    return [
        ("mm-ds", "mm-ds", (
            '<p>The mm-ds mark is a lowercase <code class="tok">m</code> on a rounded square in '
            '<code class="tok">gray-1000</code>, set beside the wordmark in Geist Sans SemiBold. On dark '
            'surfaces both invert to <code class="tok">background-100</code>.</p>'
            + band_light + band_dark)),
        ("spelling", "mm-ds spelling", (
            '<p>The preferred written format is <b>mm-ds</b>. Always write mm-ds in lowercase, including in '
            'headings, links, buttons, URLs, and social tags. Do not use MM-DS, Mm-ds, or other capitalized '
            'variations, and keep the hyphen.</p>')),
        ("usage", "Usage", callout("Using the mark", [
            "Keep the rounded-square proportions; never stretch, recolor, or add effects to the mark.",
            "Give the mark clear space equal to half its width on every side.",
            "On photos or busy surfaces, prefer the inverse mark on a solid band.",
        ])),
    ]


def sec_ai():
    files = (
        '<div class="card-grid">'
        '<a class="card" href="design.md"><span class="card-title">design.md</span>'
        '<p>Light theme. YAML frontmatter with every token value, then the rules in prose.</p></a>'
        '<a class="card" href="design.dark.md"><span class="card-title">design.dark.md</span>'
        '<p>Dark theme. Same token names, dark values.</p></a></div>')
    how = (
        '<p>Point an agent at either file and it has the entire system - no scraping, no screenshots. '
        'The two themes share names, so code can switch themes by swapping values only. Layout, shapes, '
        'motion, voice, and the do\'s and don\'ts are documented there too.</p>'
        '<pre class="code"><span class="c"># stable URLs</span>\n'
        f'{PAGES_URL}/design.md\n'
        f'{PAGES_URL}/design.dark.md\n\n'
        '<span class="c"># example prompt</span>\n'
        'Read the design spec at the URL above and build the settings\n'
        'page with those exact tokens.</pre>')
    structure = callout("What each file contains", [
        '<b>Frontmatter (YAML).</b> <code class="tok">colors</code> (scales, alpha, P3 variants), '
        '<code class="tok">typography</code>, <code class="tok">spacing</code>, '
        '<code class="tok">rounded</code>, and <code class="tok">components</code> recipes.',
        "<b>Prose.</b> Overview, color roles, layout rhythm, elevation, motion, shapes, component states, "
        "voice, and the do's and don'ts.",
        "<b>References.</b> Component values point back at tokens with "
        '<code class="tok">{colors.primary}</code>-style paths.',
    ])
    return [
        ("files", "Machine-readable specs", files),
        ("use", "How to use them", how),
        ("structure", "Structure", structure),
    ]


# ---- components -------------------------------------------------------------------
def comp_spec_table(names):
    heads = ["Token", "Background", "Text", "Type", "Radius", "Padding", "Height"]
    rows = []
    for n in names:
        c = CO[n]
        rows.append(
            f'<tr><td class="mono"><code class="tok">{esc(n)}</code></td>'
            f'<td class="mono">{esc(c.get("backgroundColor", "-"))}</td>'
            f'<td class="mono">{esc(c.get("textColor", "-"))}</td>'
            f'<td class="mono">{esc(c.get("typography", "-"))}</td>'
            f'<td class="mono">{esc(c.get("rounded", "-"))}</td>'
            f'<td class="mono">{esc(c.get("padding", "-"))}</td>'
            f'<td class="mono">{esc(c.get("height", "-"))}</td></tr>')
    return tbl(heads, rows)


def c_avatar():
    sizes = "".join(f'<span class="gavatar sz-{s}">mm</span>' for s in (20, 24, 32, 48))
    group = ('<span class="gavatar-group">' + "".join(
        f'<span class="gavatar sz-32">{t}</span>' for t in ("mm", "ds", "ai", "+3")) + "</span>")
    return [
        ("sizes", "Sizes", (
            '<p>Avatars are circles on <code class="tok">gray-100</code> with a '
            '<code class="tok">gray-alpha-400</code> border, at 20, 24, 32, and 48px.</p>' + demo(sizes))),
        ("group", "Avatar group", (
            '<p>Groups overlap by 8px with a 2px <code class="tok">background-100</code> keyline.</p>'
            + demo(group))),
    ]


def c_badge():
    # White text holds AA only on the darker solid fills; bright fills take black.
    dark_text_scales = {"amber", "teal", "green", "pink", "red"}
    def solid(scale):
        text = "#000000" if scale in dark_text_scales else "#ffffff"
        return (f'<span class="gbadge" style="background:{var_c(scale + "-700")};color:{text}">'
                f'{esc(scale)}</span>')
    def subtle(scale):
        return (f'<span class="gbadge" style="background:{var_c(scale + "-100")};'
                f'color:{var_c(scale + "-900")}">{esc(scale)}</span>')
    gray_solid = f'<span class="gbadge" style="background:{var_c("gray-1000")};color:{var_c("background-100")}">gray</span>'
    gray_subtle = f'<span class="gbadge" style="background:{var_c("gray-100")};color:{var_c("gray-900")}">gray</span>'
    sizes = (f'<span class="gbadge sz-sm" style="background:{var_c("gray-1000")};color:{var_c("background-100")}">Small</span>'
             f'<span class="gbadge" style="background:{var_c("gray-1000")};color:{var_c("background-100")}">Medium</span>'
             f'<span class="gbadge sz-lg" style="background:{var_c("gray-1000")};color:{var_c("background-100")}">Large</span>')
    return [
        ("variants", "Variants", (
            '<p>Solid badges use the <code class="tok">700</code> step with a black or white label - whichever '
            'holds AA contrast on that fill (gray steps up to <code class="tok">gray-1000</code>). Subtle badges '
            'pair <code class="tok">100</code> backgrounds with <code class="tok">900</code> text.</p>'
            + demo(gray_solid + "".join(solid(a) for a in ACCENTS))
            + demo(gray_subtle + "".join(subtle(a) for a in ACCENTS)))),
        ("sizes", "Sizes", demo(sizes)),
    ]


def c_banner():
    def banner(scale, label, action):
        return (f'<div class="gbanner" style="background:{var_c(scale + "-100")};'
                f'border-color:{var_c(scale + "-400")}">'
                f'<span style="color:{var_c(scale + "-900")}">{esc(label)}</span>'
                f'<a class="gbanner-action" href="#variants" style="color:{var_c(scale + "-900")}">{esc(action)}</a></div>')
    return [
        ("variants", "Variants", (
            '<p>Banners stretch across their container on the <code class="tok">100</code> background with a '
            '<code class="tok">400</code> border and <code class="tok">900</code> text of their scale.</p>'
            + demo(banner("blue", "A new version is available.", "Upgrade") +
                   banner("green", "Domain verified.", "View") +
                   banner("amber", "Your trial ends in 3 days.", "Add Billing") +
                   banner("red", "Build failed. Bundle exceeds 50 MB.", "View Logs"), "col"))),
    ]


def c_button():
    buttons = ('<button class="gbtn gbtn-primary" type="button">Deploy Project</button>'
               '<button class="gbtn gbtn-secondary" type="button">View Logs</button>'
               '<button class="gbtn gbtn-tertiary" type="button">Cancel</button>'
               '<button class="gbtn gbtn-error" type="button">Delete Member</button>')
    sizes = ('<button class="gbtn gbtn-primary gbtn-sm" type="button">Small · 32px</button>'
             '<button class="gbtn gbtn-primary" type="button">Medium · 40px</button>'
             '<button class="gbtn gbtn-primary gbtn-lg" type="button">Large · 48px</button>')
    states = ('<button class="gbtn" type="button" disabled>Disabled</button>'
              '<button class="gbtn gbtn-secondary" type="button" style="box-shadow:var(--focus-ring)">Focused</button>')
    return [
        ("variants", "Variants", (
            '<p>Primary is for the single most important action on a view; secondary is the default; tertiary '
            'is low-emphasis; error is for destructive actions only.</p>'
            + demo(buttons)
            + comp_spec_table(["button-primary", "button-secondary", "button-tertiary", "button-error"]))),
        ("sizes", "Sizes", demo(sizes) + comp_spec_table(["button-small", "button-large"])),
        ("states", "States", (
            '<p>States move along the scale rather than inventing values: alpha tints deepen one step on hover '
            'and again on press (tertiary rests transparent, hovers <code class="tok">gray-alpha-200</code>, '
            'presses <code class="tok">gray-alpha-300</code>); borders step <code class="tok">400</code> to '
            '<code class="tok">500</code> to <code class="tok">600</code>; solid fills step down one on hover. '
            'Disabled uses a <code class="tok">gray-100</code> fill and <code class="tok">gray-700</code> text.</p>'
            + demo(states))),
    ]


def c_checkbox():
    boxes = ('<label class="gcheck"><input type="checkbox" checked><span>Enabled</span></label>'
             '<label class="gcheck"><input type="checkbox"><span>Unchecked</span></label>'
             '<label class="gcheck"><input type="checkbox" disabled><span>Disabled</span></label>'
             '<label class="gcheck"><input type="checkbox" checked disabled><span>Checked disabled</span></label>')
    return [
        ("states", "States", (
            '<p>A 16px control with <code class="tok">rounded</code> 4px corners and a '
            '<code class="tok">gray-alpha-500</code> border; checked fills with '
            '<code class="tok">gray-1000</code>.</p>' + demo(boxes))),
    ]


def c_code_block():
    block = ('<pre class="code" style="width:100%;margin-top:0"><span class="c"># deploy from the CLI</span>\n'
             'npx vercel deploy --prod\n'
             '<span class="c"># or roll back</span>\n'
             'npx vercel rollback</pre>')
    inline = ('<p style="margin:0">Press <code class="tok">⌘K</code> to search, or run '
              '<code class="tok">build.py</code> to regenerate this site.</p>')
    return [
        ("block", "Code block", (
            '<p>Blocks sit on <code class="tok">background-200</code> with a hairline border, 12px radius, and '
            '<code class="tok">copy-13-mono</code> text. Comments use <code class="tok">gray-900</code>.</p>'
            + demo(block, "col"))),
        ("inline", "Inline code", demo(inline)),
    ]


def c_empty_state():
    inner = ('<div class="gempty"><h4>No deployments yet</h4>'
             '<p>Push to your Git repository to create one.</p>'
             '<button class="gbtn gbtn-primary" type="button">Import Project</button></div>')
    return [
        ("default", "Empty state", (
            '<p>Empty states point at the first action. A dashed <code class="tok">gray-alpha-500</code> '
            'border keeps the region visible without weight.</p>' + demo(inner, "col"))),
    ]


def c_input():
    sizes = ('<input class="ginput ginput-sm" type="text" placeholder="Small · 32px" aria-label="Small input">'
             '<input class="ginput" type="text" placeholder="Medium · 40px" aria-label="Medium input">'
             '<input class="ginput ginput-lg" type="text" placeholder="Large · 48px" aria-label="Large input">')
    field = ('<div class="gfield"><label for="demo-email">Email</label>'
             '<input class="ginput" id="demo-email" type="email" placeholder="you@example.com"></div>'
             '<div class="gfield"><label for="demo-err">Username</label>'
             '<input class="ginput error" id="demo-err" type="text" value="mm ds">'
             '<span class="err">Usernames cannot contain spaces.</span></div>')
    disabled = '<input class="ginput" type="text" placeholder="Disabled" disabled aria-label="Disabled input">'
    return [
        ("sizes", "Sizes", (
            '<p>Inputs share the button height scale and radius, on a translucent '
            '<code class="tok">gray-alpha-400</code> border.</p>'
            + demo(sizes) + comp_spec_table(["input", "input-small", "input-large"]))),
        ("label-error", "Label and error", (
            '<p>Errors switch the border to <code class="tok">red-700</code> and explain what to fix in '
            '<code class="tok">red-900</code>.</p>' + demo(field))),
        ("disabled", "Disabled", demo(disabled)),
    ]


def c_kbd():
    combos = ('<span><kbd class="key">⌘</kbd> <kbd class="key">K</kbd></span>'
              '<span><kbd class="key">⇧</kbd> <kbd class="key">⏎</kbd></span>'
              '<span><kbd class="key">esc</kbd></span>'
              '<span><kbd class="key">↑</kbd> <kbd class="key">↓</kbd></span>')
    return [
        ("default", "Keyboard input", (
            '<p>Keys render in <code class="tok">label-12</code> on <code class="tok">background-200</code> '
            'with a hairline border, one key per cap.</p>' + demo(combos))),
    ]


def c_note():
    def note(scale, label):
        return (f'<div class="gnote" style="background:{var_c(scale + "-100")};'
                f'border-color:{var_c(scale + "-400")};color:{var_c(scale + "-900")}">{esc(label)}</div>')
    plain = (f'<div class="gnote" style="background:{var_c("background-100")};'
             f'border-color:{var_c("gray-alpha-400")};color:{var_c("gray-900")}">'
             'This deployment is public.</div>')
    return [
        ("variants", "Variants", (
            '<p>Notes are compact inline messages: <code class="tok">100</code> background, '
            '<code class="tok">400</code> border, <code class="tok">900</code> text of their scale. The default '
            'gray note stays on <code class="tok">background-100</code> with the standard '
            '<code class="tok">gray-alpha-400</code> border.</p>'
            + demo(plain +
                   note("blue", "A newer deployment exists.") +
                   note("green", "Checks passed.") +
                   note("amber", "Certificate renews in 7 days.") +
                   note("red", "This action cannot be undone."), "col"))),
    ]


def c_pagination():
    pager = ('<nav class="gpager" aria-label="Pagination demo">'
             '<button type="button" disabled>Prev</button>'
             '<button type="button" aria-current="page">1</button>'
             '<button type="button">2</button>'
             '<button type="button">3</button>'
             '<span class="gpager-ellipsis">…</span>'
             '<button type="button">12</button>'
             '<button type="button">Next</button></nav>')
    return [
        ("default", "Pagination", (
            '<p>The current page takes the solid <code class="tok">gray-1000</code> fill; other pages are '
            'tertiary buttons that tint with <code class="tok">gray-alpha-200</code> on hover.</p>'
            + demo(pager))),
    ]


def c_progress():
    def bar(label, pct, fill=""):
        style = f"width:{pct}%" + (f";background:{fill}" if fill else "")
        return (f'<div class="gfield" style="width:100%;max-width:320px"><span class="flabel">{esc(label)}</span>'
                f'<div class="gprogress" role="progressbar" aria-label="{esc(label)}" aria-valuenow="{pct}" '
                f'aria-valuemin="0" aria-valuemax="100"><span style="{style}"></span></div></div>')
    bars = (bar("Default · 60%", 60)
            + bar("Success · 100%", 100, var_c("green-700"))
            + bar("Error · 35%", 35, var_c("red-700")))
    return [
        ("default", "Progress", (
            '<p>An 8px track on <code class="tok">gray-alpha-200</code>; the fill is '
            '<code class="tok">gray-1000</code> by default and may take a status color.</p>'
            + demo(bars, "col"))),
    ]


def c_radio():
    radios = ('<label class="gradio"><input type="radio" name="rd" checked><span>Hobby</span></label>'
              '<label class="gradio"><input type="radio" name="rd"><span>Pro</span></label>'
              '<label class="gradio"><input type="radio" name="rd" disabled><span>Enterprise (disabled)</span></label>')
    return [
        ("states", "States", (
            '<p>A 16px circular control; checked shows a <code class="tok">gray-1000</code> ring with an '
            'inner dot.</p>' + demo(radios))),
    ]


def c_select():
    selects = ('<select class="gselect gselect-sm" aria-label="Small select"><option>Small</option><option>Option</option></select>'
               '<select class="gselect" aria-label="Medium select"><option>Medium</option><option>Option</option></select>'
               '<select class="gselect gselect-lg" aria-label="Large select"><option>Large</option><option>Option</option></select>'
               '<select class="gselect" disabled aria-label="Disabled select"><option>Disabled</option></select>')
    return [
        ("sizes", "Sizes", (
            '<p>Selects share the input recipe plus a chevron affordance; heights are 32, 40, and 48px.</p>'
            + demo(selects))),
    ]


def c_skeleton():
    sk = ('<div style="display:flex;gap:12px;align-items:center;width:100%;max-width:360px">'
          '<span class="gskeleton" style="width:40px;height:40px;border-radius:9999px;flex:0 0 auto"></span>'
          '<span style="flex:1;display:flex;flex-direction:column;gap:8px">'
          '<span class="gskeleton" style="height:12px;width:70%"></span>'
          '<span class="gskeleton" style="height:12px;width:45%"></span></span></div>'
          '<span class="gskeleton" style="height:96px;width:100%;max-width:360px;border-radius:var(--rounded-md)"></span>')
    return [
        ("default", "Skeleton", (
            '<p>Loading placeholders shimmer between <code class="tok">gray-100</code> and '
            '<code class="tok">gray-200</code>, and freeze under '
            '<code class="tok">prefers-reduced-motion</code>.</p>' + demo(sk, "col"))),
    ]


def c_spinner():
    def spinner(px):
        bars = "".join(
            f'<span style="transform:rotate({i * 30}deg) translate(0,-130%);animation-delay:{-1.2 + i * 0.1:.1f}s"></span>'
            for i in range(12))
        return f'<span class="gspinner" style="width:{px}px;height:{px}px">{bars}</span>'
    return [
        ("sizes", "Sizes", (
            '<p>Twelve <code class="tok">gray-800</code> bars fading in sequence, at 16, 24, and 32px. The '
            'animation stops under <code class="tok">prefers-reduced-motion</code>.</p>'
            + demo(spinner(16) + spinner(24) + spinner(32)))),
    ]


def c_switch():
    switches = ('<label class="gswitch"><input type="checkbox" checked><span>Notifications</span></label>'
                '<label class="gswitch"><input type="checkbox"><span>Off</span></label>'
                '<label class="gswitch"><input type="checkbox" disabled><span>Disabled</span></label>')
    return [
        ("states", "States", (
            '<p>The track rests on <code class="tok">gray-alpha-300</code> and fills with '
            '<code class="tok">blue-700</code> when on; the knob carries the small shadow tier.</p>'
            + demo(switches))),
    ]


def c_table():
    rows = [
        ("mm-ds", "Ready", "Production", "2m ago"),
        ("docs", "Ready", "Preview", "1h ago"),
        ("api", "Building", "Preview", "just now"),
        ("marketing", "Error", "Production", "3d ago"),
    ]
    color = {"Ready": "green-900", "Building": "amber-900", "Error": "red-900"}
    body = "".join(
        f'<tr><td class="mono">{esc(p)}</td>'
        f'<td><span style="color:{var_c(color[s])}">{esc(s)}</span></td>'
        f'<td>{esc(e)}</td><td class="mono">{esc(t)}</td></tr>'
        for p, s, e, t in rows)
    table = (f'<div class="tbl-wrap" style="margin-top:0;width:100%"><table class="tbl">'
             f'<thead><tr><th>Project</th><th>Status</th><th>Environment</th><th>Updated</th></tr></thead>'
             f'<tbody>{body}</tbody></table></div>')
    return [
        ("default", "Table", (
            '<p>Tables live inside a bordered, rounded container: <code class="tok">label-12</code> headers on '
            '<code class="tok">gray-100</code>, hairline row dividers, <code class="tok">label-14</code> cells. '
            'Status text pairs a <code class="tok">900</code>-step color with a label, never color alone.</p>'
            + demo(table, "col"))),
    ]


def c_textarea():
    ta = ('<textarea class="gtextarea" placeholder="Add a deployment note…" aria-label="Deployment note"></textarea>'
          '<textarea class="gtextarea" disabled placeholder="Disabled" aria-label="Disabled textarea"></textarea>')
    return [
        ("default", "Textarea", (
            '<p>The input recipe with a comfortable multi-line height; resizes vertically only.</p>'
            + demo(ta, "col"))),
    ]


def c_tooltip():
    tip = ('<span class="gtip-wrap"><button class="gbtn gbtn-secondary" type="button" '
           'aria-describedby="tip-static">Static</button>'
           '<span class="gtip" role="tooltip" id="tip-static">Copied to clipboard</span></span>'
           '<span class="gtip-wrap gtip-hover"><button class="gbtn gbtn-secondary" type="button" '
           'aria-describedby="tip-hover">Hover me</button>'
           '<span class="gtip" role="tooltip" id="tip-hover">Deploys to production</span></span>')
    return [
        ("default", "Tooltip", (
            '<p>Tooltips invert the surface: <code class="tok">gray-1000</code> background, '
            '<code class="tok">background-100</code> text, 6px radius, and the small shadow tier. They take '
            'the lightest elevation and never hold critical information.</p>'
            + demo(tip, "tall"))),
    ]


COMPONENT_PAGES = [
    {"file": "avatar.html", "title": "Avatar", "lead": "People and teams as circles - sized, bordered, and groupable.", "sections": c_avatar},
    {"file": "badge.html", "title": "Badge", "lead": "Small status labels in solid and subtle variants across every accent scale.", "sections": c_badge},
    {"file": "banner.html", "title": "Banner", "lead": "Full-width messages for page-level state: info, success, warning, error.", "sections": c_banner},
    {"file": "button.html", "title": "Button", "lead": "Four variants and three sizes, specified entirely by tokens.", "sections": c_button},
    {"file": "checkbox.html", "title": "Checkbox", "lead": "A 16px control that fills with gray-1000 when checked.", "sections": c_checkbox},
    {"file": "code-block.html", "title": "Code Block", "lead": "Blocks and inline code set in Geist Mono on a quiet surface.", "sections": c_code_block},
    {"file": "empty-state.html", "title": "Empty State", "lead": "A bordered region that points at the first action to take.", "sections": c_empty_state},
    {"file": "input.html", "title": "Input", "lead": "Text fields on translucent borders, with label, error, and disabled states.", "sections": c_input},
    {"file": "kbd.html", "title": "Keyboard Input", "lead": "Key caps for shortcuts and command hints.", "sections": c_kbd},
    {"file": "note.html", "title": "Note", "lead": "Compact inline messages on the 100/400/900 recipe of each scale.", "sections": c_note},
    {"file": "pagination.html", "title": "Pagination", "lead": "Page controls with a solid current page and tertiary neighbors.", "sections": c_pagination},
    {"file": "progress.html", "title": "Progress", "lead": "A quiet 8px track with a token-colored fill.", "sections": c_progress},
    {"file": "radio.html", "title": "Radio", "lead": "Single-choice circles with a gray-1000 ring when selected.", "sections": c_radio},
    {"file": "select.html", "title": "Select", "lead": "The input recipe with a chevron, in three heights.", "sections": c_select},
    {"file": "skeleton.html", "title": "Skeleton", "lead": "Shimmering placeholders that respect reduced motion.", "sections": c_skeleton},
    {"file": "spinner.html", "title": "Spinner", "lead": "Twelve fading bars in three sizes.", "sections": c_spinner},
    {"file": "switch.html", "title": "Switch", "lead": "An on/off toggle that fills with blue-700.", "sections": c_switch},
    {"file": "table.html", "title": "Table", "lead": "Bordered, rounded data tables with hairline dividers.", "sections": c_table},
    {"file": "textarea.html", "title": "Textarea", "lead": "Multi-line input on the same recipe as text fields.", "sections": c_textarea},
    {"file": "tooltip.html", "title": "Tooltip", "lead": "Inverted, shadowed hints that never hold critical information.", "sections": c_tooltip},
]


# ---- pages ----------------------------------------------------------------------
PAGES = [
    {"file": "index.html", "title": "Introduction", "h1": "mm-ds Design System", "group": "Foundations",
     "lead": "A Geist-based design system for building consistent web experiences.",
     "desc": "mm-ds - a Geist-based design system: tokens, typography, components, and machine-readable specs.",
     "sections": sec_index},
    {"file": "colors.html", "title": "Colors", "group": "Foundations",
     "lead": "Learn how to work with our color system. Click a swatch to copy the token; right click to copy "
             "the raw value.",
     "desc": "The mm-ds color system - 10 scales in light and dark, with P3 variants.",
     "sections": sec_colors},
    {"file": "typography.html", "title": "Typography", "group": "Foundations",
     "lead": "Rules of typesetting throughout the system.",
     "desc": "mm-ds typography - heading, label, copy, and button tokens in Geist Sans and Geist Mono.",
     "sections": sec_typography},
    {"file": "materials.html", "title": "Materials", "group": "Foundations",
     "lead": "Presets for radii, fills, strokes, and shadows.",
     "desc": "mm-ds materials - surface and floating material presets plus the focus ring, in light and dark.",
     "sections": sec_materials},
    {"file": "brands.html", "title": "mm-ds", "group": "Brands",
     "lead": "How to use the mm-ds mark and wordmark, and how to write the name.",
     "desc": "mm-ds brand - the mark, the wordmark, spelling, and usage rules.",
     "sections": sec_brands},
] + [
    {"file": p["file"], "title": p["title"], "group": "Components", "lead": p["lead"],
     "desc": f'mm-ds {p["title"]} - token-driven component demos and states.', "sections": p["sections"]}
    for p in COMPONENT_PAGES
] + [
    {"file": "ai.html", "title": "AI & agents", "group": "Reference",
     "lead": "The whole system ships as two markdown files an agent can read in one pass - one per theme, "
             "same token names.",
     "desc": "mm-ds for AI - machine-readable design.md and design.dark.md specs and how to use them.",
     "sections": sec_ai},
]

NAV = [
    ("Foundations", [("index.html", "Introduction"), ("colors.html", "Colors"),
                     ("typography.html", "Typography"), ("materials.html", "Materials")]),
    ("Brands", [("brands.html", "mm-ds")]),
    ("Components", [(p["file"], p["title"]) for p in COMPONENT_PAGES]),
    ("Reference", [("ai.html", "AI & agents"), ("design.md", "design.md"), ("design.dark.md", "design.dark.md")]),
]

SEARCH_SVG = ('<svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">'
              '<circle cx="11" cy="11" r="7" stroke="currentColor" stroke-width="2"/>'
              '<path d="M20 20l-3.5-3.5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>')
EXT_SVG = ('<svg class="ext" width="11" height="11" viewBox="0 0 24 24" fill="none" aria-hidden="true">'
           '<path d="M7 17L17 7M9 7h8v8" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
           'stroke-linejoin="round"/></svg>')


def nav_html(active):
    out = []
    for group, items in NAV:
        out.append(f'<div class="nav-group">{esc(group)}</div>')
        for href, label in items:
            cur = ' aria-current="page"' if href == active else ""
            ext = EXT_SVG if href.endswith(".md") else ""
            mark = '<span class="nav-mark" aria-hidden="true">m</span>' if href == "brands.html" else ""
            out.append(f'<a href="{href}"{cur}>{mark}{esc(label)}{ext}</a>')
    return "\n        ".join(out)


def page_html(page, prev_pg, next_pg):
    title = "mm-ds · Geist-based design system" if page["file"] == "index.html" else f'{page["title"]} · mm-ds'
    sections = page["sections"]()
    body = []
    for sid, heading, inner in sections:
        if heading:
            body.append(f'<section id="{sid}"><h2>{heading}'
                        f'<a class="hlink" href="#{sid}" aria-label="Link to {esc(heading)}">#</a></h2>\n{inner}\n</section>')
        else:
            body.append(f'<section id="{sid}">\n{inner}\n</section>')
    pager = ""
    if prev_pg or next_pg:
        links = []
        if prev_pg:
            links.append(f'<a class="prev" href="{prev_pg["file"]}"><span class="dir">Previous</span>'
                         f'<span class="pg">{esc(prev_pg["title"])}</span></a>')
        if next_pg:
            links.append(f'<a class="next" href="{next_pg["file"]}"><span class="dir">Next</span>'
                         f'<span class="pg">{esc(next_pg["title"])}</span></a>')
        pager = f'<nav class="pager" aria-label="Pagination">{"".join(links)}</nav>'
    h1 = page.get("h1", page["title"])
    nl = "\n"
    return f'''<!doctype html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{esc(page["desc"])}">
<title>{esc(title)}</title>
<link rel="icon" type="image/svg+xml" href="assets/favicon.svg">
<script>(function(){{var p='system';try{{p=localStorage.getItem('mmds-theme')||'system'}}catch(e){{}}
var d=p==='system'?(window.matchMedia&&matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'):p;
document.documentElement.setAttribute('data-theme',d);document.documentElement.setAttribute('data-theme-pref',p);}})();</script>
<link rel="stylesheet" href="assets/tokens.css">
<link rel="stylesheet" href="assets/ds.css">
</head>
<body>
<a class="skip-link" href="#content">Skip to content</a>
<div class="frame">
  <header class="frame-head">
    <a class="brand" href="index.html">
      <span class="brand-mark" aria-hidden="true">m</span>
      <span class="brand-name">mm-ds Design System</span>
    </a>
    <div class="head-main">
      <button id="navBtn" class="navbtn" aria-label="Open navigation" aria-expanded="false" aria-controls="sidebar"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></button>
      <button class="searchbtn" type="button" data-search-open>
        {SEARCH_SVG}<span class="grow">Search mm-ds</span><kbd>⌘K</kbd>
      </button>
      <span class="head-spacer"></span>
      <div class="theme-switch" role="group" aria-label="Color theme">
        <button type="button" data-theme="system" aria-pressed="false" aria-label="System theme" data-tip="System"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true"><rect x="3" y="5" width="18" height="12" rx="2" stroke="currentColor" stroke-width="2"/><path d="M9 20h6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></button>
        <button type="button" data-theme="light" aria-pressed="false" aria-label="Light theme" data-tip="Light"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="12" cy="12" r="4" stroke="currentColor" stroke-width="2"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M19.1 4.9L17 7M7 17l-2.1 2.1" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></button>
        <button type="button" data-theme="dark" aria-pressed="false" aria-label="Dark theme" data-tip="Dark"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M21 13A8.5 8.5 0 1 1 11 3a7 7 0 0 0 10 10z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg></button>
      </div>
    </div>
  </header>
  <div class="frame-body">
    <nav class="sidebar" id="sidebar" aria-label="Site navigation">
      <div class="nav-scroll">
        {nav_html(page["file"])}
      </div>
    </nav>
    <div class="backdrop" id="navBackdrop"></div>
    <main class="main" id="content">
      <article class="doc">
        <h1>{esc(h1)}</h1>
        <p class="lead">{esc(page["lead"])}</p>
        {nl.join(body)}
        {pager}
        <footer class="foot">
          <span>Unofficial reference. Token data from Vercel's public <a href="https://vercel.com/design.md">design.md</a>; not affiliated with Vercel.</span>·
          <a href="design.md">design.md</a>·
          <a href="design.dark.md">design.dark.md</a>·
          <a href="{REPO_URL}">GitHub</a>
        </footer>
      </article>
    </main>
  </div>
</div>
<div class="search-modal" id="searchModal" hidden>
  <div class="search-scrim"></div>
  <div class="search-panel" role="dialog" aria-modal="true" aria-label="Search">
    <div class="search-head">
      {SEARCH_SVG}
      <input id="searchInput" type="text" placeholder="Search pages and tokens…" aria-label="Search pages and tokens" autocomplete="off" spellcheck="false">
      <kbd>esc</kbd>
    </div>
    <div class="search-results" id="searchResults"></div>
  </div>
</div>
<script src="assets/search-index.js"></script>
<script src="assets/ds.js"></script>
</body>
</html>
'''


# ---- tokens.css ------------------------------------------------------------------
def color_var_lines(colors, indent="  "):
    return "\n".join(f"{indent}--c-{k}: {v};" for k, v in colors.items() if not k.endswith("-p3"))


def p3_var_lines(colors, indent="    "):
    return "\n".join(f"{indent}--c-{k[:-3]}: {v};" for k, v in colors.items() if k.endswith("-p3"))


def shell_var_lines(theme, indent="  "):
    sh = SHADOWS[theme]
    gap, ring, _ = FOCUS[theme]
    # Shell-only role mapping. Divergences from a naive 1:1 map, for legibility:
    # dark bg-2/bg-elevated use gray-100 (background-200 is #000 in dark - panels
    # would vanish); light text-tertiary uses gray-900 (gray-700 is 3.2:1 on white,
    # below WCAG AA for the small text these roles style).
    per = {
        "light": {"overlay": "rgba(0, 0, 0, 0.4)", "success": "var(--c-green-800)",
                  "material": "rgba(255, 255, 255, 0.8)", "focus": "var(--c-blue-700)",
                  "bg2": "var(--c-background-200)", "elevated": "var(--c-background-100)",
                  "tertiary": "var(--c-gray-900)"},
        "dark": {"overlay": "rgba(0, 0, 0, 0.6)", "success": "var(--c-green-900)",
                 "material": "rgba(0, 0, 0, 0.75)", "focus": "var(--c-blue-900)",
                 "bg2": "var(--c-gray-100)", "elevated": "var(--c-gray-100)",
                 "tertiary": "var(--c-gray-700)"},
    }[theme]
    lines = [
        "--bg-1: var(--c-background-100)",
        f"--bg-2: {per['bg2']}",
        "--bg-3: var(--c-gray-100)",
        f"--bg-elevated: {per['elevated']}",
        "--bg-hover: var(--c-gray-alpha-100)",
        f"--bg-overlay: {per['overlay']}",
        "--bg-accent: var(--c-blue-700)",
        "--bg-accent-subtle: var(--c-blue-100)",
        "--text-primary: var(--c-gray-1000)",
        "--text-secondary: var(--c-gray-900)",
        f"--text-tertiary: {per['tertiary']}",
        "--text-accent: var(--c-blue-900)",
        f"--text-success: {per['success']}",
        "--border-primary: var(--c-gray-alpha-500)",
        "--border-secondary: var(--c-gray-alpha-400)",
        "--border-tertiary: var(--c-gray-alpha-200)",
        f"--focus-color: {per['focus']}",
        f"--focus-ring: 0 0 0 2px {gap}, 0 0 0 4px {ring}",
        f"--shadow-card: {sh['card']}",
        f"--shadow-menu: {sh['menu']}",
        f"--shadow-modal: {sh['modal']}",
        "--elevation-sm: var(--shadow-card)",
        "--elevation-md: var(--shadow-menu)",
        "--elevation-lg: var(--shadow-modal)",
        f"--material-regular: {per['material']}",
    ]
    return "\n".join(f"{indent}{l};" for l in lines)


def misc_var_lines(indent="  "):
    lines = [f"--rounded-{k}: {v}" for k, v in RD.items()]
    lines += ["--radius-4: 4px", "--radius-8: var(--rounded-sm)", "--radius-12: var(--rounded-md)",
              "--radius-full: var(--rounded-full)"]
    lines += [f"--spacing-{k}: {v}" for k, v in SP.items()]
    return "\n".join(f"{indent}{l};" for l in lines)


def tokens_css():
    return f"""/* mm-ds · generated by build.py - do not edit by hand.
   Geist token values (light + dark + P3) as CSS custom properties. */
:root{{
{color_var_lines(LC)}
{shell_var_lines('light')}
{misc_var_lines()}
}}
[data-theme="dark"]{{
{color_var_lines(DC)}
{shell_var_lines('dark')}
}}
@media (color-gamut: p3){{
  :root{{
{p3_var_lines(LC)}
  }}
  [data-theme="dark"]{{
{p3_var_lines(DC)}
  }}
}}
"""


# ---- search index ------------------------------------------------------------------
def search_index():
    ix = []
    for p in PAGES:
        ix.append({"t": p["title"] if p["group"] != "Brands" else "Brands", "k": "Page", "p": p["file"], "v": ""})

    for name in LC:
        if name.endswith("-p3"):
            continue
        ix.append({"t": name, "k": "Color", "p": "colors.html#scales", "v": f"{LC[name]} · {DC[name]}",
                   "c": LC[name]})
    def ty_anchor(name):
        if name.startswith("heading-"):
            return "typography.html#headings"
        if name.startswith("button-"):
            return "typography.html#buttons"
        if name.startswith("label-"):
            return "typography.html#label"
        return "typography.html#copy"

    for name, t in TY.items():
        ix.append({"t": name, "k": "Typography", "p": ty_anchor(name),
                   "v": f"{t['fontSize'][:-2]}/{t['lineHeight'][:-2]} · {t['fontWeight']}"})
    for k in SHADOWS["light"]:
        ix.append({"t": f"shadow-{k}", "k": "Materials",
                   "p": "materials.html#surface" if k == "card" else "materials.html#floating", "v": ""})
    for name, c in CO.items():
        target = "button.html#variants" if name.startswith("button") else "input.html#sizes"
        ix.append({"t": name, "k": "Component", "p": target, "v": f"h {c.get('height', '')}"})
    return "window.__DS_INDEX=" + json.dumps(ix, ensure_ascii=False, separators=(",", ":")) + ";"


# ---- design.md / design.dark.md ------------------------------------------------------
def design_md(theme):
    src = "tokens/geist.light.yaml" if theme == "light" else "tokens/geist.dark.yaml"
    other_file = "design.dark.md" if theme == "light" else "design.md"
    this_name, other_name = ("Light", "Dark") if theme == "light" else ("Dark", "Light")
    with open(os.path.join(HERE, src), encoding="utf-8") as f:
        fm = f.read().rstrip("\n")
    fm = re.sub(r"^description: .*$",
                f"description: mm-ds, a Geist-based design system - {this_name} theme "
                f"(the {other_name} theme is documented at /{other_file}). "
                f"Token values follow Vercel's public Geist reference.",
                fm, count=1, flags=re.M)
    sh = SHADOWS[theme]
    gap, ring, ring_name = FOCUS[theme]
    prose = f"""
# Geist (mm-ds)

## Overview

mm-ds is a Geist-based design system: minimal, high-contrast interfaces with generous whitespace and restrained color. Color signals state and hierarchy; it is never decoration. Readability and accessibility come first.

This file documents the {this_name} theme. The {other_name} theme keeps the same token names with different values and lives at `/{other_file}`. Colors are sRGB hex; the `*-p3` tokens are wide-gamut `oklch()` equivalents for Display P3 screens.

## Colors

Every non-background scale runs ten steps (`100`-`1000`), and each step maps to a role rather than a plain lightness ramp:

- `100` default background
- `200` hover background
- `300` active background
- `400` default border
- `500` hover border
- `600` active border
- `700` solid fill, high contrast
- `800` solid fill, hover
- `900` secondary text and icons
- `1000` primary text and icons

`background-100` is the main page and card surface; `background-200` is only for subtle separation, never a general fill. `gray-alpha-*` values are translucent and layer safely over any surface - use them for borders, dividers, hover tints, and overlays. Solid `gray-*` keeps its contrast anywhere - use it for text and opaque fills. Accent scales carry meaning: `blue` for links, focus, and success; `red` for errors; `amber` for warnings; `green`, `teal`, `purple`, and `pink` extend the palette. Prefer the hex tokens; each accent also ships a `*-p3` variant.

## Typography

Geist Sans sets interface text and prose; Geist Mono sets code and data (both open source). Each `typography` token carries `fontFamily`, `fontSize`, `fontWeight`, `lineHeight`, and `letterSpacing`:

- `heading-72` through `heading-14` title pages and sections; letter spacing tightens as size grows.
- `label-20` through `label-12` carry single-line UI text: navigation, form labels, table headers, metadata.
- `copy-24` through `copy-13` set multi-line body text with taller line heights.
- `button-16` through `button-12` are medium-weight labels for buttons and compact controls.

Default to `copy-14` for body and `label-14` for UI. The `-mono` variants keep the same metrics in Geist Mono; prefer tabular figures when numbers must align.

## Layout

Spacing rides a 4px base scale: 4, 8, 12, 16, 24, 32, 40, 64, 96px. Keep a three-step rhythm: 8px inside a group, 16px between groups, 32-40px between sections. Cards default to 24px padding - 16px compact, 32px hero. Center content in a 1200px column and make every layout work on mobile and desktop. Breakpoints: `sm` 401px, `md` 601px, `lg` 961px, `xl` 1200px, `2xl` 1400px.

## Elevation & Depth

Depth comes from borders and tonal surfaces before shadows, so shadows stay quiet. {this_name}-theme `box-shadow` values:

- Raised cards: `{sh["card"]}`
- Popovers and menus: `{sh["menu"]}`
- Modals and dialogs: `{sh["modal"]}`

Tooltips take the lightest tier. Pair each elevation with the matching radius below.

## Motion

Animate only to clarify a change, never to decorate. Most interactions read best instantly - `0ms` is a valid and often the right duration. When motion genuinely helps, keep it short and physical with the easing `{EASING}`: about 150ms for state changes, 200ms for popovers and tooltips, 300ms for overlays and modals. No loops, no attention-grabbing movement, and honor `prefers-reduced-motion`.

## Shapes

Radii stay tight: 6px for controls and everyday surfaces, 12px for menus and modals, 16px for fullscreen surfaces, 9999px for pills, avatars, and circular controls. Keep one radius family per view.

## Components

The `components` tokens are ready-to-apply recipes (`backgroundColor`, `textColor`, `typography`, `rounded`, `padding`, `height`) drawn from this theme:

- `button-primary`: solid `gray-1000` fill with a `background-100` label - the single most important action on a view.
- `button-secondary`: `background-100` fill with a translucent `gray-alpha-400` border.
- `button-tertiary`: transparent fill with `gray-1000` text; tint with `gray-alpha` on hover.
- `button-error`: solid `red-800` fill with white text, for destructive actions.
- `input`: `background-100` fill, translucent border, 6px radius.

Medium is 40px; `button-small`/`input-small` are 32px and `button-large`/`input-large` are 48px (large buttons step type up to `button-16`). States move along the scale: fills go `100` to `200` on hover and `300` on active; borders go `400` to `500` to `600`. Disabled uses a `gray-100` fill, `gray-700` text, and a not-allowed cursor. Focus is a two-layer ring - `box-shadow: 0 0 0 2px {gap}, 0 0 0 4px {ring}` - a 2px gap in the surface color, then a 2px `{ring_name}` ring.

## Voice & Content

Copy is part of the design; keep it precise and free of filler.

- Title Case for buttons, labels, titles, and tabs; sentence case for body, helper text, and toasts.
- Actions pair a verb with an object (`Deploy Project`, `Delete Member`) - never a bare `OK` or `Confirm`.
- Errors say what happened, then what to do next.
- Toasts name the thing that changed, drop the trailing period, and never say `successfully`.
- Empty states point at the first action to take.
- In-progress states use the present participle with an ellipsis: `Deploying…`, `Saving…`.
- Use numerals for counts, curly quotes, and a real ellipsis character; skip `please` and marketing superlatives.

## Do's and Don'ts

- Rank information with the gray scale: `1000` primary text, `900` secondary, `700` disabled.
- Reserve solid accent color for state and the single most important action on a view.
- Hold WCAG AA contrast (4.5:1 for body text).
- Show the focus ring on every interactive element at `:focus-visible`; never remove an outline without a visible replacement.
- Apply typography tokens instead of hand-setting font size, weight, or line height.
- Don't signal state with color alone; pair it with an icon or a text label.
- Don't use `background-200` as a general fill; it exists for subtle separation only.
- Don't mix rounded and sharp corners, or more than two font weights, in one view.
- Don't swap `gray-*` for `background-*`; they are separate scales.
"""
    return "---\n" + fm + "\n---\n" + prose


# ---- main -----------------------------------------------------------------------------
def main():
    def write(rel, content):
        path = os.path.join(HERE, rel)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"wrote {rel} ({len(content) // 1024} KB)")

    for i, p in enumerate(PAGES):
        prev_pg = PAGES[i - 1] if i > 0 else None
        next_pg = PAGES[i + 1] if i < len(PAGES) - 1 else None
        write(p["file"], page_html(p, prev_pg, next_pg))
    write("assets/tokens.css", tokens_css())
    write("assets/search-index.js", search_index())
    write("design.md", design_md("light"))
    write("design.dark.md", design_md("dark"))
    write(".nojekyll", "")


if __name__ == "__main__":
    main()
