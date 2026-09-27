# Validation Report

## Life Sciences Suite - Risk Management (`ls_risk_management`)

Version 19.0.1.0.0 | 30 July 2026

---

## 1. Overall delivery verdict

# CONDITIONAL PASS

The module is complete against its specification, statically clean, and
documented. It has **never been installed, started or executed**, because no
Odoo runtime, no PostgreSQL instance and no network access were available in
the build environment.

It is therefore **not** production-ready in the sense of being proven. It is
ready to enter installation and operational qualification. The outstanding
tasks in section 5 must be completed by the receiving team before the module
is used on any regulated system.

No pass rate, coverage figure or performance number is claimed anywhere in
this delivery, because none was measured.

---

## 2. Phase gates

| Phase | Verdict | Evidence and qualification |
|---|---|---|
| 1. Business analysis | **PASS** | Scope, roles and lifecycle derived from specification section 7.16. Three roles defined and implemented. Out-of-scope items declared in `DEVIATIONS.md` D-09 and D-10. |
| 2. Regulatory analysis | **PASS with declared limits** | ISO 14971:2019 clause structure verified from the published table of contents; the acceptability-criteria requirement verified from the ISO catalogue entry. The normative text is paywalled, was not retrieved, and is not reproduced. ANPP and ICH Q9 could not be verified and are **not claimed**, departing from the suite specification's traceability matrix. See `VERIFICATION_LOG.md` section 2. |
| 3. Functional specification | **PASS** | Lifecycles, workflows, business rules, menus, filters, group-by, reports, wizards and the scheduled action are all specified and implemented. |
| 4. Technical specification | **PASS** | 17 models, 212 fields, 22 database constraints, 35 ACL lines, 9 record rules, 2 reports, 1 cron. Enumerated in `API_REFERENCE.md`, generated from the sources by AST rather than maintained by hand. |
| 5. Architecture review | **PASS** | See section 3. |
| 6. Development | **PASS** | 7,281 lines of Python and 2,644 lines of XML. No placeholders, no dead code, no commented-out code, no raw SQL. Enforced by `static_check.py`. |
| 7. Testing | **CONDITIONAL PASS** | 161 tests written across 8 modules. **Never executed.** No coverage measured. The 95% target is **not demonstrated**. See `TEST_REPORT.md`. |
| 8. Static analysis | **CONDITIONAL PASS** | Custom offline analyser reports no findings, and was itself validated by 22 negative controls. `flake8`, `pylint` and `pylint-odoo` **could not be run**: no network access, so no package installation. |
| 9. Documentation | **PASS** | 12 documents. API reference and translation template generated from source. |
| 10. Final validation | **CONDITIONAL PASS** | This report. |

---

## 3. Architecture review

| Criterion | Assessment |
|---|---|
| Odoo architecture | Standard layout. No core model is modified. Inheritance is used for `mail.thread`, `mail.activity.mixin` and the module's own role mixin. |
| OCA practice | AGPL-3, semantic version, `development_status`, one model per file, alphabetised imports, complete docstrings. |
| Clean architecture | Regulatory constants isolated in `constants.py`. Acceptability criteria are data, not code. Role assertions isolated in one mixin. |
| SOLID | Single responsibility per model. The role mixin is open for extension by inheritance. Wizards depend on model methods rather than reimplementing rules. |
| DRY | The Risk Manager assertion exists once and is used nine times. Data XML with cross-references is generated from one source of truth. |
| KISS | No JavaScript, no custom widgets, no controllers, no raw SQL. |
| Separation of concerns | ISO 14971 estimation (severity, probability) is structurally separate from FMEA rating (severity, occurrence, detection). |
| Upgrade safety | Shipped configuration is `noupdate="1"`. No unverified API is relied upon; see section 4. |
| Extensibility | Generic `linked_model_id`/`linked_res_id` extension point, re-parentable root menu, extensible selections. |
| Maintainability | 161 tests, a validated static analyser, and generated reference documentation. |

---

## 4. Risk-based assessment of unverified platform facts

Each unverified Odoo 19 fact was engineered around rather than guessed. The
residual risk of each is stated honestly.

