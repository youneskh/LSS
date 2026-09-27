# Changelog

All notable changes to `ls_change_control` are recorded here. The format
follows the Keep a Changelog convention, and the module uses the Odoo version
scheme `<odoo>.<major>.<minor>.<patch>` prefixed by the Odoo series.

## 19.0.1.0.1 — 2026-09-25

Remediation of the independent audit of 2026-09-25 (report AUDIT_REPORT_FINAL_2026-09-25.md; details in REMEDIATION_REPORT_2026-09-25.md at the project root).

- Submitting a request for review no longer fails: the managers are read from `res.groups.all_user_ids` (`users` was removed in Odoo 19).
- The assessment note and the removal of activities by approvers are performed with superuser rights (the actors may not hold write access on the request).
- F-27: the viewer role implies Internal User. F-29: constraint of the decision wizard raises `ValidationError`.
- Tests ported (F-40): multi-company fixture, overdue reminders run with `freezegun`.

## [19.0.1.0.0] - 2026-07-24

### Added

* Change request model `ls.change_control.request` with the nine state lifecycle Draft, Under Review, Impact Assessment, Approved, Implementation, Verified, Closed, Rejected, Cancelled.
* Impact assessment model `ls.change_control.assessment`, one record per impact area.
* Approval model `ls.change_control.approval` with decision metadata and the `_apply_signature` extension point.
* Implementation action model `ls.change_control.implementation` with 12 action types and a mandatory evidence reference.
* Effectiveness verification model `ls.change_control.verification` with acceptance criteria and a follow-up mechanism.
* Configuration models `ls.change_control.category`, `ls.change_control.impact_area` and `ls.change_control.approval_template`.
* Four company parameters on `res.company` with a dedicated settings form.
* Decision wizard `ls.change_control.decision_wizard` for closure, rejection and cancellation.
* Four security groups in a cumulative hierarchy, 23 access rights lines and 7 record rules including 5 global multi-company rules.
* Seed configuration: 14 impact areas, 10 categories, 29 approval template lines.
* Three mail templates and three daily scheduled actions.
* Change Control Record report in PDF.
* Views: form, list, kanban, search, graph, pivot and activity on the request; form, list and search on the four child models and the two configuration models.
* Demo data: three draft change requests and three implementation actions.
* Translation template with 403 entries.
* Test suite: 121 tests in 11 files.
* Documentation set: 16 documents.

### Security

* Content fields of a request are frozen once it is submitted, for every user.
* Workflow fields are refused outside superuser mode, which an RPC context cannot reach.
* Completed assessments, decided approvals, closed actions and completed verifications are immutable and undeletable.
* A submitted change request can never be deleted or archived.

### Known limitations

* The module was never installed and the test suite was never executed. See `docs/validation_report.md`.
* No re-authentication of the signer at the moment of approval. Assigned to `ls_electronic_signature`.
* No dependency on `ls_qms` and `ls_validation`: those modules do not exist. See deviation D-1 in `docs/validation_report.md`.
