# Compliance Checklist

Module: `ls_document_management` — Odoo 19 Community. Phase 10 deliverable.

Legend: [x] done and verifiable offline · [~] done by construction, runtime
confirmation pending · [ ] not done / out of scope (with note).

## Coding requirements

- [x] Installs successfully — *by construction; runtime install pending (V-1).* Marked [~] in substance.
- [~] Installs successfully on Odoo 19 Community
- [~] Upgrades successfully (versioned, `noupdate` data, no deprecated constructs)
- [x] Respects official Odoo module architecture (standard layout, manifest)
- [x] Respects OCA conventions where applicable (licence header, version string, structure)
- [x] Does not modify Odoo core
- [x] Uses inheritance/mixins rather than core edits (`mail.thread`, `mail.activity.mixin`)
- [x] Follows MVC/ORM separation (models, views, security, data, report, wizard)
- [x] ORM best practices (compute with depends, constrains, model_create_multi)
- [x] No raw SQL in module code (one parameterised statement in a test only)
- [x] SQL-injection safe (declarative constraints; parameterised test query)
- [x] Input validation (Python + SQL constraints; state guards)
- [x] Respects access rights (26-row ACL, integrity-checked)
- [x] Respects record rules (multi-company + folder-scoped, balanced domains)

## Odoo 19 currency (verified against official docs / release notes)

- [x] Uses `<list>` not `<tree>`
- [x] Uses `<chatter/>` not `oe_chatter` div
- [x] Uses `res.groups.privilege` + `privilege_id`
- [x] Uses `group_ids` / `user.group_ids` not `groups_id`
- [x] `ir.cron` without removed `numbercall`/`doall`
- [x] Uses `models.Constraint` / `models.UniqueIndex`
- [x] Uses `Many2oneReference` and `check_company`
- [x] No `attrs=` / no `states={` field attribute

## Security and integrity

- [x] Defence in depth (ACL + record rules + server-side role checks)
- [x] Segregation of duties (Approver excludes Editor)
- [x] Approver identity enforced in `write`, not only UI
- [x] Publish/archive reserved to Manager, enforced server-side
- [x] Version content immutable after creation
- [x] SHA-256 checksum stored and verifiable
- [x] No automated deletion of controlled records
- [x] Legal hold blocks automatic archiving

## Quality gates

- [x] Static self-check: PASS (see static_check_output.txt)
- [x] Full docstring coverage
- [x] No placeholders (TODO/FIXME/stub/NotImplementedError)
- [x] Line length within 88 characters
- [~] flake8 clean — *not run offline (V-3)*
- [~] pylint-odoo clean — *not run offline (V-3)*
- [x] XML well-formed
- [~] XML valid against Odoo view schema — *validated for well-formedness; full schema validation needs Odoo (V-1)*

## Testing

- [x] Unit/functional/security tests written (101 methods)
- [ ] Tests executed — **pending a real Odoo 19 instance (V-2)**
- [ ] Coverage measured — **pending (V-2); no coverage figure claimed**

## Documentation

- [x] README
- [x] Installation guide (manuals.md §1)
- [x] Configuration guide (manuals.md §2)
- [x] User manual (manuals.md §3)
- [x] Administrator manual (manuals.md §4)
- [x] Developer manual (manuals.md §5)
- [x] API notes (manuals.md §6)
- [x] Business and regulatory analysis
- [x] Architecture review
- [x] Static analysis report
- [x] Test and validation report
- [x] Changelog

## Regulatory posture

- [x] No false claim of compliance or certification anywhere
- [x] Electronic-signature limitation stated explicitly (not 21 CFR Part 11 subpart C)
- [x] Audit-trail limitation stated (relies on chatter; full trail is `ls_audit_trail`)
- [x] Full-text-content search limitation stated
- [x] "Software does not equal compliance / validation" stated

## Overall

**CONDITIONAL PASS.** Everything verifiable without an Odoo runtime is complete
and passing. The three runtime gates that remain — install (V-1), run tests
(V-2), run pylint-odoo/flake8 (V-3) — must be executed by the implementing team
before production use. This checklist does not mark those as done, because they
have not been done here.
