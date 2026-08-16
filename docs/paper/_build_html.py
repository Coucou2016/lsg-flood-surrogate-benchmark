"""Build self-contained manuscript.html from manuscript.md + SciencePlots SVGs."""
from __future__ import annotations

import base64
import html
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
MD_PATH = ROOT / "docs" / "paper" / "manuscript.md"
OUT_PATH = ROOT / "docs" / "paper" / "manuscript.html"
FIG_DIR = ROOT / "outputs" / "figures"

FIGURES = [
    (
        "fig1",
        "fig01_cross_case_csi_rmse_wet_train.svg",
        "Figure 1. Cross-case wet_train CSI and RMSE for LF-only and LSG-Max (H-LSG) on Grp1 folds. "
        "Burnett shows the clearest multi-fidelity CSI/RMSE lift; Carlisle LF is already strong on extent; "
        "Chowilla wet_train depth RMSE collapses under LSG while CSI rises relative to LF.",
    ),
    (
        "fig2",
        "fig02_error_budget_o1o4.svg",
        "Figure 2. O1–O4 dual-path depth RMSE ladders (test split) for Carlisle TS/Max, Chowilla Max, and Burnett Max. "
        "O2−O1 isolates truncation; large O3 on Chowilla/Burnett indicates LF expressibility limits; O4 is total surrogate error.",
    ),
    (
        "fig3",
        "fig03_global_vs_hlsg_ab.svg",
        "Figure 3. Global versus residual H-LSG on Chowilla and Burnett Max Grp1. Wet_train CSI is nearly flat on both cases; "
        "the diagnostic gain is the reduced O2−O1 truncation gap under H-LSG (Chowilla 0.057→0.013; Burnett 0.049→0.009).",
    ),
    (
        "fig4",
        "fig04_uq_calibration_crps_scale.svg",
        "Figure 4. CRPS-scale variance calibration before/after. Carlisle Max: CRPS 0.039→0.028 at s=0.417. "
        "Burnett: CRPS 0.133→0.127 at s=0.604. Chowilla: CRPS essentially flat (2.155→2.155) with coverage moving away from nominal—report honestly.",
    ),
    (
        "fig5a",
        "fig05_spatial_maps_carlisle_E1.svg",
        "Figure 5a. Carlisle event E1 maps including cell-wise P(wet)=P(h≥0.03 m). "
        "Differences are relatively subtle given strong LF extent skill.",
    ),
    (
        "fig5b",
        "fig05_spatial_maps_chowilla_E1.svg",
        "Figure 5b. Chowilla event E1 maps with P(wet) panel. Illustrates the strong-LF / wet-mask tension underlying "
        "the all-cells versus wet_train anti-case.",
    ),
    (
        "fig5c",
        "fig05_spatial_maps_burnett_E1.svg",
        "Figure 5c. Burnett event E1 maps with P(wet) panel. Visual LF→LSG correction aligns with the large CSI/RMSE lift in Table 2.",
    ),
    (
        "fig6",
        "fig06_zoning_wet_correlation_ab.svg",
        "Figure 6. Chowilla Max Grp1 zoning sensitivity: global, residual_kmeans, and wet_correlation (CSI / RMSE). "
        "wet_correlation CSI 0.978 is only slightly above H-LSG 0.976; O2−O1 remains the clearer diagnostic.",
    ),
]


def b64_data_uri(path: pathlib.Path) -> str:
    raw = path.read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")
    if path.suffix.lower() == ".svg":
        return "data:image/svg+xml;base64," + b64
    return "data:image/png;base64," + b64


def inline_fmt(s: str) -> str:
    s = html.escape(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)

    # Italic only outside <code>...</code> so identifiers like coverage_*_active stay intact.
    parts = re.split(r"(<code>.*?</code>)", s)
    for i, part in enumerate(parts):
        if part.startswith("<code>"):
            continue
        parts[i] = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", part)
    s = "".join(parts)

    s = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', s)
    # Mark Chinese placeholder for font fallback styling
    s = s.replace("待补充", '<span class="dai-buchong">待补充</span>')
    s = s.replace("未运行", '<span class="dai-buchong">未运行</span>')
    return s


