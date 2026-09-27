# ls_capa 19.0.1.0.0 — Release Notes

**Release type:** Release candidate
**Target:** Odoo 19.0 Community Edition
**Date:** July 2026

---

## Summary

First release of the CAPA Management module of the Life Sciences Suite,
implementing section 7.3 of the suite functional specification.

## What is included

- CAPA records with the specified eight-state lifecycle, each transition
  gated by a server-side business rule.
- Root cause analysis supporting Five Whys, Ishikawa and FMEA, with an
  automatically computed Risk Priority Number.
- Corrective and preventive action management with mandatory completion
  evidence and optional mirroring to `project.task`.
- Effectiveness verification against pre-defined acceptance criteria,
  with one-click escalation to a follow-up CAPA.
- Four security groups in an implication chain, 20 access control lines
  and five multi-company record rules.
- Form, list, kanban, search, pivot and graph views; a closure wizard; a
  QWeb PDF report; four sequences; an optional overdue notification
  scheduled action shipped inactive.
- 112 automated tests and a complete documentation set.

## Odoo 19 compatibility

Built specifically for Odoo 19 and **not backward compatible**. It uses
`<list>`, the `<chatter>` element, `<t t-name="card">` and
`res.groups.privilege`, none of which exist in Odoo 18 or earlier.

## Known limitations

- Electronic signatures are not implemented. Odoo user tracking is not
  a 21 CFR Part 11 signature.
- The audit trail is `mail.thread` tracking, which is not hash-chained
  or tamper-evident.
- No dependency on `ls_qms`, which does not exist as an installable
  module. See architectural decision AD-01.
- CAPA records still in the Identified status can be deleted by a CAPA
  Manager.

## Before you deploy

This release has **not** been executed against a live Odoo 19 instance.
Five gates remain open:

1. Install into Odoo 19.0 Community and confirm the registry loads.
2. Run the test suite and meet the 95% coverage threshold.
3. Run `flake8`, `pylint-odoo` and `pre-commit`.
4. Confirm the `res.users` groups field name on the target build.
5. Perform an upgrade test.

The CI workflow at `.github/workflows/ci.yml` executes all five. Do not
deploy to a validated environment until it passes and the qualification
activities in `docs/VALIDATION_REPORT.md` are complete.

## Upgrade path

Not applicable — this is the first release.
