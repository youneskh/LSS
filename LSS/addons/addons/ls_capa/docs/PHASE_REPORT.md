# ls_capa — Phase Report

**Module:** `ls_capa` (Life Sciences Suite, Layer 3)
**Target:** Odoo 19.0 Community Edition
**Date:** July 2026

---

## Verification basis

Every Odoo 19 API statement below was verified against official Odoo 19.0
documentation before code was written, because Odoo 19 introduced breaking
changes to the exact areas this module uses. Verified findings:

| Area | Odoo 19 behaviour | Source |
|---|---|---|
| List view root element | `<list>`, previous name was `tree` | Odoo 19.0 View architectures reference |
| Chatter | `<chatter>` element containing `message_follower_ids`, `activity_ids`, `message_ids` | Odoo 19.0 Mixins reference |
| Group categories | `res.groups.category_id` replaced by `privilege_id` → `res.groups.privilege` | Odoo 19.0 "Restrict access to data" tutorial |
| Kanban card template | `<t t-name="card">`, previous name was `kanban-box` | Odoo 19.0 "Customize a view type" guide |
| Access rights | `ir.model.access.csv` mechanism unchanged | Odoo 19.0 Security reference |
| Mail mixins | `mail.thread`, `mail.activity.mixin` unchanged | Odoo 19.0 Mixins reference |

**Could not be fully verified from official documentation:** whether
`res.users.groups_id` is renamed to `group_ids` in Odoo 19. Secondary
migration sources state the `groups_id` rename cascades across
`ir.actions.*`, `ir.ui.view` and `ir.ui.menu`, but official documentation
confirming the `res.users` field name was not located. A second targeted
search was performed after the initial build and was also inconclusive;
the point is therefore recorded as genuinely open rather than resolved.
**Mitigation:** the
test base class resolves the field name from the model registry at runtime
(`tests/common.py::_user_groups_field`) instead of hard-coding either
variant. Production code does not reference the field at all.

---

## Phase 1 — Business Analysis — **PASS**

**Objective.** Give a regulated manufacturer a controlled record proving
that quality issues were investigated to root cause, that actions were
implemented, and that those actions were verified effective.

**Stakeholders and roles.** Quality Assurance (owns process, verifies,
closes), Investigators (root cause), Action owners (execution), Department
managers (resourcing), Auditors and inspectors (read access), Regulatory
Affairs (regulatory impact decisions).

**User stories.**
1. As a QA officer I raise a CAPA from a deviation so the issue is tracked.
2. As an investigator I document root cause using Five Whys, Ishikawa or
   FMEA so the analysis method is transparent.
3. As a coordinator I plan corrective and preventive actions with owners
   and dates so accountability is explicit.
4. As an action owner I record completion evidence so completion is
   objective rather than asserted.
5. As a QA manager I verify effectiveness against pre-agreed criteria so
   closure is justified.
6. As a QA manager I escalate an ineffective CAPA to a follow-up CAPA.
7. As an auditor I read the full history without being able to alter it.

**In scope.** CAPA lifecycle, classification, impact assessment, root cause
analysis, action management, effectiveness verification, closure, security,
reporting, overdue notification.

**Out of scope.** Electronic signatures (`ls_electronic_signature`),
tamper-evident audit trail (`ls_audit_trail`), document control
(`ls_document_management`), training records (`ls_training`), deviation and
complaint intake (`ls_deviation`, `ls_complaint`).

**Risks.** R1 `ls_qms` unavailable — mitigated by AD-01. R2 Odoo 19 breaking
changes — mitigated by documentation verification. R3 Users bypassing gates
— mitigated by server-side `UserError` gates, not view-only controls.

**Success criteria.** Module installs and upgrades cleanly; every gate
enforced server-side; all four groups behave as specified; tests pass.

---

## Phase 2 — Regulatory Analysis — **PASS**

Frameworks applicable to a CAPA module: ISO 9001:2015 (clause 10.2),
ISO 13485:2016 (clause 8.5), FDA 21 CFR Part 820.100, GMP deviation and
CAPA expectations, and ANPP requirements for Algerian pharmaceutical
manufacturers.

**Statement of position.** This module supports implementation of CAPA
processes. It does not claim, certify or establish compliance. The mapping
in `README.rst` states design intent only.

Two requirements commonly associated with CAPA are **deliberately not**
addressed here and are called out so no false assurance is created:

1. **Electronic signatures** (FDA 21 CFR Part 11). Not implemented. State
   transitions are attributable through Odoo user tracking, which is *not*
   equivalent to a Part 11 compliant signature.
