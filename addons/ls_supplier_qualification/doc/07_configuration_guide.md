# Configuration Guide

Module: `ls_supplier_qualification` · Odoo 19 Community Edition
Audience: Quality Manager, Application Administrator

---

## 1. Before you configure

The module ships a working starter configuration: 10 supplier categories,
32 assessment criteria, 2 questionnaires and 13 framework designations.

**Those values are proposals made by this module. They are not derived from any
regulation.** Criticality levels, requalification intervals, audit
periodicities, weights and thresholds must be reviewed and approved by your
quality department before first use, through your own change-control process.
Configure on a test database first, and record the approved values in a
controlled document.

## 2. Configuration order

Work in this order; each step depends on the previous one.

1. Company settings
2. Reference standards
3. Assessment criteria
4. Assessment templates
5. Supplier categories
6. User groups

## 3. Company settings

**Settings → Supplier Qualification.** These values apply to the active
company; set them for each company in a multi-company database.

### Governance

| Setting | Default | Meaning |
|---------|---------|---------|
| Enforce Segregation of Duties | Enabled | The approver of a dossier cannot be an assessor or lead auditor of that dossier, and an assessment cannot be reviewed by its own assessor. |
| Expiry Reminder (days) | 60 | How far ahead the daily jobs raise reminders for expiring approvals and for audits and reviews falling due. |
| Audit Response Lead Time (days) | 30 | Default number of days granted to a supplier to answer an issued audit report. Overridable per audit. |

Disabling segregation of duties is a documented decision. It stays visible in
the signature log, because the approver is recorded on every approval.

### Purchase control

| Setting | Default | Meaning |
|---------|---------|---------|
| Purchase Order Control | Warn | *No control* ignores qualification. *Warn* posts the issue in the order chatter and lets the order through. *Block* refuses the confirmation. |
| Check Qualified Scope | Disabled | When enabled, the control also verifies that every ordered product belongs to the supplier's qualified scope. |

Start at *Warn*. Move to *Block* only once your supplier base is qualified,
otherwise procurement stops on day one. Enable the scope check only when your
scope lines are linked to catalogue products; a scope line without a product
cannot be matched against an order line.

### Performance scorecard

| Setting | Default |
|---------|---------|
| Weight — On-Time Delivery | 30 |
| Weight — Quality Acceptance | 40 |
| Weight — Documentation | 15 |
| Weight — Responsiveness | 15 |
| Rating A Threshold | 90 |
| Rating B Threshold | 75 |
| Rating C Threshold | 60 |

Weights are relative; they do not have to sum to 100, but they are easier to
reason about when they do. Thresholds must decrease from A to C; the system
refuses any other ordering. Below the C threshold the rating is D.

Changing these values affects **new** evaluations only. Existing evaluations
keep the weights and thresholds frozen on them at creation.

## 4. Reference standards

**Configuration → Reference Standards.** Each record carries a designation, a
short code and an issuing body.

The module stores the designation only. It does not contain, reproduce or
interpret the text of any standard; that text remains the property of the
issuing body and must be obtained from it. The *Internal Scope Note* field is
yours: use it to record why your organisation applies a framework to its
suppliers.

Add your own entries for national requirements or customer-specific standards.

## 5. Assessment criteria

**Configuration → Assessment Criteria.**

| Field | Guidance |
|-------|----------|
| Criterion | The question, in your own words. Keep it answerable by observation or by a document. |
| Code | Short, stable, used in reports. The starter set uses `DOMAIN-nn`. |
| Domain | One of twelve areas. Drives grouping in lists and in the assessment report. |
| Default Weight | Relative importance. The starter set uses 1 for informational, 2 for important, 3 for essential. |
| Mandatory by Default | A mandatory criterion scored below the template minimum forces a Fail, whatever the total. Use sparingly. |
| Related Frameworks | Your own association between this question and a framework. A traceability aid, not a statement about that framework's content. |
| Internal Reference | Your procedure or clause mapping. Free text. |
| Assessor Guidance | What evidence to look for and how to score. Shown to the assessor. |

