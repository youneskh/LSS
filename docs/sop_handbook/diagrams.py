# -*- coding: utf-8 -*-
"""SVG diagrams of the SOP handbook.

Two families of diagrams are produced:

* state diagrams, drawn from the state lists that the modules actually
  define (read from the installed database, see ``STATES``);
* explanatory schematics (document pyramid, V-model, OOS phases, ...),
  which illustrate a concept and are captioned as such.

Every function returns an SVG string. Labels are passed per language.
"""
from html import escape

NAVY = "#1F3A5F"
TEAL = "#0F7C80"
AMBER = "#C98200"
RED = "#B03A2E"
GREEN = "#2E7D4F"
GREY = "#6B7280"
LIGHT = "#EEF3F8"
LINE = "#9AA8B8"
FONT = "Source Sans 3, DejaVu Sans, sans-serif"


def _t(x, y, text, size=13, color="#1b1b1b", anchor="middle", weight=400,
       italic=False, lh=1.18):
    """Multi-line text; lines separated by newlines."""
    lines = str(text).split("\n")
    n = len(lines)
    y0 = y - (n - 1) * size * lh / 2
    style = "font-style:italic;" if italic else ""
    out = []
    for i, line in enumerate(lines):
        out.append(
            f'<text x="{x}" y="{y0 + i * size * lh + size * 0.35:.1f}" '
            f'font-family="{FONT}" font-size="{size}" fill="{color}" '
            f'text-anchor="{anchor}" font-weight="{weight}" style="{style}">'
            f'{escape(line)}</text>')
    return "".join(out)


def _svg(w, h, body, title="", max_pct=100):
    style = f' style="max-width:{max_pct:.0f}%"' if max_pct < 100 else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{escape(title)}" class="diagram"{style}>'
            f'<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" '
            f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M0,0 L10,5 L0,10 z" fill="{GREY}"/></marker>'
            f'<marker id="ahn" viewBox="0 0 10 10" refX="9" refY="5" '
            f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M0,0 L10,5 L0,10 z" fill="{NAVY}"/></marker></defs>'
            f'{body}</svg>')


def _box(x, y, w, h, fill, stroke=None, rx=8, dash=False):
    d = ' stroke-dasharray="5,4"' if dash else ""
    s = stroke or fill
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
            f'fill="{fill}" stroke="{s}" stroke-width="1.4"{d}/>')


def _arrow(x1, y1, x2, y2, color=GREY, dash=False, marker="ah", width=1.6):
    d = ' stroke-dasharray="5,4"' if dash else ""
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" '
            f'stroke-width="{width}"{d} marker-end="url(#{marker})"/>')


def _path(d, color=GREY, dash=False, marker="ah", width=1.6):
    da = ' stroke-dasharray="5,4"' if dash else ""
    return (f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"'
            f'{da} marker-end="url(#{marker})"/>')


# ---------------------------------------------------------------------------
# State diagrams
# ---------------------------------------------------------------------------
TERMINAL_BAD = {"cancelled", "rejected", "withdrawn", "refused", "declined",
                "disqualified", "terminated", "decommissioned", "destroyed",
                "failed", "missed", "not_achieved", "discrepancy", "expired"}
SIDE = TERMINAL_BAD | {"superseded", "obsolete", "suspended", "on_hold",
                       "quarantined", "maintenance", "notice", "deficiency",
                       "blocked", "removed", "restricted", "out_of_service",
                       "retired", "escalated", "revoked", "expiring",
                       "under_revision", "disposed", "archived",
                       "conditional", "out_of_specification", "wont_answer",
                       "sampled", "returned", "disaggregated"}


def state_flow(main, side=(), lang="en", note=""):
    """Draw a lifecycle.

    main: list of (key, en_label, fr_label) on the nominal path.
    side: list of (key, en_label, fr_label) exits shown underneath.
    In the French handbook the software label (English) is kept, because
    the interface is in English, and the French meaning is added in italics.
    """
    per_row = 5 if len(main) > 5 else len(main)
    cw, ch, gap = 176, 58, 22
    rows = (len(main) + per_row - 1) // per_row
    cols = max(per_row, min(len(side), 5))
    width = cols * cw + (cols - 1) * gap + 20
    side_h = 0
    if side:
        side_rows = (len(side) + 4) // 5
        side_h = 40 + side_rows * 66
    height = rows * (ch + 34) + side_h + (26 if note else 6)
    body = []
    pos = {}
    for i, (key, en, fr) in enumerate(main):
        r, c = divmod(i, per_row)
        if r % 2 == 1:  # boustrophedon keeps the arrows short
            c = per_row - 1 - c
        x = 10 + c * (cw + gap)
        y = 8 + r * (ch + 34)
        pos[key] = (x, y)
        first = i == 0
        last = i == len(main) - 1
        fill = NAVY if first else (GREEN if last else TEAL)
        body.append(_box(x, y, cw, ch, fill, rx=10))
        if lang == "fr" and fr and fr.lower() != en.lower():
            body.append(_t(x + cw / 2, y + 22, en, 14, "#fff", weight=600))
            body.append(_t(x + cw / 2, y + 42, fr, 12, "#E3EEF7", italic=True))
        else:
            body.append(_t(x + cw / 2, y + ch / 2, en, 14, "#fff", weight=600))
        body.append(_t(x + 14, y + 12, str(i + 1), 10, "#CFE3F0", anchor="start"))
    for i in range(len(main) - 1):
        (x1, y1), (x2, y2) = pos[main[i][0]], pos[main[i + 1][0]]
        if y1 == y2:
            if x2 > x1:
                body.append(_arrow(x1 + cw, y1 + ch / 2, x2 - 2, y2 + ch / 2))
            else:
                body.append(_arrow(x1, y1 + ch / 2, x2 + cw + 2, y2 + ch / 2))
        else:
            body.append(_arrow(x1 + cw / 2, y1 + ch, x2 + cw / 2, y2 - 2))
    if side:
        y0 = rows * (ch + 34) + 12
        lbl = "Sorties possibles" if lang == "fr" else "Other outcomes"
        body.append(_t(10, y0 + 6, lbl, 12, GREY, anchor="start", weight=600))
        sw = 176
        for j, (key, en, fr) in enumerate(side):
            r, c = divmod(j, 5)
            x = 10 + c * (sw + gap)
            y = y0 + 20 + r * 66
            bad = key in TERMINAL_BAD
            col = RED if bad else AMBER
            body.append(_box(x, y, sw, 50, "#fff", stroke=col, rx=10, dash=True))
            if lang == "fr" and fr and fr.lower() != en.lower():
                body.append(_t(x + sw / 2, y + 18, en, 13, col, weight=600))
                body.append(_t(x + sw / 2, y + 36, fr, 11.5, GREY, italic=True))
            else:
                body.append(_t(x + sw / 2, y + 25, en, 13, col, weight=600))
    if note:
        body.append(_t(10, height - 10, note, 11, GREY, anchor="start", italic=True))
    return _svg(width, height, "".join(body), "state diagram", max_pct=min(100, width / 988 * 100 + 8))


