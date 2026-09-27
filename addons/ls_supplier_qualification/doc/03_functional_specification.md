# Phase 3 — Functional Specification

Module: `ls_supplier_qualification` · Odoo 19 Community Edition
Status at end of phase: **PASS**

---

## 3.1 Functional description

The module manages the life of a supplier inside a regulated organisation, from
the moment it is registered until it is disqualified. The central object is the
**qualification dossier**: one per supplier and per company. Everything else
hangs off it — the qualified scope, the assessments, the audits, the
performance scorecards, the periodic reviews and the signature log.

The dossier does not decide anything by itself. It computes, at all times, the
list of prerequisites that are not met, and it refuses to move forward while
that list is non-empty. The prerequisites come from the **supplier category**,
which carries the organisation's own rules: whether an assessment is required,
whether an audit is required, how long an approval lasts, how often the
supplier is audited and reviewed.

Once approved, the dossier has a hard end of validity. A daily job moves it to
Expired when that date passes and warns beforehand. Downstream, the purchase
flow reads the dossier status and either ignores it, warns about it, or refuses
to confirm the order, depending on a company setting.

## 3.2 Menus and navigation

```
Supplier Qualification
├── Qualification
│   ├── Qualification Dossiers        action_ls_supplier_qualification
│   ├── Qualified Scope               action_ls_supplier_material
│   └── Expiring Approvals            action_ls_supplier_qualification_expiring
├── Evaluation
│   ├── Assessments                   action_ls_supplier_assessment
│   ├── Audits                        action_ls_supplier_audit
│   └── Audit Findings                action_ls_supplier_audit_finding
├── Monitoring
│   ├── Performance Evaluations       action_ls_supplier_performance
│   ├── Periodic Reviews              action_ls_supplier_review
│   └── Signature Log                 action_ls_supplier_signature
└── Configuration                     (Supplier Manager only)
    ├── Supplier Categories           action_ls_supplier_category
    ├── Assessment Criteria           action_ls_supplier_criterion
    ├── Assessment Templates          action_ls_supplier_assessment_template
    └── Reference Standards           action_ls_supplier_standard
```

The root menu is visible to the Supplier Viewer group and above. Additional
entry points: a smart button on the contact form, a warning banner on the
purchase order form, and a settings section under **Settings → Supplier
Qualification**.

## 3.3 State machines

### 3.3.1 Qualification dossier

```
                        ┌─────────────────────────────┐
                        ▼                             │
  draft ──► assessment ──► audit ──► approval ──► approved ──┐
              │  ▲            │          │            │      │
              │  └────────────┘          │            ▼      │
              │                          │       conditional │
              │                          │            │      │
              └──────────────────────────┘            ▼      ▼
                                                 suspended  expired
                                                      │      │
                                                      └──┬───┘
                                                         ▼
                                                    assessment
                                                    (requalify)

  any state ──► disqualified   (terminal)
```

| Transition | Method | Guard |
|------------|--------|-------|
| draft → assessment | `action_start_assessment` | State is draft. |
| assessment, approval → audit | `action_start_audit` | — |
| assessment, audit → approval | `action_submit_for_approval` | `_get_blocking_reasons()` returns an empty list. |
| approval → approved / conditional | approval wizard → `_apply_approval` | Login match, future expiry date, conditions if conditional, segregation of duties. |
| approved, conditional → suspended | status wizard | State is approved or conditional. |
| suspended → approved / conditional | status wizard | Approval not expired. |
| any → disqualified | status wizard | Not already disqualified. |
| approved, conditional → expired | `_cron_check_expiry` | `expiry_date < today`. |
| expired, suspended → assessment | `action_requalify` | Clears the approval fields. |
| assessment, audit, approval → draft | `action_reset_to_draft` | Manager only in the UI. |

**Prerequisites checked by `_get_blocking_reasons()`**

1. If the category requires an assessment: at least one assessment in state
   Completed or Reviewed with a Pass or Conditional result.
2. If the category requires an initial audit: at least one Closed audit whose
   outcome is Acceptable or Acceptable with Actions.
3. No open critical audit finding on the dossier.
4. At least one scope line in state Qualified.

### 3.3.2 Assessment

`draft → in_progress → done → reviewed`, with `cancelled` reachable from any
state except `reviewed`, and `cancelled → draft`.

| Transition | Guard |
|------------|-------|
| draft → in_progress | At least one criterion line. |
| in_progress → done | Every criterion scored below the minimum carries a comment; a written conclusion exists. Appends an `authored` signature entry. |
| done → reviewed | The reviewer is not the assessor when segregation of duties is enabled. Appends a `reviewed` signature entry. |

### 3.3.3 Audit

