# Changelog

## 19.0.1.0.1 — 2026-09-25

Remediation of the independent audit of 2026-09-25 (report AUDIT_REPORT_FINAL_2026-09-25.md; details in REMEDIATION_REPORT_2026-09-25.md at the project root).

- F-37: validation items can be signed (signature mixin); an execution approval marks the protocol executed whether the execution was created from the protocol button or directly.
- F-42: the daily validation status job saves the recomputed status.
- Password verification works with `auth_totp` installed (`credentials` parameter name).
- Counter searches accept the `in` / `not in` operators that Odoo 19 sends. F-32: dead `numbercall` hook removed.
- Reports: `t-field` moved out of table cells. F-23: `@api.ondelete` deletion guards. Tests ported (F-40).