# ---------------------------------------------------------------------------
# Explanatory schematics
# ---------------------------------------------------------------------------
L = {
    "pyramid": {
        "en": ["Quality policy\n& manual", "Procedures (SOP)\nwho, what, when",
               "Work instructions\nhow, step by step",
               "Records & forms\nevidence that it was done"],
        "fr": ["Politique &\nmanuel qualité", "Procédures (SOP)\nqui, quoi, quand",
               "Instructions de travail\ncomment, pas à pas",
               "Enregistrements & formulaires\npreuve de réalisation"],
    },
}


def doc_pyramid(lang="en"):
    labels = L["pyramid"][lang]
    mods = {"en": ["ls_qms (Policy)", "ls_qms (SOP) · ls_document_management",
                   "ls_qms (Work Instruction)",
                   "ls_qms (Quality Record) · every module's records"],
            "fr": ["ls_qms (Policy)", "ls_qms (SOP) · ls_document_management",
                   "ls_qms (Work Instruction)",
                   "ls_qms (Quality Record) · enregistrements de chaque module"]}[lang]
    W, H = 900, 330
    body = []
    cols = [NAVY, TEAL, "#3F8FA0", "#6FA7B4"]
    cx = 250
    for i in range(4):
        top = 16 + i * 76
        half_top = 30 + i * 55
        half_bot = 30 + (i + 1) * 55
        if i == 0:
            pts = f"{cx},{top} {cx + half_bot},{top + 70} {cx - half_bot},{top + 70}"
        else:
            pts = f"{cx - half_top},{top} {cx + half_top},{top} {cx + half_bot},{top + 70} {cx - half_bot},{top + 70}"
        body.append(f'<polygon points="{pts}" fill="{cols[i]}"/>')
        body.append(_t(cx, top + (46 if i == 0 else 36), labels[i], 12.5, "#fff", weight=600))
        body.append(_arrow(cx + half_bot + 10, top + 40, 520, top + 40, LINE))
        body.append(_t(528, top + 40, mods[i], 12.5, NAVY, anchor="start"))
    return _svg(W, H, "".join(body), "document pyramid")


def suite_map(lang="en"):
    fr = lang == "fr"
    groups = [
        ("Système qualité" if fr else "Quality system", NAVY,
         ["ls_qms", "ls_document_management", "ls_training"]),
        ("Événements qualité" if fr else "Quality events", RED,
         ["ls_deviation", "ls_capa", "ls_complaint", "ls_change_control"]),
        ("Surveillance & maîtrise" if fr else "Oversight & control", TEAL,
         ["ls_audit", "ls_risk_management", "ls_supplier_qualification", "ls_recall"]),
        ("Intégrité des données" if fr else "Data integrity", "#5B4B8A",
         ["ls_audit_trail", "ls_electronic_signature"]),
        ("Opérations GxP" if fr else "GxP operations", GREEN,
         ["ls_validation", "ls_calibration", "ls_environmental_monitoring", "ls_lab"]),
        ("Métiers" if fr else "Industry modules", AMBER,
         ["ls_pharma", "ls_cosmetics", "ls_medical_device", "ls_medical_plastics"]),
        ("Affaires réglementaires" if fr else "Regulatory affairs", GREY,
         ["ls_import_export"]),
    ]
    W = 960
    body = []
    x, y = 10, 10
    colw = 228
    col_x = [10, 250, 490, 730]
    placements = [(0, 0), (1, 0), (2, 0), (3, 0), (0, 1), (1, 1), (2, 1)]
    heights = []
    for (title, col, mods), (cx, cy) in zip(groups, placements):
        x = col_x[cx]
        y = 10 + cy * 215
        h = 40 + len(mods) * 38
        body.append(_box(x, y, colw, h, "#fff", stroke=col, rx=12))
        body.append(f'<rect x="{x}" y="{y}" width="{colw}" height="30" rx="12" fill="{col}"/>')
        body.append(f'<rect x="{x}" y="{y + 18}" width="{colw}" height="12" fill="{col}"/>')
        body.append(_t(x + colw / 2, y + 16, title, 13.5, "#fff", weight=700))
        for k, m in enumerate(mods):
            body.append(_box(x + 12, y + 38 + k * 38, colw - 24, 30, LIGHT, rx=6))
            body.append(_t(x + colw / 2, y + 53 + k * 38, m, 12.5, NAVY, weight=600))
        heights.append(y + h)
    H = max(heights) + 70
    note = ("Aucun module n'a de lien relationnel vers un autre module LS : les passages de relais "
            "(déviation → CAPA, constat d'audit → CAPA, excursion → déviation…)\n"
            "se font par un champ de référence saisi par l'utilisateur. La procédure doit donc imposer "
            "la saisie et la vérification de ces références.") if fr else (
            "No LS module holds a relational link to another LS module: hand-offs "
            "(deviation → CAPA, audit finding → CAPA, excursion → deviation…)\n"
            "are made through a reference field typed by the user. The procedures must therefore "
            "require these references to be entered and checked.")
    body.append(_t(10, H - 34, note, 12, GREY, anchor="start", italic=True))
    return _svg(W, H, "".join(body), "suite map")


