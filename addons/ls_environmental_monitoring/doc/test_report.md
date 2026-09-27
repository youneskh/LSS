# Test Report — `ls_environmental_monitoring`

**Date:** July 2026
**Version under test:** 19.0.1.0.0
**Verdict:** CONDITIONAL PASS

---

## 1. What was actually executed

Honest reporting of what ran matters more than a coverage figure. The build
environment has Python 3.12 and lxml, but **no Odoo runtime, no PostgreSQL and
no network access**. The test suite therefore divides into two parts with very
different levels of evidence.

| Part | Tests | Executed? | Evidence |
|---|---|---|---|
| Pure evaluation engine | 38 | **Yes** | 38 passed, 0 failed, 0 errors |
| Database-backed Odoo tests | 104 | **No** | Written and syntax-checked only |

Test counts in this report were obtained by parsing the test sources and
counting `test_` methods, not by transcription.

### 1.1 Executed: pure evaluation engine

`tests/test_evaluation_engine.py` imports only `models/constants.py` and
`models/evaluation.py`, neither of which imports Odoo. These tests were executed
in this environment.

```
Executed tests: 38   failures: 0   errors: 0
```

**Measured statement coverage**, obtained with the Python standard library
`trace` module:

| Module | Executable statements | Covered | Coverage |
|---|---|---|---|
| `models/evaluation.py` | 103 | 103 | **100.0%** |
| `models/constants.py` | 144 | 144 | **100.0%** |
| **Combined** | **247** | **247** | **100.0%** |

This is a measured figure, not an estimate. It covers the limit comparison
rules, the severity ranking, the descriptive statistics and the trend direction
classifier — that is, the logic on which every compliance decision in the module
depends.

### 1.2 Not executed: database-backed tests

The following were written, are syntactically valid Python, and have **never
been run**:

| File | Tests | Area covered |
|---|---|---|
| `tests/test_limit.py` | 14 | Limit approval, versioning, supersession, immutability, precedence |
| `tests/test_sample_workflow.py` | 16 | State machine, segregation of duties, overdue detection, cancellation |
| `tests/test_result_evaluation.py` | 17 | Evaluation, snapshotting, freezing, amendment |
| `tests/test_excursion.py` | 17 | Automatic creation, escalation rules, lifecycle, closure controls |
| `tests/test_scheduling.py` | 17 | Plan approval, generation, idempotency, calendar arithmetic |
| `tests/test_trend.py` | 9 | Scope, statistics, undefined values, review lock |
| `tests/test_security.py` | 14 | Access rights per role, multi-company isolation, ACL coverage |
| **Total** | **104** | |

**No coverage figure is claimed for the code these tests exercise.** Measured
coverage of the Odoo-dependent code is **0%**, because none of it has been
executed.

---

## 2. Static analysis

`static_check.py` runs offline using only the standard library and lxml.

```
Python files parsed : 34
XML files parsed    : 23
Models detected     : 18
ACL models covered  : 18
Manifest data files : 24
RESULT: PASS (no errors)
```

Checks performed: Python parses; XML well-formed; manifest completeness in both
directions; XML id references resolve; view field references resolve against the
target model, descending into sub-views via the comodel; every model has an
access rule; every access rule names a real model; no Odoo 18 constructs removed
in 19; no placeholder tokens; no raw SQL; licence headers present; no trailing
whitespace or tabs.

### 2.1 Negative control

A static checker that has never been observed to fail proves nothing.
`negative_control.py` copies the module, injects one deliberate fault at a time
and asserts that the checker reports it.

```
Baseline: unmodified module passes.
19 fault classes injected, 19 detected, 0 missed.
NEGATIVE CONTROL PASSED
```

Fault classes proven to be detected: non-existent field in a view; non-existent
field in a sub-view; unresolvable XML id reference; manifest listing a missing
file; XML file absent from the manifest; access rule naming an unknown model;
duplicate access rule id; non-boolean permission value; reintroduced `<tree>`;
reintroduced `attrs`; reintroduced `_sql_constraints`; reintroduced
`read_group`; raw SQL; placeholder token; malformed XML; Python syntax error;
missing licence header; non-conforming manifest version; trailing whitespace.

Two defects **in the checker itself** were found and fixed by this exercise:

1. Reversing an Odoo model XML id by replacing underscores with dots is
   ambiguous for model names containing an underscore, and wrongly reported
   `ls.env.sampling_point` as uncovered. Fixed by mapping forward from the model
   name instead.
2. The forbidden-construct and placeholder scans iterated only over XML that had
   parsed successfully, so a file that was both malformed and used a removed
   construct escaped the second check. Fixed by scanning raw file text.

Without the negative control, the checker's clean result would have been
misleading on both counts.

---

## 3. Not performed

| Activity | Status | Reason |
|---|---|---|
| Installation against Odoo 19 | **Not performed** | No Odoo runtime available |
| Upgrade from a previous version | **Not performed** | First release; no prior version exists |
| Execution of the 104 database tests | **Not performed** | No Odoo runtime or PostgreSQL |
| `flake8` | **Not performed** | Not installed; no network access to install it |
| `pylint` / `pylint-odoo` | **Not performed** | Not installed; no network access to install it |
| Performance testing | **Not performed** | Requires a live database with representative volumes |
| Browser or tour testing | **Not performed** | Requires a running server |
| Report rendering | **Not performed** | QWeb templates are well-formed XML but have never been rendered |

A PEP 8 subset was checked by `static_check.py` (line length, trailing
whitespace, tabs). This is **not** a substitute for `flake8`.

---

## 4. Verdict

**CONDITIONAL PASS.**

Justification for the "pass" component:

- The compliance-critical evaluation logic is isolated in pure functions, is
  covered by 38 executed tests at 100% measured statement coverage, and its
  boundary behaviour is verified by dedicated tests.
- Static analysis is clean and the checker has been proven to detect 19 classes
  of injected fault.
- Every model has access rules; every view field reference resolves.

Justification for the "conditional" component:

- 104 of the 142 tests written have never been executed.
- The module has never been installed against Odoo 19.
- Several Odoo 19 API facts could not be verified and were engineered around;
  `doc/deviations.md` section B7 identifies `<chatter/>` as the highest-severity
  remaining risk.
- No linter beyond the custom checker has been run.

**This module must not be considered qualified until the receiving organisation
completes the activities listed in section 5 of `doc/regulatory_mapping.md`.**
