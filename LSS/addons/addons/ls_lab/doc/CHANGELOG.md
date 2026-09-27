# CHANGELOG — `ls_lab`

All notable changes to this module are recorded here.
Format follows Keep a Changelog; versioning follows the Odoo module convention
`<odoo version>.<major>.<minor>.<patch>`.

---

## 19.0.1.0.1 — 2026-09-25

Remediation of the independent audit of 2026-09-25 (report AUDIT_REPORT_FINAL_2026-09-25.md; details in REMEDIATION_REPORT_2026-09-25.md at the project root).

- F-06: a customer delivery of a lot held by an open OOS/OOT investigation, or by a reject / quarantine / further-investigation disposition, is refused.
- A failing result entered by an analyst opens the investigation (created with superuser rights; the analyst is recorded as investigator).
- F-16: samples and stability studies refuse the lot of another product and check company consistency.
- F-27: the viewer role implies Internal User. F-23: `@api.ondelete` deletion guards. Tests ported (F-40).

## [19.0.1.0.0] — 2026-08-07

### Added

- Analytical test method register with draft → review → approved → obsolete
  lifecycle, immutability once approved, and version succession.
- Product specifications with line-level acceptance criteria, the same lifecycle,
  and a constraint permitting one approved version per product and type.
- Six criterion types: range, minimum, maximum, text match, pass/fail,
  informative.
- Sample registration binding a sample to one approved specification version and
  generating one result line per specification line.
- Sample state machine: received → in progress → testing → results recorded →
  reviewed → approved → reported, plus a terminal cancelled state.
- Test results with a conformity evaluation computed from the approved
  specification and not writable by any user.
- Automatic OOS creation on a non-conforming result and automatic OOT creation on
  a justified out-of-trend assertion.
- Two-phase OOS investigation with a Phase I laboratory assessment checklist,
  Phase II investigation beyond the laboratory, authorised retest and resample,
  final conclusion and product disposition.
- Stability studies with configurable storage conditions and time points, derived
  due dates, and a pull wizard that creates the sample.
- Certificates of Analysis with issue, supersession and versioning.
- Two QWeb PDF reports: Certificate of Analysis and OOS Investigation Report.
- Four security groups with an implication hierarchy, a `res.groups.privilege`
  record, a complete ACL matrix and record rules.
- Segregation of duties enforced at the ORM layer for result review, sample
  approval and investigation closure.
- Three notification-only scheduled actions: due stability time points, overdue
  samples, and test methods due for periodic review.
- Three wizards: sample cancellation with mandatory reason, stability pull, and
  signature-intent confirmation.
- Offline static checker validating against the real Odoo 19 RNG schemas.
- Negative-control harness seeding 25 faults; all 25 detected.
- Retrofit scanner for other suite modules.
- 88 tests across 8 suites, written but not executed.

### Verified against Odoo 19 source (branch `19.0`)

- `res.users.group_ids`, `ir.rule.groups`, `ir.ui.menu.group_ids`
- `res.groups.privilege_id` and the `res.groups.privilege` model
- `models.Constraint` as the constraint mechanism, used by core itself
- `uom.uom` and `stock.lot` model names
- absence of `numbercall` and `doall` from `ir.cron`
- absence of the `quality` module from Community Edition
- per-view-type RNG schemas; no `view.rng` exists
- `<group>` permits neither `expand` nor `string`

### Known limitations

- Not installed on a live Odoo 19 server; delivery gate is CONDITIONAL PASS.
- Tests written but not executed; no coverage measured.
- Electronic signature is intent-confirmation only; Part 11 is not claimed.
- No statistical trend analysis; no shelf-life extrapolation.
- No enforcement that an instrument is in calibration at test time.
