# PHASE 1 — BUSINESS ANALYSIS · PHASE 2 — REGULATORY ANALYSIS

**Module:** `ls_lab` — Laboratory Management
**Suite:** Life Sciences Suite for Odoo 19 Community Edition
**Date:** 2026-08-06

---

# PHASE 1 — BUSINESS ANALYSIS

## 1.1 Business objectives

| # | Objective |
|---|-----------|
| BO-01 | Provide a single controlled register of analytical test methods with an approval lifecycle and versioning. |
| BO-02 | Provide versioned, approved product specifications against which results are evaluated. |
| BO-03 | Register and track laboratory samples from receipt to reporting with an auditable state machine. |
| BO-04 | Record test results such that the pass/fail evaluation is **derived from the approved specification**, never asserted by the analyst. |
| BO-05 | Detect out-of-specification results automatically and force a structured, two-phase investigation before disposition. |
| BO-06 | Manage stability studies with configurable storage conditions and time points, and generate the pull samples from them. |
| BO-07 | Issue Certificates of Analysis derived only from reviewed and approved results. |
| BO-08 | Enforce segregation of duties between analyst, reviewer and approver at the ORM layer. |
| BO-09 | Preserve the integrity of approved records: approved objects are frozen and superseded by new versions, never edited in place. |

## 1.2 Business requirements

| # | Requirement | Objective |
|---|-------------|-----------|
| BR-01 | Test methods shall have states Draft → Under Review → Approved → Obsolete. | BO-01 |
| BR-02 | An approved test method shall not be modifiable; revision shall create a new version. | BO-01, BO-09 |
| BR-03 | A specification shall consist of a header plus one line per test with explicit acceptance criteria. | BO-02 |
| BR-04 | At most one approved specification shall exist per (product, specification type) at any time. | BO-02 |
| BR-05 | A sample shall reference exactly one approved specification version, captured at registration. | BO-03 |
| BR-06 | Test result lines shall be generated from the referenced specification, not entered ad hoc. | BO-04 |
| BR-07 | The evaluation field shall be computed and shall not be writable by any user. | BO-04 |
| BR-08 | Any result evaluating to `fail` shall block sample approval until an OOS investigation is concluded. | BO-05 |
| BR-09 | Retesting and resampling shall require documented authorisation recorded before the retest is performed. | BO-05 |
| BR-10 | Stability storage conditions and time points shall be configuration data, not shipped constants. | BO-06 |
| BR-11 | A Certificate of Analysis shall only be issuable from a sample in state Approved. | BO-07 |
| BR-12 | The user reviewing results shall not be the user who entered them. | BO-08 |
| BR-13 | The user approving a sample shall not be the user who reviewed it. | BO-08 |
| BR-14 | The QA approver closing an OOS shall not be the investigator. | BO-08 |
| BR-15 | Scheduled actions shall notify only; they shall never change a regulated state. | BO-09 |

## 1.3 Stakeholders

| Stakeholder | Interest |
|-------------|----------|
| QC Laboratory Manager | Throughput, resourcing, method and specification lifecycle, final approval. |
| Laboratory Analyst | Sample handling, test execution, result entry. |
| Laboratory Reviewer / Senior Analyst | Second-person verification of results. |
| Quality Assurance | OOS oversight, disposition decisions, batch-supporting data, CoA issue. |
| Regulatory Affairs | Evidence for submissions and inspections. |
| Stability Coordinator | Study protocols, pull schedules, time point adherence. |
| Production / Planning | Release status of tested lots. |
| IT / Validation | Installation, configuration, computerised system validation. |
| Inspector / Auditor (external) | Read-only reconstruction of who did what, when, and on what basis. |

## 1.4 User roles

| Role | Group | Capability summary |
|------|-------|--------------------|
| Laboratory Viewer | `ls_lab_group_viewer` | Read-only on all laboratory records. |
| Laboratory Analyst | `ls_lab_group_analyst` | Register samples, enter results, request retest; cannot review, approve, or issue CoA. |
| Laboratory Reviewer | `ls_lab_group_reviewer` | Review results and samples, conduct OOS Phase I; cannot approve samples or close OOS. |
| Laboratory Manager | `ls_lab_group_manager` | Approve methods, specifications, samples; close OOS; issue CoA; configure master data. |

Groups are hierarchical: manager implies reviewer implies analyst implies viewer.

## 1.5 User stories

