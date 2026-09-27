# Administrator Manual — `ls_environmental_monitoring`

## 1. Roles and access

Three roles are defined. **They do not imply one another**, so assign each user
the single role they need. The reason is recorded in `doc/deviations.md`
section B2: the Odoo 19 field name for implied groups could not be verified, so
each role carries its own complete set of access rules.

| Model | Viewer | Technician | Manager |
|---|---|---|---|
| Grades, areas, parameters, methods | read | read | full |
| Sampling points, limits, plans, plan lines | read | read | full |
| Samples, results | read | read, write, create | full |
| Excursions | read | read | full |
| Trend analyses and lines | read | read | full |
| Sample generation wizard | — | full | full |
| Sample cancellation wizard | — | full | full |
| Trend, excursion closure and amendment wizards | — | — | full |

Technicians cannot delete samples. Deletion of a draft sample is a manager
action; anything beyond draft is cancelled rather than deleted, by anyone.

### Restrictions enforced in code, not by access rules

An access rule applies to a whole model and cannot restrict an individual state
transition. The following are enforced in Python:

| Restriction | Enforced in |
|---|---|
| Review and approval require the manager role | `ls.env.sample._check_manager_role` |
| A sample is reviewed by someone other than the results author | `ls.env.sample.action_review` |
| A sample is approved by someone other than the results author | `ls.env.sample.action_approve` |
| A limit is approved by someone other than its author | `ls.env.limit.action_approve` |
| A plan is approved by someone other than its author | `ls.env.plan.action_approve` |
| An excursion is closed by someone other than its owner | `ls.env.excursion.close` |

**Consequence for staffing:** the workflow cannot complete with a single user.
At least one technician and one manager are required.

### Menu visibility

Menus carry no group restriction; visibility follows the access rules. A viewer
sees every menu, because a viewer can read every model. Attempting an action
they lack rights for produces an access error rather than a hidden button. The
reason is in `doc/deviations.md` section B4.

---

## 2. Scheduled jobs

**Settings → Technical → Scheduled Actions**

| Job | Frequency | Effect |
|---|---|---|
| Generate Scheduled Samples | Daily | Creates samples due today or earlier under every approved plan |
| Notify Overdue Samples | Daily | Posts a message on each sample past its scheduled date and not collected |

Both are **idempotent**. Running either twice has no additional effect: sample
generation skips dates already generated, and the notification posts an additive
message.

A single generation run creates at most 5000 samples
(`constants.MAX_SAMPLES_PER_SCHEDULING_RUN`). This caps the damage from a
mistaken date on a plan line. If a run hits the cap, the next run continues from
where it stopped.

Deactivate the generation job if your procedure requires samples to be raised
manually.

Only `name`, `model_id`, `state`, `code`, `interval_number`, `interval_type` and
`active` are set on these records; fields whose behaviour in Odoo 19 could not be
verified are left at their defaults. See `doc/deviations.md` section B6.

---

## 3. Multi-company

Every substantive model carries `company_id`, and thirteen **global** record
rules restrict visibility to the user's active companies.

Cross-company references are rejected by constraints: an area cannot sit inside
a parent area of another company, a sampling point must belong to an area of its
own company, and a limit must reference a sampling point and parameter of its
own company.

Both sequences are created without a company, so the sample and excursion
reference series are shared across companies. If you need a separate series per
company, create company-specific `ir.sequence` records with the codes
`ls.env.sample` and `ls.env.excursion`.

---

## 4. Data retention

The following cannot be deleted through the interface:

| Record | Rule |
|---|---|
| Excursion | Never deletable; cancel instead |
| Sample | Deletable only while draft; cancel instead |
| Result | Removable only while its sample awaits collection |
| Limit | Deletable only while draft; supersede instead |
| Plan | Not deletable once approved |

**Uninstalling the module deletes every record it owns.** In a regulated
environment these are retained records. Export or archive before uninstalling
and follow your change control procedure.

---

## 5. Performance notes

Indexes are declared on the fields used for filtering and grouping:
`company_id` on every model, plus `state`, `scheduled_date`, `sampling_point_id`,
`area_id`, `parameter_id`, `evaluation`, `is_breach` and `collection_datetime`
where relevant.

Aggregate counts use `_read_group` rather than per-record searches, so a list of
areas or sampling points issues one query for its counts rather than one per row.

`is_overdue` is computed rather than stored, because it depends on the current
date. A search method translates a filter on it into a domain over the stored
`state` and `scheduled_date` fields, so filtering remains efficient.

**No performance testing has been carried out.** See `doc/test_report.md`.

---

## 6. Troubleshooting

**Installation fails with a view parsing error mentioning `chatter`.**
The `<chatter/>` element form could not be verified for Odoo 19. Remove the
seven occurrences under `views/` and reinstall. Field tracking is unaffected;
only the inline message log is lost. See `doc/deviations.md` section B7.

**Installation fails with an error about a required field on `res.groups`.**
The group-to-privilege link was omitted deliberately. If Odoo 19 requires it,
add a `res.groups.privilege` record and reference it from each group. See
`doc/deviations.md` section B1.

**A translation call raises an AttributeError.**
`self.env._()` was used as the suite convention and not re-verified. Replace with
`from odoo import _` and `_(...)`. See `doc/deviations.md` section B8.

**Sample generation produces nothing.**
Check that the plan is **approved** — a draft plan generates nothing — that its
lines have a start date in the past, and that the generation date reaches the
next due date.

**Many results show "No Approved Limit".**
Limits exist in draft but were never approved, or none covers the occupancy
state recorded on the sample. Use **Sampling Points → Without Approved Limits**.

**A manager cannot approve a sample.**
They entered the results. Approval requires a different user.
