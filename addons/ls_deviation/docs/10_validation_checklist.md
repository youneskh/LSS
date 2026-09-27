# 10 — Validation Support and Compliance Checklist

## 10.1 Status of this phase

**Phase gate: FAIL — final validation cannot be claimed.**

The master prompt's Phase 10 asks for verification that the module is
production ready, upgrade safe, secure, maintainable, fully documented and
fully tested. Three of those six cannot be asserted, because the module has
never been executed. This document therefore functions as a **pre-validation
checklist**, not as a validation report.

| Attribute | Claim | Basis |
|---|---|---|
| Production ready | **No** | Never installed |
| Upgrade safe | **Partially designed for; unproven** | `noupdate="1"` on master data and sequence; no upgrade executed |
| Secure | **Designed; partially proven** | 4 groups, 29 ACL rows, 11 record rules, 13 security tests written but not executed |
| Maintainable | **Yes, by inspection** | Static checks pass; documented extension points |
| Fully documented | **Yes** | 12 documents plus source docstrings |
| Fully tested | **No** | 92 tests written, 0 executed |

## 10.2 Computerised system validation position

This module is a component of a computerised system. Validation is performed
by the regulated organisation against its own intended use, not by the
software author. This module supplies:

- A functional specification (`03_functional_specification.md`) usable as an input to a URS/FS traceability exercise
- A technical specification (`04_technical_specification.md`) usable as a design specification input
- An automated test suite usable as a component of OQ, once executed
- An explicit statement of what is unverified (`00_VERIFICATION_STATUS.md`)

It does **not** supply a validation package. IQ, OQ and PQ remain the
responsibility of the implementing organisation.

## 10.3 Pre-release checklist

Every item below is currently **open**.

| # | Item | Status |
|---|---|---|
| 1 | Install into scratch Odoo 19 Community | Open |
| 2 | Resolve load errors, checking `00_VERIFICATION_STATUS.md` section 4 first | Open |
| 3 | Install with demo data | Open |
| 4 | Execute the 92 automated tests | Open |
| 5 | Measure coverage; assess against the 95% target | Open |
| 6 | Run `flake8` | Open |
| 7 | Run `pylint` and `pylint-odoo` | Open |
| 8 | Upgrade test (`-u ls_deviation`) | Open |
| 9 | Uninstall test on a scratch database | Open |
| 10 | Render the PDF report for a fully populated deviation | Open |
| 11 | Verify each of the four roles in the UI | Open |
| 12 | Verify multi-company isolation in the UI | Open |
| 13 | Complete the ISO and EU GMP clause mapping against the actual standard texts | Open |
| 14 | Review Décret exécutif n° 22-247 and complete the ANPP mapping | Open |
| 15 | Confirm the site deviation SOP matches the enforced workflow, or configure/extend accordingly | Open |
| 16 | Decide whether Part 11 electronic signatures are required; if so, do not deploy without `ls_electronic_signature` | Open |
| 17 | Establish database-level protection of the transition log if required by the site data integrity policy | Open |
| 18 | Define the closure target intervals per severity per the site procedure | Open |
| 19 | Assign roles per user against documented authorisation | Open |
| 20 | Perform UAT with real deviation scenarios | Open |

## 10.4 Design controls supporting data integrity (ALCOA+)

Stated as design intent; effectiveness is unproven until item 4 is complete.

| Principle | Mechanism |
|---|---|
| Attributable | Distinct user fields for reporter, owner, QA reviewer, impact assessor, disposition approver, closer; every transition logs its actor |
| Legible | Structured fields rather than free-text narrative; PDF report |
| Contemporaneous | Occurrence, detection and recording timestamps with a chronology constraint; no draft state in which recording can be deferred |
| Original | Record created at reporting and retained; deletion blocked past Reported |
| Accurate | SQL and Python constraints; workflow guards refusing incomplete transitions |
| Complete | Mandatory extension rationale, conclusions and follow-up; closure blocked on open actions and unapproved dispositions |
| Consistent | Single state machine with a central transition choke point |
| Enduring | Records retained in PostgreSQL; cancellation instead of deletion |
| Available | Search, filters, analysis views and printable report |

## 10.5 Statement

No claim of compliance or certification is made. The module supports the
implementation of a deviation-handling process. It has not been validated, has
not been installed, and must not be deployed into a regulated environment
until at minimum items 1 to 12 of section 10.3 are closed.
