# SPECIFICATION DEVIATIONS — `ls_lab`

Every departure from the Life Sciences Suite Functional Specification v1.0
(§8.6 and related sections), with its rationale. Nothing is omitted silently.

---

## D-01 — `quality` is not a dependency, and the specification is wrong about it

**Specification:** §5.2.6 documents `quality` as a Layer 1 **native Odoo 19
Community** module under LGPLv3 with models `quality.point`, `quality.check`,
`quality.alert`, and §15.1 lists its dependencies.

**Finding:** `quality` **does not exist in Odoo 19 Community Edition**. The
`addons/` listing for branch `19.0` contains 631 modules and **zero** whose name
contains `qualit`; `addons/quality/__manifest__.py` returns HTTP 404.

**Deviation:** `ls_lab` neither depends on `quality` nor references `quality.*`
models. All quality-control functionality is implemented natively.

**Impact on the suite:** §5.2.6 and §15.1 of the specification should be
corrected. Any earlier module declaring `quality` as a dependency will fail to
install.

---

## D-02 — `maintenance` dependency corrected

**Specification:** §5.2.10 and §15.1 state `maintenance` depends on `base, hr`.

**Finding:** the Odoo 19 manifest declares `'depends': ['mail']`. `maintenance`
**is** present in Community.

**Deviation:** documentation-level correction only; `ls_lab` does not depend on
`maintenance`.

---

## D-03 — No suite module declared as a dependency

**Specification:** §15.4 gives `ls_lab` dependencies as `ls_qms`,
`ls_calibration`, `stock`.

**Deviation:** declared dependencies are `base, mail, product, stock, uom`.

**Rationale:** declaring a sibling suite module that is not installable blocks
installation of this one. Cross-module links are carried as free-text reference
fields instead: `capa_reference`, `validation_reference`,
`instrument_reference`. This is the architectural principle already established
across the suite.

**Consequence:** instrument calibration status is **not** enforced by this module.
An organisation wanting that enforcement must add a bridge module.

---

## D-04 — Model naming follows the specification, not Odoo convention

**Specification:** §8.6 names models `ls.lab.test_method`, `ls.lab.test_result`,
`ls.lab.stability_study`.

**Deviation:** none — the specification names are used verbatim, including
underscores, although the prevailing Odoo convention is dot separation.

**Rationale:** consistency with the specification and with earlier suite modules
outweighs convention. Changing it later would be a breaking migration.

---

## D-05 — Additional models beyond the specification

**Specification:** §8.6 lists six models.

**Deviation:** ten concrete models are delivered. Added:

| Model | Reason |
|-------|--------|
| `ls.lab.specification_line` | A specification without line-level acceptance criteria cannot drive automatic evaluation. |
| `ls.lab.stability_timepoint` | Pull scheduling has no home otherwise. |
| `ls.lab.coa` | §8.6 requires CoA generation; it needs a record to version and freeze. |
| `ls.lab.storage_condition` | Required by both samples and stability studies; avoids free-text drift. |

---

## D-06 — OOS model renamed in scope

**Specification:** `ls.lab.oos`.

**Deviation:** the model is `ls.lab.oos` as specified, but handles **both** OOS
and OOT through the `oos_type` field rather than a separate model.

**Rationale:** the two share an identical investigation lifecycle. Two models
would duplicate the entire two-phase structure.

---

## D-07 — Out-of-trend is asserted, not computed

**Specification:** §8.6 lists "OOS/OOT Management".

**Deviation:** the module performs **no statistical trend analysis**. `is_oot` is
a Boolean asserted by the analyst or reviewer, with a mandatory justification.

**Rationale:** out-of-trend determination requires a historical control model,
control-limit policy and statistical method that vary by organisation and product.
Automating it with an assumed method would produce results the organisation could
not defend. Stated in §1.8 of the business analysis and in the user manual.

---

## D-08 — Stability shelf-life extrapolation is out of scope

**Specification:** §8.6 lists "Stability Studies — ICH stability study management".

**Deviation:** studies, time points, pull samples and results are managed.
Regression modelling, extrapolation and shelf-life assignment are **not**
implemented.

**Rationale:** the statistical evaluation of stability data is being reorganised
by the consolidated ICH Q1, which reached Step 2b on 11 April 2025 and had not
reached Step 4 at build time. Implementing an extrapolation method now would
encode a reference in transition.

---

## D-09 — No storage conditions or time points shipped

**Deviation:** the module ships **no** storage condition records, **no** time
point schedules, **no** acceptance limits and **no** pharmacopoeial content —
not even as demo data.

**Rationale:** ICH Q1 is mid-revision (D-08). Shipping values would embed a
guideline version the organisation may not be operating under, and demo data
carrying acceptance limits could be mistaken for approved configuration. A
regression test (`test_no_storage_condition_shipped`) enforces this.

---

## D-10 — Instrument calibration linkage is by reference

**Specification:** §8.6 lists "Instrument Calibration — Link to calibration
management".

**Deviation:** `instrument_reference` is a free-text `Char`. There is no
Many2one to a calibration record and **no enforcement that an instrument is in
calibration** at the time of test.

**Rationale:** follows D-03. This is a real functional gap relative to the
specification and is stated as such rather than implied to be covered.

---

## D-11 — `uom.uom` used instead of the free-text workaround

**Deviation from earlier suite modules:** earlier modules used a free-text `Char`
for units because `uom.uom` availability in Community could not be verified.

**Finding:** `uom` is present in Odoo 19 Community and the model is `uom.uom`
(`addons/uom/models/uom_uom.py` line 18).

**Deviation:** `ls_lab` uses a proper `Many2one` to `uom.uom`. This is an
improvement, but it makes `ls_lab` inconsistent with earlier modules until they
are retrofitted.

---

## D-12 — Record rules are group-scoped where useful

**Deviation from earlier suite modules:** earlier modules made all record rules
global because the `ir.rule` group field name was unverified.

**Finding:** the field is `groups` (`odoo/addons/base/models/ir_rule.py` line 25).

**Deviation:** `ls_lab` uses group-scoped rules alongside global multi-company
rules.

---

## D-13 — Sample state machine extended by one state

**Specification:** §8.6 gives Received → In Progress → Testing → Results Recorded
→ Reviewed → Approved → Reported.

**Deviation:** all seven specified states are implemented verbatim, plus a
terminal `cancelled` state.

**Rationale:** a sample can be broken, mis-registered or withdrawn. Without a
cancellation path the only alternative is deletion, which would destroy the audit
history.

---

## D-14 — Menu structure follows the specification with two additions

**Specification:** §8.6 lists ten menu entries.

**Deviation:** all ten are present. Added: **Stability → Time Points** and
**Configuration → Storage Conditions**, both required to reach models the
specified menus do not expose.

---

## D-15 — Certificate reads results at print time

**Deviation:** the CoA renders the source sample's results at print time rather
than storing a snapshot.

**Rationale:** the source sample is frozen at `approved` and its reviewed results
cannot be modified, so the rendered content is stable. Accepted as architecture
review finding AR-04 rather than left undocumented.

**Residual risk:** if a future module were to make approved samples editable,
this assumption would break.

---

## D-16 — Outlier testing not implemented

**Deviation:** no outlier test is provided in the OOS investigation.

**Rationale:** the FDA OOS guidance treats outlier testing restrictively.
Providing a button for it would invite exactly the misuse the guidance warns
against. Investigators record their scientific reasoning in the findings fields
instead.