| # | Story |
|---|-------|
| US-01 | As a Laboratory Manager, I define an analytical test method and approve it so that it can be referenced by specifications. |
| US-02 | As a Laboratory Manager, I build a product specification from approved methods and approve it so that samples can be tested against it. |
| US-03 | As a Laboratory Analyst, I register a received sample against the approved specification so that its test list is created automatically. |
| US-04 | As a Laboratory Analyst, I enter a numeric result and the system tells me whether it conforms, so that I cannot mis-state conformity. |
| US-05 | As a Laboratory Reviewer, I review results entered by another analyst so that second-person verification is evidenced. |
| US-06 | As a Laboratory Manager, I approve a sample only when every mandatory test is reviewed and no OOS is open. |
| US-07 | As a Laboratory Reviewer, I open an OOS investigation automatically raised by a failing result and complete the Phase I laboratory assessment. |
| US-08 | As a Laboratory Manager, I authorise a retest with written justification before any retest is performed. |
| US-09 | As a Laboratory Manager, I close an OOS with a conclusion and a product disposition. |
| US-10 | As a Stability Coordinator, I define a study with configurable time points and generate a pull sample at each point. |
| US-11 | As a Laboratory Manager, I issue a Certificate of Analysis for an approved sample and print it as PDF. |
| US-12 | As an Auditor, I read the full history of a result without being able to modify anything. |

## 1.6 Use cases

| # | Use case | Primary actor | Precondition | Postcondition |
|---|----------|---------------|--------------|---------------|
| UC-01 | Create and approve test method | Manager | — | Method in state Approved, frozen |
| UC-02 | Revise approved test method | Manager | Method Approved | New Draft version; predecessor Obsolete |
| UC-03 | Create and approve specification | Manager | Approved methods exist | Specification Approved; prior version superseded |
| UC-04 | Register sample | Analyst | Approved specification exists | Sample in Received; result lines generated |
| UC-05 | Enter results | Analyst | Sample in In Progress or Testing | Results in Entered; evaluation computed |
| UC-06 | Review results | Reviewer ≠ analyst | All mandatory results Entered | Results Reviewed; sample Reviewed |
| UC-07 | Approve sample | Manager ≠ reviewer | Sample Reviewed; no open OOS | Sample Approved |
| UC-08 | Handle OOS | Reviewer, Manager | Result evaluates Fail | OOS raised, investigated, concluded |
| UC-09 | Authorise retest | Manager | OOS in Phase I or II | Authorisation recorded with justification |
| UC-10 | Run stability pull | Coordinator | Study Ongoing; time point Planned | Sample created and linked to time point |
| UC-11 | Issue CoA | Manager | Sample Approved | CoA Issued; PDF printable |
| UC-12 | Cancel sample | Manager | Sample not Approved/Reported | Sample Cancelled with recorded reason |

## 1.7 Functional scope (in scope)

1. Analytical test method register with lifecycle and versioning.
2. Product specification register with lines, lifecycle and versioning.
3. Sample registration and state machine.
4. Test result capture with computed conformity evaluation.
5. OOS/OOT investigation with two-phase structure, retest/resample authorisation, conclusion and disposition.
6. Stability study register with configurable storage conditions and time points, and pull-sample generation.
7. Certificate of Analysis with QWeb PDF report.
8. OOS investigation QWeb PDF report.
9. Storage condition master data.
10. Four security groups, ACLs and record rules.
11. Three notification-only scheduled actions.
12. Search, list, form, kanban, pivot and graph views, filters and Group By.
13. Three wizards: sample cancellation, stability pull, signature-intent confirmation.

## 1.8 Out of scope (explicitly)

1. Direct instrument interfacing or data acquisition (no LIMS driver layer, no chromatography data system integration).
2. Statistical out-of-trend determination. `is_oot` is a manually asserted flag with mandatory justification; the module performs no trend statistics.
3. Stability shelf-life extrapolation or regression modelling.
4. Electronic signature re-authentication. See §2.6.
5. Pharmacopoeial monograph content of any kind.
6. Shipping of ICH storage conditions or time points as data.
7. Sample scheduling/workload balancing algorithms.
8. Chain-of-custody barcode scanning workflows.
9. Environmental monitoring sample handling — provided by `ls_environmental_monitoring`.
10. CAPA records — referenced by free-text field only; provided by `ls_capa`.
11. Instrument calibration records — referenced by free-text field only; provided by `ls_calibration`.

## 1.9 Risks