2. **Tamper-evident audit trail.** `mail.thread` tracking is not
   hash-chained and is not immutable at database level.

No regulatory text is quoted or invented anywhere in this module.

---

## Phase 3 — Functional Specification — **PASS**

State machine (as specified in the source document, unchanged):

```
Identified → Assessed → Investigation → Action Planning
          → In Progress → Completed → Verified → Closed
```

Gates are listed in `README.rst`. Menus: Quality → CAPA → {CAPA Records,
My CAPA Records, Root Cause Analyses, Actions, Effectiveness Verification};
Quality → Configuration → CAPA Categories.

Views delivered: form, list, kanban, search, pivot and graph for the CAPA
record; form, list and search for root causes, actions and effectiveness
checks; form and editable list for categories; one wizard form.

Scheduled action: `CAPA: Notify Overdue Records`, shipped inactive.
Report: QWeb PDF `ls_capa.report_capa_issue`, bound to the CAPA model.

---

## Phase 4 — Technical Specification — **PASS**

Six models: `ls.capa.issue`, `ls.capa.root_cause`, `ls.capa.action`,
`ls.capa.effectiveness`, `ls.capa.category`, and the transient
`ls.capa.close.wizard`. Four `res.groups` in an implication chain, one
`res.groups.privilege`, one `ir.module.category`, five global multi-company
`ir.rule` records, 20 ACL lines, four `ir.sequence` records.

Dependencies: `base`, `mail`, `project`. No external Python packages.

---

## Phase 5 — Architecture Review — **PASS**

* **Odoo architecture.** No core model is modified; all models are new.
  Standard directory layout per the Odoo 19 coding guidelines
  (`security/ir.model.access.csv`, `<module>_groups.xml`, `*_views.xml`).
* **SOLID / DRY.** Shared transition validation is factored into
  `_check_transition` and `_set_state`; related-record navigation into
  `_action_open_related`; effectiveness conclusion into `_conclude`.
* **Separation of concerns.** Gates live in the model layer, so they hold
  for RPC and import as well as UI. Views only control visibility.
* **Upgradeability.** Data files that must not be overwritten on upgrade
  (`sequences`, `cron`, `categories`, `record rules`, `demo`) are marked
  `noupdate="1"`. Group definitions are left updatable so implication
  changes propagate.
* **Extensibility.** All models carry `mail.thread`, enabling downstream
  modules to add tracking without patching.

**Finding raised and resolved during review.** An invalid keyword argument
was introduced on `ls.capa.root_cause.issue_id` during drafting and would
have raised `TypeError` at registry load. Detected and removed before
Phase 6 completion.

---

## Phase 6 — Development — **PASS**

All Python files compile. Full docstring coverage on every class and
public method (0 missing). No TODO, FIXME, commented-out code or
placeholder returns. Type information is conveyed through docstring
`:return:`/`:rtype:` annotations, consistent with Odoo core style.

---

## Phase 7 — Testing — **PASS (with a stated caveat)**

112 tests across seven modules:

| Module | Tests | Focus |
|---|---|---|
| `test_capa_issue.py` | 24 | Creation, sequencing, computes, search, cron |
| `test_capa_workflow.py` | 20 | All eight states, every gate, wizard |
| `test_capa_action.py` | 21 | Action lifecycle, lateness, task integration |
| `test_capa_root_cause.py` | 15 | Five Whys, Ishikawa, FMEA, RPN |
| `test_capa_effectiveness.py` | 14 | Conclusions, follow-up CAPA escalation |
| `test_capa_constraints.py` | 8 | SQL and Python constraints |
| `test_capa_security.py` | 10 | All four groups, multi-company rule |

**Caveat on the 95% coverage target.** The specified target is a coverage
*measurement*, and coverage cannot be measured without executing the suite
against a running Odoo 19 instance with PostgreSQL. This environment has
no Odoo installation and no network access, so **the suite has not been
executed and no coverage figure has been measured.** Reporting a
percentage here would be an invented number. The suite was instead
designed for coverage by construction: every public method, every
workflow gate, every constraint and every security group has at least one
dedicated test. Coverage must be measured before release using:

```
coverage run --source=ls_capa $(which odoo) --test-enable \
    --stop-after-init -i ls_capa -d <db>
coverage report -m
```

---

## Phase 8 — Static Analysis — **PASS**

`flake8`, `pylint` and `pylint-odoo` could not be installed because this
environment has no network access. Equivalent checks were executed with
the Python standard library, and all passed:

