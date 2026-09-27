# Phase 7 — Test Report

## 7.1 Execution status — read this first

**The tests described in this document have never been executed.** The build
environment carries no Odoo runtime and no PostgreSQL server, so the suite
could not be run. Consequently:

- **no pass rate is claimed;**
- **no coverage figure is claimed;**
- the target of 95 per cent coverage set by the development framework is
  **not demonstrated**, and this document does not assert that it is met.

What can be stated is that every test module compiles, that every model,
field and method it names exists in the source, and that the assertions were
written against the implementation as read, not against an assumption of it.
Executing the suite is the first task of the receiving team.

## 7.2 How to execute the suite

```bash
odoo-bin -d <database> -i ls_pharma --test-enable --stop-after-init
```

All tests are tagged `post_install, -at_install`, so they run once the
module and its dependencies are fully installed.

## 7.3 Test modules

| Module | Tests | What it covers |
|---|---|---|
| `common.py` | fixtures | Products, materials, five users, and a helper that drives a batch to review |
| `test_gs1.py` | 15 | Check digit arithmetic, key validation, element strings, serial generation |
| `test_material.py` | 8 | Mixin fields, code uniqueness, the four-state lifecycle, the animal-origin rule, retest period |
| `test_batch.py` | 14 | Sequence, yield computation, both yield limits, the state machine, every guard, component verification, date rules, counters |
| `test_batch_record.py` | 13 | Master record check, step settlement, reviewer separation, discrepancy gating, control conformity, labelling reconciliation, clearance moments, reserve samples, completion percentage, rejection |
| `test_batch_release.py` | 12 | The wizard, the checklist, the four gate conditions, the manufacturer separation, append-only writes and deletes, the digest, the certificate lines, the one-decision rule |
| `test_stability.py` | 15 | The shipped ICH conditions, all three frequency series, schedule generation and idempotence, scheduled dates, the time point lifecycle, out-of-specification results, significant change, samples, the wizard, completion guards |
| `test_serialization.py` | 12 | Generation, uniqueness, element strings, invalid check digits at both layers, past expiry, the unit lifecycle, packing, empty and uncommissioned containers, invalid container codes, disaggregation |
| `test_ctd.py` | 12 | Sequence, the shipped template, loading and idempotence, completion percentage, section and dossier lifecycles, authorisation number, deficiency, deletion guard |
| `test_security.py` | 9 | The six groups, the quality-production separation in the role model, viewer and operator rights, the absence of any delete right on a decision, record rule coverage, the append-only guard under `sudo` |
| `test_installation.py` | 11 | Module state, sequences, shipped data, crons and their execution, reports, root menu, view validity, checklist coherence, access coverage |

121 test methods across ten test modules, plus the shared fixtures.
The counts above were obtained by counting the `def test_` definitions in
the sources, not estimated.

## 7.4 Test types against the framework's categories

| Category | Where it is covered |
|---|---|
| Unit | `test_gs1.py`, the computed-field assertions throughout |
| Integration | `test_batch_release.py` and the `_run_batch_to_review` fixture, which crosses batch, record, step and release |
| Functional | The lifecycle tests in every module |
| Security | `test_security.py`, including a `sudo` escalation attempt against the append-only guard |
| Installation | `test_installation.py`, which asserts what the data files created |
| Constraint | Every `assertRaises(UserError)` case, of which there are more than thirty |
| Workflow | The state machine tests in batch, record, stability, serialisation and dossier |
| Upgrade | **Not covered.** See section 7.6 |
| Performance | **Not covered.** See section 7.6 |

## 7.5 Notable test design choices

- No test names an external XML identifier. Units of measure are found by
  searching; products are created. A test suite that hard-codes another
  module's identifier fails for reasons that have nothing to do with the code
  under test.
- The GS1 test reproduces the worked example published by GS1 US, in which
  the twelve data digits 629104150021 yield the check digit 3. That is an
  external oracle rather than a restatement of the implementation.
- The stability tests assert the exact month series 0, 3, 6, 9, 12, 18, 24
  for a twenty-four month long term study, derived from the published
  frequencies rather than from the code.
- The security test attempts the write under `sudo`, because a guard that
  only holds for unprivileged users is not a guard.

## 7.6 Gaps, stated plainly

| Gap | Consequence |
|---|---|
| The suite has never run | No behaviour is confirmed; a defect could exist in any assertion |
| No coverage measurement | The proportion of code exercised is unknown |
| No upgrade test | Migration from a future version is untested |
| No performance test | Behaviour at volume is unknown; the serial generator in particular draws in a loop and its behaviour for very large quantities has not been measured |
| No multi-company test | The record rules are asserted to exist, not asserted to isolate |
| No report rendering test | The two QWeb templates have never been rendered |

## Gate verdict

**CONDITIONAL PASS.** The suite is written, complete against the
specification, and internally consistent with the code. It is unexecuted, so
this gate cannot be closed. It closes when the receiving team runs the suite
and records the result.
