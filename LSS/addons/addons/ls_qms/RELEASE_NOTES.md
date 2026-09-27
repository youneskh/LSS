# Release Notes — `ls_qms` 19.0.1.0.0

## Summary

First release of the Quality Management System module of the Life Sciences
Suite, for Odoo 19 Community Edition. It covers controlled quality
documentation, quality objectives measured against recorded values, and
quality records under retention control.

## Compatibility

| Item | Value |
|---|---|
| Odoo | 19.0 Community Edition only |
| Earlier Odoo series | Not supported. The module uses `models.Constraint`, `<list>`, `<chatter/>` and `res.groups.privilege`, all specific to Odoo 19 |
| Odoo Enterprise | Not required, and no Enterprise code is used |
| Dependencies | `base`, `mail`, `hr` |

## Upgrade path

None. This is the first release.

## Before deploying

Read `docs/13_validation_report.md`. Three points decide whether this release
fits your context:

1. The module has never been installed or executed. Install it in a
   qualification environment and run the test suite before any production use.
2. Approval is not an authenticated electronic signature, and change tracking
   is not a protected audit trail. If 21 CFR Part 11 applies to your records,
   this release alone does not meet sections 11.10(e), 11.100 and 11.200.
3. No ANPP technical requirement was verified during development, and none is
   claimed.

## Deferred to a later release

| Item | Reason |
|---|---|
| Authenticated electronic signature | Belongs to `ls_electronic_signature`; the extension point is in place |
| Field level audit trail with hash chain | Belongs to `ls_audit_trail` |
| Translation template | Must be produced by the Odoo export from an installed database |
| Distribution and acknowledgement of documents | Not in the scope of section 7.2 of the reference specification |
