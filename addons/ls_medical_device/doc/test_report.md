# Test Report — `ls_medical_device`

**Status: TESTS WRITTEN, NEVER EXECUTED.**

This report describes a test suite that exists as source code and has not been
run. No assertion in it has been observed to pass or fail. It is included so
the receiving organisation knows what has been prepared and what remains to be
demonstrated — not as evidence that the module works.

## 1. Why the suite was not executed

The build environment provides Python 3.12 and `lxml` only. It has no Odoo
runtime, no PostgreSQL instance and no network access, so `pip install` is
unavailable. Odoo tests require a live registry and database; neither could be
provided.

## 2. Suite inventory

| Module | Tests | Classes |
|---|---:|---|
| `test_device.py` | 20 | TestDevice |
| `test_udi.py` | 8 | TestUdi |
| `test_risk.py` | 13 | TestRiskManagement |
| `test_clinical.py` | 14 | TestClinicalEvaluation, TestPmcfEvaluation |
| `test_technical_file.py` | 11 | TestTechnicalFile |
| `test_ce_marking.py` | 9 | TestCeMarking |
| `test_pms.py` | 23 | TestPmsPlan, TestPmsReport |
| `test_security.py` | 17 | TestAccessRights, TestSegregationOfDuties, TestRecordRules |
| `test_wizards.py` | 11 | TestDeviceStateWizard, TestPmsReportWizard |
| `test_install.py` | 11 | TestInstallation |
| **Total** | **137** | 15 |

All tests derive from `MedicalDeviceCommon` (`tests/common.py`), which builds
five users at the four access levels, a notified body, and three devices of
classes I, IIa and III.

Users are created with `new_test_user`, which accepts group external
identifiers as a string. This avoids depending on the `res.users` groups field
name, which could not be verified for Odoo 19.0.

## 3. Coverage by concern

| Concern | Covered by |
|---|---|
| Sequence allocation and display names | test_device, test_pms |
| Device life cycle and transition preconditions | test_device, test_wizards |
| Retention periods (Art. 10(8), 10 and 15 years) | test_device |
| Periodic report obligation derived from risk class | test_device, test_install |
| UDI uniqueness, life cycle, issuing entity note | test_udi |
| Risk index arithmetic and residual-vs-initial rule | test_risk |
| Risk file statistics and approval gate | test_risk |
| Clinical equivalence, investigation and PMCF justifications | test_clinical |
| PMCF annual update for class III (Art. 61(11)) | test_clinical |
| Documentation seeding, completeness, evidence reference | test_technical_file |
| Certificate route, validity, expiry, expiry cron | test_ce_marking |
| Plan mandatory elements at approval (Annex III 1.1) | test_pms |
| Report content, trend signal, Art. 86(2) submission flag | test_pms |
| Access rights per level | test_security |
| Segregation of duties and self-approval refusal | test_security |
| Multi-company record rule behaviour | test_security |
| Wizard transitions and bulk report creation | test_wizards |
| Installed artefacts (data, sequences, crons, groups, menus) | test_install |

## 4. Not covered

Stated so the gaps are not mistaken for coverage:

- **Performance and load.** No test measures query counts or execution time.
  Section 7 of the master framework asks for performance tests; none are
  present, because a meaningful measurement requires a populated database.
- **Upgrade tests.** No test installs an earlier version and upgrades to this
  one. This module is version 19.0.1.0.0 with no predecessor, so there is no
  upgrade path to exercise yet.
- **QWeb report rendering.** The three PDF reports are not rendered by any
  test. Rendering requires wkhtmltopdf and a running server.
- **View rendering.** Views are validated structurally by the static checker,
  not rendered by Odoo. A view that parses and whose fields resolve can still
  fail at render time on an attribute Odoo 19 no longer accepts.
- **Concurrency.** No test exercises simultaneous approval of the same record.

## 5. Defects found while writing the tests

Writing tests against the model source — rather than against an inventory of
its names — surfaced three defects that were fixed:

| Defect | Resolution |
|---|---|
| `ls.md.pms_report.notified_body_submission_required` was set only by an `@api.onchange`, so a report created through the ORM for an implantable device silently lost its Article 86(2) obligation | Defaulted in `create()` as well, without overriding an explicit value |
| `DEVICE_ALLOWED_TRANSITIONS` permitted `conformity_assessment → development` (rework), but `action_start_development` refused any state other than draft, so the wizard failed on a declared transition | `action_start_development` now accepts both draft and conformity assessment |
| Five source lines exceeded the 88-character limit | Reformatted |

Three test assumptions were also wrong and were corrected against the method
bodies: the PMS content gate is on approval rather than submission; the plan
setup omitted two of the five mandated elements; and `next_review_date` is a
user-maintained field, not a computed one.

**This is the finding that matters most.** Roughly a quarter of the
assumptions checked in the first pass were wrong, because they were derived
from a field and method inventory rather than from the method bodies. The
remaining assertions were subsequently written against the bodies, but none
has been executed, so the residual error rate in this suite is unknown and
should be assumed non-zero.

## 6. How to execute the suite

```bash
odoo -d <database> -i ls_medical_device \
     --test-enable --test-tags /ls_medical_device --stop-after-init
```

With coverage measurement:

```bash
coverage run --source=/path/to/addons/ls_medical_device \
    odoo-bin -d <database> -i ls_medical_device \
    --test-enable --test-tags /ls_medical_device --stop-after-init
coverage report -m
```

The master framework sets a minimum coverage target of 95%. **No coverage
figure is claimed here**, because none was measured. The target remains to be
demonstrated by the receiving organisation.

## 7. Static analysis actually performed

| Check | Result |
|---|---|
| Python syntax (`py_compile`, `ast.parse`) — 33 files | Pass |
| XML well-formedness (`lxml`) — 25 files | Pass |
| Manifest and disk agreement | Pass |
| Package imports match module files | Pass |
| View fields resolve against models | Pass |
| View buttons resolve to model methods | Pass |
| XML ID references resolve | Pass |
| ACL covers every model (45 lines, 17 models) | Pass |
| `comodel_name` resolution | Pass |
| No placeholder tokens | Pass |
| No raw SQL | Pass |
| PEP 8 subset (line length, tabs, trailing whitespace) | Pass |
| Docstrings on modules, classes, public methods | Pass |
| `widget="percentage"` only on 0–1 ratio fields | Pass |
| Test field and action names resolve | Pass |

The checker itself was validated by injecting 16 known faults into a copy of
the module and confirming each was detected (16/16). A checker whose failure
path has never been exercised provides no assurance.

**Not run:** `flake8`, `pylint`, `pylint-odoo`. These could not be installed.
The PEP 8 subset above is a substitute for a small part of what `flake8` would
report, not an equivalent.
