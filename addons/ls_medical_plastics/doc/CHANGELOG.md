# Changelog

All notable changes to `ls_medical_plastics` are recorded here.
The format follows Keep a Changelog; versioning follows the Odoo convention
`19.0.<major>.<minor>.<patch>`.

---

## 19.0.1.0.1 — 2026-09-25

Remediation of the independent audit of 2026-09-25 (report AUDIT_REPORT_FINAL_2026-09-25.md; details in REMEDIATION_REPORT_2026-09-25.md at the project root).

- F-42: the tool status job saves the recomputed maintenance and requalification status.
- F-16: material consumption lines and runs refuse the lot of another product. Reject quantities cannot exceed production when a reject line is added.
- A draft run no longer prevents sending its tool to maintenance. F-22: `<chatter/>` in 6 forms.
- F-27: the viewer role implies Internal User. F-23: `@api.ondelete` deletion guards.
- Tests ported (F-40): specifications reviewed by a second engineer, onchange tested on a form record.

## [19.0.1.0.0] — August 2026

### Added

**Tool management**
- `ls.mp.tool`: mould and tool register with a six-state lifecycle.
- `ls.mp.tool.cavity`: cavity register generated automatically from the cavity
  count; individual cavities can be blocked with a mandatory reason.
- `ls.mp.tool.maintenance`: maintenance events with shot-count snapshot,
  findings, actions taken and automatic quarantine when requalification is
  required.
- Cumulative shot counting derived from closed runs plus an opening counter.
- Dual preventive maintenance scheduling on shot count and elapsed months, with
  a four-value status indicator.
- Requalification scheduling and an overdue flag.

**Materials and components**
- `ls.mp.material.grade`: polymer and masterbatch register with a six-state
  qualification workflow and a drug-contact flag.
- `ls.mp.component`: moulded article master data with category, criticality,
  sterility, approved grades and a four-state release workflow.

**Process specifications**
- `ls.mp.molding_parameter`: versioned specification with a draft, review and
  approval workflow; only one approved version per component, tool and work
  centre; approving supersedes the previous version automatically.
- `ls.mp.molding_parameter.line`: numeric and qualitative parameters with
  ranges, critical flags and monitoring frequencies.
- Segregation of duties enforced at ORM level between author, reviewer and
  approver.
- Periodic review scheduling.

**Production execution**
- `ls.mp.injection_molding`: eight-state run record with setup, start-up
  verification, production, review and closure.
- Production blocked at start-up when required readings are missing, material
  consumption is unrecorded, or a critical parameter is out of tolerance.
- Review blocked for the operator and the setter of the run.
- Closed runs frozen against modification and deletion.
- `ls.mp.injection_molding.reading`: append-only readings that freeze the
  acceptance criteria at capture; corrections supersede rather than overwrite.
- `ls.mp.injection_molding.material`: per-lot consumption with a mandatory lot
  reference for drug-contact grades.
- `ls.mp.injection_molding.scrap` and `ls.mp.scrap.reason`: reject recording by
  reason and cavity, with start-up scrap excluded from the quality reject rate.

**Wizards**
- Bulk parameter reading capture with correction support.
- Controlled return of a tool to service.
- Traceability enquiry across four search modes.

**Reporting**
- Moulding run record, including superseded readings with correction reasons.
- Tool logbook.
- Graph and pivot analysis restricted to closed runs.

**Security**
- Five roles in an implication chain.
- 41 access control lines; no role holds write or delete on readings.
- 12 global multi-company record rules.

**Platform**
- `models.Constraint` used throughout in place of `_sql_constraints`.
- `<list>` view syntax; `_compute_display_name`; `self.env._()`; `stock.lot`.

**Quality artefacts**
- 139 automated tests across 11 classes.
- Offline static checker, itself validated by 16 deliberate fault injections.
- Full documentation set including a deviations and limitations register.

### Known limitations

No electronic signatures, no comprehensive audit trail, no calibration
management, no machine data acquisition. Tests are written but have never been
executed. See `DEVIATIONS_AND_LIMITATIONS.md` and `VALIDATION_REPORT.md`.