| # | Risk | Impact | Mitigation |
|---|------|--------|------------|
| R-01 | Module never installed on live Odoo 19 in this environment. | Install-time failure undetected. | Static checker validates against the **actual Odoo 19 RNG schemas** retrieved from source; risk stated openly in the validation report. |
| R-02 | Specification changed after samples reference it. | Results evaluated against shifting criteria. | Approved specifications frozen; samples store `specification_id` and evaluation reads the stored line. |
| R-03 | Analyst self-reviews results. | Loss of second-person verification. | ORM-level constraint on reviewer identity. |
| R-04 | Evaluation overwritten to hide a failure. | Data integrity breach. | `evaluation` is computed, stored, non-writable; no UI field is editable. |
| R-05 | Retest performed before authorisation. | Regulatory finding. | Retest creation blocked unless authorisation recorded first. |
| R-06 | Hardcoded ICH conditions become obsolete. | Incorrect regulatory reference. | No conditions shipped; ICH Q1 is mid-revision (see §2.3). |
| R-07 | Suite sibling modules absent at install. | Install failure. | No `ls_*` module declared as a dependency; cross-references are free-text. |
| R-08 | `quality` module assumed present. | Install failure. | Verified absent from Odoo 19 Community; not depended upon. |

## 1.10 Success criteria

| # | Criterion | Verification |
|---|-----------|--------------|
| SC-01 | Every Python file compiles. | `py_compile` — Phase 8 |
| SC-02 | Every XML file is well-formed. | `lxml.etree.parse` — Phase 8 |
| SC-03 | Every view arch validates against the correct Odoo 19 RNG. | RNG validation — Phase 8 |
| SC-04 | Every model has ACL rows for all four groups. | Static checker — Phase 8 |
| SC-05 | Every view field resolves on its model. | Static checker — Phase 8 |
| SC-06 | Every button method exists. | Static checker — Phase 8 |
| SC-07 | Every external ID resolves. | Static checker — Phase 8 |
| SC-08 | No `<tree>`, no `_sql_constraints`, no `numbercall`/`doall`, no `groups_id`. | Static checker — Phase 8 |
| SC-09 | Checker itself detects seeded faults. | Negative control harness — Phase 8 |
| SC-10 | Tests written for every workflow rule. | Phase 7 |

**PHASE 1 GATE: PASS** — all deliverables produced; scope and out-of-scope explicitly enumerated.

---

# PHASE 2 — REGULATORY ANALYSIS

## 2.1 Statement of position

This module **supports implementation** of laboratory processes. It does **not** confer
compliance with any framework. No certification is claimed. Every citation below is given
with its source; where a status could not be confirmed it is marked **UNVERIFIED**.

## 2.2 Frameworks applicable to this module

| Framework | Relevance to `ls_lab` | Status |
|-----------|----------------------|--------|
| FDA 21 CFR Part 211 Subpart I (Laboratory Controls, §§211.160–211.176) | Specifications, test procedures, sampling, stability | Cited below |
| FDA 21 CFR Part 211 Subpart J (Records and Reports, §§211.180–211.198) | Laboratory records, second-person review, investigations | Cited below |
| FDA OOS Guidance (Level 2 revision) | Two-phase OOS investigation structure, retest justification | Verified, see §2.4 |
| FDA 21 CFR Part 11 | Electronic records and signatures | Partial — see §2.6 |
| ICH Q1A(R2) / consolidated ICH Q1 | Stability study design | Verified, in transition — see §2.3 |
| ICH Q2(R2) | Analytical procedure validation | Referenced as method attribute only |
| EU GMP Chapter 6 | Quality Control | Reference level |
| ISO/IEC 17025 | Testing laboratory competence | Reference level |
| ISO 13485:2016 | Device QMS, monitoring and measurement | Reference level |
| Algerian BPF / ANPP corpus | National pharmaceutical GMP | **Reference level only** — see §2.7 |

## 2.3 Stability — verified regulatory position

The consolidated **ICH Q1 draft "Stability Testing of Drug Substances and Drug Products"
reached Step 2b of the ICH process on 11 April 2025** and entered public consultation, which
has since closed. The document is explicitly **not** to be used or referenced as the final
guideline and will undergo change through Step 4.

FDA published the corresponding draft guidance in **June 2025 under docket
FDA-2025-D-1106**, marked *Draft — not for implementation*. It is described as a consolidated
revision of ICH Q1A(R2), Q1B, Q1C, Q1D, Q1E and Q5C.

**Until Step 4 and regional adoption, the legacy Q1A(R2)–Q1E and Q5C guidelines remain the
applicable standard.** Q1A(R2) itself reached Step 4 on 6 February 2003.

