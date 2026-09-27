# Changelog — `ls_environmental_monitoring`

All notable changes to this module are recorded here. The format follows
Keep a Changelog, and the module uses the Odoo convention
`<odoo version>.<major>.<minor>.<patch>`.

## 19.0.1.0.1 — 2026-09-25

Remediation of the independent audit of 2026-09-25 (report AUDIT_REPORT_FINAL_2026-09-25.md; details in REMEDIATION_REPORT_2026-09-25.md at the project root).

- F-41 (decision): the access rights are kept as specified in the README role table: limits and plans are authored by managers; the tests now author them with a second manager.
- A reviewed sample can be returned to analysis (transition added, as documented on the action). Monthly and yearly schedules are anchored on the start date and no longer drift (31 Jan, 28 Feb, 31 Mar).
- Counter searches accept the `in` / `not in` operators that Odoo 19 sends; the approved-limit counter declares its dependency.
- F-27: the three roles imply Internal User. F-23: `@api.ondelete` deletion guards.

## [19.0.1.0.0] — July 2026

First release. Target platform: Odoo 19.0 Community Edition.

### Added

**Programme definition**
- Cleanroom grades, monitored areas with a nestable hierarchy, monitored
  parameters and documented sampling and test methods.
- Sampling points recording physical position, selection rationale and whether
  the location is critical.

**Acceptance criteria**
- Alert, action and specification limits per sampling point, parameter,
  occupancy state and bound direction.
- Limit versioning with supersession, mandatory justification, approval by a
  second person, and immutability once approved.
- Threshold ordering validation consistent with the bound direction.
- Optional escalation of alert exceedances to a formal excursion.

**Scheduling**
- Monitoring plans with lines, versioning and approval by a second person.
- Idempotent sample generation, by wizard or by a daily job, with calendar
  arithmetic for monthly and yearly frequencies.
- Overdue detection with a search method, and a daily notification job.

**Execution**
- Sample lifecycle from draft to approved with a declarative transition map.
- Attribution of collection, results entry, review and approval to the acting
  user with a system-set timestamp.
- Rejection of a collection timestamp in the future.
- Mandatory reason for cancellation, with the record retained.

**Evaluation**
- Automatic evaluation against approved limits, with the most severe breached
  threshold determining the outcome.
- Snapshotting of the applied thresholds onto each result.
- Support for quantitative and qualitative parameters, and for parameters
  constrained on both sides through paired limits.
- Freezing of results on approval, with a controlled amendment route that
  preserves the original value.

**Excursions**
- Automatic creation on approval for breaches requiring one, grouped per sample.
- Lifecycle from open through assessment and investigation to controlled
  closure, with closure by a user other than the owner.
- Free-text external reference and an overridable hook for a corrective action
  module.
- Excursions cannot be deleted, only cancelled.

**Trending**
- Descriptive analysis over released results with counts, exceedance rates and
  summary statistics.
- Statistics that are undefined for the data are flagged as unavailable rather
  than reported as zero.
- Direction indicator that reports insufficient data below six values, labelled
  in the interface as not a significance test.

**Security**
- Three roles with 46 explicit access rules and no implied relationships.
- Thirteen global record rules for multi-company isolation.
- Segregation of duties enforced in the model layer.

**Reporting**
- Environmental Monitoring Record and Excursion Report as QWeb PDF.

**Quality artefacts**
- Offline static checker validating manifest completeness, XML id resolution,
  view field resolution, access rule coverage, removed Odoo 18 constructs,
  placeholder tokens, raw SQL and licence headers.
- Negative control harness proving the checker detects 19 fault classes.
- 142 tests: 38 pure-logic, executed at 100% measured statement coverage, and
  104 database-backed, written but not executed.
- Eleven documents including a regulatory mapping with per-provision
  verification status and a full deviations register.

### Deliberately not included

Electronic signatures; field-level audit trail; corrective and preventive action
management; deviation management; instrument interfaces; continuous monitoring;
product disposition decisions; statistical significance testing; and any numeric
acceptance criterion. Reasons are given in `doc/regulatory_mapping.md`
section 4.

### Known limitations

- Never installed against a live Odoo 19 instance.
- 104 of 142 tests never executed.
- `flake8` and `pylint-odoo` not run; unavailable in the build environment.
- Several Odoo 19 API facts unverified and engineered around; see
  `doc/deviations.md` section B. The `<chatter/>` element is the
  highest-severity remaining risk.
