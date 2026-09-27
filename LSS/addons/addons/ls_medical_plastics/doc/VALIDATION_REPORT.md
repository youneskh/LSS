# Validation Report and Delivery Gate

**Module:** `ls_medical_plastics` · **Version:** 19.0.1.0.0
**Date:** August 2026

---

## 1. Overall verdict

> ## CONDITIONAL PASS
>
> The module is **statically verified and dynamically unverified**.
>
> It is **not** qualified for use in a regulated production environment until
> the receiving organisation completes the tasks in section 5.

---

## 2. Phase gate results

| Phase | Gate | Verdict | Basis |
|---|---|---|---|
| 1 | Business analysis | PASS | Scope, roles and success criteria defined |
| 2 | Regulatory analysis | **CONDITIONAL PASS** | Frameworks identified; ISO clause numbering and all ANPP/BPF requirements **unverifiable** and therefore not claimed |
| 3 | Functional specification | PASS | Menus, workflows, state machines, rules and reports specified |
| 4 | Technical specification | PASS | 17 model definitions, 293 fields, constraints and security specified |
| 5 | Architecture review | **CONDITIONAL PASS** | Clean structure; several Odoo 19 API facts unverifiable and engineered around |
| 6 | Development | PASS | All code written; no placeholders, no dead code, no raw SQL |
| 7 | Testing | **FAIL against target** | 139 tests written; **none executed**; 95% coverage target **not demonstrated** |
| 8 | Static analysis | **CONDITIONAL PASS** | Custom checker clean and self-validated; `flake8`/`pylint-odoo` **not run** |
| 9 | Documentation | PASS | Full documentation set delivered |
| 10 | Final validation | **CONDITIONAL PASS** | This report |

Phase 7 is recorded as **FAIL against its stated target**. The development
framework set a minimum of 95% coverage. Zero tests were executed, so coverage
is not 95%, not any other number, and not measurable. Recording this as a pass
would be a fabrication.

---

## 3. What was actually verified

| Verification | Method | Result |
|---|---|---|
| Python syntax, every file | `ast.parse`, `py_compile` | PASS |
| XML well-formedness, every file | `lxml.etree.parse` | PASS |
| Manifest lists exactly the files present | Custom checker | PASS |
| Data file load order is valid | Custom checker | PASS |
| Every view field exists on its model | Custom checker | PASS |
| Every XML reference resolves | Custom checker | PASS |
| Every model has access control lines | Custom checker | PASS |
| Every ACL group exists | Custom checker | PASS |
| Every object button calls an existing method | Custom checker | PASS |
| No placeholder tokens remain | Custom checker | PASS |
| No raw SQL in shipped code | Custom checker | PASS |
| Report actions resolve to templates | Custom checker | PASS |
| The checker detects injected faults | 16 negative controls | 16 of 16 |
| Archive integrity | `unzip -t` | PASS |

---

## 4. What was *not* verified

| Not verified | Why |
|---|---|
| That the module installs | No Odoo runtime available |
| That the module upgrades | No previous installed version |
| That any test passes | No Odoo runtime, no PostgreSQL |
| Test coverage | Requires execution |
| `flake8`, `pylint`, `pylint-odoo` | Not installable without network access |
| That views render | No browser, no runtime |
| That reports produce a PDF | No rendering engine |
| Performance at realistic volume | No database |
| That the Odoo 19 APIs used exist as assumed | Documentation partly inaccessible; see the unverified list below |

### 4.1 Unverified platform facts carried into delivery

Each was researched, could not be confirmed, and was engineered around so that
being wrong cannot silently corrupt data. Full detail in
`DEVIATIONS_AND_LIMITATIONS.md`, Part B.

