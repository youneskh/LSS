# Changelog

## 19.0.1.0.1 — 2026-09-25

Remediation of the independent audit of 2026-09-25 (report AUDIT_REPORT_FINAL_2026-09-25.md; details in REMEDIATION_REPORT_2026-09-25.md at the project root).

- Tests ported to Odoo 19 (F-40): `group_ids`, single-class `assertRaises`, attempt log kept outside the test savepoint, gap test detaches the attempt log first.
- F-26: the module is delivered in `test_addons/`, outside the production addons path.

