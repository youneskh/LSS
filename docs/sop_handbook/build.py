# -*- coding: utf-8 -*-
"""Build the Life Sciences Suite SOP handbook (French and English PDFs).

Usage (from this directory, with the Python environment that has
``playwright`` and ``pypdf``)::

    python build.py            # both languages
    python build.py fr         # one language

Pipeline:
1. content/*.py hold the text (both languages side by side);
2. diagrams.py draws the SVG figures; states.py holds the lifecycles read
   from the installed modules;
3. the book is rendered to HTML, printed to PDF by Chromium (two passes so
   that the table of contents carries real page numbers), and a cover page
   is prepended.
"""
import datetime
import html
import os
import re
import sys

from pypdf import PdfReader, PdfWriter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import diagrams  # noqa: E402
from states import flow_labels  # noqa: E402
from content import BOOK  # noqa: E402

BUILD = os.path.join(HERE, "build")
ASSETS = os.path.join(HERE, "assets")
CHROME = os.environ.get("CHROME_PATH", "/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
os.makedirs(BUILD, exist_ok=True)

UI = {
    "en": {
        "book": "Life Sciences Suite — SOP Handbook",
        "sections": ["Objective", "Scope", "Responsibilities", "Definitions", "Workflow in the software",
                     "Procedure", "Controls enforced by the software", "Good practices",
                     "Pitfalls to avoid", "Records and evidence", "Performance indicators",
                     "References", "Demonstration"],
        "meta": ["Module", "Menu", "Owner (suggested)", "Related SOPs", "Version", "Effective date",
                 "Approved by"],
        "role": "Role (software group)", "resp": "Responsibility",
        "term": "Term", "def": "Definition",
        "toc": "Contents", "part": "Part", "fig": "Figure", "screen": "Screenshot",
        "shot_note": "Screenshot of the running software (Odoo 19.0 Community, LS modules, demonstration data).",
        "to_fill": "to be completed by QA",
    },
    "fr": {
        "book": "Life Sciences Suite — Manuel des SOP",
        "sections": ["Objet", "Domaine d'application", "Responsabilités", "Définitions",
                     "Déroulement dans le logiciel", "Mode opératoire", "Contrôles imposés par le logiciel",
                     "Bonnes pratiques", "Erreurs à éviter", "Enregistrements et preuves",
                     "Indicateurs de performance", "Références", "Démonstration"],
        "meta": ["Module", "Menu", "Propriétaire (suggéré)", "SOP liées", "Version", "Date d'application",
                 "Approuvé par"],
        "role": "Rôle (groupe du logiciel)", "resp": "Responsabilité",
        "term": "Terme", "def": "Définition",
        "toc": "Sommaire", "part": "Partie", "fig": "Figure", "screen": "Capture d'écran",
        "shot_note": "Capture d'écran du logiciel en fonctionnement (Odoo 19.0 Community, modules LS, données de démonstration).",
        "to_fill": "à compléter par l'AQ",
    },
}


# ---------------------------------------------------------------------------
# Light markup: [[Button]]  {{Menu ▸ Path}}  **bold**  `code`  *italic*
# ---------------------------------------------------------------------------
def md(text):
    if text is None:
        return ""
    t = html.escape(str(text), quote=False)
    t = re.sub(r"\[\[(.+?)\]\]", r"<kbd>\1</kbd>", t)
    t = re.sub(r"\{\{(.+?)\}\}", r'<span class="menu">\1</span>', t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", t)
    return t


def paras(text):
    if not text:
        return ""
    if isinstance(text, (list, tuple)):
        return "".join(f"<p>{md(x)}</p>" for x in text)
    return "".join(f"<p>{md(x)}</p>" for x in str(text).split("\n\n"))


def ul(items, cls=""):
    if not items:
        return ""
    c = f' class="{cls}"' if cls else ""
    return f"<ul{c}>" + "".join(f"<li>{md(i)}</li>" for i in items) + "</ul>"


class Book:
    def __init__(self, lang):
        self.lang = lang
        self.ui = UI[lang]
        self.toc = []  # (level, anchor, label, code)
        self.fig = 0
        self.out = []
        self.markers = True

    def anchor(self, aid):
        if not self.markers:
            return ""
        return f'<span class="marker">@@A:{aid}@@</span>'

    def figure_svg(self, svg, caption):
        self.fig += 1
        return (f'<figure>{svg}<figcaption>{self.ui["fig"]} {self.fig} — {md(caption)}</figcaption></figure>')

    def figure_img(self, name, caption):
        path = os.path.join(ASSETS, "screens", name + ".jpg")
        if not os.path.exists(path):
            return ""
        self.fig += 1
        return (f'<figure><img src="file://{path}"/><figcaption>{self.ui["fig"]} {self.fig} — '
                f'{md(caption)} <span class="small">({self.ui["shot_note"]})</span></figcaption></figure>')

    def schematic(self, key, caption):
        return self.figure_svg(diagrams.SCHEMATICS[key](self.lang), caption)

    def flow(self, flow_id, caption):
        model, main, side = flow_labels(flow_id)
        note = (f"Model: {model}" if self.lang == "en" else f"Modèle : {model}")
        svg = diagrams.state_flow(main, side, self.lang, note)
        return self.figure_svg(svg, caption)

    # -- blocks -------------------------------------------------------------
    def render_block(self, b):
        """Generic blocks used in front matter, openers and annexes."""
        kind = b[0]
        if kind == "h2":
            aid = b[2] if len(b) > 2 else None
            if aid:
                self.toc.append((2, aid, b[1], ""))
                return f"<h2>{self.anchor(aid)}{md(b[1])}</h2>"
            return f"<h2>{md(b[1])}</h2>"
        if kind == "h3":
            return f"<h3>{md(b[1])}</h3>"
        if kind == "p":
            return paras(b[1])
        if kind == "ul":
            return ul(b[1])
        if kind == "checks":
            return ul(b[1], "checks")
        if kind == "box":
            _, cls, title, content = b
            inner = ul(content, "checks") if isinstance(content, list) else paras(content)
            return f'<div class="box {cls}"><h4>{md(title)}</h4>{inner}</div>'
        if kind == "table":
            _, head, rows = b[:3]
            cls = b[3] if len(b) > 3 else ""
            h = "".join(f"<th>{md(x)}</th>" for x in head)
            r = "".join("<tr>" + "".join(f"<td>{md(c)}</td>" for c in row) + "</tr>" for row in rows)
            return f'<table class="{cls}"><thead><tr>{h}</tr></thead><tbody>{r}</tbody></table>'
        if kind == "schematic":
            return self.schematic(b[1], b[2])
        if kind == "flow":
            return self.flow(b[1], b[2])
        if kind == "shot":
            return self.figure_img(b[1], b[2])
        if kind == "html":
            return b[1]
        if kind == "pagebreak":
            return '<div class="page-break"></div>'
        raise ValueError(kind)

    def chapter(self, ch):
        aid = ch["id"]
        self.toc.append((0, aid, ch[self.lang]["title"], ""))
        parts = [f'<section class="page-break">', f"<h1>{self.anchor(aid)}{md(ch[self.lang]['title'])}</h1>"]
        for b in ch[self.lang]["blocks"]:
            parts.append(self.render_block(b))
        parts.append("</section>")
        return "".join(parts)

    def part_opener(self, part):
        aid = part["id"]
        L = part[self.lang]
        self.toc.append((0, aid, f'{self.ui["part"]} {part["num"]} — {L["title"]}', ""))
        mods = "".join(f"<li>{md(m)}</li>" for m in L.get("modules", []))
        return (f'<section class="part-opener">{self.anchor(aid)}<div class="num">{part["num"]}</div>'
                f'<h1>{md(L["title"])}</h1><p class="lead">{md(L["lead"])}</p>'
                f'<ul class="mods">{mods}</ul></section>')

    def module_intro(self, mod):
        aid = mod["id"]
        L = mod[self.lang]
        self.toc.append((1, aid, L["title"], ""))
        out = [f'<section class="module-intro"><h1>{self.anchor(aid)}{md(L["title"])}</h1>',
               f'<p><span class="tag">{md(mod["tech"])}</span></p>']
        for b in L["blocks"]:
            out.append(self.render_block(b))
        out.append("</section>")
        return "".join(out)

    def sop(self, s):
        L = s[self.lang]
        ui = self.ui
        aid = s["code"].lower()
        self.toc.append((2, aid, L["title"], s["code"]))
        sec = iter(range(1, 30))
        h = []
        h.append(f'<section class="sop"><div class="sop-head">{self.anchor(aid)}<div class="code">{s["code"]}</div>'
                 f'<h1>{md(L["title"])}</h1><div class="mod">{s["module"]}</div></div>')
        m = ui["meta"]
        related = ", ".join(s.get("related", [])) or "—"
        h.append('<table class="meta-table"><tbody>'
                 f'<tr><td class="k">{m[0]}</td><td>{md(s["module"])}</td><td class="k">{m[4]}</td><td><span class="blank"></span></td></tr>'
                 f'<tr><td class="k">{m[1]}</td><td>{md(s.get("menu", "—"))}</td><td class="k">{m[5]}</td><td><span class="blank"></span></td></tr>'
                 f'<tr><td class="k">{m[2]}</td><td>{md(L.get("owner", "—"))}</td><td class="k">{m[6]}</td><td><span class="blank"></span></td></tr>'
                 f'<tr><td class="k">{m[3]}</td><td colspan="3">{md(related)}</td></tr>'
                 '</tbody></table>')

        def head(i):
            return f'<div class="sec"><span class="n">{next(sec)}</span><h3>{ui["sections"][i]}</h3></div>'

        h.append(head(0) + paras(L["objective"]))
        h.append(head(1) + paras(L["scope"]))
        if L.get("roles"):
            rows = "".join(f"<tr><td style='width:36%'><b>{md(r)}</b></td><td>{md(d)}</td></tr>" for r, d in L["roles"])
            h.append(head(2) + f'<table><thead><tr><th>{ui["role"]}</th><th>{ui["resp"]}</th></tr></thead><tbody>{rows}</tbody></table>')
        if L.get("defs"):
            rows = "".join(f"<tr><td style='width:28%'><b>{md(t)}</b></td><td>{md(d)}</td></tr>" for t, d in L["defs"])
            h.append(head(3) + f'<table><thead><tr><th>{ui["term"]}</th><th>{ui["def"]}</th></tr></thead><tbody>{rows}</tbody></table>')
        figs = []
        for f in s.get("flows", []):
            figs.append(self.flow(f[0], f[1][self.lang]))
        for f in s.get("schematics", []):
            figs.append(self.schematic(f[0], f[1][self.lang]))
        if figs:
            h.append(head(4) + "".join(figs))
        steps = "".join(f'<li><b class="st">{md(t)}.</b> {md(d)}</li>' for t, d in L["steps"])
        h.append(head(5) + f'<ol class="steps">{steps}</ol>')
        if L.get("controls"):
            h.append(f'<div class="box ctrl"><h4>{next(sec)}. {ui["sections"][6]}</h4>{ul(L["controls"], "checks")}</div>')
        if L.get("good"):
            h.append(f'<div class="box good"><h4>{next(sec)}. {ui["sections"][7]}</h4>{ul(L["good"], "checks")}</div>')
        if L.get("pitfalls"):
            h.append(f'<div class="box bad"><h4>{next(sec)}. {ui["sections"][8]}</h4>{ul(L["pitfalls"], "checks")}</div>')
        if L.get("records") or L.get("kpis"):
            left = f'<div><div class="sec"><span class="n">{next(sec)}</span><h3>{ui["sections"][9]}</h3></div>{ul(L.get("records", []))}</div>'
            right = f'<div><div class="sec"><span class="n">{next(sec)}</span><h3>{ui["sections"][10]}</h3></div>{ul(L.get("kpis", []))}</div>'
            h.append(f'<div class="two">{left}{right}</div>')
        if s.get("refs"):
            from content.refs import REFS
            items = [REFS[r][self.lang] if r in REFS else r for r in s["refs"]]
            h.append(head(11) + f'<ul class="refs">{"".join(f"<li>{md(i)}</li>" for i in items)}</ul>')
        if L.get("example"):
            h.append(f'<div class="box demo"><h4>{next(sec)}. {ui["sections"][12]}</h4>{paras(L["example"])}</div>')
        for shot in s.get("shots", []):
            h.append(self.figure_img(shot[0], shot[1][self.lang]))
        if L.get("note"):
            h.append(f'<div class="box warn"><h4>{"Attention" if self.lang == "fr" else "Caution"}</h4>{paras(L["note"])}</div>')
        h.append("</section>")
        return "".join(h)

    # -- assembly -----------------------------------------------------------
    def body(self, pages=None):
        self.toc, self.fig = [], 0
        chunks = []
        for item in BOOK:
            kind = item["kind"]
            if kind == "chapter":
                chunks.append(self.chapter(item))
            elif kind == "part":
                chunks.append(self.part_opener(item))
            elif kind == "module":
                chunks.append(self.module_intro(item))
            elif kind == "sop":
                chunks.append(self.sop(item))
        toc_html = self.toc_html(pages)
        front = self.front_toc_position(chunks, toc_html)
        css = open(os.path.join(ASSETS, "handbook.css"), encoding="utf-8").read()
        css = css.replace("url(fonts/", f"url(file://{ASSETS}/fonts/")
        return (f'<!doctype html><html lang="{self.lang}"><head><meta charset="utf-8">'
                f'<title>{self.ui["book"]}</title><style>{css}</style></head><body>{front}</body></html>')

    def front_toc_position(self, chunks, toc_html):
        # the table of contents follows the first chapter ("about this handbook")
        return chunks[0] + toc_html + "".join(chunks[1:])

    def toc_html(self, pages):
        rows = []
        for level, aid, label, code in self.toc:
            p = pages.get(aid, "") if pages else "000"
            c = f'<span class="code">{code}</span>' if code else ""
            rows.append(f'<div class="row lvl{level}"><span class="t">{c}{md(label)}</span>'
                        f'<span class="dots"></span><span class="p">{p}</span></div>')
        return f'<section class="toc page-break"><h1>{self.ui["toc"]}</h1>{"".join(rows)}</section>'


def cover_html(lang):
    ui = UI[lang]
    css = open(os.path.join(ASSETS, "handbook.css"), encoding="utf-8").read()
    css = css.replace("url(fonts/", f"url(file://{ASSETS}/fonts/")
    fr = lang == "fr"
    title = "Manuel des procédures opératoires normalisées" if fr else "Standard Operating Procedures Handbook"
    sub = ("Procédures, démonstrations, bonnes pratiques et schémas pour les 22 modules "
           "Life Sciences Suite et les modules OCA associés — Odoo 19 Community"
           if fr else
           "Procedures, demonstrations, good practices and diagrams for the 22 Life Sciences Suite "
           "modules and the related OCA modules — Odoo 19 Community")
    today = datetime.date.today().isoformat()
    status = "Document de travail — à approuver par l'AQ" if fr else "Working document — for QA approval"
    art = []
    import random
    rnd = random.Random(3)
    for i in range(14):
        x = 120 + i * 11
        art.append(f'<rect x="{x}" y="{rnd.randint(0, 60)}" width="6" height="{rnd.randint(80, 260)}" rx="3" fill="#0F7C80" opacity="{0.15 + (i % 5) * 0.08:.2f}"/>')
    svg = (f'<svg class="band" viewBox="0 0 210 297" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">'
           f'<rect width="210" height="297" fill="#1F3A5F"/>'
           f'<circle cx="190" cy="40" r="80" fill="#244A73"/><circle cx="200" cy="250" r="55" fill="#1A3354"/>'
           f'{"".join(art)}<rect x="0" y="292" width="210" height="5" fill="#C98200"/></svg>')
    return (f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><style>{css}'
            f'@page {{ size: A4; margin: 0; }}</style></head><body><div class="cover">{svg}'
            f'<div class="inner"><div class="kicker">Life Sciences Suite</div><h1>{title}</h1>'
            f'<div class="sub">{sub}</div><div class="lang">{"FRANÇAIS" if fr else "ENGLISH"}</div></div>'
            f'<div class="meta"><span>{"Édition" if fr else "Edition"} {today}</span>'
            f'<span>{status}</span></div>'
            f'</div></body></html>')


FOOTER = ('<div style="width:100%;font-family:DejaVu Sans,sans-serif;font-size:7.5px;color:#6B7280;'
          'padding:0 16mm 0 18mm;display:flex;justify-content:space-between;">'
          '<span>{book}</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>')


def print_pdf(pw_browser, html_str, out, footer=None):
    tmp = out + ".html"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(html_str)
    page = pw_browser.new_page()
    page.goto("file://" + tmp)
    page.wait_for_load_state("load")
    page.evaluate("document.fonts.ready")
    opts = dict(path=out, format="A4", print_background=True, prefer_css_page_size=True, outline=True, tagged=True)
    if footer:
        opts.update(display_header_footer=True, header_template="<span></span>", footer_template=footer,
                    margin={"top": "17mm", "bottom": "18mm", "left": "18mm", "right": "16mm"})
    page.pdf(**opts)
    page.close()
    os.remove(tmp)


def find_markers(pdf_path):
    pages = {}
    reader = PdfReader(pdf_path)
    for i, p in enumerate(reader.pages, start=1):
        text = (p.extract_text() or "").replace("\n", "")
        for m in re.finditer(r"@@A:([a-z0-9_\-]+)@@", text):
            pages.setdefault(m.group(1), i)
    return pages


def build(lang):
    from playwright.sync_api import sync_playwright
    bk = Book(lang)
    body_pdf = os.path.join(BUILD, f"_body_{lang}.pdf")
    footer = FOOTER.format(book=UI[lang]["book"])
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME)
        print_pdf(browser, bk.body(None), body_pdf, footer)
        pages = find_markers(body_pdf)
        missing = [a for _, a, _, _ in bk.toc if a not in pages]
        if missing:
            print("warning: anchors not found:", missing[:10])
        print_pdf(browser, bk.body(pages), body_pdf, footer)
        pages2 = find_markers(body_pdf)
        drift = {a: (pages[a], pages2.get(a)) for a in pages if pages2.get(a) != pages[a]}
        if drift:
            print("page drift after second pass, third pass:", list(drift.items())[:5])
            print_pdf(browser, bk.body(pages2), body_pdf, footer)
            pages = pages2
        # final pass without the invisible markers, then check that each SOP
        # starts on the page announced by the table of contents
        bk.markers = False
        print_pdf(browser, bk.body(pages), body_pdf, footer)
        reader = PdfReader(body_pdf)
        bad = []
        for level, aid, label, code in bk.toc:
            if code and aid in pages:
                text = re.sub(r"\s", "", reader.pages[pages[aid] - 1].extract_text() or "")
                if code not in text:
                    bad.append((code, pages[aid]))
        if bad:
            raise SystemExit(f"TOC check failed for {len(bad)} SOP(s): {bad[:5]}")
        cover_pdf = os.path.join(BUILD, f"_cover_{lang}.pdf")
        print_pdf(browser, cover_html(lang), cover_pdf)
        browser.close()
    name = "LSS_SOP_Handbook_FR.pdf" if lang == "fr" else "LSS_SOP_Handbook_EN.pdf"
    out = os.path.join(BUILD, name)
    w = PdfWriter()
    w.append(cover_pdf)
    w.append(body_pdf, import_outline=True)
    w.add_metadata({"/Title": UI[lang]["book"], "/Author": "Life Sciences Suite project",
                    "/Subject": "Standard Operating Procedures", "/Lang": lang})
    with open(out, "wb") as fh:
        w.write(fh)
    os.remove(cover_pdf)
    os.remove(body_pdf)
    n = len(PdfReader(out).pages)
    print(f"{out}: {n} pages, {os.path.getsize(out) / 1e6:.1f} MB, {len(bk.toc)} TOC entries")
    return out, pages


if __name__ == "__main__":
    langs = sys.argv[1:] or ["fr", "en"]
    for lg in langs:
        build(lg)
