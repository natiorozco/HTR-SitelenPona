"""Gráficas SVG para la batería, sin dependencias externas.

Cada gráfica es un conjunto de paneles (uno por agente) con el mismo eje y.
En cada panel hay una línea por serie (p. ej. un valor de N), con la media
entre semillas y una barra de error de ±1 desviación estándar. Cada serie
lleva color, forma de marcador y etiqueta directa al final de la línea, para
que no dependa solo del color. Al pasar el mouse sobre un punto (abriendo el
SVG en el navegador) se ve el valor exacto.
"""

from html import escape
from typing import Dict, List, Optional, Sequence, Tuple

# Paleta categórica validada (claro / oscuro), en orden fijo.
LIGHT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
DARK = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300"]
MARKERS = ["circle", "square", "triangle", "diamond", "circle", "square"]

STYLE = """
  .bg { fill: #fcfcfb; }
  .t1 { fill: #1a1a19; } .t2 { fill: #52514e; } .t3 { fill: #898781; }
  .grid { stroke: #e1e0d9; stroke-width: 1; }
  .axis { stroke: #c3c2b7; stroke-width: 1; }
  .ref { stroke: #898781; stroke-width: 1; stroke-dasharray: 4 3; }
  %s
  .pt { stroke: #fcfcfb; }
  @media (prefers-color-scheme: dark) {
    .bg { fill: #1a1a19; }
    .t1 { fill: #ffffff; } .t2 { fill: #c3c2b7; } .t3 { fill: #898781; }
    .grid { stroke: #2c2c2a; } .axis { stroke: #383835; }
    %s
    .pt { stroke: #1a1a19; }
  }
  text { font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }
  .pt:hover { stroke-width: 3; }
"""

# (media, desviación, n) por punto
Point = Tuple[float, float, int]


def _series_css(n: int) -> Tuple[str, str]:
    light = " ".join(f".s{i} {{ stroke: {LIGHT[i]}; fill: {LIGHT[i]}; }}" for i in range(n))
    dark = " ".join(f".s{i} {{ stroke: {DARK[i]}; fill: {DARK[i]}; }}" for i in range(n))
    return light, dark


def _marker(kind: str, x: float, y: float, cls: str, tip: str) -> str:
    r = 5
    title = f"<title>{escape(tip)}</title>"
    common = f'class="{cls} pt" stroke-width="2"'
    if kind == "square":
        shape = f'<rect x="{x - r}" y="{y - r}" width="{2 * r}" height="{2 * r}" rx="1" {common}>'
        return shape + title + "</rect>"
    if kind == "triangle":
        pts = f"{x},{y - r - 1} {x - r - 1},{y + r} {x + r + 1},{y + r}"
        return f'<polygon points="{pts}" {common}>{title}</polygon>'
    if kind == "diamond":
        pts = f"{x},{y - r - 1} {x + r + 1},{y} {x},{y + r + 1} {x - r - 1},{y}"
        return f'<polygon points="{pts}" {common}>{title}</polygon>'
    return f'<circle cx="{x}" cy="{y}" r="{r}" {common}>{title}</circle>'


def _nice_max(v: float) -> float:
    if v <= 0:
        return 1.0
    for step in (0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000,
                 10000, 20000, 50000, 100000, 200000, 500000, 1000000):
        if v <= step * 5:
            return step * 5 if v > step * 4 else step * (int(v / step) + 1)
    return v * 1.1