| Unverified fact | Mitigation | Residual risk if the assumption is wrong |
|---|---|---|
| `ir.rule` groups field name | All record rules are global; no groups field is written | **None.** The field is never referenced. |
| `res.users` groups field name | `has_group()` with external identifiers | **None.** The field is never referenced. |
| Cycle-detection helper name | Explicit bounded ancestry walk | **None.** No base-model helper is called. |
| `ir.cron` `numbercall` / `doall` | Both omitted | **Low.** The ORM applies its own defaults; scheduling frequency may need adjusting after installation. |
| Kanban card template API | No kanban view shipped | **None** functionally; a usability limitation only. |
| `ir.sequence` company resolution | Company-independent sequences shipped | **Low.** Numbering works; only per-company numbering would be affected. Listed as an OQ item. |
| `mail.mail_activity_data_todo` exists | Resolved with `raise_if_not_found=False`, falling back to a chatter message | **None.** Both branches are safe. |

Facts that **were** verified and are relied upon — `models.Constraint`,
`<chatter/>`, `res.groups.privilege` with `privilege_id`, ACL `group_id`, and
global record rules — should still be confirmed at installation qualification,
since documentation and runtime can diverge.

---

## 5. Outstanding qualification tasks

To be completed by the receiving team. This module is not qualified until they
are done and recorded.

### Installation qualification

1. Install on Odoo 19.0 Community and record the outcome.
2. Confirm the shipped example matrix loads **draft** and **not default**.
3. Confirm all 3 groups, 35 ACL lines, 9 record rules, 4 sequences and 1
   scheduled action are present.
4. Confirm the `res.groups.privilege` record and the `privilege_id` links.
5. Confirm all form views render, including the `<chatter/>` element.
6. Confirm the `ir.cron` record was created with the omitted fields defaulted.

### Operational qualification

7. Execute the test suite; record the actual pass rate.
8. Measure and record coverage against the 95% target.
9. Run `flake8`, `pylint` and `pylint-odoo`; resolve findings.
10. Exercise both segregation-of-duties rules with real users and confirm both
    refusals.
11. Confirm an analyst cannot approve, accept residual risk or close, both
    through the interface and through the external API.
12. Render both PDF reports.
13. Run the scheduled action and confirm the owner notification.
14. Confirm sequence numbering, including per-company behaviour if required.
15. Confirm multi-company isolation with a real second company.

### Performance qualification

16. Load-test the register at your expected record volume.
17. Confirm the review scheduled action completes within its window at that
    volume.
18. Confirm concurrent approval behaviour.

### Process

19. Define and approve your own risk matrix. **Do not use the shipped
    example.** ISO 14971:2019 requires the organisation to establish its own
    objective acceptability criteria.
20. Write the SOP governing use of the module.
21. Train users and record the training.
22. Maintain the risk management plan and risk management file outside this
    module (deviation D-09).
23. Integrate `ls_electronic_signature` where signed approvals are required
    (deviation D-10).

---

## 6. Compliance checklist

| Item | Status |
|---|---|
| Installs on Odoo 19 Community | **Not verified** — no runtime |
| Upgrades safely | **Not verified** — no runtime |
| No Enterprise-only code | **Verified** — depends only on `base` and `mail` |
| No Odoo core modification | **Verified** |
| No raw SQL | **Verified** — enforced by static analysis |
| Access rights on every model | **Verified** — 35 lines, all 16 accessible models |
| Record rules present | **Verified** — 9 global company rules |
| Segregation of duties at ORM level | **Implemented and unit-tested; tests not executed** |
| Input validation | **Verified** — 22 database constraints plus Python constraints |
| No placeholders or dead code | **Verified** — enforced by static analysis |
| Fully documented | **Verified** — 12 documents |
| Fully tested | **NO** — 161 tests written, none executed |
| Coverage ≥ 95% | **NOT DEMONSTRATED** — not measured |
| Production ready | **NO** — see section 1 |
| No unverified regulatory claim | **Verified** — see `VERIFICATION_LOG.md` and `REGULATORY_TRACEABILITY.md` |

---

## 7. Declaration

This module supports the implementation of processes aligned with
ISO 14971:2019. It does not certify, guarantee or evidence compliance with
ISO 14971:2019 or any other regulatory framework. Compliance depends on the
organisation's procedures, its validation activities, the competence of its
personnel and its quality system as a whole.

Every claim in this delivery is either sourced in `VERIFICATION_LOG.md` or
explicitly marked as unverified. Where a fact could not be verified, the
software was engineered so as not to depend on it, and the gap is stated
rather than closed with an assumption.