def handoffs(lang="en"):
    """Event hand-offs by reference, as implemented."""
    fr = lang == "fr"
    nodes = {
        "dev": (40, 40, "Déviation" if fr else "Deviation", RED),
        "cmp": (40, 150, "Réclamation" if fr else "Complaint", RED),
        "aud": (40, 260, "Constat d'audit" if fr else "Audit finding", TEAL),
        "val": (40, 370, "Écart de validation" if fr else "Validation discrepancy", GREEN),
        "exc": (40, 480, "Excursion EM" if fr else "EM excursion", GREEN),
        "capa": (560, 200, "CAPA", NAVY),
        "cc": (560, 380, "Maîtrise des\nchangements" if fr else "Change control", NAVY),
    }
    body = []
    for k, (x, y, lbl, col) in nodes.items():
        w = 260 if k in ("capa", "cc") else 230
        body.append(_box(x, y, w, 60, col, rx=10))
        body.append(_t(x + w / 2, y + 30, lbl, 14, "#fff", weight=700))
    how = {
        "dev": "état CAPA Required" if fr else "state CAPA Required",
        "cmp": "état CAPA Required" if fr else "state CAPA Required",
        "aud": "champ CAPA reference obligatoire\npour accepter la réponse" if fr else "CAPA reference required\nto accept the response",
        "val": "champ CAPA reference si\n« CAPA requise »" if fr else "CAPA reference when\n'CAPA required' is ticked",
        "exc": "External Record Reference" ,
    }
    for k in ("dev", "cmp", "aud", "val", "exc"):
        x, y = nodes[k][0] + 230, nodes[k][1] + 30
        body.append(_path(f"M{x},{y} C{x + 120},{y} {440},{230} {558},{230}", GREY, dash=True))
        body.append(_t(x + 12, y - 12, how[k], 11, GREY, anchor="start", italic=True))
    body.append(_path("M690,262 L690,378", GREY, dash=True))
    body.append(_t(700, 322, "action = changement\n→ demande de changement" if fr else
                   "action = a change\n→ change request", 11, GREY, anchor="start", italic=True))
    return _svg(840, 560, "".join(body), "hand-offs")


def pdca(lang="en"):
    fr = lang == "fr"
    q = [("PLAN", "Planifier" if fr else "Plan", "Politique, objectifs,\nplans qualité, risques" if fr else "Policy, objectives,\nquality plans, risks", NAVY),
         ("DO", "Réaliser" if fr else "Do", "Procédures, formation,\nlots, analyses" if fr else "Procedures, training,\nbatches, testing", TEAL),
         ("CHECK", "Vérifier" if fr else "Check", "Audits, tendances EM,\nKPI, revue de direction" if fr else "Audits, EM trends,\nKPIs, management review", AMBER),
         ("ACT", "Agir" if fr else "Act", "CAPA, maîtrise des\nchangements" if fr else "CAPA, change\ncontrol", GREEN)]
    cx, cy, r = 300, 220, 170
    body = []
    import math
    for i, (code, name, desc, col) in enumerate(q):
        a0 = math.radians(-90 + i * 90 + 2)
        a1 = math.radians(-90 + (i + 1) * 90 - 2)
        x0, y0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
        x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
        ri = 70
        xi1, yi1 = cx + ri * math.cos(a1), cy + ri * math.sin(a1)
        xi0, yi0 = cx + ri * math.cos(a0), cy + ri * math.sin(a0)
        body.append(f'<path d="M{x0:.1f},{y0:.1f} A{r},{r} 0 0 1 {x1:.1f},{y1:.1f} L{xi1:.1f},{yi1:.1f} A{ri},{ri} 0 0 0 {xi0:.1f},{yi0:.1f} z" fill="{col}"/>')
        am = math.radians(-45 + i * 90)
        body.append(_t(cx + 122 * math.cos(am), cy + 122 * math.sin(am), code, 20, "#fff", weight=700))
        tx = cx + (r + 30) * math.cos(am)
        ty = cy + (r + 20) * math.sin(am)
        anchor = "start" if math.cos(am) > 0 else "end"
        body.append(_t(tx, ty - 16, name, 15, col, anchor=anchor, weight=700))
        body.append(_t(tx, ty + 12, desc, 12.5, "#333", anchor=anchor))
    body.append(_t(cx, cy, "QMS", 22, NAVY, weight=700))
    return _svg(640, 440, "".join(body), "PDCA")


def v_model(lang="en"):
    fr = lang == "fr"
    left = [("URS", "Besoins utilisateur" if fr else "User requirements"),
            ("FS / DS", "Spécifications" if fr else "Specifications"),
            ("DQ", "Qualification de conception" if fr else "Design qualification")]
    right = [("PQ", "Qualification de performance" if fr else "Performance qualification"),
             ("OQ", "Qualification opérationnelle" if fr else "Operational qualification"),
             ("IQ", "Qualification d'installation" if fr else "Installation qualification")]
    body = []
    for i, (c, d) in enumerate(left):
        x, y = 30 + i * 90, 30 + i * 90
        body.append(_box(x, y, 250, 56, NAVY))
        body.append(_t(x + 125, y + 20, c, 15, "#fff", weight=700))
        body.append(_t(x + 125, y + 40, d, 11.5, "#DCE7F2"))
    for i, (c, d) in enumerate(right):
        x, y = 640 - i * 90, 30 + i * 90
        body.append(_box(x, y, 250, 56, GREEN))
        body.append(_t(x + 125, y + 20, c, 15, "#fff", weight=700))
        body.append(_t(x + 125, y + 40, d, 11.5, "#E0F0E6"))
        body.append(_arrow(30 + i * 90 + 250 + 6, 58 + i * 90, x - 6, 58 + i * 90, LINE, dash=True))
    body.append(_box(335, 300, 250, 50, AMBER))
    body.append(_t(460, 325, "Construction / installation" if fr else "Build / installation", 13, "#fff", weight=700))
    body.append(_arrow(290, 262, 350, 298))
    body.append(_arrow(570, 298, 630, 262))
    body.append(_box(30, 380, 860, 44, LIGHT, stroke=LINE))
    body.append(_t(460, 402, ("Plan directeur (VMP) → protocoles approuvés → exécutions revues → écarts clos → rapport de synthèse → revalidation"
                              if fr else "Master plan (VMP) → approved protocols → reviewed executions → closed discrepancies → summary report → revalidation"),
                   12.5, NAVY, weight=600))
    body.append(_t(460, 450, ("Les flèches pointillées relient chaque niveau de spécification au test qui le vérifie."
                              if fr else "Dashed arrows link each specification level to the test that verifies it."), 11, GREY, italic=True))
    return _svg(920, 465, "".join(body), "V model")


