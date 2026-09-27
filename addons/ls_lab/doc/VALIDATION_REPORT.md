# VALIDATION REPORT — `ls_lab` 19.0.1.0.0

**Phase 10 — Final Validation**
**Date:** 2026-08-07
**Module:** `ls_lab` — Laboratory Management, Odoo 19 Community Edition

---

# DELIVERY GATE: **CONDITIONAL PASS**

The condition is stated first, before anything else in this document:

> **This module has never been installed, executed or exercised on a running
> Odoo 19 server.** The build environment contained no Odoo runtime and no
> PostgreSQL server. Everything below is static verification. Static
> verification of the schema is not a substitute for installation.

The gate becomes an unconditional PASS only when sections 6 and 7 of
`TEST_REPORT.md` are completed on a real instance.

---

## 1. What was verified, and how

| # | Verification | Method | Result |
|---|--------------|--------|--------|
| V-01 | Every Python file compiles | `py_compile` on all 25 files | **PASS** |
| V-02 | Every XML file is well-formed | `lxml.etree.parse` on all 15 files | **PASS** |
| V-03 | View archs conform to the Odoo 19 grammar | RelaxNG validation against the **actual** Odoo 19 RNG schemas retrieved from branch `19.0` | **PASS** |
| V-04 | Search-view `<group>` attributes are legal | Allow-list derived from `common.rng` | **PASS** |
| V-05 | Every view field exists on its model | AST field inventory, following nested One2many/Many2many contexts | **PASS** |
| V-06 | Every button method exists | AST method inventory | **PASS** |
| V-07 | Every internal external identifier resolves | Declared vs referenced identifier sets | **PASS** |
| V-08 | ACL matrix is complete | 10 models × 4 groups + 3 wizards = 49 rows | **PASS** |
| V-09 | Every manifest data file exists | Manifest parsed with `ast.literal_eval` | **PASS** |
| V-10 | No forbidden Odoo 19 construct present | 10 pattern classes | **PASS** |
| V-11 | The checker detects what it claims to detect | 25 seeded faults injected one at a time | **25/25 PASS** |
| V-12 | No suite module is a hard dependency | Manifest check | **PASS** |
| V-13 | No regulatory value is shipped as data | Manifest and data file inspection, plus a regression test | **PASS** |

### On V-03 and V-11

These two are the substantive additions of this build.

**V-03.** Odoo 19 ships **no `view.rng`**. It ships one RNG per view type. A
diagnostic validating all archs against a single `view.rng` validates against a
schema that does not exist, which produces either spurious findings or, worse,
silence. This module validates each arch against the schema Odoo 19 itself uses,
shipped in `tools/rng/`.

**V-11.** A checker reporting zero findings is worthless until shown to report
findings when they exist. The negative control seeds 25 faults, one per run, and
asserts each is caught. Baseline is clean, so no injected fault is confused with
a pre-existing one. **Fault F01 is the exact construct that caused the reported
`ls_cosmetics` install failure**, so this checker would have caught that defect.

---

## 2. What was NOT verified — stated plainly

| # | Item | Status |
|---|------|--------|
| N-01 | Installation on Odoo 19 | **NOT VERIFIED.** No Odoo runtime existed. |
| N-02 | Upgrade from a prior version | **NOT VERIFIED.** No prior version exists. |
| N-03 | Test execution | **NOT VERIFIED.** 91 tests written, 0 executed. |
| N-04 | Code coverage | **NOT MEASURED.** 95% is a target, not a result. |
| N-05 | `flake8` | **NOT RUN.** Not installed in the build environment. |
| N-06 | `pylint` / `pylint-odoo` | **NOT RUN.** Not installed in the build environment. |
| N-07 | QWeb PDF rendering | **NOT VERIFIED.** Templates are well-formed; rendering was not observed. |
| N-08 | Widget rendering | **NOT VERIFIED.** Widget names were taken from Odoo 19 core usage. |
| N-09 | Performance under load | **NOT MEASURED.** No performance test was executed. |
| N-10 | Form and kanban arch validity | **NOT RNG-VALIDATED.** Odoo 19 ships no schema for these types, so neither Odoo nor this checker validates them. Field and method references in them *are* checked. |
| N-11 | Multi-company behaviour at runtime | **NOT VERIFIED.** Rules are declared and tested statically only. |
| N-12 | Behaviour of the Odoo 19 `<chatter/>` element in these forms | **NOT VERIFIED.** Usage matches core. |

Phase 8 of the development framework is therefore **partially complete**: RNG
validation and the custom checker are done; the three external linters are not.

---

## 3. Regulatory position

| Claim | Status |
|-------|--------|
| Supports implementation of laboratory processes | Yes, as designed |
| Certifies compliance with any framework | **No. Not claimed.** |
| Implements FDA 21 CFR Part 11 electronic signatures | **No. Explicitly not claimed.** |
| Implements the FDA OOS guidance two-phase structure | The structure is implemented; conformity to the guidance is the organisation's assessment, not this module's claim |
| Ships ICH storage conditions or time points | **No, deliberately.** ICH Q1 reached Step 2b on 11 April 2025 and had not reached Step 4 at build time |
| Ships pharmacopoeial content | **No.** Method references are free text |
| Claims conformity with Algerian ANPP/BPF requirements | **No.** Carried at reference level only; no Algerian regulatory text was read during this build |

### Sourced regulatory facts relied upon

