# Deviations and Limitations Register

**Module:** `ls_medical_plastics` · **Version:** 19.0.1.0.0

Every departure from the Life Sciences Suite specification, and every known
limitation of the delivered module, is recorded here. Nothing is omitted
because it is inconvenient.

---

## Part A — Deviations from the suite specification

### A1. Reduced module dependencies

**Specification states:** `ls_medical_plastics` depends on `ls_qms`,
`ls_validation`, `mrp`, `stock`.

**Delivered:** `base`, `mail`, `product`, `stock`, `mrp`.

**Rationale:** declaring a dependency on a module that is not present in the
addons path makes the module **uninstallable**. `ls_qms` and `ls_validation`
are not part of this delivery. Declaring them would have produced a module that
cannot be installed at all, which is a worse outcome than a documented
reduction in coupling.

**Mitigation:** integration is provided through extension points rather than
hard dependencies:

| Suite capability | Extension point in this module |
|---|---|
| Deviation management | `ls.mp.injection_molding.deviation_reference` (Char) |
| Document control | `ls.mp.component.specification_reference`, `drawing_reference` |
| Validation records | `ls.mp.tool.qualification_date`, `requalification_interval_months` |

When the corresponding suite modules are installed, these Char fields should be
migrated to Many2one relations by a small bridge module. No data is lost by
this approach because the references are already recorded.

---

### A2. Additional models beyond the specification

**Specification lists:** `ls.mp.injection_molding`, `ls.mp.molding_parameter`,
`ls.mp.component`, `ls.mp.tool`.

**Delivered:** the four above plus eight more.

| Added model | Why it is required |
|---|---|
| `ls.mp.molding_parameter.line` | A specification is a *set* of parameters; without lines the specification model could hold only one parameter |
| `ls.mp.injection_molding.reading` | The specification's own feature list requires "Process parameter tracking", which needs recorded values distinct from the specification |
| `ls.mp.injection_molding.material` | "Material traceability" is a listed feature and requires per-lot consumption records |
| `ls.mp.injection_molding.scrap` | Reject recording by reason and cavity; required to compute a meaningful reject rate |
| `ls.mp.tool.cavity` | Cavity-level attribution of defects; blocking one cavity without withdrawing the tool |
| `ls.mp.tool.maintenance` | "Tool management" implies a maintenance history; a single date field cannot record findings and actions |
| `ls.mp.material.grade` | Traceability to a *qualified* resin grade, not merely to a product |
| `ls.mp.scrap.reason` | A configurable defect taxonomy rather than free text |

Each added model serves a feature the specification itself lists. No model was
added speculatively.

---

### A3. Units of measure recorded as free text

**Deviation:** moulding parameter units (bar, degC, s, mm/s) and material
consumption units are `Char` fields, not `Many2one` to a unit-of-measure model.

**Rationale, part one:** moulding process units are not stock units. Pressure,
temperature and time are not convertible within Odoo's unit-of-measure category
system, which is built around quantity conversion for inventory.

**Rationale, part two:** the stability of the `uom.uom` model name in Odoo 19
**could not be verified from official documentation**. A `Many2one` to a model
name that has changed would make the module uninstallable. The module was
engineered to avoid the dependency.

**Consequence:** no automatic unit conversion or validation of unit strings.
Sites must standardise unit labels by procedure.

---

### A4. No kanban views and no custom JavaScript

The Odoo 19 kanban card template API and the OWL component registration
surface **could not be verified from official documentation**. Rather than ship
views that might fail to render or install, list, form, search, graph and pivot
views are provided and kanban is omitted.

---

## Part B — Odoo 19 facts that could not be verified

Each item below was researched, could not be confirmed from an official source,
and was then engineered around so that the unverified fact cannot break the
installation.

| Unverified fact | Risk if assumed wrongly | Mitigation applied |
|---|---|---|
| Field name grouping `res.groups` into categories (Odoo 19 reworked this) | Install failure on an unknown field | **No group category declared at all.** Groups are functional but not clustered under an application heading |
| Field name holding group links on `ir.rule` | Install failure | **All record rules are global** (multi-company only). Role restriction is done through `ir.model.access.csv` and Python checks. `ir.rule.global` is never written, being computed |
| Field name holding group links on `ir.ui.view` | Install failure | Replaced with the `groups=` **attribute on view nodes**, which is documented view-arch syntax |
| Presence of `numbercall` and `doall` on `ir.cron` | Install failure | Both **omitted**; only `name`, `model_id`, `state`, `code`, `interval_number`, `interval_type`, `user_id`, `active` are set |
| `uom.uom` model name stability | Install failure | Unit fields are `Char` (see A3) |
| Chatter markup form in Odoo 19 | Degraded rendering, or install failure | See B1 below |
| Arch of `mrp.production` form view | Install failure of the inherited view | See B2 below |