**Design consequence (BR-10).** Because the governing reference is actively in transition,
`ls_lab` ships **no** storage conditions, **no** time point schedules and **no** shelf-life
rules as data or constants. `ls.lab.storage_condition` and
`ls.lab.stability_timepoint` are configuration objects populated by the implementing
organisation against whichever guideline version applies to it. This is a deliberate design
decision, recorded here so that it is not mistaken for an omission.

**UNVERIFIED:** whether ICH Q1 has reached Step 4 after this build date. Implementers must
check current status.

## 2.4 OOS handling — verified regulatory position

The FDA guidance *Investigating Out-of-Specification (OOS) Test Results for Pharmaceutical
Production — Level 2 revision* is dated **May 2022**, docket **FDA-1998-D-0019**, issued by
CDER. It supersedes the 2006 version.

The guidance defines OOS results as **all test results falling outside the specifications or
acceptance criteria established in drug applications, drug master files, official compendia,
or by the manufacturer**, and states that the term also applies to in-process laboratory tests
outside established specifications.

The guidance covers the responsibilities of laboratory personnel, the laboratory phase of the
investigation, additional testing that may be necessary, when to expand the investigation
outside the laboratory, and final evaluation of all results. It states that retesting of a
portion of the original sample may form part of the investigation, and that implicit in the
requirement to investigate is the need to implement corrective and preventive action,
consistent with ICH Q10.

`21 CFR 211.165(f)` requires that finished drug products failing to meet established
standards, specifications or other relevant quality control criteria be rejected.

**Design consequences.**

| Guidance element | Implementation in `ls_lab` |
|------------------|----------------------------|
| OOS = result outside established acceptance criteria | `evaluation` computed against the approved specification line; `fail` raises an OOS record automatically. |
| Laboratory phase of investigation | `ls.lab.oos` Phase I block with explicit assessment fields (analyst interview, calculation check, instrument check, standard check, sample integrity, method adherence). |
| Investigation expanded outside the laboratory | Phase II block, entered only when Phase I concludes no assignable laboratory cause. |
| Retesting requires scientific justification | `retest_authorised` cannot be set without `retest_justification` and an authorising user; retest results cannot be created before authorisation. |
| Final evaluation and disposition | `final_conclusion` and `product_disposition` mandatory before closure. |
| CAPA linkage | `capa_reference` free-text field (no hard dependency on `ls_capa`). |

The module does **not** implement outlier tests. Outlier testing is a scientific decision the
guidance treats restrictively; automating it would risk misuse.

## 2.5 Laboratory records and second-person review

`21 CFR 211.194(a)` requires complete laboratory records including data on all tests
performed. `21 CFR 211.194(a)(7)–(8)` addresses the initials or signature of the person
performing the test and of a second person showing that records were reviewed for accuracy,
completeness and compliance with established standards.

**UNVERIFIED:** exact current sub-paragraph numbering was not re-read from eCFR during this
build. The requirement for a documented second-person review of laboratory records is the
basis for BR-12 and is implemented regardless of citation numbering.

**Design consequence.** `ls.lab.test_result` records `analyst_id` and `reviewed_by_id`
separately, and a Python constraint forbids them being the same user. Sample approval adds a
third distinct user.

## 2.6 Electronic signatures — scope limitation (stated prominently)

`ls_lab` provides a **signature-intent confirmation** wizard. It records: the signing user,
the UTC timestamp, the record signed, and the **meaning** of the signature (reviewed /
approved / authorised).

It does **NOT**:

- perform re-authentication of the user at the moment of signing;
- implement two distinct identification components;
- implement signature/record cryptographic binding;
- constitute a Part 11 compliant electronic signature.

**21 CFR Part 11 compliance is NOT claimed for this module.** Organisations requiring Part 11
electronic signatures must implement re-authentication at the platform level and validate it.
This limitation is repeated in the README, the Administrator Manual and the Validation Report.

## 2.7 Algerian regulatory corpus

Consistent with the suite-wide position, the Algerian ANPP / BPF corpus is carried at
**reference level only**. No Algerian regulatory text was read during this build, nothing was
derived from it, and no conformity with Algerian requirements is claimed or implied. Local
regulatory assessment remains the implementing organisation's responsibility.

## 2.8 What this module does not do

1. It does not certify compliance with any framework.
2. It does not replace laboratory SOPs.
3. It does not validate analytical methods — it records their validation status as an attribute.
4. It does not perform statistical trend analysis.
5. It does not make product disposition decisions — it records the decision and who made it.

**PHASE 2 GATE: PASS** — applicable frameworks identified; load-bearing claims sourced;
unverified items flagged; no compliance claimed.