def flush_table(table_rows: list[str]) -> str:
    rows: list[list[str]] = []
    for r in table_rows:
        cells = [c.strip() for c in r.strip().strip("|").split("|")]
        rows.append(cells)
    if len(rows) >= 2 and all(set(c) <= set("-: ") for c in rows[1]):
        header, body = rows[0], rows[2:]
    else:
        header, body = rows[0], rows[1:]
    parts = [
        "<table>",
        "<thead><tr>" + "".join(f"<th>{html.escape(h)}</th>" for h in header) + "</tr></thead>",
        "<tbody>",
    ]
    for br in body:
        while len(br) < len(header):
            br.append("")
        parts.append(
            "<tr>"
            + "".join(f"<td>{inline_fmt(c)}</td>" for c in br[: len(header)])
            + "</tr>"
        )
    parts.append("</tbody></table>")
    return "\n".join(parts)


def md_to_body(md: str, fig_html: dict[str, str]) -> str:
    lines = md.splitlines()
    out: list[str] = []
    in_table = False
    table_rows: list[str] = []
    in_code = False
    code_buf: list[str] = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        if line.startswith("```"):
            if not in_code:
                in_code = True
                code_buf = []
            else:
                out.append("<pre><code>" + html.escape("\n".join(code_buf)) + "</code></pre>")
                in_code = False
            i += 1
            continue
        if in_code:
            code_buf.append(line)
            i += 1
            continue

        if line.strip().startswith("|") and "|" in line.strip()[1:]:
            if not in_table:
                in_table = True
                table_rows = []
            table_rows.append(line)
            i += 1
            continue
        if in_table:
            out.append(flush_table(table_rows))
            in_table = False
            table_rows = []

        if line.startswith("# "):
            out.append(f"<h1>{inline_fmt(line[2:])}</h1>")
        elif line.startswith("## "):
            title = line[3:].strip()
            out.append(f'<h2 id="{html.escape(title[:40])}">{inline_fmt(title)}</h2>')
        elif line.startswith("### "):
            title = line[4:].strip()
            out.append(f"<h3>{inline_fmt(title)}</h3>")
            if title.startswith("6.1"):
                out.append(fig_html["fig1"])
            elif title.startswith("6.2"):
                out.append(fig_html["fig2"])
            elif title.startswith("6.3"):
                out.append(fig_html["fig3"])
            elif title.startswith("6.5"):
                out.append(fig_html["fig4"])
            elif title.startswith("6.6"):
                out.append(fig_html["fig5a"])
                out.append(fig_html["fig5b"])
                out.append(fig_html["fig5c"])
            elif title.startswith("6.7"):
                out.append(fig_html["fig6"])
        elif line.startswith("---"):
            out.append("<hr/>")
        elif line.strip().startswith(">"):
            quote_lines: list[str] = []
            while i < n and lines[i].strip().startswith(">"):
                quote_lines.append(re.sub(r"^>\s?", "", lines[i].rstrip()))
                i += 1
            out.append(
                '<p class="eq">' + "<br/>".join(inline_fmt(q) for q in quote_lines) + "</p>"
            )
            continue
        elif line.strip() == "":
            out.append("")
        elif line.strip().startswith("- ") or re.match(r"^\d+\. ", line.strip()):
            items: list[str] = []
            ordered = bool(re.match(r"^\d+\. ", line.strip()))
            while i < n and (
                lines[i].strip().startswith("- ") or re.match(r"^\d+\. ", lines[i].strip())
            ):
                it = re.sub(r"^(?:- |\d+\. )", "", lines[i].strip())
                items.append(f"<li>{inline_fmt(it)}</li>")
                i += 1
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>" + "".join(items) + f"</{tag}>")
            continue
        else:
            paras = [line]
            i += 1
            while (
                i < n
                and lines[i].strip()
                and not lines[i].startswith("#")
                and not lines[i].startswith("|")
                and not lines[i].startswith("---")
                and not lines[i].startswith("```")
                and not lines[i].strip().startswith(">")
                and not lines[i].strip().startswith("- ")
                and not re.match(r"^\d+\. ", lines[i].strip())
            ):
                paras.append(lines[i])
                i += 1
            text = " ".join(p.strip() for p in paras)
            out.append(f"<p>{inline_fmt(text)}</p>")
            continue
        i += 1

    if in_table:
        out.append(flush_table(table_rows))
    return "\n".join(out)


