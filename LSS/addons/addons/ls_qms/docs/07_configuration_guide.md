# 07 — Configuration Guide

## 1. System parameters

Settings, Technical, System Parameters, or the menu Quality Management,
Configuration, System Parameters, which is filtered on the `ls_qms.` prefix.

| Key | Default | Effect | Behaviour if the value is invalid |
|---|---|---|---|
| `ls_qms.default_review_period_months` | 24 | Review period proposed on a new document | Falls back to 24 if absent, not a number, or negative |
| `ls_qms.review_reminder_lead_days` | 30 | Number of days before the review date at which the reminder is raised | Falls back to 30 under the same conditions |
| `ls_qms.enforce_segregation_of_duties` | True | Forbids the author to approve their own document | Falls back to True under the same conditions |
| `ls_qms.default_retention_period_months` | 60 | Retention period proposed on a new quality record | Falls back to 60 under the same conditions |

The defaults are the values shipped in `data/ir_config_parameter_data.xml`.
Setting `ls_qms.enforce_segregation_of_duties` to `False` removes a control
that most quality frameworks expect. Record the decision and its justification
before doing so.

## 2. Assigning the roles

Settings, Users and Companies, Users, tab Access Rights, privilege **Quality
Management**. Assign one group per user. The groups are cumulative through
`implied_ids`, so assigning Manager also grants Approver, User and Viewer.

| Population | Group |
|---|---|
| Production and laboratory operators | Viewer |
| Quality assurance officers, document authors | User |
| Heads of department, approvers | Approver |
| Quality assurance manager | Manager |

## 3. Sequences

Settings, Technical, Sequences.

| Code | Prefix | Padding |
|---|---|---|
| `ls.qms.policy` | POL- | 4 |
| `ls.qms.sop` | SOP- | 4 |
| `ls.qms.work_instruction` | WI- | 4 |
| `ls.qms.quality_plan` | QPL- | 4 |
| `ls.qms.objective` | OBJ- | 4 |
| `ls.qms.quality_record` | QR- | 5 |

Changing a prefix affects new records only. Existing references are never
regenerated. Sequences are created with `company_id` unset, so they are
shared by every company. To number per company, create a company specific
sequence with the same code, which is the standard Odoo behaviour.

## 4. Departments

Departments come from the `hr` module. Create them under Employees,
Configuration, Departments before assigning them to documents.

## 5. Scheduled actions

Settings, Technical, Scheduled Actions.

| Action | Default interval |
|---|---|
| Life Sciences QMS: Document Review Reminder | 1 day |
| Life Sciences QMS: Objective Monitoring | 1 week |
| Life Sciences QMS: Record Retention Review | 1 month |

All three are idempotent: a second run within the same window does not
duplicate an activity.
