# ls_capa — Validation Report

**Module:** `ls_capa` 19.0.1.0.0
**Status:** **NOT VALIDATED — qualification not performed**

---

## 1. Statement of status

This document is **not** evidence of a completed validation. It is a
validation *plan and gap record*.

No Installation Qualification, Operational Qualification or Performance
Qualification has been executed against this module. Executing them
requires a target environment, an approved protocol, trained personnel
and quality approval — none of which are supplied by software.

**Software cannot validate itself.** Computerised system validation is
an activity performed by the implementing organization against its own
intended use and risk assessment. A vendor statement of compliance would
have no standing with an inspector, and none is made here.

## 2. What the module contributes toward validation

The module supplies inputs a validation team would otherwise have to
create. It does not supply the validation.

| Deliverable | Status |
|---|---|
| Functional Specification | Source specification section 7.3, plus `docs/PHASE_REPORT.md` phases 1–4 |
| Design documentation | `README.rst`, `docs/DEVELOPER_MANUAL.md`, `docs/API_REFERENCE.md` |
| Configuration documentation | `docs/CONFIGURATION.md` |
| Automated test suite | 112 tests, `docs/TEST_REPORT.md` |
| Operating procedures input | `docs/USER_MANUAL.md`, `docs/ADMINISTRATOR_MANUAL.md` |
| Change control input | `CHANGELOG.md`, semantic module version |

## 3. Deliverables the organization must produce

| Deliverable | Owner | Status |
|---|---|---|
| Validation Plan | Validation | Not started |
| User Requirements Specification | Quality | Not started |
| Risk assessment against intended use | Quality / Validation | Not started |
| Configuration Specification | IT / Validation | Not started |
| IQ protocol and execution | IT / Validation | Not started |
| OQ protocol and execution | Validation | Not started |
| PQ protocol and execution | Quality | Not started |
| Traceability matrix URS → FS → test | Validation | Not started |
| SOPs for CAPA and for system administration | Quality | Not started |
| Training records | Quality | Not started |
| Validation Summary Report | Validation | Not started |

## 4. Proposed IQ checks

Derived from `docs/INSTALLATION.md` section 5. These are proposed
protocol content, not executed results.

| # | Check | Acceptance criterion |
|---|---|---|
| IQ-01 | Odoo version | 19.0 Community confirmed |
| IQ-02 | Module version installed | 19.0.1.0.0 in *Apps* |
| IQ-03 | Dependencies present | `base`, `mail`, `project` installed |
| IQ-04 | Installation log | No ERROR or WARNING for `ls_capa` |
| IQ-05 | Security groups | Four groups under CAPA Management privilege |
| IQ-06 | Access control lines | 20 ACL records present |
| IQ-07 | Record rules | Five multi-company rules present and global |
| IQ-08 | Sequences | Four sequences present with documented prefixes |
| IQ-09 | Default categories | Five categories present |
| IQ-10 | Scheduled action | Present and inactive as shipped |
| IQ-11 | Report registered | `ls_capa.report_capa_issue` bound to the model |

## 5. Proposed OQ checks

Each maps to an automated test. The automated suite provides supporting
evidence but does **not** replace witnessed OQ execution where the
organization's procedure requires it.

| # | Function | Acceptance criterion | Automated evidence |
|---|---|---|---|
| OQ-01 | Reference allocation | Unique sequential reference per CAPA | `test_sequence_allocated`, `test_sequence_unique_across_records` |
| OQ-02 | Lifecycle | All eight statuses reachable in order | `test_full_happy_path` |
| OQ-03 | Step skipping prevented | Out-of-order transition rejected | `test_transition_from_wrong_state_is_blocked` |
| OQ-04 | Impact assessment gate | Assess rejected without assessment | `test_assess_requires_impact_assessment` |
| OQ-05 | Root cause gate | Planning rejected without confirmed analysis | `test_action_planning_requires_confirmed_root_cause` |
| OQ-06 | Action completion evidence | Done rejected without evidence | `test_done_requires_evidence` |
| OQ-07 | Effectiveness gate | Verify rejected without effective check | `test_verify_requires_effective_check` |
| OQ-08 | Closure gate | Close rejected without summary | `test_close_requires_summary` |
| OQ-09 | FMEA scale | Ratings outside 1–10 rejected | `test_fmea_rating_out_of_range_rejected` |
| OQ-10 | Access control | Each group limited to its matrix row | ten tests in `test_capa_security.py` |
| OQ-11 | Multi-company isolation | Other-company records not visible | `test_multi_company_rule_hides_other_company_records` |
| OQ-12 | Record deletion restriction | Progressed CAPA cannot be deleted | `test_unlink_blocked_after_progress` |
| OQ-13 | Chatter records transitions | Each transition logged with user and time | `test_state_changes_are_logged` |
| OQ-14 | Report output | PDF contains all sections | Manual check required |

## 6. Proposed PQ approach

PQ is performed by quality staff on the validated configuration, using
real CAPA scenarios drawn from the organization's own history, over a
defined period, against the approved SOP. Suggested scenarios: a CAPA
raised from a deviation and closed as effective; a CAPA concluded not
effective and escalated to a follow-up; a CAPA involving an action that
is cancelled with justification; a CAPA crossing a company boundary in a
multi-company database.

## 7. Data integrity assessment (ALCOA+)

An honest assessment, not a compliance claim.

| Principle | Module contribution | Gap |
|---|---|---|
| Attributable | User recorded on every transition and message | No electronic signature binding |
| Legible | Structured fields and printable report | None identified |
| Contemporaneous | Server timestamps on messages, completion and closure | Planned dates are user-entered and can be back-dated |
| Original | Records held in PostgreSQL | No hash chain proving originality |
| Accurate | Constraints and gates enforce required content | Content accuracy depends on the user |
| Complete | Chatter retains history; progressed records not deletable | Identified-state records can be deleted |
| Consistent | Single enforced workflow | None identified |
| Enduring | Standard database retention | Retention policy is organizational |
| Available | Search, filter, print | None identified |

**Two material gaps** must be closed before this module supports a
Part 11 regulated process: electronic signatures
(`ls_electronic_signature`) and a tamper-evident audit trail
(`ls_audit_trail`). Neither is implemented here.

## 8. Conclusion

The module is a **release candidate** with a documented design, a
substantial automated test suite and an explicit statement of what it
does not provide.

It is **not validated**, and it must not be described as validated,
compliant or Part 11 ready. Whether it is fit for a given regulated use
can only be established by the implementing organization through the
qualification activities listed in section 3.