def risk_matrix(lang="en"):
    fr = lang == "fr"
    body = []
    x0, y0, s = 150, 20, 64
    lv = {1: "#3D9A5B", 2: "#3D9A5B", 3: "#E0A100", 4: "#D46A1E", 5: RED}
    for i in range(5):
        for j in range(5):
            sev, prob = 5 - i, j + 1
            score = sev * prob
            level = 1 if score <= 4 else 2 if score <= 6 else 3 if score <= 12 else 4 if score <= 16 else 5
            col = {1: "#3D9A5B", 2: "#8DBF5A", 3: "#E0A100", 4: "#D46A1E", 5: RED}[level]
            body.append(f'<rect x="{x0 + j * s}" y="{y0 + i * s}" width="{s - 3}" height="{s - 3}" rx="5" fill="{col}"/>')
            body.append(_t(x0 + j * s + s / 2 - 1, y0 + i * s + s / 2, str(score), 15, "#fff", weight=700))
        body.append(_t(x0 - 12, y0 + i * s + s / 2, str(5 - i), 14, NAVY, anchor="end", weight=700))
        body.append(_t(x0 + i * s + s / 2, y0 + 5 * s + 16, str(i + 1), 14, NAVY, weight=700))
    body.append(_t(60, y0 + 2.5 * s, "Gravité" if fr else "Severity", 15, NAVY, weight=700))
    body.append(_t(x0 + 2.5 * s, y0 + 5 * s + 42, "Probabilité" if fr else "Probability", 15, NAVY, weight=700))
    leg = [("#3D9A5B", "Acceptable"), ("#E0A100", "ALARP / à réduire" if fr else "ALARP / reduce"), (RED, "Inacceptable" if fr else "Unacceptable")]
    for k, (c, t) in enumerate(leg):
        body.append(f'<rect x="520" y="{60 + k * 34}" width="22" height="22" rx="4" fill="{c}"/>')
        body.append(_t(552, 71 + k * 34, t, 13, "#333", anchor="start"))
    body.append(_t(520, 200, ("Exemple illustratif 5 × 5.\nLes niveaux, couleurs et seuils réels sont\nceux de la matrice approuvée dans\nRisk Management ▸ Configuration ▸ Risk Matrices."
                              if fr else "Illustrative 5 × 5 example.\nThe real levels, colours and thresholds are\nthose of the approved matrix in\nRisk Management ▸ Configuration ▸ Risk Matrices."), 11.5, GREY, anchor="start", italic=True))
    return _svg(860, 400, "".join(body), "risk matrix")


def oos_flow(lang="en"):
    fr = lang == "fr"
    body = []
    def node(x, y, w, h, txt, col, fg="#fff"):
        body.append(_box(x, y, w, h, col))
        body.append(_t(x + w / 2, y + h / 2, txt, 12.5, fg, weight=600))
    node(20, 20, 200, 56, "Résultat hors spéc. /\nhors tendance" if fr else "Out-of-specification /\nout-of-trend result", RED)
    node(270, 20, 200, 56, "Phase I\nenquête laboratoire" if fr else "Phase I\nlaboratory investigation", NAVY)
    body.append(_arrow(220, 48, 268, 48))
    body.append(f'<polygon points="600,20 690,48 600,76 510,48" fill="{AMBER}"/>')
    body.append(_t(600, 48, "Cause labo\nassignable ?" if fr else "Assignable\nlab cause?", 11.5, "#fff", weight=700))
    body.append(_arrow(470, 48, 508, 48))
    node(730, 20, 200, 56, "Retest / ré-échantillonnage\nautorisé et justifié" if fr else "Retest / resample\nauthorised & justified", TEAL)
    body.append(_arrow(690, 48, 728, 48))
    body.append(_t(708, 36, "oui" if fr else "yes", 11, GREY))
    node(500, 130, 200, 56, "Phase II\nenquête complète" if fr else "Phase II\nfull investigation", NAVY)
    body.append(_arrow(600, 76, 600, 128))
    body.append(_t(612, 104, "non" if fr else "no", 11, GREY, anchor="start"))
    node(500, 230, 200, 56, "Conclusion +\ndisposition du produit" if fr else "Conclusion +\nproduct disposition", TEAL)
    body.append(_arrow(600, 186, 600, 228))
    body.append(_path("M830,76 L830,258 L702,258"))
    node(170, 230, 260, 56, "Clôture par un autre\nutilisateur (unité qualité)" if fr else "Closure by another user\n(quality unit)", GREEN)
    body.append(_arrow(500, 258, 432, 258))
    body.append(_t(475, 320, ("Le lot reste bloqué en livraison tant que l'enquête est ouverte (contrôle sur stock.move.line)."
                              if fr else "The lot stays blocked for delivery while the investigation is open (control on stock.move.line)."),
                   11.5, GREY, italic=True))
    return _svg(950, 340, "".join(body), "OOS")