| Fact | Mitigation |
|---|---|
| Group-category field on `res.groups` | No category declared |
| Group-link field on `ir.rule` | All rules global; roles enforced via ACL and Python |
| Group-link field on `ir.ui.view` | Replaced by the `groups=` node attribute |
| `numbercall` / `doall` on `ir.cron` | Omitted |
| `uom.uom` model name stability | Unit fields are `Char` |
| Chatter markup in Odoo 19 | Official Odoo 19 documentation followed; lower-risk failure mode chosen |
| Arch of the `mrp.production` form | **Highest-risk item**; documented removal procedure if installation fails |

---

## 5. Outstanding qualification tasks

These are the responsibility of the receiving organisation. The module cannot
be used in a regulated environment until they are complete.

### 5.1 Installation Qualification (IQ)

1. Install on the target Odoo 19 Community instance and record the outcome.
2. Confirm the five groups, four sequences, 21 scrap reasons and two scheduled
   actions are created.
3. Confirm the `mrp.production` view inheritance applied; if installation
   failed on it, apply the documented removal and record the deviation.
4. Record the exact Odoo version, Python version, PostgreSQL version and module
   checksum in the validation file.
5. Verify the chatter renders correctly; if not, apply the substitution in
   `DEVIATIONS_AND_LIMITATIONS.md` B1 and record it as a change.

### 5.2 Operational Qualification (OQ)

6. Execute the full test suite and record the actual pass and fail counts.
7. Measure coverage with `coverage.py` and record the actual figure.
8. Run `flake8`, `pylint` and `pylint-odoo`; record and disposition findings.
9. Challenge each control by attempting to break it as a user:
   - edit a captured reading;
   - delete a captured reading;
   - modify a closed run;
   - review a run as its own operator;
   - approve a specification as its author;
   - start production with a critical parameter out of tolerance.
   Each attempt must be refused. Record the evidence.
10. Print both reports and verify the moulding run record shows superseded
    readings together with their correction reasons.
11. Verify multi-company isolation with a real second company.

### 5.3 Performance Qualification (PQ)

12. Run the process with real tools, components and specifications over a
    representative period.
13. Confirm tool shot counting matches the machine counters.
14. Confirm the maintenance status changes at the intervals configured.
15. Observe both scheduled actions over several cycles.
16. Perform a traceability challenge: select a finished lot and demonstrate that
    the resin lots, tool, cavities and specification version can be produced
    within the time the site's procedure requires.
17. Assess performance at the site's expected data volume.

### 5.4 Procedural controls the software cannot supply

18. Electronic signatures, if required by a predicate rule.
19. An audit trail of all record changes, if required.
20. Deviation management for the references recorded on runs.
21. Instrument calibration for the devices producing the readings.
22. A procedure requiring contemporaneous recording, since the system permits
    late entry.
23. Role coverage planning so three distinct users are always available for the
    specification workflow.

---

## 6. Compliance checklist

| Requirement | Status |
|---|---|
| Installs successfully | **Not verified** |
| Upgrades successfully | **Not verified** |
| Follows Odoo module architecture | Verified statically |
| Avoids modifying Odoo core | Verified — inheritance only |
| Uses inheritance where appropriate | Verified |
| Prevents SQL injection | Verified — no raw SQL; ORM only |
| Validates user input | Verified — constraints and Python checks present |
| Respects access rights | Verified statically; **not executed** |
| Respects record rules | Verified statically; **not executed** |
| No placeholders or omitted functionality | Verified |
| Fully documented | Verified |
| Fully tested | **NO — tests written, never executed** |
| Coverage at or above 95% | **NO — not measured, not claimed** |
| Production ready | **NO — conditional on section 5** |

---

## 7. Statement

This module has been designed and written to production standards and verified
by every means available in an environment without an Odoo runtime, a database
or network access. Within those limits it is clean.

It has never been installed, never been executed, and never been tested against
a running system. It must not be described as validated, qualified or compliant
on the basis of this delivery.

The honest one-line summary is: **a complete, statically clean, dynamically
unproven module, ready to enter qualification.**
