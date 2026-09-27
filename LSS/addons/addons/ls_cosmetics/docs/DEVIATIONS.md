# Deviation Register

Every deviation from the Life Sciences Suite Functional Specification
(§8.5, `ls_cosmetics`), with its rationale. Deviations are declared, not
silently taken.

---

## D-01 — Reduced dependencies

**Specification:** `ls_cosmetics` depends on `ls_qms`, `mrp`, `stock`.

**Delivered:** depends on `base`, `mail`, `product`, `stock`, `mrp`.

**Rationale:** `ls_qms` is a suite module that is not present in this
deliverable. Declaring a dependency on a module that does not exist on the
addons path makes installation fail outright. The module is therefore
standalone. Where QMS integration is wanted later, it is added by a bridge
module that depends on both — the standard Odoo pattern — rather than by a
dependency that blocks installation today.

---

## D-02 — Models named for what they hold

**Specification model list:** `ls.cosmetic.formulation`,
`ls.cosmetic.ingredient`, `ls.cosmetic.safety_assessment`, `ls.cosmetic.pif`.

**Delivered:** those four, plus six more:

| Added model | Why it is required |
|---|---|
| `ls.cosmetic.formulation.line` | A composition is a set of substance/concentration pairs; the annex evaluation is per line |
| `ls.cosmetic.restriction` | Annexes II–VI have to live somewhere with their provenance |
| `ls.cosmetic.claim` | The specification lists "Claims Management" as a feature but no model |
| `ls.cosmetic.claim.evidence` | Art. 11(2)(d) requires *proof*; a text field cannot carry study references and attachments |
| `ls.cosmetic.label` | The specification lists "Labeling Management" as a feature but no model |
| `ls.cosmetic.dz_authorization` | The specification asks for national cosmetics regulation support |

**Rationale:** the specification's own feature table requires these; omitting
the models would mean the features could not be delivered.

---

## D-03 — No annex substance data shipped

**Delivered:** `ls.cosmetic.restriction` ships empty.

**Rationale:** Annexes II to VI are amended several times a year. An embedded
snapshot would be stale on arrival and would carry false authority. Absence of
data is reported as **"not evaluated"** and never as "compliant", so a missing
entry cannot be mistaken for a clean result.

---

## D-04 — The last-batch market date is manual

**Rationale:** the ten-year clock of Art. 11(1) runs from the date the last
batch was placed on the market. Odoo records stock moves, which are commercial
events and not necessarily the regulatory one. Deriving the date automatically
would put an unverifiable value on a regulatory retention period. A person
enters it.

---

## D-05 — Crons notify, they never decide

**Rationale:** the three scheduled actions post chatter notices. None archives
a dossier, withdraws an authorisation or changes a state. Ending the retention
of a regulatory dossier is a decision; the module records decisions made by
people rather than making them.

---

## D-06 — No ANPP claim for cosmetics

**Specification:** the regulatory traceability matrix (§14) does not mark
`ls_cosmetics` against ANPP, and this module makes no ANPP claim.

**Rationale:** cosmetics and body hygiene products in Algeria fall under the
Ministère du Commerce under décret exécutif n° 97-37 as modified by n° 10-114.
The ANPP is the pharmaceutical authority. Asserting an ANPP requirement for
cosmetics would be a fabrication.

**Further, not verified:** the composition and numbering of the Algerian
annexes of permitted and prohibited substances could not be established from
the ministry's published index. No Algerian annex numbering is encoded
anywhere in this module.

---

## D-07 — Record rules and menus carry no groups

**Rationale:** the `res.groups` Many2many field names on `ir.rule` and
`ir.ui.menu` could not be confirmed for Odoo 19. Writing the wrong field name
makes the module fail to install. Rules are global (correct for multi-company
scoping) and menu visibility follows from the ACL. Segregation of duties is
enforced by the ACL and the workflow methods, both of which use stable APIs.
See ADMIN_GUIDE §4 for the one-line tightening once confirmed.

---

## D-08 — No kanban views, no custom JavaScript

**Rationale:** the Odoo 19 kanban template API (`<t t-name="card">`) and the
OWL component API could not be verified against official Odoo 19
documentation to the depth needed to ship working assets. List, form and
search views cover every workflow. A kanban view that fails to render is worse
than no kanban view.

---

## D-09 — Concentration is a plain float, not `widget="percentage"`

**Rationale:** `widget="percentage"` renders a 0–1 ratio as a percentage.
Concentrations here are entered on a 0–100 scale in % w/w, as the annexes
express them. Using the widget would display 70 % w/w as 7000 %. The field is
a plain float with six decimal places, labelled in % w/w.

---

## D-10 — `ir.rule.global` is never written

**Rationale:** `global` is a computed field on `ir.rule`, derived from whether
groups are assigned. Writing it explicitly in a data file is an error. The
rules here are global as a consequence of assigning no groups, which is the
supported way to express it.

---

## D-11 — The offline checker cannot do schema validation

**Found by:** live installation on Odoo 19, 2026-08-05.

**What happened:** all eight search views shipped with
`<group expand="0" string="Group By">`, valid in earlier Odoo versions and
rejected by Odoo 19. The offline checker passed them, because it validates
XML well-formedness and field cross-references but has no copy of Odoo's
`*_view.rng` schemas and therefore cannot know which elements and attributes
a given version accepts.

**Mitigation:** the checker now encodes the specific rule as `search-schema`,
and gained `--odoo-rng`, which runs the real validation wherever Odoo is
importable:

    python3 tools/static_check.py /mnt/extra-addons/ls_cosmetics --odoo-rng

**Residual risk:** the encoded rule covers one construct that was actually
hit. Other version-specific schema constraints remain undetectable offline.
Run `--odoo-rng` inside the container before believing any offline pass.
Note also that Odoo 19 ships **no schema for `<form>`**, so form views are
checked by Python validators instead and are not covered by RNG at all.

---

## D-12 — Groups must imply `base.group_user`

**Found by:** live test execution on Odoo 19, 2026-08-06 (3 of 5 errors).

**What happened:** the four security groups were defined without implying
`base.group_user`. Odoo 19 treats `base.group_user` as "Role / User", and
without it a user is not an internal user: `res.company` is unreadable and
`mail.message` cannot be created. Because every regulated model in this
module inherits `mail.thread`, the very first `create()` by such a user
raised AccessError.

**Why the offline checker missed it:** the checker verifies that every model
has an ACL line and that group references resolve. It has no model of Odoo's
group-implication semantics and cannot know that an application group must
imply the internal-user role. This class of defect is only reachable by
executing code as a non-superuser, which requires a running Odoo.

**Fix:** `group_ls_cosmetics_user` now implies `base.group_user`; the
formulator, safety assessor and regulatory manager groups inherit it through
the existing implication chain.