def em_chart(lang="en"):
    fr = lang == "fr"
    import random
    random.seed(7)
    vals = [2, 1, 3, 0, 2, 4, 1, 2, 6, 3, 2, 1, 11, 4, 2, 3, 1, 2, 5, 2]
    x0, y0, w, h = 70, 20, 780, 250
    body = [f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" fill="#FAFBFC" stroke="{LINE}"/>']
    ymax = 14
    def Y(v): return y0 + h - v / ymax * h
    alert, action = 5, 10
    body.append(f'<line x1="{x0}" y1="{Y(alert)}" x2="{x0 + w}" y2="{Y(alert)}" stroke="{AMBER}" stroke-width="2" stroke-dasharray="7,5"/>')
    body.append(f'<line x1="{x0}" y1="{Y(action)}" x2="{x0 + w}" y2="{Y(action)}" stroke="{RED}" stroke-width="2" stroke-dasharray="7,5"/>')
    body.append(_t(x0 + w - 6, Y(alert) - 9, ("Limite d'alerte" if fr else "Alert limit") + " = 5", 12, AMBER, anchor="end", weight=700))
    body.append(_t(x0 + w - 6, Y(action) - 9, ("Limite d'action" if fr else "Action limit") + " = 10", 12, RED, anchor="end", weight=700))
    step = w / (len(vals) - 1)
    pts = " ".join(f"{x0 + i * step:.1f},{Y(v):.1f}" for i, v in enumerate(vals))
    body.append(f'<polyline points="{pts}" fill="none" stroke="{NAVY}" stroke-width="2"/>')
    for i, v in enumerate(vals):
        c = RED if v >= action else AMBER if v >= alert else NAVY
        body.append(f'<circle cx="{x0 + i * step:.1f}" cy="{Y(v):.1f}" r="5" fill="{c}"/>')
    for v in range(0, ymax + 1, 2):
        body.append(_t(x0 - 8, Y(v), str(v), 11, GREY, anchor="end"))
    body.append(_t(28, y0 + h / 2, "UFC" if fr else "CFU", 12, GREY))
    body.append(_t(x0 + w / 2, y0 + h + 24, ("Prélèvements successifs d'un même point (données illustratives)"
                                               if fr else "Successive samples of one sampling point (illustrative data)"), 12, GREY, italic=True))
    return _svg(880, 310, "".join(body), "EM limits")


def calibration_chart(lang="en"):
    fr = lang == "fr"
    body = []
    x0, y0, w, h = 90, 30, 700, 210
    def Y(v): return y0 + h / 2 - v * (h / 2) / 1.6
    body.append(f'<rect x="{x0}" y="{Y(1.0)}" width="{w}" height="{Y(-1.0) - Y(1.0)}" fill="#E7F3EC"/>')
    body.append(f'<line x1="{x0}" y1="{Y(0)}" x2="{x0 + w}" y2="{Y(0)}" stroke="{LINE}"/>')
    body.append(_t(x0 - 8, Y(1.0), "+tol", 11, GREEN, anchor="end", weight=700))
    body.append(_t(x0 - 8, Y(-1.0), "−tol", 11, GREEN, anchor="end", weight=700))
    body.append(_t(x0 - 8, Y(0), ("réf." if fr else "ref."), 11, GREY, anchor="end"))
    pts = [("10 °C", 0.3, 0.1), ("50 °C", 0.8, 0.2), ("100 °C", 1.35, 0.15), ("150 °C", 0.9, -0.1)]
    for i, (lbl, af, al) in enumerate(pts):
        x = x0 + 90 + i * 170
        c = RED if abs(af) > 1 else NAVY
        body.append(f'<circle cx="{x - 18}" cy="{Y(af)}" r="7" fill="{c}"/>')
        body.append(f'<rect x="{x + 11}" y="{Y(al) - 7}" width="14" height="14" fill="{GREEN}"/>')
        body.append(_arrow(x - 10, Y(af), x + 8, Y(al), LINE))
        body.append(_t(x, y0 + h + 18, lbl, 12, "#333"))
    body.append(f'<circle cx="{x0 + 10}" cy="{y0 + h + 48}" r="7" fill="{NAVY}"/>')
    body.append(_t(x0 + 24, y0 + h + 48, ("Valeur trouvée (as-found)" if fr else "As-found value"), 12, "#333", anchor="start"))
    body.append(f'<rect x="{x0 + 230}" y="{y0 + h + 41}" width="14" height="14" fill="{GREEN}"/>')
    body.append(_t(x0 + 252, y0 + h + 48, ("Valeur après ajustement (as-left)" if fr else "As-left value"), 12, "#333", anchor="start"))
    body.append(f'<circle cx="{x0 + 510}" cy="{y0 + h + 48}" r="7" fill="{RED}"/>')
    body.append(_t(x0 + 524, y0 + h + 48, ("Hors tolérance → évaluation d'impact" if fr else "Out of tolerance → impact assessment"), 12, RED, anchor="start"))
    return _svg(880, 300, "".join(body), "calibration")


def hash_chain(lang="en", what="audit"):
    fr = lang == "fr"
    body = []
    for i in range(4):
        x = 20 + i * 215
        body.append(_box(x, 30, 185, 120, "#fff", stroke=NAVY, rx=10))
        body.append(f'<rect x="{x}" y="30" width="185" height="28" rx="10" fill="{NAVY}"/>')
        body.append(f'<rect x="{x}" y="46" width="185" height="12" fill="{NAVY}"/>')
        body.append(_t(x + 92, 44, (("Entrée n° " if fr else "Entry #") if what == "audit" else ("Signature n° " if fr else "Signature #")) + str(101 + i), 13, "#fff", weight=700))
        body.append(_t(x + 12, 76, ("contenu" if fr else "content") + f" c{101 + i}", 12, "#333", anchor="start"))
        body.append(_t(x + 12, 100, f"hash(c{101 + i})", 12, TEAL, anchor="start"))
        body.append(_t(x + 12, 124, ("chaîne" if fr else "chain") + f" = H(h{100 + i} + c{101 + i})", 11.5, NAVY, anchor="start", weight=600))
        if i < 3:
            body.append(_arrow(x + 185, 124, x + 213, 124, NAVY, marker="ahn"))
    body.append(_t(450, 185, ("Modifier, insérer ou supprimer une entrée change toutes les empreintes suivantes : la vérification le détecte."
                              if fr else "Altering, inserting or deleting an entry changes every following digest: the verification detects it."),
                   12, GREY, italic=True))
    return _svg(900, 205, "".join(body), "hash chain")


def recall_timeline(lang="en"):
    fr = lang == "fr"
    steps = [("Décision" if fr else "Decision", "Initiate", NAVY),
             ("Traçage" if fr else "Trace", "Trace Distribution", TEAL),
             ("Communication", "Record as Sent", TEAL),
             ("Réconciliation" if fr else "Reconcile", ("Consignataires" if fr else "Consignees"), TEAL),
             ("Efficacité" if fr else "Effectiveness", ("Niveaux A–E" if fr else "Levels A–E"), AMBER),
             ("Clôture" if fr else "Close", ("Rapport final" if fr else "Final report"), GREEN)]
    body = [f'<line x1="40" y1="70" x2="880" y2="70" stroke="{LINE}" stroke-width="4"/>']
    for i, (a, b, c) in enumerate(steps):
        x = 60 + i * 160
        body.append(f'<circle cx="{x}" cy="70" r="20" fill="{c}"/>')
        body.append(_t(x, 70, str(i + 1), 15, "#fff", weight=700))
        body.append(_t(x, 118, a, 14, c, weight=700))
        body.append(_t(x, 140, b, 11.5, GREY, italic=True))
    lv = [("A", "100 %"), ("B", ">10 % <100 %"), ("C", "10 %"), ("D", "2 %"), ("E", "0")]
    body.append(_t(40, 186, ("Niveaux de vérification d'efficacité (21 CFR 7.42(b)(3)) — part des consignataires contactés :"
                             if fr else "Effectiveness check levels (21 CFR 7.42(b)(3)) — share of consignees contacted:"), 12.5, NAVY, anchor="start", weight=600))
    for i, (l, p) in enumerate(lv):
        x = 40 + i * 170
        body.append(_box(x, 200, 150, 40, LIGHT, stroke=LINE))
        body.append(_t(x + 75, 220, f"{'Niveau' if fr else 'Level'} {l} : {p}", 12.5, NAVY, weight=600))
    return _svg(900, 255, "".join(body), "recall")


def ishikawa(lang="en"):
    fr = lang == "fr"
    cats = (["Méthode", "Matière", "Machine", "Main-d'œuvre", "Milieu", "Mesure"] if fr
            else ["Method", "Material", "Machine", "Manpower", "Mother nature\n(environment)", "Measurement"])
    body = [f'<line x1="40" y1="170" x2="720" y2="170" stroke="{NAVY}" stroke-width="4"/>',
            _box(722, 138, 160, 64, RED), _t(802, 170, "Effet :\nle problème" if fr else "Effect:\nthe problem", 13, "#fff", weight=700)]
    for i, c in enumerate(cats):
        top = i % 2 == 0
        x = 150 + (i // 2) * 210
        y = 50 if top else 290
        body.append(f'<line x1="{x}" y1="{y + (20 if top else -20)}" x2="{x + 90}" y2="170" stroke="{TEAL}" stroke-width="2.5"/>')
        body.append(_box(x - 70, y - 22 if top else y - 20, 150, 40, TEAL, rx=6))
        body.append(_t(x + 5, y - 2 if top else y, c, 12.5, "#fff", weight=700))
    body.append(_t(440, 335, ("Diagramme d'Ishikawa (6M) — une des méthodes d'analyse des causes proposées dans ls_capa (avec 5 Pourquoi et AMDE)."
                              if fr else "Ishikawa (6M) diagram — one of the root-cause methods offered in ls_capa (with Five Whys and FMEA)."),
                   11.5, GREY, italic=True))
    return _svg(900, 350, "".join(body), "ishikawa")


def batch_release(lang="en"):
    fr = lang == "fr"
    checks = (["Dossier(s) de lot approuvé(s)\npar l'unité qualité", "Aucun écart ouvert\n(211.192)",
               "Rendement dans les limites\nou enquête référencée", "Date de péremption\nrenseignée",
               "Contrôles de libération\nconfirmés"] if fr else
              ["Batch record(s) approved\nby the quality unit", "No open discrepancy\n(211.192)",
               "Yield within limits or\ninvestigation referenced", "Expiry date\nrecorded", "Release checks\nconfirmed"])
    body = []
    for i, c in enumerate(checks):
        y = 14 + i * 62
        body.append(_box(20, y, 260, 50, LIGHT, stroke=LINE))
        body.append(_t(150, y + 25, c, 12, NAVY, weight=600))
        body.append(_path(f"M280,{y + 25} C340,{y + 25} 340,165 398,165", LINE))
    body.append(f'<polygon points="400,165 500,105 600,165 500,225" fill="{AMBER}"/>')
    body.append(_t(500, 165, ("Décision QA\n(≠ fabricant)" if fr else "QA decision\n(≠ manufacturer)"), 13, "#fff", weight=700))
    body.append(_box(650, 90, 210, 50, GREEN)); body.append(_t(755, 115, "Released", 15, "#fff", weight=700))
    body.append(_box(650, 190, 210, 50, RED)); body.append(_t(755, 215, "Rejected", 15, "#fff", weight=700))
    body.append(_arrow(575, 150, 648, 115)); body.append(_arrow(575, 180, 648, 215))
    body.append(_t(755, 268, ("Livraison client du lot autorisée\nseulement après « Released »"
                              if fr else "Customer delivery of the lot\nallowed only once Released"), 11.5, GREY, italic=True))
    return _svg(880, 330, "".join(body), "batch release")


def serial_hierarchy(lang="en"):
    fr = lang == "fr"
    body = []
    body.append(_box(330, 16, 220, 56, NAVY)); body.append(_t(440, 44, ("Palette — SSCC" if fr else "Pallet — SSCC"), 14, "#fff", weight=700))
    for i in range(3):
        x = 120 + i * 230
        body.append(_box(x, 120, 180, 50, TEAL)); body.append(_t(x + 90, 145, ("Carton — SSCC" if fr else "Case — SSCC"), 13, "#fff", weight=700))
        body.append(_arrow(440, 72, x + 90, 118, LINE))
        for k in range(3):
            xx = x - 10 + k * 70
            body.append(_box(xx, 220, 60, 44, LIGHT, stroke=LINE))
            body.append(_t(xx + 30, 242, "GTIN\n+ SN", 10.5, NAVY, weight=600))
            body.append(_arrow(x + 90, 170, xx + 30, 218, LINE))
    body.append(_t(440, 300, ("Unité de vente : GTIN-14 + numéro de série (état Commissioned avant expédition). "
                              "Conteneur : SSCC 18 chiffres, clé modulo 10." if fr else
                              "Saleable unit: GTIN-14 + serial number (Commissioned before shipping). "
                              "Container: 18-digit SSCC with modulo-10 check digit."), 11.5, GREY, italic=True))
    return _svg(880, 320, "".join(body), "serialisation")


def ctd_triangle(lang="en"):
    fr = lang == "fr"
    body = []
    body.append(f'<polygon points="400,20 560,120 240,120" fill="{GREY}"/>')
    body.append(_t(400, 92, ("Module 1\nrégional" if fr else "Module 1\nregional"), 12.5, "#fff", weight=700))
    body.append(f'<polygon points="240,126 560,126 640,196 160,196" fill="{NAVY}"/>')
    body.append(_t(400, 162, ("Module 2 — résumés" if fr else "Module 2 — summaries"), 13, "#fff", weight=700))
    parts = [("Module 3", "Qualité" if fr else "Quality"), ("Module 4", "Non clinique" if fr else "Nonclinical"), ("Module 5", "Clinique" if fr else "Clinical")]
    for i, (a, b) in enumerate(parts):
        x = 160 + i * 162
        body.append(_box(x, 202, 156, 70, TEAL, rx=4))
        body.append(_t(x + 78, 237, f"{a}\n{b}", 13, "#fff", weight=700))
    body.append(_t(400, 300, ("Structure ICH M4 ; ls_pharma suit l'état de chaque section (Load CTD Structure)."
                              if fr else "ICH M4 structure; ls_pharma tracks the status of each section (Load CTD Structure)."), 11.5, GREY, italic=True))
    return _svg(800, 318, "".join(body), "CTD")


def training_loop(lang="en"):
    fr = lang == "fr"
    import math
    items = (["Exigence\n(poste, service, personne)", "Cours approuvé\n(version)", "Session\n& présence",
              "Certification\n(auto à la clôture)", "Expiration /\nrappel", "Matrice\n& écarts"] if fr else
             ["Requirement\n(job, department, person)", "Approved course\n(version)", "Session\n& attendance",
              "Certification\n(auto on close)", "Expiry /\nreminder", "Matrix\n& gaps"])
    cx, cy, r = 430, 190, 150
    body = []
    pts = []
    for i, t in enumerate(items):
        a = math.radians(-90 + i * 60)
        x, y = cx + r * 1.55 * math.cos(a), cy + r * math.sin(a)
        pts.append((x, y))
    for i in range(6):
        (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % 6]
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        body.append(_path(f"M{x1:.0f},{y1:.0f} Q{mx + (mx - cx) * 0.25:.0f},{my + (my - cy) * 0.25:.0f} {x2:.0f},{y2:.0f}", LINE))
    for i, (x, y) in enumerate(pts):
        col = [NAVY, TEAL, TEAL, GREEN, AMBER, NAVY][i]
        body.append(_box(x - 95, y - 27, 190, 54, col, rx=10))
        body.append(_t(x, y, items[i], 12.5, "#fff", weight=700))
    return _svg(860, 390, "".join(body), "training")


def supplier_lifecycle(lang="en"):
    fr = lang == "fr"
    body = []
    steps = [("Registered", "Enregistré"), ("Under Assessment", "Évaluation"), ("Under Audit", "Audit"),
             ("Pending Approval", "Approbation"), ("Approved", "Approuvé")]
    for i, (en, frl) in enumerate(steps):
        x = 14 + i * 172
        col = GREEN if i == 4 else NAVY if i == 0 else TEAL
        body.append(_box(x, 20, 156, 56, col))
        body.append(_t(x + 78, 40, en, 13, "#fff", weight=700))
        if fr:
            body.append(_t(x + 78, 60, frl, 11.5, "#E3EEF7", italic=True))
        if i < 4:
            body.append(_arrow(x + 156, 48, x + 170, 48))
    body.append(_box(430, 120, 440, 54, LIGHT, stroke=LINE))
    body.append(_t(650, 147, ("Suivi : évaluations de performance · revues périodiques · requalification"
                              if fr else "Monitoring: performance evaluations · periodic reviews · requalification"), 12.5, NAVY, weight=600))
    body.append(_path("M792,76 L792,118", LINE))
    body.append(_box(14, 120, 380, 54, "#FBEDEC", stroke=RED))
    body.append(_t(204, 147, ("Bon de commande bloqué si le fournisseur\nn'est pas qualifié (button_confirm)"
                              if fr else "Purchase order blocked when the supplier\nis not qualified (button_confirm)"), 12, RED, weight=600))
    body.append(_t(440, 205, ("Autres états : Conditionally Approved, Suspended, Expired, Disqualified."
                              if fr else "Other states: Conditionally Approved, Suspended, Expired, Disqualified."), 11.5, GREY, italic=True))
    return _svg(880, 220, "".join(body), "supplier")


def md_gates(lang="en"):
    fr = lang == "fr"
    body = []
    states = ["Draft", "Under Development", "Conformity Assessment", "On the Market"]
    for i, s in enumerate(states):
        x = 14 + i * 218
        body.append(_box(x, 20, 196, 50, [NAVY, TEAL, TEAL, GREEN][i]))
        body.append(_t(x + 98, 45, s, 13, "#fff", weight=700))
        if i < 3:
            body.append(_arrow(x + 196, 45, x + 216, 45))
    gates = (["Finalité prévue enregistrée", "Documentation technique approuvée",
              "Certificat Issued / Valid si la classe exige un organisme notifié", "Date de première mise sur le marché"]
             if fr else ["Intended purpose recorded", "Approved technical documentation",
                         "Certificate Issued / Valid when the class requires a notified body", "Date of first placing on the market"])
    body.append(_t(14, 100, ("Conditions vérifiées par le logiciel :" if fr else "Conditions checked by the software:"), 12.5, NAVY, anchor="start", weight=700))
    for i, g in enumerate(gates):
        body.append(_t(30, 126 + i * 22, "✓ " + g, 12, "#333", anchor="start"))
    body.append(_t(460, 126, ("Dossiers associés : UDI · gestion des risques (ISO 14971) ·\névaluation clinique · PMCF · SAC/PMS · marquage CE"
                              if fr else "Related files: UDI · risk management (ISO 14971) ·\nclinical evaluation · PMCF · PMS · CE marking"), 12, TEAL, anchor="start", weight=600))
    return _svg(900, 220, "".join(body), "medical device")


def shot_counter(lang="en"):
    fr = lang == "fr"
    body = []
    x0, w = 60, 720
    body.append(f'<rect x="{x0}" y="40" width="{w}" height="40" rx="6" fill="{LIGHT}" stroke="{LINE}"/>')
    body.append(f'<rect x="{x0}" y="40" width="{w * 0.82}" height="40" rx="6" fill="{TEAL}"/>')
    body.append(f'<line x1="{x0 + w * 0.75}" y1="30" x2="{x0 + w * 0.75}" y2="90" stroke="{AMBER}" stroke-width="3" stroke-dasharray="5,4"/>')
    body.append(f'<line x1="{x0 + w}" y1="30" x2="{x0 + w}" y2="90" stroke="{RED}" stroke-width="3"/>')
    body.append(_t(x0 + w * 0.75, 18, ("Seuil d'alerte" if fr else "Warning threshold"), 12, AMBER, weight=700))
    body.append(_t(x0 + w, 18, ("Maintenance due" if not fr else "Maintenance due"), 12, RED, weight=700, anchor="end"))
    body.append(_t(x0 + 10, 60, ("Coups depuis la dernière maintenance : 82 %" if fr else "Shots since last maintenance: 82 %"), 13, "#fff", anchor="start", weight=700))
    body.append(_t(420, 120, ("La maintenance préventive est déclenchée par nombre de coups ou par durée (le premier atteint)."
                              if fr else "Preventive maintenance is triggered by shot count or elapsed time, whichever comes first."), 12, GREY, italic=True))
    return _svg(840, 140, "".join(body), "shot counter")


def pif_map(lang="en"):
    fr = lang == "fr"
    body = []
    nodes = [(20, 30, ("Ingrédients\n& restrictions (annexes II–VI)" if fr else "Ingredients &\nrestrictions (Annexes II–VI)"), NAVY),
             (250, 30, ("Formule\n(total 100 % p/p)" if fr else "Formulation\n(total 100 % w/w)"), TEAL),
             (480, 30, ("Rapport de sécurité\n(CPSR partie A / B)" if fr else "Safety report\n(CPSR Part A / B)"), TEAL),
             (710, 30, ("Dossier d'information\nproduit (art. 11)" if fr else "Product information\nfile (Art. 11)"), GREEN),
             (250, 150, ("Étiquetage\n(art. 19, liste INCI)" if fr else "Labelling\n(Art. 19, INCI list)"), TEAL),
             (480, 150, ("Allégations\n(critères communs)" if fr else "Claims\n(common criteria)"), TEAL),
             (710, 150, ("Autorisation préalable\nAlgérie (décret 97-37)" if fr else "Algerian prior\nauthorisation (Decree 97-37)"), AMBER)]
    for x, y, t, c in nodes:
        body.append(_box(x, y, 200, 70, c)); body.append(_t(x + 100, y + 35, t, 12, "#fff", weight=700))
    body.append(_arrow(220, 65, 248, 65)); body.append(_arrow(450, 65, 478, 65)); body.append(_arrow(680, 65, 708, 65))
    body.append(_arrow(350, 100, 350, 148)); body.append(_arrow(580, 100, 580, 148)); body.append(_arrow(810, 100, 810, 148))
    body.append(_t(450, 250, ("Chaque étape est approuvée par un autre utilisateur que celui qui l'a préparée (quatre yeux)."
                              if fr else "Each step is approved by a user other than the one who prepared it (four eyes)."), 11.5, GREY, italic=True))
    return _svg(930, 265, "".join(body), "cosmetics")


def four_eyes(lang="en"):
    fr = lang == "fr"
    body = []
    body.append(_box(20, 20, 220, 70, NAVY)); body.append(_t(130, 55, ("Auteur / exécutant" if fr else "Author / performer"), 14, "#fff", weight=700))
    body.append(_box(330, 20, 220, 70, TEAL)); body.append(_t(440, 55, ("Vérificateur" if fr else "Reviewer"), 14, "#fff", weight=700))
    body.append(_box(640, 20, 220, 70, GREEN)); body.append(_t(750, 55, ("Approbateur" if fr else "Approver"), 14, "#fff", weight=700))
    body.append(_arrow(240, 55, 328, 55)); body.append(_arrow(550, 55, 638, 55))
    body.append(_t(440, 125, ("Le logiciel refuse que la même personne tienne deux rôles sur un même enregistrement lorsque la règle existe"
                              if fr else "The software refuses the same person in two roles on one record wherever the rule exists"), 12.5, RED, weight=600))
    body.append(_t(440, 147, ("(ex. : revue d'analyse, approbation de SOP, libération de lot, clôture d'excursion, approbation de protocole)."
                              if fr else "(e.g. result review, SOP approval, batch release, excursion closure, protocol approval)."), 12, GREY, italic=True))
    return _svg(880, 165, "".join(body), "four eyes")


def alcoa(lang="en"):
    fr = lang == "fr"
    import math
    items = (["Attribuable", "Lisible", "Contemporain", "Original", "Exact", "Complet", "Cohérent", "Durable", "Disponible"] if fr else
             ["Attributable", "Legible", "Contemporaneous", "Original", "Accurate", "Complete", "Consistent", "Enduring", "Available"])
    cx, cy = 430, 170
    body = [f'<circle cx="{cx}" cy="{cy}" r="62" fill="{NAVY}"/>', _t(cx, cy, "ALCOA+", 20, "#fff", weight=700)]
    for i, t in enumerate(items):
        a = math.radians(-90 + i * 40)
        x, y = cx + 260 * math.cos(a), cy + 130 * math.sin(a)
        col = TEAL if i < 5 else GREEN
        body.append(f'<line x1="{cx + 62 * math.cos(a):.0f}" y1="{cy + 62 * math.sin(a):.0f}" x2="{x - 60 * math.cos(a):.0f}" y2="{y - 18 * math.sin(a):.0f}" stroke="{LINE}"/>')
        body.append(_box(x - 70, y - 17, 140, 34, col, rx=17))
        body.append(_t(x, y, t, 12.5, "#fff", weight=700))
    return _svg(860, 340, "".join(body), "ALCOA+")


def doc_review_timeline(lang="en"):
    fr = lang == "fr"
    body = [f'<line x1="40" y1="80" x2="860" y2="80" stroke="{LINE}" stroke-width="3"/>']
    marks = [(60, "Rév. 1 publiée" if fr else "Rev. 1 published", "date_effective", NAVY),
             (400, "Revue périodique\n(24 mois par défaut)" if fr else "Periodic review\n(24 months default)", "date_next_review", AMBER),
             (560, "Rév. 2 : New Revision\n+ raison du changement" if fr else "Rev. 2: New Revision\n+ reason for change", "", TEAL),
             (800, "Rév. 1 → Obsolete" if fr else "Rev. 1 → Obsolete", "", GREY)]
    for x, t, f, c in marks:
        body.append(f'<circle cx="{x}" cy="80" r="11" fill="{c}"/>')
        body.append(_t(x, 40, t, 12.5, c, weight=700))
        if f:
            body.append(_t(x, 110, f, 11, GREY, italic=True))
    body.append(_t(450, 150, ("Une seule révision publiée à la fois ; le contenu publié est figé."
                              if fr else "Only one revision is published at a time; published content is frozen."), 12, GREY, italic=True))
    return _svg(900, 165, "".join(body), "review timeline")


SCHEMATICS = {
    "pyramid": doc_pyramid, "suite_map": suite_map, "handoffs": handoffs, "pdca": pdca,
    "v_model": v_model, "risk_matrix": risk_matrix, "oos": oos_flow, "em_chart": em_chart,
    "calibration": calibration_chart, "hash_chain": hash_chain,
    "sig_chain": lambda lang: hash_chain(lang, "sig"), "recall": recall_timeline,
    "ishikawa": ishikawa, "batch_release": batch_release, "serial": serial_hierarchy,
    "ctd": ctd_triangle, "training": training_loop, "supplier": supplier_lifecycle,
    "md_gates": md_gates, "shot_counter": shot_counter, "pif": pif_map,
    "four_eyes": four_eyes, "alcoa": alcoa, "review_timeline": doc_review_timeline,
}
