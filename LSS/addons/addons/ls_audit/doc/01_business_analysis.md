# 01 — Business Analysis

Phase 1 deliverable. Module: `ls_audit`.

## 1. Business objectives

| # | Objective | How the module serves it |
|---|---|---|
| O1 | Demonstrate to an inspector that audits were planned, not improvised | `ls.audit.program` groups audits over a defined period; each audit carries a planned date constrained to fall inside that period |
| O2 | Demonstrate auditor impartiality | Hard constraints refuse an audit whose team overlaps its auditees or the owners of the audited areas |
| O3 | Demonstrate auditor competence | An audit cannot be scheduled unless every team member holds a current qualification covering the audited areas |
| O4 | Prevent silent rewriting of what was audited | Checklist question text is copied into the audit at load time; approved checklists are immutable; changes require a new version |
| O5 | Ensure findings are actually resolved, not merely answered | A finding cannot close without a documented verification method and result, and never by the auditee |
| O6 | Make audit records defensible | Closed and issued records become read-only; every state change is attributed and timestamped in the chatter |
| O7 | Prevent findings from being quietly forgotten | Response deadlines are computed from the finding category; scheduled actions surface overdue audits and findings |

## 2. Stakeholders

| Stakeholder | Interest | Primary concern |
|---|---|---|
| Quality Manager | Owns the programme and the QMS | Coverage, timeliness, closure rate |
| Lead Auditor | Plans and runs engagements | Team qualification, evidence, report quality |
| Auditor | Executes fieldwork | Efficient recording of assessments and evidence |
| Auditee / Process Owner | Answers findings | Clear findings, realistic deadlines, visibility of what is owed |
| Regulatory Affairs | Faces the inspector | Retrievability, completeness, defensibility |
| IT / System Owner | Runs the system | Upgrade safety, access control, backup |
| Inspector / Notified Body | External assessment | Evidence that the process is real and followed |

## 3. User roles

Four hierarchical security groups, each implying the one below.

| Group | Technical name | Can do |
|---|---|---|
| Auditee | `group_ls_audit_auditee` | See audits they take part in, their own findings, and issued reports on which they are a recipient. Answer findings. |
| Auditor | `group_ls_audit_auditor` | Everything above, plus see all audits and findings, record assessments and evidence, raise findings, prepare reports. |
| Lead Auditor | `group_ls_audit_lead_auditor` | Everything above, plus create and drive audits through their lifecycle, accept or reject responses, verify and close findings. |
| Manager | `group_ls_audit_manager` | Everything above, plus maintain configuration, approve checklists, drive programmes, review, approve and issue reports, delete records. |

## 4. User stories

**Programme**
- As a Quality Manager, I plan an annual programme so that coverage is decided in advance and can be shown to an inspector.
- As a Quality Manager, I cannot approve an empty programme, so an approved programme always means something.
- As a Quality Manager, I cannot close a programme while an audit is still open, so a closed programme is a true statement.

**Planning**
- As a Lead Auditor, I am prevented from staffing an audit with someone who owns the area, so impartiality is structural rather than a matter of memory.
- As a Lead Auditor, I am prevented from scheduling an audit with a lapsed qualification, so competence is verified before fieldwork rather than questioned afterwards.
- As a Lead Auditor, I load an approved checklist so that the questions asked are the ones that were reviewed and approved.

**Fieldwork**
- As an Auditor, I cannot record a non-conformity without evidence, so every adverse assessment is supportable.
- As an Auditor, I cannot complete an audit while a mandatory question is unanswered, so coverage is complete.
- As an Auditor, I raise a finding directly from the question that failed, so the link between question and finding is never lost.

**Findings**
- As an Auditee, I see only my own findings, so my worklist is what I actually owe.
- As an Auditee, I am told exactly what the category requires — root cause, CAPA reference, or both — before I can submit.
- As a Lead Auditor, I can reject an inadequate response and send it back, so acceptance means something.
- As a Lead Auditor, I cannot close a finding without documenting how effectiveness was verified and what the verification showed.

**Reporting**
- As a Lead Auditor, I prepare a report but cannot review or approve my own work.
- As a Manager, I cannot issue a report to nobody.
- As anyone, once a report is issued it can no longer be edited.

## 5. Functional scope

**In scope**

1. Audit programme management with completion statistics.
2. Auditable area hierarchy with ownership.
3. Auditor qualification register with expiry, lead flag and scope.
4. Versioned, approved checklist templates.
5. Audit engagement lifecycle across six states.
6. Question-by-question assessment with evidence.
7. Finding lifecycle across six states with deadline computation.
8. Auditee response capture through a guided wizard.
9. Effectiveness verification and closure.
10. Audit report lifecycle with prepare, review, approve and issue as separate acts.
11. Two PDF outputs: audit report and finding notice.
12. Three scheduled notifications.
13. Row-level access control by role.
14. Justified cancellation of programmes, audits, findings and reports.

**Out of scope**

1. **CAPA management.** No CAPA module exists to depend on. Findings carry a free-text `capa_reference`.
2. **21 CFR Part 11 electronic signatures.** See `02_regulatory_analysis.md` §4.
3. **Document management.** Evidence is attached through Odoo's standard attachment mechanism, not a controlled DMS.
4. **Training records.** Qualification is recorded as a date and a certificate reference, not as completed courses.
5. **Supplier qualification.** Supplier audits can be recorded, but supplier approval status is not managed here.
6. **Kanban views.** Odoo 19 kanban template syntax could not be verified.
7. **Audit time and expense tracking.**
8. **External auditor portal access.**

## 6. Risks

| # | Risk | Impact | Mitigation |
|---|---|---|---|
| R1 | The test suite has never run | High — undetected runtime defects | Mandatory execution before use; documented in README §1.3 |
| R2 | Users mistake approvals for Part 11 signatures | High — regulatory | Explicit disclaimer in the PDF signature block, README and this document set |
| R3 | Impartiality constraints are too strict for a small site | Medium — adoption | Constraints act on team-versus-auditee overlap and area ownership only; a small site can widen area granularity |
| R4 | Configuration is per-company; a second company starts empty | Medium — usability | Documented in README §1.3 item 3 and the configuration guide |
| R5 | Odoo 19 API assumptions prove wrong on a specific point release | Medium | Every version-sensitive decision is documented at its call site; validation harness checks for known regressions |
| R6 | Free-text CAPA reference drifts from the real CAPA system | Medium — traceability | Documented as a bridge-module gap |

## 7. Success criteria

| # | Criterion | Verified by |
|---|---|---|
| S1 | Module installs on a clean Odoo 19 Community database | Not yet verified — requires execution |
| S2 | Module upgrades without data loss | Not yet verified — requires execution |
| S3 | Every impartiality and competence rule is enforced, not advisory | `test_audit_independence.py`, `test_audit_workflow.py` — written, not executed |
| S4 | Every model has an access rule | `test_security.test_every_model_has_an_access_rule` and the static harness |
| S5 | No model, view or data file is undeclared or unresolvable | Static harness — **PASS** |
| S6 | No dead code, no placeholder, no TODO | Static harness — **PASS** |
| S7 | Every function carries a docstring | Static harness — **PASS**, 254 of 254 |