CSS = r"""
:root { --text:#111; --muted:#444; --rule:#ccc; --bg:#fff; --accent:#1a365d; }
* { box-sizing: border-box; }
html { font-size: 11pt; }
body {
  margin: 0 auto;
  max-width: 48rem;
  padding: 2.2rem 1.4rem 4rem;
  color: var(--text);
  background: var(--bg);
  font-family: "Times New Roman", Times, "Nimbus Roman", "Liberation Serif",
               "Microsoft YaHei", SimSun, "Songti SC", serif;
  line-height: 1.45;
}
h1 { font-size: 1.55rem; line-height: 1.25; margin: 0 0 0.8rem; color: var(--accent); }
h2 { font-size: 1.22rem; margin: 1.8rem 0 0.7rem; border-bottom: 1px solid var(--rule);
     padding-bottom: 0.25rem; page-break-after: avoid; }
h3 { font-size: 1.05rem; margin: 1.2rem 0 0.45rem; page-break-after: avoid; }
p { margin: 0.55rem 0; text-align: justify; hyphens: auto; }
ul, ol { margin: 0.4rem 0 0.7rem 1.3rem; }
li { margin: 0.2rem 0; }
code { font-family: Consolas, "Courier New", monospace; font-size: 0.92em; }
pre { background: #f7f7f7; padding: 0.7rem; overflow: auto; border: 1px solid var(--rule); }
table { width: 100%; border-collapse: collapse; margin: 0.8rem 0 1rem; font-size: 0.88rem;
        page-break-inside: avoid; }
th, td { border: 1px solid #bbb; padding: 0.28rem 0.35rem; vertical-align: top; }
th { background: #f0f3f7; text-align: left; }
figure { margin: 1.1rem 0 1.4rem; page-break-inside: avoid; }
figure img { width: 100%; height: auto; display: block; }
figcaption { font-size: 0.9rem; color: var(--muted); margin-top: 0.4rem; text-align: left; }
hr { border: 0; border-top: 1px solid var(--rule); margin: 1.2rem 0; }
a { color: #0b3d91; text-decoration: none; }
.dai-buchong { font-family: "Microsoft YaHei", SimSun, "Songti SC", "Times New Roman", serif; }
.eq { display:block; text-align:center; margin: 0.85rem 0; font-style: italic; }
@media print {
  body { max-width: none; padding: 12mm 14mm; font-size: 10.5pt; }
  a { color: inherit; text-decoration: none; }
  h2, h3, figure, table { break-inside: avoid; page-break-inside: avoid; }
}
"""


def main() -> None:
    md = MD_PATH.read_text(encoding="utf-8")
    fig_html: dict[str, str] = {}
    for key, fname, caption in FIGURES:
        uri = b64_data_uri(FIG_DIR / fname)
        fig_html[key] = (
            f'<figure id="{key}">\n'
            f'  <img src="{uri}" alt="{html.escape(caption[:120])}" />\n'
            f"  <figcaption>{html.escape(caption)}</figcaption>\n"
            f"</figure>"
        )
    body = md_to_body(md, fig_html)
    doc = (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8" />\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1" />\n'
        "<title>Where does spatial localization help LSG?</title>\n"
        f"<style>\n{CSS}\n</style>\n"
        "</head>\n"
        f"<body>\n{body}\n</body>\n"
        "</html>\n"
    )
    OUT_PATH.write_text(doc, encoding="utf-8")
    print(f"wrote {OUT_PATH} ({OUT_PATH.stat().st_size} bytes)")
    print(f"img tags: {doc.count('<img ')}")
    print(f"data: URIs: {doc.count('src=\"data:')}")


if __name__ == "__main__":
    main()