Do not delete a criterion that has been used: archive it instead. Deleting
breaks nothing in past assessments, because the lines carry their own weight
and score, but it removes the wording from the report.

## 6. Assessment templates

**Configuration → Assessment Templates.** A template is a questionnaire plus a
scoring rule.

| Field | Guidance |
|-------|----------|
| Maximum score per criterion | The scale. Default 5, meaning each criterion is scored 0 to 5. |
| Minimum score for mandatory criteria | Below this, a mandatory criterion forces a Fail. Default 3. |
| Pass threshold | Weighted percentage at or above which the result is Pass. Default 80. |
| Conditional threshold | Weighted percentage at or above which the result is Conditional. Below it, Fail. Default 60. |
| Intended Supplier Categories | Informative. Any template can be used on any assessment. |
| Criteria | The questions, each with a weight and a mandatory flag that override the criterion defaults. |

**How the result is computed.** Each line contributes `score × weight`. The
percentage is the sum of those, divided by the sum of `maximum score × weight`.
Then: any mandatory criterion below the minimum → Fail; otherwise percentage at
or above the pass threshold → Pass; at or above the conditional threshold →
Conditional; below → Fail.

*Worked example, using the shipped short template.* Twelve criteria, weights
summing to 24, scale 0–5, so the maximum weighted score is 120. A supplier
scoring an average of 4 across the board reaches 96, that is 80 %, which is
above the 75 % pass threshold of that template — Pass. If one mandatory
criterion is scored 2, the result becomes Fail regardless of the 80 %.

These rules are copied onto each assessment when it is created. Editing a
template never changes a past result.

## 7. Supplier categories

**Configuration → Supplier Categories.** The category carries your
qualification rules.

| Field | Effect |
|-------|--------|
| Criticality | Proposed onto each dossier; contributes to the risk level. |
| Requires Assessment | A completed assessment with a Pass or Conditional result becomes a prerequisite for approval. |
| Requires Initial Audit | A closed audit with an acceptable outcome becomes a prerequisite for approval. |
| Requires Periodic Audit | Drives the *Next Audit Date* on approved dossiers. |
| Audit Interval (months) | Months between two periodic audits. |
| Requalification Interval (months) | Proposed validity of an approval. |
| Review Interval (months) | Months between two periodic reviews. |
| Applicable Frameworks | Which frameworks you apply to suppliers of this category. |

Changing a category affects the prerequisites evaluated from that moment on.
It does not retroactively invalidate an existing approval.

## 8. User groups

**Settings → Users & Companies → Users.**

| Group | Give it to |
|-------|-----------|
| Supplier Viewer | Anyone who must consult qualification status: buyers, warehouse, regulatory affairs. |
| Supplier Assessor | People who conduct assessments and audits and record performance. |
| Supplier Manager | Quality managers who approve, suspend, disqualify and configure. |

The groups are cumulative: Manager implies Assessor implies Viewer. Assign one
group per person, the highest they need.

No group is granted automatically to new users. That is deliberate: access to
qualification data should follow a decision, not a default.

## 9. Scheduled actions

**Settings → Technical → Scheduled Actions.** Three daily actions, active on
installation.

| Action | What it does |
|--------|--------------|
| Check approval validity | Expires elapsed approvals; warns about approvals expiring within the reminder lead time. |
| Check audit and review due dates | Raises activities for audits and reviews falling due. |
| Check qualified scope validity | Suspends scope lines whose own validity has elapsed. |

Keep them daily. They are idempotent: running them twice creates no duplicate
activity and performs no second state change.

## 10. Configuration checklist

Sign this off before go-live.

- [ ] Company governance settings reviewed and approved
- [ ] Purchase control level chosen, with a documented go-live plan
- [ ] Performance weights and thresholds approved by the quality department
- [ ] Reference standards list matches the frameworks you actually apply
- [ ] Criteria reviewed, reworded where needed, mandatory flags agreed
- [ ] Templates reviewed; scale and thresholds approved
- [ ] Categories reviewed; intervals and audit requirements approved
- [ ] Users assigned to groups; segregation-of-duties decision recorded
- [ ] Scheduled actions confirmed active
- [ ] Configuration recorded in a controlled document under your change control