`draft → planned → in_progress → report_draft → report_issued → response_received → closed`,
with `cancelled` reachable from any state except `closed`.

| Transition | Guard / effect |
|------------|----------------|
| draft → planned | Schedules an activity for the lead auditor on the planned date. |
| planned → in_progress | Sets `date_start` if empty. |
| in_progress → report_draft | Sets `date_stop` if empty. |
| report_draft → report_issued | Outcome and conclusion required. Sets `report_date` and derives `response_due_date` from `ls_audit_response_days`. Appends an `authored` signature entry and sends the report e-mail if a supplier contact has an address. |
| report_issued → response_received | Sets `response_received_date`. |
| report_issued, response_received → closed | Refused while `open_finding_count > 0`. Appends a `verified` signature entry. |

### 3.3.4 Audit finding

`open → response_received → action_agreed → implemented → verified → closed`,
with `cancelled` reachable from any state except `closed`.

Each step requires its own field: supplier response, corrective action and due
date, implementation date, verification method. Closure appends a `verified`
signature entry.

### 3.3.5 Scope line, performance evaluation, periodic review

* Scope line: `draft → qualified`, with `suspended` and `rejected`, and a return
  to `draft`. A qualified line requires a qualification date.
* Performance evaluation: `draft → confirmed`, with `cancelled` and a return to
  draft from `cancelled`.
* Periodic review: `draft → done`, with `cancelled` from draft only.
  Completing applies the decision to the dossier and appends a `reviewed`
  signature entry.

## 3.4 Approval workflow

1. The assessor submits the dossier. The prerequisites are re-checked server-side.
2. An activity is scheduled for the responsible user.
3. A Supplier Manager opens the approval wizard, which shows the latest
   assessment score, the number of open critical findings and any remaining
   blocking reason.
4. The manager chooses Approve or Approve with Conditions, sets the
   requalification interval and the end of validity, writes a justification and
   retypes their login.
5. On confirmation the module checks the login, the expiry date, the conditions
   and the segregation-of-duties rule, writes the approval onto the dossier,
   appends a signature entry, posts a chatter message and queues the
   notification e-mail.

## 3.5 Business rules

| # | Rule | Where enforced |
|---|------|----------------|
| BRU-01 | One live dossier per supplier per company. | `_check_unique_active_dossier` |
| BRU-02 | Supplier and category are frozen once the dossier leaves the assessment stage. | `write` override |
| BRU-03 | An approved dossier must carry an approval date, an approver and an end of validity. | `_check_approval_completeness` |
| BRU-04 | The end of validity is strictly after the approval date. | `_check_validity_dates` |
| BRU-05 | A conditional approval must state its conditions. | `_check_conditional_approval` |
| BRU-06 | The approver may not be an assessor or lead auditor of the dossier. | `_check_segregation_of_duties` |
| BRU-07 | Scoring rules are copied onto the assessment at creation and never re-read from the template. | `create` override |
| BRU-08 | A mandatory criterion below `mandatory_min_score` forces a Fail. | `_compute_scores` |
| BRU-09 | A score cannot exceed the frozen scale and cannot be negative. | `_check_score_range`, SQL check |
| BRU-10 | A criterion appears at most once per assessment and per template. | SQL unique |
| BRU-11 | An audit with a critical finding cannot conclude Acceptable. | `_check_outcome_consistency` |
| BRU-12 | Critical and major findings need a documented corrective action past the response stage. | `_check_corrective_action` |
| BRU-13 | An audit cannot be closed with an open finding. | `action_close` |
| BRU-14 | Two confirmed performance evaluations of a dossier cannot overlap. | `_check_no_overlap` |
| BRU-15 | Late deliveries ≤ total deliveries; rejected lots ≤ inspected lots; counters ≥ 0. | `_check_counters` |
| BRU-16 | Indicators are percentages between 0 and 100. | `_check_percentages` |
| BRU-17 | Rating thresholds decrease from A to C; at least one weight is positive. | `res.company` constraints |
| BRU-18 | Signature entries can be created but never written or deleted. | `write` / `unlink` overrides |
| BRU-19 | Deletion is refused on dossiers past draft, started assessments, planned audits, confirmed evaluations and completed reviews. | `unlink` overrides |
| BRU-20 | A scope line in Qualified requires a qualification date; its end of validity is after it. | `_check_qualification_date`, `_check_dates` |

## 3.6 Notifications and scheduled actions

| Trigger | Effect |
|---------|--------|
| Dossier submitted for approval | Activity for the responsible user. |
| Dossier approved | `mail_template_qualification_approved` to the responsible user. |
| Audit planned | Activity for the lead auditor, deadline on the planned date. |
| Audit report issued | `mail_template_audit_report_issued` to the supplier contact when it has an e-mail address. |
| Performance rating C or D | Activity on the dossier for the responsible user. |
| Review completed | Chatter message on the dossier stating the decision. |