### B1. Chatter markup — a genuine conflict between sources

The official Odoo 19 documentation for view architectures **still documents the
chatter as a `div` element carrying the class `oe_chatter`** containing the
`message_follower_ids`, `activity_ids` and `message_ids` fields. Community and
OCA sources indicate that a dedicated `<chatter/>` tag replaced that `div` at
Odoo 18.

These sources conflict and the conflict could not be resolved authoritatively.

**Decision:** follow the official Odoo 19 documentation and use the `div` form.

**Reasoning about failure modes:** if the `div` form is merely deprecated, the
view still loads because the three fields genuinely exist on the model, and the
chatter renders in a degraded style — an appearance problem. If the
`<chatter/>` tag were used and turned out not to be valid, view validation
would fail and **the module would not install** — a total failure. The lower-risk
option was chosen.

**Action for the receiving team:** if the chatter renders poorly, replace the
`div` block with `<chatter/>` in the form views. The affected files are
`views/mp_material_grade_views.xml`, `mp_component_views.xml`,
`mp_tool_views.xml`, `mp_tool_maintenance_views.xml`,
`mp_molding_parameter_views.xml` and `mp_injection_molding_views.xml`.

### B2. Inheritance of the manufacturing order form

`views/mrp_production_views.xml` inserts a smart button using
`<xpath expr="//div[@name='button_box']" position="inside">`. The `button_box`
container is the universal Odoo convention for smart buttons, but **the exact
arch of the Odoo 19 `mrp.production` form view could not be verified**.

**Risk:** if that container is absent or renamed, the module fails to install.

**Action for the receiving team:** this is the single highest-risk file in the
module. If installation fails with an xpath error, remove
`views/mrp_production_views.xml` from the `data` list in `__manifest__.py`. The
module loses only the navigation button; the `mp_run_ids` relation and the
`action_view_mp_runs` method remain available.

---

## Part C — Functional limitations

| Limitation | Consequence | Workaround |
|---|---|---|
| No electronic signatures | Identities are Odoo accounts; no signature meaning is captured | Deploy a dedicated signature module |
| No comprehensive audit trail | Field-level change history is limited to `tracking=True` fields in the chatter | Deploy a dedicated audit trail module |
| No instrument calibration management | Parameter values are keyed in without instrument status verification | Deploy a calibration module and reference it by procedure |
| No automated data acquisition from moulding machines | All readings are manual | Machine integration would require a site-specific interface |
| Reject rate excludes start-up scrap by design | The figure is a *quality* reject rate, not a total material yield | Total scrap is available as `qty_startup_scrap` plus `qty_rejected` |
| Cavity blocking does not adjust expected output | Parts-per-shot is not modelled | Record actual produced quantity |
| Late entry of readings is possible | A reading can be captured after the event with the current timestamp | Enforce contemporaneous recording by procedure |
| Single-level genealogy | The traceability wizard resolves one moulding step, not an assembly tree | Multi-level genealogy requires the manufacturing order structure |
| No demo data shipped | Nothing to explore on a fresh database | Follow `doc/CONFIGURATION.md` |

---

## Part D — Verification limitations of the delivery itself

| What was done | What was **not** done |
|---|---|
| Every Python file parsed with `ast` / `py_compile` | Nothing executed against a Python interpreter with Odoo loaded |
| Every XML file parsed with `lxml` | No view validated against the Odoo view schema |
| Custom static checker run clean, itself validated with 16 deliberate fault injections | `flake8`, `pylint`, `pylint-odoo` **not run** — not installable without network access |
| 100+ test methods written | **Tests never executed. No coverage measured. No pass rate exists.** |
| Manifest, ACL and reference integrity cross-validated statically | Module **never installed** on Odoo 19; no upgrade path tested |

The static checker's own known blind spots: it cannot resolve fields inside
inline sub-views (it skips them rather than guess), it cannot validate view
attribute semantics, and it cannot confirm that any Odoo API used actually
exists in Odoo 19.