| Fact | Source |
|------|--------|
| FDA OOS guidance is the Level 2 revision, May 2022, docket FDA-1998-D-0019, CDER | FDA guidance document listing |
| OOS = results outside specifications or acceptance criteria established in applications, DMFs, compendia or by the manufacturer; also applies to in-process tests | The guidance itself |
| Retesting a portion of the original sample may form part of the investigation | The guidance itself |
| 21 CFR 211.165(f) requires rejection of finished products failing to meet standards | 21 CFR 211 |
| ICH Q1A(R2) reached Step 4 on 6 February 2003 | ICH Q1A(R2) |
| Consolidated ICH Q1 reached Step 2b on 11 April 2025; consultation closed; Step 4 not reached | ICH process records and the FDA draft guidance, June 2025, docket FDA-2025-D-1106 |

**Flagged as unverified:** the exact current sub-paragraph numbering of
21 CFR 211.194(a) was not re-read from eCFR during this build. The
second-person review requirement is implemented regardless of citation numbering.
Whether ICH Q1 has since reached Step 4 must be re-checked by the implementer.

---

## 4. Compliance checklist

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| C-01 | Installs successfully | **UNVERIFIED** | N-01 |
| C-02 | Upgrades successfully | **UNVERIFIED** | N-02 |
| C-03 | Respects the official Odoo module architecture | **PASS** | Layout, §4.1 of the technical spec |
| C-04 | Does not modify Odoo core | **PASS** | No core model is inherited except mail mixins |
| C-05 | Uses inheritance where possible | **PASS** | Two abstract mixins carry shared behaviour |
| C-06 | Follows MVC separation | **PASS** | Views declare buttons; logic lives in models |
| C-07 | Follows ORM best practice | **PASS** | `_read_group` used; no raw SQL |
| C-08 | Prevents SQL injection | **PASS** | No raw SQL; enforced by the checker |
| C-09 | Validates user input | **PASS** | 9 Python constraints, 9 SQL constraints |
| C-10 | Respects access rights | **PASS (static)** | 49 ACL rows; runtime unverified |
| C-11 | Respects record rules | **PASS (static)** | 11 rules; runtime unverified |
| C-12 | No placeholders, TODOs or dead code | **PASS** | Enforced by the checker |
| C-13 | Complete docstrings | **PASS** | Every method documented |
| C-14 | Fully documented | **PASS** | 13 documents delivered |
| C-15 | Fully tested | **PARTIAL** | Tests written, not executed |
| C-16 | Passes automated quality checks | **PARTIAL** | Custom checker and RNG pass; external linters not run |
| C-17 | Upgrade-safe | **PASS (by design)** | `noupdate="1"` on sequences and crons; no column renames |
| C-18 | Maintainable | **PASS** | Single evaluation point; extension points documented |
| C-19 | No false regulatory claims | **PASS** | Limitations stated in README, manuals, wizard, form views and the PDF report |
| C-20 | No invented API, module or regulation | **PASS** | Every Odoo fact carries a source citation |

---

## 5. Residual risks

| # | Risk | Severity | Mitigation |
|---|------|----------|------------|
| RR-01 | An install-time failure not detectable offline | **Medium** | RNG validation against real schemas removes the largest known class; install on a scratch database first |
| RR-02 | A test fails on first execution | Medium | Expected; execute on a scratch database and record in `TEST_REPORT.md` |
| RR-03 | Linter findings on first run | Low | Cosmetic; run `flake8` and `pylint-odoo` before production |
| RR-04 | Three-user segregation is impossible in a small laboratory | **Medium** | Stated in the configuration guide; there is no override, by design |
| RR-05 | Signature mistaken for a Part 11 signature | **High if unaddressed** | Stated in six places including the printed CoA; quality unit must acknowledge before go-live |
| RR-06 | Out-of-trend expected to be automatic | Medium | Stated in the user manual, deviations register and on the result form |
| RR-07 | Instrument calibration not enforced | **Medium** | Stated in deviation D-10; control by procedure or add a bridge module |
| RR-08 | Other suite modules carry the search-view defect | **High for the suite** | `tools/retrofit_scan.py` provided; run it against the addons directory |
| RR-09 | ICH Q1 reaches Step 4 after this build | Low | No guideline value is embedded, so no code change would be required |
| RR-10 | Form and kanban archs are not RNG-validated | Low | Odoo does not validate them either; field and method references are still checked |

---

## 6. Deliverables

| Deliverable | Status |
|-------------|--------|
| Complete directory tree | Delivered |
| 10 concrete models, 2 mixins, 3 wizards | Delivered |
| 253 declared fields | Delivered |
| 9 view files, 25 view records, menus | Delivered |
| Security: privilege, 4 groups, 49 ACL rows, 11 record rules | Delivered |
| Data: 6 sequences, 3 scheduled actions | Delivered |
| Reports: 2 actions, 2 QWeb templates | Delivered |
| Tests: 8 suites, 91 tests | Delivered, unexecuted |
| Tooling: checker, negative control, retrofit scanner, RNG schemas | Delivered |
| Translation template: 361 strings | Delivered |
| Documentation: 13 documents | Delivered |
| Icon | Delivered |

---

## 7. Conclusion

`ls_lab` is delivered **statically verified and functionally complete against its
specification**, with every departure from that specification recorded in
`SPECIFICATION_DEVIATIONS.md` and every Odoo 19 API fact traced to a source file
and line in `API_VERIFICATION_RECORD.md`.

It is **not** validated software. It has never run. Before any regulated use:

1. Install on a non-production Odoo 19 Community database.
2. Execute the test suite; complete `TEST_REPORT.md` §3 and §6.
3. Measure coverage; complete §4.
4. Run `flake8`, `pylint` and `pylint-odoo`; complete §5.
5. Run `tools/retrofit_scan.py` against the other suite modules.
6. Have the quality unit read and accept the electronic signature limitation.
7. Perform your own computerised system validation. This module does not
   validate itself and does not claim to.

**Gate: CONDITIONAL PASS.**

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Developer | | | |
| Reviewer | | | |
| Quality approver | | | |