def line_panels(
    path: str,
    title: str,
    subtitle: str,
    x_label: str,
    y_label: str,
    xs: Sequence[int],
    panels: Dict[str, Dict[str, Dict[int, Point]]],
    y_max: Optional[float] = None,
    ref_line: Optional[Tuple[float, str]] = None,
    y_fmt: str = "{:.2f}",
) -> None:
    """Escribe un SVG con un panel por agente.

    panels[agente][serie][x] = (media, desviación, n)
    """
    series_names: List[str] = []
    for per_series in panels.values():
        for s in per_series:
            if s not in series_names:
                series_names.append(s)

    if y_max is None:
        top = max(m + sd for per in panels.values() for pts in per.values() for m, sd, _ in pts.values())
        if ref_line:
            top = max(top, ref_line[0])
        y_max = _nice_max(top)

    pw, ph = 340, 240                    # área de datos de cada panel
    ml, mr, mt, mb = 64, 56, 108, 52      # márgenes
    gap = 40
    W = ml + len(panels) * pw + (len(panels) - 1) * gap + mr
    H = mt + ph + mb

    light, dark = _series_css(len(series_names))
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
           f'role="img" aria-label="{escape(title)}">',
           f"<style>{STYLE % (light, dark)}</style>",
           f'<rect class="bg" width="{W}" height="{H}"/>',
           f'<text class="t1" x="{ml}" y="26" font-size="16" font-weight="600">{escape(title)}</text>',
           f'<text class="t2" x="{ml}" y="46" font-size="12">{escape(subtitle)}</text>']

    # Leyenda en una fila
    lx = ml
    for i, s in enumerate(series_names):
        out.append(_marker(MARKERS[i], lx + 6, 66, f"s{i}", s))
        out.append(f'<text class="t2" x="{lx + 16}" y="70" font-size="12">{escape(s)}</text>')
        lx += 24 + 8 * len(s) + 16

    ticks = 5
    for pi, (agent, per_series) in enumerate(panels.items()):
        x0 = ml + pi * (pw + gap)
        y0 = mt

        def sx(idx):
            return x0 + (idx + 0.5) * pw / len(xs)

        def sy(v):
            return y0 + ph - (v / y_max) * ph

        out.append(f'<text class="t1" x="{x0}" y="{y0 - 8}" font-size="13" font-weight="600">{escape(agent)}</text>')
        for t in range(ticks + 1):
            v = y_max * t / ticks
            y = sy(v)
            out.append(f'<line class="{"axis" if t == 0 else "grid"}" x1="{x0}" x2="{x0 + pw}" y1="{y}" y2="{y}"/>')
            if pi == 0:
                out.append(f'<text class="t3" x="{x0 - 8}" y="{y + 4}" font-size="11" text-anchor="end">'
                           f'{escape(y_fmt.format(v))}</text>')
        for idx, xv in enumerate(xs):
            out.append(f'<text class="t3" x="{sx(idx)}" y="{y0 + ph + 18}" font-size="11" '
                       f'text-anchor="middle">{xv}</text>')
        out.append(f'<text class="t2" x="{x0 + pw / 2}" y="{y0 + ph + 40}" font-size="12" '
                   f'text-anchor="middle">{escape(x_label)}</text>')

        if ref_line:
            ry = sy(ref_line[0])
            out.append(f'<line class="ref" x1="{x0}" x2="{x0 + pw}" y1="{ry}" y2="{ry}"/>')
            out.append(f'<text class="t3" x="{x0 + pw - 2}" y="{ry - 5}" font-size="11" '
                       f'text-anchor="end">{escape(ref_line[1])}</text>')

        end_labels = []                  # (y, x, texto) para separarlas al final
        for si, s in enumerate(series_names):
            pts = per_series.get(s, {})
            coords = [(idx, pts[xv]) for idx, xv in enumerate(xs) if xv in pts]
            if not coords:
                continue
            d = " ".join(f"{'M' if k == 0 else 'L'}{sx(i):.1f},{sy(m):.1f}" for k, (i, (m, _, _)) in enumerate(coords))
            out.append(f'<path d="{d}" class="s{si}" fill="none" stroke-width="2" style="fill:none"/>')
            for i, (m, sd, n) in coords:
                if sd > 0:
                    x = sx(i)
                    out.append(f'<path d="M{x},{sy(min(y_max, m + sd)):.1f} V{sy(max(0, m - sd)):.1f} '
                               f'M{x - 4},{sy(min(y_max, m + sd)):.1f} h8 M{x - 4},{sy(max(0, m - sd)):.1f} h8" '
                               f'class="s{si}" stroke-width="1" opacity="0.6" style="fill:none"/>')
            for i, (m, sd, n) in coords:
                tip = f"{agent}, {s}, {x_label} = {xs[i]}: {y_fmt.format(m)} ± {y_fmt.format(sd)} ({n} semillas)"
                out.append(_marker(MARKERS[si], sx(i), sy(m), f"s{si}", tip))
            # etiqueta directa al final de la línea
            li, (lm, _, _) = coords[-1]
            end_labels.append([sy(lm) + 4, sx(li) + 10, s])

        # Separar etiquetas que caen casi en el mismo punto (mínimo 13 px).
        end_labels.sort()
        for j in range(1, len(end_labels)):
            if end_labels[j][0] - end_labels[j - 1][0] < 13:
                end_labels[j][0] = end_labels[j - 1][0] + 13
        for y, x, s in end_labels:
            out.append(f'<text class="t2" x="{x}" y="{y}" font-size="11">{escape(s)}</text>')

    if panels:
        out.append(f'<text class="t2" x="16" y="{mt + ph / 2}" font-size="12" text-anchor="middle" '
                   f'transform="rotate(-90 16 {mt + ph / 2})">{escape(y_label)}</text>')
    out.append("</svg>")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out) + "\n")
