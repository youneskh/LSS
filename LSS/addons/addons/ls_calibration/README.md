# Calibration Management (`ls_calibration`)

Instrument register, calibration planning, execution and out-of-tolerance
management for regulated life sciences environments.

**Odoo 19.0 Community Edition · AGPL-3 · version 19.0.1.0.0**

---

> ## Delivery status: CONDITIONAL PASS
>
> This module compiles, its XML is well-formed and its static checks are clean.
> It has **never been installed against a running Odoo 19 instance** and its
> **112 tests have never been executed**. No coverage figure is claimed.
> Do not deploy to a regulated production environment before completing the
> qualification tasks listed in
> `docs/03_architecture_review_and_delivery_gate.md` §10.4.

---

## What it does

- **Instrument register** with identification, measuring range, criticality,
  GxP classification and a lifecycle from draft through in service,
  quarantine and out of service to retirement.
- **Calibration points** carrying the acceptance tolerance at each verified
  value, in absolute, percent-of-reading or percent-of-span form. Acceptance
  limits are derived, not typed.
- **Reference standards** with their own traceability certificate, issuing
  laboratory, expiry and measurement uncertainty.
- **Calibration plans** with an approval workflow, an effective window and a
  guarantee that only one approved plan is effective per instrument at a time.
- **Schedule generation** from approved plans up to a horizon date.
- **Calibration execution** capturing as-found and as-left readings per point,
  evaluating each against its limits, and aggregating them into an overall
  result that distinguishes a clean pass from a pass obtained only after
  adjustment.
- **Review and approval** with segregation of duties enforced in the ORM: the
  performer, the reviewer and the approver must be three different users.
- **Immutability**: an approved record refuses every data write, its readings
  become read-only, and it cannot be deleted.
- **Out-of-tolerance handling**: an as-found failure raises an event, puts the
  instrument in quarantine, and drives an impact assessment, a product-impact
  classification and a disposition through to closure.
- **Certificates**: internal ones printed from the module, external ones stored
  as the received document. Certificates are never deletable.

## What it deliberately does not do

| Not implemented | Where it lives instead |
|---|---|
| 21 CFR Part 11 electronic signatures | `ls_electronic_signature` |
| Tamper-evident hash-chained audit trail | `ls_audit_trail` |
| CAPA workflow | `ls_capa` (referenced here as text) |
| Controlled procedure documents | `ls_document_management` (referenced here as text) |
| Batch and lot identification | A manufacturing module (recorded here as text) |
| Measurement uncertainty budgets | Out of scope |

**Approving a calibration record in this module is not signing it.** Approval
records a user identity, a timestamp and a tracked chatter message. There is no
re-authentication and no signature meaning.

## Dependencies

`base`, `mail`. Nothing else.

The suite specification lists `maintenance` and `ls_qms` as dependencies;
neither is declared. Whether the Odoo 19 Maintenance application ships in
Community Edition could not be verified from official documentation, and
declaring an absent module blocks installation. See `docs/` for the full
deviations register.

## Installation

```bash
# 1. Place the module on the addons path
cp -r ls_calibration /path/to/addons/

# 2. Install
odoo -d <database> -i ls_calibration --stop-after-init

# 3. Run the tests (required before regulated use)
odoo -d <database> -i ls_calibration --test-enable \
     --test-tags /ls_calibration --stop-after-init

# 4. Measure coverage (required before regulated use)
coverage run --source=/path/to/addons/ls_calibration \
  odoo-bin -d <database> -i ls_calibration --test-enable \
  --test-tags /ls_calibration --stop-after-init
coverage report -m
```

## Static analysis

The build environment has no network access, so `flake8`, `pylint` and
`pylint-odoo` could not be installed. A custom offline checker ships with the
module:

```bash
python3 tools/static_check.py .            # check the module
python3 tools/static_check.py --self-test  # prove the checker works
```

The self-test injects twelve known faults and asserts each is detected, plus a
positive control confirming clean input produces no finding. Run it before
trusting the checker's verdict.

## Configuration

1. **Instrument Categories** (Configuration) — define families such as
   balances, temperature sensors or pressure gauges, each with a default
   interval and criticality.
2. **Reference Standards** (Configuration) — register each standard with its
   traceability certificate number, issuing laboratory and expiry date.
3. **Users** — assign one of Viewer, Technician, Approver or Manager. Assign
   the Approver and Technician roles to different people; the module refuses a
   calibration approved by its own performer.
4. **Scheduled actions** — the weekly notification cron ships **inactive**.
   Activate it once notification recipients are configured.

## Typical flow

```
Register instrument  ──►  Define calibration points  ──►  Place in service
                                                                │
                              ┌─────────────────────────────────┘
                              ▼
              Create plan  ──►  Approve plan  ──►  Generate schedule
                                                        │
                                                        ▼
        Start  ──►  Enter readings  ──►  Mark performed  ──►  Submit
                                                        │
                    ┌───────────────────────────────────┘
                    ▼
        Review (user B)  ──►  Approve (user C)  ──►  Issue certificate
                                    │
                                    └──► as-found failed?
                                              │
                                              ▼
                              OOT event raised, instrument quarantined
                                              │
                              Assess impact ──► Disposition ──► Close
```

## Tolerance semantics

A percentage tolerance is expressed **in percent**: enter `0.5` for 0.5 %, not
`50` and not `0.005`. This is asserted by `test_percent_is_not_a_ratio`.

| Type | Absolute tolerance |
|---|---|
| Absolute | the value as entered |
| % of reading | value × \|nominal\| ÷ 100 |
| % of span | value × \|range max − range min\| ÷ 100 |

## A note on zero

A measured value of zero is a legitimate reading. The module therefore carries
a separate `as_found_recorded` / `as_left_recorded` flag rather than inferring
"not measured" from a zero value. Entering a value in the user interface sets
the flag automatically.

## Documentation

| File | Contents |
|---|---|
| `docs/01_analysis_and_functional_spec.md` | Business analysis, regulatory analysis, functional specification (phases 1–3) |
| `docs/02_technical_spec_generated.md` | Field, constraint and method inventory, generated from source by AST |
| `docs/03_architecture_review_and_delivery_gate.md` | Architecture review, deviations register, static-analysis report, delivery gate and IQ/OQ/PQ task list (phases 5, 8, 10) |
| `docs/USER_MANUAL.md` | Role-by-role operating instructions |
| `docs/CHANGELOG.md` | Release history |

## Regulatory position

This module supports the implementation of processes aligned with calibration
provisions in 21 CFR Part 211, 21 CFR Part 820, EU GMP, ISO 13485 clause 7.6,
ISO 9001 clause 7.1.5 and ISO/IEC 17025 clause 6.5. **It does not certify
compliance with any of them.** Compliance additionally requires written
procedures, trained personnel, a validated system and management oversight.
Clause-by-clause mapping, and an explicit statement of which requirement
wording could not be verified from official sources, is in
`docs/01_analysis_and_functional_spec.md` §2.

No ANPP-specific behaviour is implemented. No official ANPP publication setting
out calibration requirements was available, so nothing is claimed.

## Licence

AGPL-3. Copyright 2026 Life Sciences Suite Architecture Team.
