# Validation Report

Module: `ls_calibration` `19.0.1.0.0`. Date: July 2026.

## 1. Purpose and status of this document

This document reports what was verified during the construction of the
module and what remains to be verified in the target environment. **It is not
a computerised system validation report.** A CSV report is produced by the
regulated organisation, on its own infrastructure, under its own procedures,
and covers the installed system, not the source code.

This module is one component of that system. It can support a validation
exercise; it cannot replace one.

## 2. Verified during construction

| # | Item | Method | Result |
|---|------|--------|--------|
| V-01 | Python syntax of the 22 source files | AST parsing | Pass |
| V-02 | Well-formedness of the 14 XML files | lxml parsing | Pass |
| V-03 | Every file declared in the manifest exists | Manifest analysis | Pass |
| V-04 | Every internal XML identifier resolves | Cross-reference analysis | Pass |
| V-05 | Access rights cover every model of the module | CSV analysis against the declared models | Pass |
| V-06 | Access rights reference existing groups | CSV analysis against the security file | Pass |
| V-07 | No deprecated Odoo 17, 18 or 19 construct | Pattern analysis | Pass |
| V-08 | No placeholder, no commented-out code, no method without docstring | AST and pattern analysis | Pass |
| V-09 | The field tables of the technical specification match the source | Generated from the source | Pass |
| V-10 | Odoo 19 constraint API | Official Odoo 19 documentation | Verified: `models.Constraint` replaces `_sql_constraints` |
| V-11 | Odoo 19 translation API | Official Odoo 19 coding guidelines | Verified: `self.env._` |
| V-12 | List view element | Odoo 18 change | Verified: `<list>` |
| V-13 | Chatter element | Odoo 18 change | Verified: `<chatter/>` for Odoo 18; assumed unchanged in 19 |
| V-14 | Regulatory status of 21 CFR Part 820 | FDA and Federal Register | Verified: QMSR effective 2 February 2026, incorporating ISO 13485:2016 by reference |

## 3. Not verified, to be verified in the target environment

Each item is a specific action, not a general reservation.

| # | Item to verify | How | Impact if it fails |
|---|----------------|-----|--------------------|
| NV-01 | The module installs on Odoo 19 Community | `odoo-bin -i ls_calibration` | Blocking |
| NV-02 | The module updates without loss | Update on a copy of production | Blocking |
| NV-03 | The 101 tests pass | `--test-enable --test-tags ls_calibration` | Blocking |
| NV-04 | Coverage reaches the 95 % target | `coverage report` | Major |
| NV-05 | flake8, pylint and pylint-odoo report nothing blocking | Run in the target environment | Major |
| NV-06 | `<chatter/>` is still the Odoo 19 element | Open any form | Major, cosmetic to blocking |
| NV-07 | `maintenance.equipment.category` is readable by an internal user | Open the instrument form as a technician | Major |
| NV-08 | `implied_ids` still exists on `res.groups` in Odoo 19 | The installation would fail otherwise | Blocking |
| NV-09 | The `ir.cron` fields used are still valid in Odoo 19 | The installation would fail otherwise | Blocking |
| NV-10 | `_render_qweb_html(report_ref, res_ids)` signature | Run `test_report` | Minor, tests only |
| NV-11 | The name of the users-to-groups field | Resolved at run time by the fixtures | Minor, tests only |
| NV-12 | The PDF reports render with the installed `wkhtmltopdf` | Print a record and a certificate | Major |
| NV-13 | The demonstration data loads, including its four `<function>` calls | Install with demonstration data | Minor |

## 4. Declared limitations

These are scope decisions, not defects. They are repeated here because a
validation file must state them.

| # | Limitation |
|---|------------|
| L-01 | The approval records the signer, the time and the meaning of the signature, but does **not** re-authenticate the signer. The module alone does not provide FDA 21 CFR Part 11 electronic signatures. |
| L-02 | The audit trail is the standard Odoo change tracking on the tracked fields. It is neither exhaustive at field level nor tamper evident. |
| L-03 | The out-of-tolerance action reference is free text, not a controlled link to a deviation record. |
| L-04 | The calibration procedures are referenced, not managed under document control. |
| L-05 | The national requirements applicable in Algeria were not verified against any ANPP publication. |
| L-06 | The `ls_qms` dependency required by the suite specification is deliberately omitted, because that module does not exist and declaring it would prevent installation. |
| L-07 | The calibration status is not storable and therefore not usable as a group-by axis. |
| L-08 | Filtering on the calibration status is resolved in Python, not in SQL. |

## 5. Data integrity assessment against ALCOA+

| Principle | Assessment |
|-----------|------------|
| Attributable | Performer, submitter and approver are recorded as user references, not as free text. Depends on individual user accounts being used. |
| Legible | The records are readable in the interface and in the PDF reports. |
| Contemporaneous | The calibration date is entered by the technician; the submission and approval timestamps are set by the server, not by the user. |
| Original | The electronic record is the original; the PDF states this explicitly. |
| Accurate | The verdicts and the result are computed from the readings and cannot be entered manually. |
| Complete | Submission is refused while any mandatory element is missing. |
| Consistent | The workflow is identical for every record; the sequences give a chronological identifier. |
| Enduring | Approved records and issued certificates cannot be deleted by any role. |
| Available | The history is on the instrument form; the reports are printable at any time. |

Residual weakness: the audit trail depth, limitation L-02.

## 6. Recommended qualification approach for the organisation

1. Write a user requirements specification and trace it to Phase 1 of this
   documentation set.
2. Perform a risk assessment of the intended use, considering that the module
   controls a GxP decision, namely whether an instrument may be used.
3. Installation qualification: verify checks IV-01 to IV-08 of the
   installation guide on the qualified instance.
4. Operational qualification: execute NV-01 to NV-13 above, plus the twenty
   business rules of the functional specification, as documented test cases.
5. Performance qualification: run one complete calibration cycle per
   instrument category, with the real users and the real procedures,
   including one deliberate out-of-tolerance case.
6. Write the procedures that the software does not enforce: how a deviation
   is opened after an out-of-tolerance event, how the calibration intervals
   are justified and reviewed, how the certificates of the external
   laboratories are checked.
7. Train the users and record the training.

## 7. Conclusion

The module is complete against its specification, is internally consistent,
enforces its twenty business rules in code, and declares its eight
limitations. It has not been executed. It is therefore delivered as **Beta**,
and the manifest states this.

Promotion to production status requires the closure of NV-01 to NV-13.
