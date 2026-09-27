# Changelog

All notable changes to `ls_deviation` are recorded here.
Format based on Keep a Changelog. Versioning follows the Odoo convention
`<odoo_version>.<major>.<minor>.<patch>`.

## 19.0.1.0.1 — 2026-09-25

Remediation of the independent audit of 2026-09-25 (report AUDIT_REPORT_FINAL_2026-09-25.md; details in REMEDIATION_REPORT_2026-09-25.md at the project root).

- F-27: the viewer role implies Internal User.
- Tests ported (F-40): date fixtures, stage log read back from the database, Odoo 19 boolean search operator.

## [19.0.1.0.0] — 2026-07-24

### Added

- `ls.deviation` with a seven-state workflow, 56 fields, chatter, activities and tracking
- `ls.deviation.investigation` with configurable root cause analysis methods
- `ls.deviation.disposition` with seven decisions and segregated approval
- `ls.deviation.action` for immediate, containment and correction actions
- `ls.deviation.stage.log`, append-only transition log
- `ls.deviation.type`, `ls.deviation.category`, `ls.deviation.rca.method`, `ls.deviation.tag` master data
- Closure targets per severity on `res.company`, exposed in Settings
- Close, Cancel/Send Back and Extend Target Date wizards
- Daily overdue notification scheduled action with mail template
- QWeb PDF deviation report including the transition log
- Four hierarchical security groups, 29 ACL rows, 11 record rules
- Form, list, kanban, search, graph, pivot, calendar and activity views
- 92 automated test methods across 8 modules
- 12 documentation files
- 8 deviation types, 8 categories and 5 RCA methods as supplied master data
- Installation-safe demo data referencing no external master records

### Regulatory basis

- Mandatory `justification` field per 21 CFR 211.100(b)
- Mandatory `extension_rationale` and `other_batches_lot_ids` per 21 CFR 211.192
- Mandatory `conclusion` and `followup` at closure per 21 CFR 211.192

### Known limitations

- Never installed or executed; see `docs/00_VERIFICATION_STATUS.md`
- No 21 CFR Part 11 electronic signature
- Transition log is append-only at application level only
- Disposition records a decision; it does not move stock
- No dependency on `ls_qms` or `ls_capa`, which do not exist
