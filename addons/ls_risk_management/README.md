# Life Sciences Suite — Risk Management

**Technical name:** `ls_risk_management`
**Version:** 19.0.1.0.0
**Target:** Odoo 19.0 **Community** Edition
**Licence:** AGPL-3
**Author:** Life Sciences Suite Architecture Team

Risk register, risk assessment, risk control and FMEA for regulated life
sciences environments: pharmaceutical manufacturing, medical devices, medical
plastics, cosmetics and QC laboratories.

---

## Status: CONDITIONAL PASS — read this first

This module is complete, statically clean and documented. It has **never been
installed, started or executed**, because the build environment had no Odoo
runtime, no PostgreSQL and no network access.

| | |
|---|---|
| Python syntax, 21 files | **Verified** |
| XML well-formedness, 16 files | **Verified** |
| Custom static analysis | **Verified**, no findings |
| Static analyser itself | **Validated** by 22 negative controls, 22/22 detected |
| 161 automated tests | **Written, never executed** |
| Coverage | **Not measured.** The 95% target is **not** demonstrated |
| `flake8` / `pylint` / `pylint-odoo` | **Not run** — no network, no package installation |
| Installed against live Odoo 19 | **No** |

Outstanding qualification tasks are enumerated in
[`doc/VALIDATION_REPORT.md`](doc/VALIDATION_REPORT.md) section 5.

---

## The design decision that shapes everything

ISO 14971:2019 requires the manufacturer to **establish objective criteria for
risk acceptability**, and does **not** itself specify acceptable risk levels.
(Verified from the ISO catalogue entry; see
[`doc/VERIFICATION_LOG.md`](doc/VERIFICATION_LOG.md).)

So this module hardcodes no threshold anywhere. Acceptability lives in
`ls.risk.matrix` as reviewable, approvable, version-controlled configuration.
The 5x5 matrix that ships is delivered **unapproved and not default**, and
cannot be used until your organisation reviews and approves it. That is not an
oversight — a module that shipped ready-made acceptability criteria would be
inviting you to adopt someone else's risk appetite.

---

## What it provides

**Risk register** — one record per identified risk, with the hazard, sequence
of events, hazardous situation and harm recorded as four separate fields so
the causal chain is documented rather than collapsed into one paragraph.
Six-state lifecycle: Draft → Assessed → Risk Control → Monitoring → Closed,
plus Cancelled.

**Risk matrix** — configurable severity and probability scales with objective
definitions, and a per-cell risk band and acceptability decision. Draft →
Approved → Obsolete. Approved matrices are immutable; supersede rather than
edit.

**Risk assessment** — four assessment types (initial, residual, periodic
review, production/post-production). Risk level and acceptability are derived
from the approved matrix and cannot be typed in. **The assessor cannot approve
their own assessment**, enforced in the ORM.

**Risk control measures** — the three control option categories with a
documented preference order, so reliance on the weakest option is visible.
Separate implementation and effectiveness verification, with **different
people required for each**. Declaration and promotion of risks introduced by a
control measure itself.

**Residual risk** — acceptance recorded with author, timestamp and
justification. Where acceptability is *Not Acceptable*, the module **refuses**
to record acceptance without a benefit-risk analysis.

**FMEA** — worksheets with failure modes, S/O/D ratings, RPN, dual action
thresholds, revised ratings, revisions, and promotion of a failure mode into
the risk register. Kept structurally separate from the ISO 14971 assessment
path, because detection is an FMEA construct and does not belong in a
14971 risk estimation.

**Periodic review** — review intervals, overdue flagging, a *Reviews Due*
view, and a daily scheduled action notifying risk owners.

**Reports** — Risk Record and FMEA Worksheet, both carrying an explicit
statement that they do not constitute a compliance claim.

---

## Dependencies

```python
"depends": ["base", "mail"]
```

Deliberately **not** `ls_qms`, although the suite specification lists it.
Depending on a suite module that is not on the addons path would block
installation. Integration uses an extension point instead. See
[`doc/DEVIATIONS.md`](doc/DEVIATIONS.md) D-01.

---

## Install

```bash
odoo-bin -d YOUR_DATABASE -i ls_risk_management --stop-after-init
```

Then define and approve a risk matrix before anything else:
[`doc/CONFIGURATION.md`](doc/CONFIGURATION.md).

---

## Roles

| Group | Can |
|---|---|
| **Risk Viewer** | Read everything |
| **Risk Analyst** | Create and edit risks, assessments, control measures, FMEA |
| **Risk Manager** | The above, plus approve, accept residual risk, close, cancel, configure |

Two segregation-of-duties rules are enforced in the ORM and apply to everyone,
administrators included: an assessor cannot approve their own assessment, and
an implementation verifier cannot verify effectiveness. **Provision at least
two Risk Managers**, or approvals will deadlock.

Hiding a button is not a control. Nine workflow methods assert the caller's
role themselves, so the external API and server actions are covered too.

---

## Documentation

| Document | Contents |
|---|---|
| [`VERIFICATION_LOG.md`](doc/VERIFICATION_LOG.md) | Every verified and unverified fact, with sources |
| [`VALIDATION_REPORT.md`](doc/VALIDATION_REPORT.md) | Phase gates, delivery verdict, outstanding qualification |
| [`TEST_REPORT.md`](doc/TEST_REPORT.md) | The 161 tests and their unexecuted status |
| [`DEVIATIONS.md`](doc/DEVIATIONS.md) | 10 declared deviations with rationale |
| [`REGULATORY_TRACEABILITY.md`](doc/REGULATORY_TRACEABILITY.md) | ISO 14971:2019 clause to field mapping |
| [`INSTALLATION.md`](doc/INSTALLATION.md) | Prerequisites, install, upgrade, uninstall |
| [`CONFIGURATION.md`](doc/CONFIGURATION.md) | Defining acceptability criteria, roles, multi-company |
| [`USER_MANUAL.md`](doc/USER_MANUAL.md) | Day-to-day use |
| [`ADMINISTRATOR_MANUAL.md`](doc/ADMINISTRATOR_MANUAL.md) | Security model, integrity controls, performance |
| [`DEVELOPER_MANUAL.md`](doc/DEVELOPER_MANUAL.md) | Architecture, conventions, extension points |
| [`API_REFERENCE.md`](doc/API_REFERENCE.md) | Generated from source by AST |
| [`CHANGELOG.md`](doc/CHANGELOG.md) | Release history |

---

## Tooling

```bash
python3 static_check.py         # must report no findings
python3 negative_controls.py    # must report 22/22
python3 tools_generate_data.py  # regenerate cross-referenced data XML
python3 tools_generate_docs.py  # regenerate API reference and .pot
```

The negative controls exist because a static checker that has never been shown
to fail proves nothing. Twenty-two deliberate faults are injected one at a
time into throwaway copies and each must be detected.

---

## What this module does not do

- It does not hold your risk management plan or risk management file
  (deviation D-09).
- Its approvals are **not** 21 CFR Part 11 electronic signatures
  (deviation D-10).
- It claims **no** ANPP or ICH Q9 support. Neither could be verified from
  official documentation, so neither is claimed, notwithstanding the suite
  specification's traceability matrix.
- It does not make any organisation compliant with anything. It records the
  evidence that supports your own compliance activities.