| Scheduled action | Frequency | Behaviour |
|------------------|-----------|-----------|
| `cron_ls_supplier_qualification_expiry` | Daily | Moves elapsed approvals to Expired with a chatter message and a requalification activity. For approvals expiring within `ls_expiry_reminder_days`, schedules one non-duplicated activity and queues `mail_template_qualification_expiring`. |
| `cron_ls_supplier_due_dates` | Daily | Schedules non-duplicated activities for audits and reviews falling due within the reminder lead time. |
| `cron_ls_supplier_material_expiry` | Daily | Suspends qualified scope lines whose own validity has elapsed, recording the reason. |

## 3.7 Reports

| Report | Model | Content |
|--------|-------|---------|
| Supplier Qualification Dossier | `ls.supplier.qualification` | Supplier block, category, criticality, risk level, status, approval block, qualified scope, assessments, audits, performance evaluations, periodic reviews, signature log with truncated hashes, and a footer stating that the document is not a certificate of compliance. |
| Supplier Assessment Report | `ls.supplier.assessment` | Subject, frozen scoring rules, every scored criterion with weight, mandatory flag, score, evidence and comment, the result block and the written conclusion. |
| Supplier Audit Report | `ls.supplier.audit` | Supplier and contact, audit metadata, team, framework basis, scope, findings table, severity summary, outcome and conclusion. |

## 3.8 Dashboards, KPIs and analysis views

Odoo Community provides graph and pivot views; both are used. No Enterprise
dashboard component is referenced.

| KPI | Where |
|-----|-------|
| Dossiers by category and status | Qualification graph and pivot views. |
| Mean assessment score by supplier | Assessment graph; assessment pivot by supplier and type. |
| Overall performance score by supplier and year | Performance graph and pivot, with on-time delivery and quality acceptance as additional measures. |
| Open critical and major findings | Field on the dossier list and kanban, filter in the search view. |
| Risk level distribution | Group-by on the dossier search view. |
| Approvals expiring | Dedicated menu entry and `Expiring Soon` filter. |
| Audits with open findings | `With Open Findings` filter on the audit search view. |

**Risk level rule.** The risk level is a deterministic score defined by this
module, not derived from any regulatory text: criticality contributes 2 for
critical and 1 for major; a Fail assessment contributes 3 and a Conditional
one 1; a D performance rating contributes 3 and a C rating 1; each open
critical finding contributes 3 and each open major finding 1. A total of 4 or
more is High, 2 or 3 is Medium, below 2 is Low.

## 3.9 Search views, filters and group-by

| Model | Filters | Group by |
|-------|---------|----------|
| Qualification | My Dossiers, Approved, In Qualification, Pending Approval, Not Approved, Expiring Soon, High Risk, Open Critical Findings, Audit Due, Review Due, Archived | Status, Category, Criticality, Risk Level, Responsible, Validity End |
| Scope | Qualified, Under Qualification, Suspended, Expires Within 90 Days | Supplier, Material Type, Status |
| Assessment | My Assessments, Draft, In Progress, To Review, Failed, This Year | Supplier, Type, Result, Status, Assessor, Date |
| Audit | My Audits, Planned, Not Closed, With Open Findings, Not Acceptable | Supplier, Type, Outcome, Status, Planned Date |
| Finding | Not Closed, Critical, Major, Overdue Action | Supplier, Severity, Status |
| Performance | Confirmed, Action Required, Rating C or D | Supplier, Rating, Period End |
| Review | Draft, Completed, Adverse Decision | Supplier, Decision, Review Date |
| Signature | — | Signer, Meaning, Signed Model, Signature Date |
| Category | Critical, Major, Minor, Audit Required, Archived | Criticality |
| Criterion | Mandatory, Archived | Domain, Mandatory |
| Contact | Approved Supplier | — |

## 3.10 Actions and wizards

| Wizard | Purpose | Inputs |
|--------|---------|--------|
| `ls.supplier.approve.wizard` | Approve or conditionally approve a dossier. | Decision, requalification interval, end of validity, conditions, justification, login confirmation. |
| `ls.supplier.status.wizard` | Suspend, reinstate or disqualify. | Action, justification, login confirmation. |

| Server action | Purpose |
|---------------|---------|
| `action_ls_supplier_signature_verify` | Recomputes the SHA-256 chain of the active company and returns a success or failure notification listing the broken sequence numbers. |

Object buttons are documented per model in `doc/11_api_documentation.md`.

---

**Phase 3 gate: PASS.** No open issue. Phase 4 may start.
