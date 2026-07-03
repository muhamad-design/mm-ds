#!/usr/bin/env python3
"""
mm-ds build - generates the docs site + machine-readable specs from tokens/.

  Inputs : tokens/geist.light.yaml, tokens/geist.dark.yaml
           (Geist token data - colors incl. P3, typography, spacing, rounded,
            components - as published in Vercel's public design.md)
  Output : 11 HTML pages, assets/tokens.css, assets/search-index.js,
           design.md, design.dark.md, .nojekyll

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
DURATIONS = [
    ("instant", 0, "The default. Most state changes read best with no transition at all."),
    ("state", 150, "Small state changes - hover, press, selection."),
    ("popover", 200, "Popovers, tooltips, dropdown menus."),
    ("overlay", 300, "Overlays, modals, drawers."),
]

STEPS = [str(n) for n in range(100, 1100, 100)]
ACCENTS = ["blue", "red", "amber", "green", "teal", "purple", "pink"]
STEP_ROLES = [
    ("100", "Default background"), ("200", "Hover background"), ("300", "Active background"),
    ("400", "Default border"), ("500", "Hover border"), ("600", "Active border"),
    ("700", "Solid fill, high contrast"), ("800", "Solid fill, hover"),
    ("900", "Secondary text and icons"), ("1000", "Primary text and icons"),
]
SPACE_USE = {
    "1": "Tightest gaps - icon to label", "2": "Inside a group", "3": "Compact padding",
    "4": "Between groups; compact cards", "6": "Card padding", "8": "Between sections",
    "10": "Large section breaks", "16": "Page-level air", "24": "Hero spacing",
}


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


def callout(title, items, cls=""):
    lis = "".join(f"<li>{i}</li>" for i in items)
    return f'<div class="callout {cls}"><h4>{esc(title)}</h4><ul>{lis}</ul></div>'


# ---- page content --------------------------------------------------------------
def sec_index():
    foundations = [
        ("colors.html", "Colors", "Ten-step scales where every step has a job: backgrounds, borders, fills, text."),
        ("typography.html", "Typography", "Geist Sans and Geist Mono across heading, label, copy, and button tokens."),
        ("layout.html", "Layout", "A 4px spacing scale, a 1200px content column, and five breakpoints."),
        ("elevation.html", "Elevation", "Borders and tonal surfaces first; three quiet shadow tiers."),
        ("motion.html", "Motion", "Instant by default; one springy curve when motion earns its place."),
        ("shapes.html", "Shapes", "Tight radii: 6, 12, 16, and full - one family per view."),
    ]
    patterns = [
        ("components.html", "Components", "Buttons and inputs as token recipes, with sizes and states."),
        ("voice.html", "Voice & content", "How interface copy is written: precise, verb-first, no filler."),
        ("guidelines.html", "Do's & don'ts", "The rules that keep every surface consistent and accessible."),
    ]
    def cards(items):
        return '<div class="card-grid">' + "".join(
            f'<a class="card" href="{f}"><span class="card-title">{esc(t)}</span><p>{esc(d)}</p></a>'
            for f, t, d in items) + "</div>"
    consuming = (
        '<p>Web surfaces can link the generated custom properties directly; agents and tools read the '
        'markdown specs or the YAML token files.</p>'
        '<pre class="code"><span class="c">/* web */</span>\n'
        '&lt;link rel="stylesheet" href="assets/tokens.css"&gt;\n'
        'color: var(--c-gray-1000);\n'
        'background: var(--c-background-100);\n'
        'border-radius: var(--rounded-sm);\n\n'
        '<span class="c"># AI agents - machine-readable specs</span>\n'
        f'{PAGES_URL}/design.md\n'
        f'{PAGES_URL}/design.dark.md</pre>')
    return [
        ("foundations", "Foundations", cards(foundations)),
        ("patterns", "Patterns", cards(patterns)),
        ("principles", "Principles", callout("What the system optimizes for", [
            "<b>Minimal and high contrast.</b> Generous whitespace, near-neutral surfaces, restrained color.",
            "<b>Color signals state.</b> Accents mark links, errors, and warnings - never decoration.",
            "<b>Both themes are first-class.</b> Every token name resolves in light and dark; designs never branch on mode.",
            "<b>Accessible by default.</b> WCAG AA contrast and a visible focus ring everywhere.",
            "<b>Readable by machines.</b> The same tokens ship as YAML, CSS variables, and per-theme markdown specs.",
        ])),
        ("consuming", "Consuming the system", consuming),
        ("attribution", "Attribution", (
            '<p>Token values follow Vercel\'s public Geist reference, published at '
            '<a href="https://vercel.com/design.md">vercel.com/design.md</a> for exactly this kind of reuse by '
            'tools and agents. mm-ds is an unofficial personal implementation and is not affiliated with or '
            'endorsed by Vercel. The Geist typefaces are used under the SIL Open Font License.</p>')),
    ]


def sec_colors():
    steps = tbl(["Step", "Role"], [
        f'<tr><td class="mono"><code class="tok">{s}</code></td><td>{esc(r)}</td></tr>' for s, r in STEP_ROLES])
    base_note = ('<p>Four aliases sit on top of the scales: <code class="tok">primary</code> and '
                 '<code class="tok">secondary</code> for text, <code class="tok">tertiary</code> for the '
                 'link-and-focus blue, and <code class="tok">neutral</code> for a plain neutral fill.</p>')
    accents_html = ('<p><code class="tok">blue</code> carries links, focus, and success; '
                    '<code class="tok">red</code> errors; <code class="tok">amber</code> warnings. '
                    '<code class="tok">green</code>, <code class="tok">teal</code>, <code class="tok">purple</code>, '
                    'and <code class="tok">pink</code> extend the palette for charts and product accents. '
                    'Click any value to copy it.</p>')
    for a in ACCENTS:
        accents_html += f'<h3 id="{a}">{a}<a class="hlink" href="#{a}" aria-label="Link to {a}">#</a></h3>'
        accents_html += color_table([f"{a}-{s}" for s in STEPS])
    p3_html = ('<p>Every accent step also ships a wide-gamut <code class="tok">oklch()</code> value for '
               'Display P3 screens, under the same name with a <code class="tok">-p3</code> suffix. '
               'The sRGB hex is the fallback.</p>')
    for a in ACCENTS:
        rows = []
        for s in STEPS:
            k = f"{a}-{s}-p3"
            rows.append(f'<tr><td class="mono"><code class="tok">{k}</code></td>'
                        f'<td class="mono">{copyb(LC[k])}</td><td class="mono">{copyb(DC[k])}</td></tr>')
        p3_html += f'<h3 id="p3-{a}">{a} P3</h3>' + tbl(["Token", "Light", "Dark"], rows)
    return [
        ("steps", "How steps work", (
            '<p>Each non-background scale runs ten steps, <code class="tok">100</code> to '
            '<code class="tok">1000</code>. A step is a role, not just a lightness: backgrounds live at the '
            'bottom, borders in the middle, fills and text at the top. Hover and active states move one step up.</p>'
            + steps)),
        ("base", "Base tokens", base_note + color_table(["primary", "secondary", "tertiary", "neutral"])),
        ("backgrounds", "Backgrounds", (
            '<p><code class="tok">background-100</code> is the page and card surface. '
            '<code class="tok">background-200</code> exists only for subtle separation between areas - '
            'never as a general fill.</p>' + color_table(["background-100", "background-200"]))),
        ("gray", "Gray", (
            '<p>Solid gray holds its contrast on any surface - use it for text and opaque fills.</p>'
            + color_table([f"gray-{s}" for s in STEPS]))),
        ("gray-alpha", "Gray alpha", (
            '<p>The translucent companion scale. Because it layers over whatever sits underneath, it is the '
            'right choice for borders, dividers, hover tints, and overlays.</p>'
            + color_table([f"gray-alpha-{s}" for s in STEPS]))),
        ("accents", "Accent scales", accents_html),
        ("p3", "Wide gamut (P3)", p3_html),
    ]


def type_specimen_rows(keys):
    rows = []
    for k in keys:
        t = TY[k]
        fam = t["fontFamily"]
        ff = "var(--font-mono)" if fam == "Geist Mono" else "var(--font-sans)"
        ls = t.get("letterSpacing", "")
        style = (f"font-family:{ff};font-size:{t['fontSize']};font-weight:{t['fontWeight']};"
                 f"line-height:{t['lineHeight']};letter-spacing:{ls or 'normal'}")
        spec = f"{fam} · {t['fontWeight']} · {t['fontSize'][:-2]}/{t['lineHeight'][:-2]}" + (f" · {ls}" if ls else "")
        rows.append(f'<div class="type-row"><div class="type-specimen" style="{style}">'
                    f'The quick brown fox jumps over the lazy dog</div>'
                    f'<div class="type-meta"><code class="tok">{esc(k)}</code>'
                    f'<span class="type-spec">{esc(spec)}</span></div></div>')
    return f'<div class="type-list">{"".join(rows)}</div>'


def sec_typography():
    keys = list(TY.keys())
    groups = {
        "headings": [k for k in keys if k.startswith("heading-")],
        "buttons": [k for k in keys if k.startswith("button-")],
        "labels": [k for k in keys if k.startswith("label-")],
        "copy": [k for k in keys if k.startswith("copy-")],
    }
    all_rows = []
    for k in keys:
        t = TY[k]
        all_rows.append(
            f'<tr><td class="mono"><code class="tok">{esc(k)}</code></td><td>{esc(t["fontFamily"])}</td>'
            f'<td class="mono">{esc(t["fontSize"])}</td><td class="mono">{esc(t["fontWeight"])}</td>'
            f'<td class="mono">{esc(t["lineHeight"])}</td><td class="mono">{esc(t.get("letterSpacing", "0"))}</td></tr>')
    return [
        ("families", "Families", (
            '<p><b>Geist Sans</b> sets interface text and prose; <b>Geist Mono</b> sets code, data, and anything '
            'that benefits from tabular figures. Both are open-source typefaces released under the SIL Open Font '
            'License. Two weights per view is the ceiling.</p>')),
        ("headings", "Headings", (
            '<p><code class="tok">heading-72</code> down to <code class="tok">heading-14</code> title pages and '
            'sections. Letter spacing tightens as the size grows, so the big sizes stay dense and intentional.</p>'
            + type_specimen_rows(groups["headings"]))),
        ("buttons", "Buttons", (
            '<p>Medium-weight labels for buttons and compact controls.</p>'
            + type_specimen_rows(groups["buttons"]))),
        ("labels", "Labels", (
            '<p>Single-line, scannable text: navigation, form labels, table headers, metadata. The '
            '<code class="tok">-mono</code> variants keep the same metrics in Geist Mono.</p>'
            + type_specimen_rows(groups["labels"]))),
        ("copy", "Copy", (
            '<p>Multi-line body text with taller line heights. <code class="tok">copy-14</code> and '
            '<code class="tok">label-14</code> cover most interface text.</p>'
            + type_specimen_rows(groups["copy"]))),
        ("all", "All tokens", tbl(
            ["Token", "Family", "Size", "Weight", "Line height", "Letter spacing"], all_rows)),
    ]


def sec_layout():
    bars = []
    for k, v in SP.items():
        if k == "base":
            continue
        px = int(v[:-2])
        pct = max(px / 96 * 100, 3)
        bars.append(f'<div class="bar-row"><span class="bar-name"><code class="tok">spacing-{esc(k)}</code></span>'
                    f'<span class="bar-val">{esc(v)}</span>'
                    f'<span class="bar-track"><span class="bar-fill" style="width:{pct:.1f}%"></span></span>'
                    f'<span class="bar-desc">{esc(SPACE_USE.get(k, ""))}</span></div>')
    bp_rows = [f'<tr><td class="mono"><code class="tok">{n}</code></td><td class="mono">{copyb(v)}</td></tr>'
               for n, v in BREAKPOINTS]
    return [
        ("spacing", "Spacing", (
            '<p>Everything sits on a <b>4px base</b> (<code class="tok">spacing-base</code>). The named steps '
            f'multiply it: 4, 8, 12, 16, 24, 32, 40, 64, 96.</p><div class="bar-list">{"".join(bars)}</div>')),
        ("rhythm", "Rhythm", callout("The three-step rhythm", [
            "<b>8px</b> between elements inside a group.",
            "<b>16px</b> between groups.",
            "<b>32-40px</b> between sections.",
            "Cards take <b>24px</b> padding - 16px when compact, 32px for hero areas.",
        ])),
        ("container", "Container", (
            '<p>Content centers in a <b>1200px</b> column, with side padding that grows at wider breakpoints. '
            'Every layout must hold up on both mobile and desktop.</p>')),
        ("breakpoints", "Breakpoints", tbl(["Token", "Min width"], bp_rows)),
    ]


def sec_elevation():
    tiers = [
        ("card", "Card", "Raised cards and subtle lifts. Tooltips use this tier too."),
        ("menu", "Menu", "Popovers, dropdown menus, and other transient surfaces."),
        ("modal", "Modal", "Modals and dialogs - the deepest shadow in the system."),
    ]
    cells = []
    for key, name, desc in tiers:
        cells.append(
            f'<div><div class="elev-card" style="box-shadow:var(--shadow-{key})"></div>'
            f'<div class="demo-head"><code class="tok">shadow-{key}</code></div>'
            f'<div class="demo-desc">{esc(desc)}</div>'
            f'<div class="elev-vals"><span>L {esc(SHADOWS["light"][key])}</span>'
            f'<span>D {esc(SHADOWS["dark"][key])}</span></div></div>')
    return [
        ("approach", "Borders first", (
            '<p>Hierarchy comes from borders and tonal surfaces before shadows, so the shadows that remain are '
            'quiet. The cards below use the live values - flip the theme to compare. Pair each tier with the '
            'matching radius from <a href="shapes.html">Shapes</a>.</p>')),
        ("tiers", "Tiers", f'<div class="elev-grid">{"".join(cells)}</div>'),
    ]


def sec_motion():
    bars = []
    for name, ms, desc in DURATIONS:
        fill = (f'<span class="bar-fill" style="width:{max(ms / 300 * 100, 2):.0f}%"></span>'
                if ms else '<span class="bar-zero">0</span>')
        bars.append(f'<div class="bar-row"><span class="bar-name"><code class="tok">{name}</code></span>'
                    f'<span class="bar-val">{ms}ms</span>'
                    f'<span class="bar-track">{fill}</span>'
                    f'<span class="bar-desc">{esc(desc)}</span></div>')
    ez = (f'<div class="ez-row"><div class="ez-meta"><code class="tok">ease</code>'
          f'<div class="ez-desc">One springy curve for everything that moves - a fast start with a slight '
          f'overshoot at the end.</div><div class="ez-curve">{copyb(EASING)}</div></div>'
          f'<div class="ez-track"><span class="ez-dot" style="animation-timing-function:{EASING}"></span></div></div>')
    return [
        ("principles", "Principles", (
            '<p>Motion exists to clarify a change, never to decorate. Most interactions read best '
            '<b>instantly - 0ms is a valid duration</b> and often the right one. When something genuinely moves or '
            'reveals, keep it short and physical.</p>')),
        ("durations", "Durations", f'<div class="bar-list">{"".join(bars)}</div>'),
        ("easing", "Easing", ez),
        ("reduced", "Reduced motion", callout("Always honor the user", [
            'Respect <code class="tok">prefers-reduced-motion</code>: drop every nonessential animation.',
            "No loops, no attention-grabbing movement.",
        ])),
    ]


def sec_shapes():
    shapes = [
        ("sm", "Everyday surfaces - buttons, inputs, cards.", ""),
        ("md", "Menus and modals.", ""),
        ("lg", "Fullscreen and near-fullscreen surfaces.", ""),
        ("full", "Pills, avatars, and circular controls.", "pill"),
    ]
    cells = []
    for k, desc, extra in shapes:
        cells.append(
            f'<div><div class="demo-box {extra}" style="border-radius:var(--rounded-{k})"></div>'
            f'<div class="demo-head"><code class="tok">rounded-{k}</code>'
            f'<span class="demo-val">{esc(RD[k])}</span></div>'
            f'<div class="demo-desc">{esc(desc)}</div></div>')
    return [
        ("radii", "Radii", (
            '<p>Radii stay tight and consistent.</p>'
            f'<div class="demo-grid">{"".join(cells)}</div>')),
        ("rules", "Rules", callout("Keep corners coherent", [
            "One radius family per view - never mix rounded and sharp corners.",
            "Bigger surface, bigger radius: 6px controls, 12px menus and modals, 16px fullscreen.",
            '<code class="tok">rounded-full</code> is reserved for pills, avatars, and circles.',
        ])),
    ]


def comp_spec_table(names):
    heads = ["Token", "Background", "Text", "Type", "Radius", "Padding", "Height"]
    rows = []
    for n in names:
        c = CO[n]
        rows.append(
            f'<tr><td class="mono"><code class="tok">{esc(n)}</code></td>'
            f'<td class="mono">{esc(c.get("backgroundColor", "transparent"))}</td>'
            f'<td class="mono">{esc(c.get("textColor", "-"))}</td>'
            f'<td class="mono">{esc(c.get("typography", "-"))}</td>'
            f'<td class="mono">{esc(c.get("rounded", "-"))}</td>'
            f'<td class="mono">{esc(c.get("padding", "-"))}</td>'
            f'<td class="mono">{esc(c.get("height", "-"))}</td></tr>')
    return tbl(heads, rows)


def sec_components():
    buttons_demo = (
        '<div class="demo-panel">'
        '<button class="gbtn gbtn-primary" type="button">Deploy Project</button>'
        '<button class="gbtn gbtn-secondary" type="button">View Logs</button>'
        '<button class="gbtn gbtn-tertiary" type="button">Cancel</button>'
        '<button class="gbtn gbtn-error" type="button">Delete Member</button>'
        '</div>')
    sizes_demo = (
        '<div class="demo-panel">'
        '<button class="gbtn gbtn-primary gbtn-sm" type="button">Small · 32px</button>'
        '<button class="gbtn gbtn-primary" type="button">Medium · 40px</button>'
        '<button class="gbtn gbtn-primary gbtn-lg" type="button">Large · 48px</button>'
        '</div>')
    disabled_demo = (
        '<div class="demo-panel">'
        '<button class="gbtn" type="button" disabled>Disabled</button>'
        '<button class="gbtn gbtn-secondary" type="button">Tab here to see the focus ring</button>'
        '</div>')
    inputs_demo = (
        '<div class="demo-panel">'
        '<input class="ginput ginput-sm" type="text" placeholder="Small · 32px" aria-label="Small input">'
        '<input class="ginput" type="text" placeholder="Medium · 40px" aria-label="Medium input">'
        '<input class="ginput ginput-lg" type="text" placeholder="Large · 48px" aria-label="Large input">'
        '</div>')
    lf, df = FOCUS["light"], FOCUS["dark"]
    states = (
        '<p>States move along the color scale instead of inventing new values: a <code class="tok">100</code> '
        'fill becomes <code class="tok">200</code> on hover and <code class="tok">300</code> on active; borders '
        'step <code class="tok">400</code> to <code class="tok">500</code> to <code class="tok">600</code>. '
        'Solid fills step one up on hover.</p>'
        + callout("Disabled and focus", [
            'Disabled: <code class="tok">gray-100</code> fill, <code class="tok">gray-700</code> text, '
            '<code class="tok">gray-400</code> border, <code class="tok">not-allowed</code> cursor.',
            'Focus is a two-layer ring: a 2px gap in the surface color, then a 2px blue ring. Light: '
            f'<code class="tok">box-shadow: 0 0 0 2px {lf[0]}, 0 0 0 4px {lf[1]}</code> ({lf[2]}).',
            f'Dark: <code class="tok">box-shadow: 0 0 0 2px {df[0]}, 0 0 0 4px {df[1]}</code> ({df[2]}).',
            'Every interactive element shows the ring at <code class="tok">:focus-visible</code>.',
        ]))
    return [
        ("buttons", "Buttons", (
            '<p>Four variants, all live below and specified entirely by tokens. Primary is for the single most '
            'important action on a view; secondary is the default; tertiary is low-emphasis; error is for '
            'destructive actions only.</p>'
            + buttons_demo + comp_spec_table(["button-primary", "button-secondary", "button-tertiary", "button-error"])
            + '<h3 id="button-sizes">Sizes</h3>'
            + sizes_demo + comp_spec_table(["button-small", "button-large"]))),
        ("inputs", "Inputs", (
            '<p>Text fields share the button height scale and radius.</p>'
            + inputs_demo + comp_spec_table(["input", "input-small", "input-large"]))),
        ("states", "States", states + disabled_demo),
    ]


def sec_voice():
    return [
        ("principles", "Principles", (
            '<p>Copy is part of the design. Keep it precise, verb-first, and free of filler - the interface '
            'should read the way it works.</p>')),
        ("rules", "Rules", callout("Writing interface copy", [
            "<b>Case.</b> Title Case for buttons, labels, titles, and tabs; sentence case for body, helper "
            "text, and toasts.",
            '<b>Actions.</b> Pair a verb with an object - <code class="tok">Deploy Project</code>, '
            '<code class="tok">Delete Member</code> - never a bare <code class="tok">OK</code> or '
            '<code class="tok">Confirm</code>.',
            "<b>Errors.</b> Say what happened, then what to do next.",
            "<b>Toasts.</b> Name the thing that changed, drop the trailing period, and never write "
            '<code class="tok">successfully</code>.',
            "<b>Empty states.</b> Point at the first action the user should take.",
            '<b>Progress.</b> Present participle plus an ellipsis: <code class="tok">Deploying…</code>, '
            '<code class="tok">Saving…</code>.',
            "<b>Mechanics.</b> Numerals for counts, curly quotes, a real ellipsis character; skip "
            '<code class="tok">please</code> and marketing superlatives.',
        ])),
    ]


def sec_guidelines():
    return [
        ("do", "Do", callout("Always", [
            'Rank information with the gray scale: <code class="tok">1000</code> primary text, '
            '<code class="tok">900</code> secondary, <code class="tok">700</code> disabled.',
            "Reserve solid accent color for state and the single most important action on a view.",
            "Hold WCAG AA contrast - 4.5:1 for body text.",
            'Show the focus ring on every interactive element at <code class="tok">:focus-visible</code>; '
            "never remove an outline without a visible replacement.",
            "Apply typography tokens instead of hand-setting size, weight, or line height.",
        ], "accent")),
        ("dont", "Don't", callout("Never", [
            "Signal state with color alone - pair it with an icon or a text label.",
            'Use <code class="tok">background-200</code> as a general fill; it exists for subtle separation only.',
            "Mix rounded and sharp corners, or more than two font weights, in one view.",
            'Swap <code class="tok">gray-*</code> for <code class="tok">background-*</code>; they are '
            "separate scales.",
        ], "danger")),
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
        'The two themes share names, so code can switch themes by swapping values only.</p>'
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


# ---- pages ----------------------------------------------------------------------
PAGES = [
    {"file": "index.html", "title": "Introduction", "h1": "mm-ds", "group": "Getting started",
     "lead": "A Geist-based design system for mm products: minimal, high-contrast, light and dark. "
             "Token-for-token aligned with Vercel's public Geist reference, and readable by people and AI "
             "agents alike.",
     "desc": "mm-ds - a Geist-based design system: tokens, typography, components, and machine-readable specs.",
     "sections": sec_index},
    {"file": "colors.html", "title": "Colors", "group": "Foundations",
     "lead": "Ten-step scales where every step has a job. Solid gray for text and fills, translucent gray-alpha "
             "for borders and overlays, and seven accent scales that carry meaning.",
     "desc": "The mm-ds color system - gray, gray-alpha, and seven accent scales in light and dark, with P3 "
             "variants.",
     "sections": sec_colors},
    {"file": "typography.html", "title": "Typography", "group": "Foundations",
     "lead": "Geist Sans for interface and prose, Geist Mono for code and data. Every size, weight, and tracking "
             "value ships as a token.",
     "desc": "mm-ds typography - heading, label, copy, and button tokens in Geist Sans and Geist Mono.",
     "sections": sec_typography},
    {"file": "layout.html", "title": "Layout", "group": "Foundations",
     "lead": "A 4px spacing scale, a three-step rhythm, a 1200px content column, and five breakpoints.",
     "desc": "mm-ds layout - the 4px spacing scale, rhythm rules, container width, and breakpoints.",
     "sections": sec_layout},
    {"file": "elevation.html", "title": "Elevation", "group": "Foundations",
     "lead": "Depth comes from borders and tonal surfaces first. Three quiet shadow tiers cover cards, menus, "
             "and modals.",
     "desc": "mm-ds elevation - three box-shadow tiers for cards, menus, and modals in light and dark.",
     "sections": sec_elevation},
    {"file": "motion.html", "title": "Motion", "group": "Foundations",
     "lead": "Instant by default. When motion earns its place, it is short, physical, and rides a single curve.",
     "desc": "mm-ds motion - durations and the one easing curve, with reduced-motion rules.",
     "sections": sec_motion},
    {"file": "shapes.html", "title": "Shapes", "group": "Foundations",
     "lead": "Tight radii - 6, 12, 16, and full - matched to surface size, one family per view.",
     "desc": "mm-ds shapes - the four radius tokens and the rules for applying them.",
     "sections": sec_shapes},
    {"file": "components.html", "title": "Components", "group": "Patterns",
     "lead": "Buttons and inputs as token recipes: variants, sizes, and states - all rendered live from the "
             "same variables this site ships.",
     "desc": "mm-ds components - button and input recipes with sizes, states, and the focus ring.",
     "sections": sec_components},
    {"file": "voice.html", "title": "Voice & content", "group": "Patterns",
     "lead": "Interface copy is part of the design: precise, verb-first, and free of filler.",
     "desc": "mm-ds voice and content - the writing rules for interface copy.",
     "sections": sec_voice},
    {"file": "guidelines.html", "title": "Do's & don'ts", "group": "Patterns",
     "lead": "The short list that keeps every surface consistent, accessible, and unmistakably on-system.",
     "desc": "mm-ds do's and don'ts - the rules that keep surfaces consistent and accessible.",
     "sections": sec_guidelines},
    {"file": "ai.html", "title": "AI & agents", "group": "Reference",
     "lead": "The whole system ships as two markdown files an agent can read in one pass - one per theme, "
             "same token names.",
     "desc": "mm-ds for AI - machine-readable design.md and design.dark.md specs and how to use them.",
     "sections": sec_ai},
]

NAV = [
    ("Getting started", [("index.html", "Introduction")]),
    ("Foundations", [("colors.html", "Colors"), ("typography.html", "Typography"), ("layout.html", "Layout"),
                     ("elevation.html", "Elevation"), ("motion.html", "Motion"), ("shapes.html", "Shapes")]),
    ("Patterns", [("components.html", "Components"), ("voice.html", "Voice & content"),
                  ("guidelines.html", "Do's & don'ts")]),
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
            out.append(f'<a href="{href}"{cur}>{esc(label)}{ext}</a>')
    return "\n      ".join(out)


def page_html(page, prev_pg, next_pg):
    title = "mm-ds · Geist-based design system" if page["file"] == "index.html" else f'{page["title"]} · mm-ds'
    sections = page["sections"]()
    body = []
    for sid, heading, inner in sections:
        body.append(f'<section id="{sid}"><h2>{heading}'
                    f'<a class="hlink" href="#{sid}" aria-label="Link to {esc(heading)}">#</a></h2>\n{inner}\n</section>')
    toc = "\n      ".join(f'<a href="#{sid}">{esc(h)}</a>' for sid, h, _ in sections)
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
<header class="mobilebar">
  <button id="navBtn" aria-label="Open navigation"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></button>
  <span class="mobilebar-brand">mm-ds</span>
  <button data-search-open aria-label="Search">{SEARCH_SVG}</button>
</header>
<div class="shell">
  <nav class="sidebar" id="sidebar" aria-label="Site navigation">
    <a class="brand" href="index.html">
      <span class="brand-mark" aria-hidden="true">m</span>
      <span><span class="brand-name">mm-ds</span><span class="brand-sub">Design System</span></span>
    </a>
    <button class="searchbtn" type="button" data-search-open>
      {SEARCH_SVG}<span class="grow">Search…</span><kbd>⌘K</kbd>
    </button>
    <div class="nav-scroll">
      {nav_html(page["file"])}
    </div>
    <div class="sidebar-foot">
      <span class="ver">alpha</span>
      <div class="theme-switch" role="radiogroup" aria-label="Color theme">
        <button type="button" data-theme="system" aria-checked="false" aria-label="System theme" title="System"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" aria-hidden="true"><rect x="3" y="5" width="18" height="12" rx="2" stroke="currentColor" stroke-width="2"/><path d="M9 20h6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></button>
        <button type="button" data-theme="light" aria-checked="false" aria-label="Light theme" title="Light"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="12" cy="12" r="4" stroke="currentColor" stroke-width="2"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M19.1 4.9L17 7M7 17l-2.1 2.1" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></button>
        <button type="button" data-theme="dark" aria-checked="false" aria-label="Dark theme" title="Dark"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M21 13A8.5 8.5 0 1 1 11 3a7 7 0 0 0 10 10z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg></button>
      </div>
    </div>
  </nav>
  <div class="backdrop" id="navBackdrop"></div>
  <main class="main" id="content">
    <article class="doc">
      <p class="eyebrow">{esc(page["group"])}</p>
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
    <aside class="toc" aria-label="On this page">
      <div class="toc-title">On this page</div>
      {toc}
    </aside>
  </main>
</div>
<div class="search-modal" id="searchModal" hidden>
  <div class="search-scrim"></div>
  <div class="search-panel" role="dialog" aria-modal="true" aria-label="Search">
    <div class="search-head">
      {SEARCH_SVG}
      <input id="searchInput" type="text" placeholder="Search pages and tokens…" autocomplete="off" spellcheck="false">
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
    per = {
        "light": {"overlay": "rgba(0, 0, 0, 0.4)", "success": "var(--c-green-800)",
                  "material": "rgba(255, 255, 255, 0.8)", "focus": "var(--c-blue-700)"},
        "dark": {"overlay": "rgba(0, 0, 0, 0.6)", "success": "var(--c-green-900)",
                 "material": "rgba(0, 0, 0, 0.75)", "focus": "var(--c-blue-900)"},
    }[theme]
    lines = [
        "--bg-1: var(--c-background-100)",
        "--bg-2: var(--c-background-200)",
        "--bg-3: var(--c-gray-100)",
        "--bg-elevated: var(--c-background-100)",
        "--bg-hover: var(--c-gray-alpha-100)",
        f"--bg-overlay: {per['overlay']}",
        "--bg-accent: var(--c-blue-700)",
        "--bg-accent-subtle: var(--c-blue-100)",
        "--text-primary: var(--c-gray-1000)",
        "--text-secondary: var(--c-gray-900)",
        "--text-tertiary: var(--c-gray-700)",
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
        ix.append({"t": p["title"], "k": "Page", "p": p["file"], "v": ""})

    def anchor(name):
        if name.startswith("background"):
            return "colors.html#backgrounds"
        if name.startswith("gray-alpha"):
            return "colors.html#gray-alpha"
        if name.startswith("gray"):
            return "colors.html#gray"
        for a in ACCENTS:
            if name.startswith(a):
                return f"colors.html#{a}"
        return "colors.html#base"

    for name in LC:
        if name.endswith("-p3"):
            continue
        ix.append({"t": name, "k": "Color", "p": anchor(name), "v": f"{LC[name]} · {DC[name]}", "c": LC[name]})
    for name, t in TY.items():
        ix.append({"t": name, "k": "Typography", "p": "typography.html#all",
                   "v": f"{t['fontSize'][:-2]}/{t['lineHeight'][:-2]} · {t['fontWeight']}"})
    for k, v in SP.items():
        ix.append({"t": f"spacing-{k}", "k": "Spacing", "p": "layout.html#spacing", "v": v})
    for n, v in BREAKPOINTS:
        ix.append({"t": f"breakpoint-{n}", "k": "Layout", "p": "layout.html#breakpoints", "v": v})
    for k, v in RD.items():
        ix.append({"t": f"rounded-{k}", "k": "Shapes", "p": "shapes.html#radii", "v": v})
    for k in SHADOWS["light"]:
        ix.append({"t": f"shadow-{k}", "k": "Elevation", "p": "elevation.html#tiers", "v": ""})
    for name, c in CO.items():
        ix.append({"t": name, "k": "Component",
                   "p": "components.html#buttons" if "button" in name else "components.html#inputs",
                   "v": f"h {c.get('height', '')}"})
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