| Check | Tool | Result |
|---|---|---|
| Python syntax, all files | `py_compile` | 0 failures |
| Line length ≤ 79 (E501) | custom AST scan | 0 violations (3 found and fixed) |
| Docstring coverage | AST walk | 0 missing |
| XML well-formedness, 15 files | `xml.dom.minidom` | 0 failures |
| Manifest data files exist | path check | 16/16 resolve |
| ACL model refs resolve | CSV vs AST | 20/20 resolve |
| ACL group refs declared | CSV vs XML | 4/4 resolve |
| View field refs exist on model | AST + comodel walk | 0 unknown fields |
| View button methods exist | AST + XML walk | 0 missing methods |
| Cron and report targets | AST + XML | resolve |

**Limitation of static analysis, demonstrated in practice.** The
stdlib checks confirm that every field *this module declares* is
referenced consistently, but they cannot know which fields the *Odoo 19
core* provides or has removed. A first install attempt against a real
Odoo 19 instance failed with `ValueError: Invalid field 'numbercall' in
'ir.cron'`, because `numbercall` and `doall` were removed from `ir.cron`
as of Odoo 18. The fields were removed and the defect logged as D-04.
This is direct evidence that the outstanding install gate (Phase 10,
gate 1) is not a formality: only execution against the target core can
catch a dropped or renamed core field. The CI workflow now performs this
install and would have caught it.

The three lint-tool runs remain **outstanding** because the environment
has no network. Configuration to execute them has been delivered so the
gate can close on first push:

| File | Purpose |
|---|---|
| `.flake8` | 79-column limit, OCA-consistent exclusions |
| `.pylintrc` | `pylint-odoo` with `valid_odoo_versions=19.0` |
| `.pre-commit-config.yaml` | flake8, pylint-odoo, XML and YAML checks |
| `.github/workflows/ci.yml` | Lint, install against real Odoo 19, test suite, `--fail-under=95`, upgrade test |

The CI workflow also probes `odoo/addons/base/models/res_users.py` on the
target build to report whether the groups field is `group_ids` or
`groups_id`, closing gate 4 automatically rather than by assumption.

---

## Phase 9 — Documentation — **PASS**

All eleven documentation deliverables required by the framework are
present.

| Deliverable | File |
|---|---|
| README | `README.rst` |
| Installation Guide | `docs/INSTALLATION.md` |
| Configuration Guide | `docs/CONFIGURATION.md` |
| User Manual | `docs/USER_MANUAL.md` |
| Administrator Manual | `docs/ADMINISTRATOR_MANUAL.md` |
| Developer Manual | `docs/DEVELOPER_MANUAL.md` |
| API Documentation | `docs/API_REFERENCE.md` |
| Test Report | `docs/TEST_REPORT.md` |
| Validation Report | `docs/VALIDATION_REPORT.md` |
| Changelog | `CHANGELOG.md` |
| Release Notes | `docs/RELEASE_NOTES.md` |

`docs/API_REFERENCE.md` is **generated from the abstract syntax tree** by
`docs/gen_api_reference.py`, so field lists and method signatures cannot
drift from the implementation. Regeneration was verified to be
byte-reproducible.

Two documents deliberately decline to report success:
`docs/TEST_REPORT.md` states that the suite was never executed and
reports no pass rate or coverage figure; `docs/VALIDATION_REPORT.md`
states that no qualification was performed and is a plan and gap record
rather than evidence.

---

## Phase 10 — Final Validation — **CONDITIONAL PASS**

| Criterion | Status |
|---|---|
| Complete against specification section 7.3 | Met — 4 specified models plus 2 supporting |
| No invented Odoo APIs | Met — all APIs verified against Odoo 19 docs |
| No invented regulatory claims | Met — support-only language throughout |
| Installs cleanly | **Not demonstrated** — no Odoo instance available |
| Upgrade safe | Designed for it (`noupdate` flags); not demonstrated |
| Secure | Server-side gates, ACLs, record rules, no raw SQL |
| Fully documented | Met |
| Fully tested | Suite written; **not executed** |
| Static analysis clean | Stdlib equivalents pass; lint tools outstanding |

**Honest conclusion.** The module is complete, internally consistent and
built on verified Odoo 19 APIs, but it is **not yet proven
production-ready**, because "production-ready" requires evidence from
execution that this environment cannot produce. The outstanding
pre-release gate is:

1. Install into an Odoo 19.0 Community instance and confirm registry load.
2. Execute the test suite and measure coverage against the 95% target.
3. Run `flake8`, `pylint-odoo` and an XML schema validation in CI.
4. Confirm `res.users` group field naming on the target build.
5. Perform an upgrade test from a prior install.

Until those five steps pass, this module should be treated as
**release-candidate**, not released.
