# ls_capa — API Reference

**Generated from source.** This document is produced by parsing the
module's Python sources with `ast`, so field lists and signatures
cannot drift from the code. Regenerate with `docs/gen_api_reference.py`.

Odoo target: 19.0 Community. Module version: 19.0.1.0.1.

---

## `ls.capa.action`

*Class* `LsCapaAction` — `models/capa_action.py`

A single corrective or preventive action within a CAPA.

- `_description` = 'CAPA Action'
- `_inherit` = [...]
- `_order` = 'issue_id, sequence, date_planned, id'

### Fields

| Field | Type | Key attributes |
|---|---|---|
| `name` | Char | required=True, readonly=True, default=lambda, index=True |
| `issue_id` | Many2one | comodel_name='ls.capa.issue', required=True, index=True |
| `root_cause_id` | Many2one | comodel_name='ls.capa.root_cause' |
| `sequence` | Integer | default=10 |
| `action_type` | Selection | required=True, tracking=True, default='corrective' |
| `description` | Text | required=True |
| `responsible_id` | Many2one | comodel_name='res.users', required=True, tracking=True, default=lambda |
| `date_planned` | Date | required=True, tracking=True |
| `date_done` | Date | readonly=True, tracking=True |
| `completion_evidence` | Text | — |
| `state` | Selection | required=True, tracking=True, default='draft', index=True |
| `cancellation_reason` | Text | — |
| `task_id` | Many2one | comodel_name='project.task', readonly=True |
| `company_id` | Many2one | comodel_name='res.company', store=True, related='issue_id.company_id', index=True |
| `is_late` | Boolean | compute='_compute_is_late' |

### Public methods

- **`create(self, vals_list)`** `@api.model_create_multi`
  Allocate the action reference from the sequence.
- **`action_start(self)`** 
  Move a draft action to In Progress.
- **`action_done(self)`** 
  Mark an action as completed and stamp the completion date.
- **`action_cancel(self)`** 
  Cancel an action that is no longer applicable.
- **`action_reset_to_draft(self)`** 
  Return a cancelled action to draft.
- **`action_create_task(self)`** 
  Create a ``project.task`` mirroring this action.

### Internal methods

- `_compute_is_late(self)` `@api.depends('date_planned', 'state')`
  Flag actions that passed their planned date while still open.
- `_search_is_late(self, operator, value)` 
  Allow searching on the non-stored late flag.
- `_check_root_cause_issue(self)` `@api.constrains('root_cause_id', 'issue_id')`
  Ensure a linked root cause belongs to the same CAPA.
- `_check_cancellation_reason(self)` `@api.constrains('state', 'cancellation_reason')`
  Require a justification when an action is cancelled.

---

## `ls.capa.category`

*Class* `LsCapaCategory` — `models/capa_category.py`

Classification scheme applied to CAPA records.

- `_description` = 'CAPA Category'
- `_order` = 'sequence, name'

### Fields

| Field | Type | Key attributes |
|---|---|---|
| `name` | Char | required=True |
| `code` | Char | required=True |
| `sequence` | Integer | default=10 |
| `description` | Text | — |
| `default_due_days` | Integer | default=30 |
| `active` | Boolean | default=True |
| `company_id` | Many2one | comodel_name='res.company', required=True, default=lambda |
| `issue_ids` | One2many | comodel_name='ls.capa.issue' |
| `issue_count` | Integer | compute='_compute_issue_count' |

### Public methods

- **`action_view_issues(self)`** 
  Open the CAPA records classified under this category.

### Internal methods

- `_compute_issue_count(self)` `@api.depends('issue_ids')`
  Count CAPA records linked to each category.
- `_check_code(self)` `@api.constrains('code')`
  Reject blank or whitespace-only category codes.

---

## `ls.capa.effectiveness`

*Class* `LsCapaEffectiveness` — `models/capa_effectiveness.py`

An effectiveness check verifying that a CAPA prevented recurrence.

- `_description` = 'CAPA Effectiveness Check'
- `_inherit` = [...]
- `_order` = 'issue_id, date_planned, id'

### Fields

| Field | Type | Key attributes |
|---|---|---|
| `name` | Char | required=True, readonly=True, default=lambda, index=True |
| `issue_id` | Many2one | comodel_name='ls.capa.issue', required=True, index=True |
| `method` | Selection | required=True, tracking=True, default='data_review' |
| `criteria` | Text | required=True |
| `date_planned` | Date | required=True, tracking=True |
| `date_check` | Date | readonly=True, tracking=True |
| `verifier_id` | Many2one | comodel_name='res.users', required=True, tracking=True, default=lambda |
| `result` | Selection | required=True, tracking=True, default='pending', index=True |
| `conclusion` | Text | — |
| `state` | Selection | required=True, tracking=True, default='draft' |
| `new_capa_id` | Many2one | comodel_name='ls.capa.issue', readonly=True |
| `company_id` | Many2one | comodel_name='res.company', store=True, related='issue_id.company_id', index=True |

### Public methods

- **`create(self, vals_list)`** `@api.model_create_multi`
  Allocate the effectiveness check reference from the sequence.
- **`action_plan(self)`** 
  Move a draft check to Planned.
- **`action_mark_effective(self)`** 
  Conclude the check as Effective.
- **`action_mark_not_effective(self)`** 
  Conclude the check as Not Effective.
- **`action_create_followup_capa(self)`** 
  Raise a follow-up CAPA after an ineffective verification.

### Internal methods

- `_check_conclusion(self)` `@api.constrains('state', 'result', 'conclusion')`
  Require a conclusion and a decided result on completed checks.
- `_check_date_planned(self)` `@api.constrains('date_planned', 'issue_id')`
  Ensure verification is not scheduled before identification.
- `_conclude(self, result)` 
  Complete the check with the supplied result.

---

## `ls.capa.issue`

*Class* `LsCapaIssue` — `models/capa_issue.py`

A Corrective And Preventive Action record.

- `_description` = 'CAPA Record'
- `_inherit` = [...]
- `_order` = 'date_identified desc, id desc'
- `_rec_name` = 'name'

### Fields

| Field | Type | Key attributes |
|---|---|---|
| `name` | Char | required=True, readonly=True, default=lambda, index=True |
| `title` | Char | required=True, tracking=True |
| `description` | Text | required=True |
| `source` | Selection | required=True, tracking=True |
| `source_reference` | Char | — |
| `capa_type` | Selection | required=True, tracking=True, default='corrective' |
| `severity` | Selection | required=True, tracking=True, default='minor' |
| `priority` | Selection | tracking=True, default='1' |
| `category_id` | Many2one | comodel_name='ls.capa.category', tracking=True |
| `date_identified` | Date | required=True, tracking=True, default=fields.Date.context_today |
| `date_due` | Date | readonly=False, store=True, compute='_compute_date_due', tracking=True |
| `date_closed` | Datetime | readonly=True, tracking=True |
| `identified_by_id` | Many2one | comodel_name='res.users', required=True, tracking=True, default=lambda |
| `owner_id` | Many2one | comodel_name='res.users', required=True, tracking=True, default=lambda |
| `closed_by_id` | Many2one | comodel_name='res.users', readonly=True |
| `company_id` | Many2one | comodel_name='res.company', required=True, default=lambda, index=True |
| `active` | Boolean | default=True |
| `state` | Selection | required=True, tracking=True, default='identified', index=True |
| `immediate_action` | Text | — |
| `impact_assessment` | Text | — |
| `quality_impact` | Boolean | tracking=True |
| `regulatory_impact` | Boolean | tracking=True |
| `safety_impact` | Boolean | tracking=True |
| `closure_summary` | Text | — |
| `root_cause_ids` | One2many | comodel_name='ls.capa.root_cause' |
| `action_ids` | One2many | comodel_name='ls.capa.action' |
| `effectiveness_ids` | One2many | comodel_name='ls.capa.effectiveness' |
| `root_cause_count` | Integer | compute='_compute_relation_counts' |
| `action_count` | Integer | compute='_compute_relation_counts' |
| `action_done_count` | Integer | compute='_compute_relation_counts' |
| `effectiveness_count` | Integer | compute='_compute_relation_counts' |
| `progress` | Float | store=True, compute='_compute_progress' |
| `is_overdue` | Boolean | compute='_compute_is_overdue' |
| `days_to_due` | Integer | compute='_compute_is_overdue' |

### Public methods

- **`create(self, vals_list)`** `@api.model_create_multi`
  Allocate the CAPA reference from the sequence on creation.
- **`copy_data(self, default)`** 
  Reset the reference so duplicates receive their own sequence value.
- **`unlink(self)`** 
  Prevent deletion of CAPA records that left the Identified state.
- **`action_assess(self)`** 
  Move from Identified to Assessed.
- **`action_start_investigation(self)`** 
  Move from Assessed to Investigation.
- **`action_start_action_planning(self)`** 
  Move from Investigation to Action Planning.
- **`action_start_progress(self)`** 
  Move from Action Planning to In Progress.
- **`action_complete(self)`** 
  Move from In Progress to Completed.
- **`action_verify(self)`** 
  Move from Completed to Verified.
- **`action_open_close_wizard(self)`** 
  Open the closure wizard used to capture the closure summary.
- **`action_close(self)`** 
  Move from Verified to Closed.
- **`action_view_root_causes(self)`** 
  Open the root cause analyses of this CAPA.
- **`action_view_actions(self)`** 
  Open the actions of this CAPA.
- **`action_view_effectiveness(self)`** 
  Open the effectiveness checks of this CAPA.

### Internal methods

- `_compute_date_due(self)` `@api.depends('date_identified', 'category_id', 'category_id.default_due_days')`
  Propose a due date from the identification date and category.
- `_compute_relation_counts(self)` `@api.depends('root_cause_ids', 'action_ids', 'action_ids.state', 'effectiveness_ids')`
  Compute the counts displayed in the form view smart buttons.
- `_compute_progress(self)` `@api.depends('action_ids', 'action_ids.state')`
  Compute completion progress over non-cancelled actions.
- `_compute_is_overdue(self)` `@api.depends('date_due', 'state')`
  Flag CAPA records whose due date has passed before closure.
- `_search_is_overdue(self, operator, value)` 
  Allow searching and filtering on the non-stored overdue flag.
- `_check_dates(self)` `@api.constrains('date_identified', 'date_due')`
  Ensure the due date is not earlier than the identification date.
- `_check_closure_summary(self)` `@api.constrains('state', 'closure_summary')`
  Require a closure summary on closed records.
- `_set_state(self, new_state)` 
  Write the new state and post a tracked note in the chatter.
- `_check_transition(self, expected_states)` 
  Verify every record is in one of the states allowed for a step.
- `_action_open_related(self, model, name, context)` 
  Build a window action listing records related to this CAPA.
- `_cron_notify_overdue(self)` `@api.model`
  Post a chatter reminder on every overdue open CAPA record.

---

## `ls.capa.root_cause`

*Class* `LsCapaRootCause` — `models/capa_root_cause.py`

A root cause analysis performed within a CAPA investigation.

- `_description` = 'CAPA Root Cause Analysis'
- `_inherit` = [...]
- `_order` = 'issue_id, sequence, id'

### Fields

| Field | Type | Key attributes |
|---|---|---|
| `name` | Char | required=True, readonly=True, default=lambda, index=True |
| `issue_id` | Many2one | comodel_name='ls.capa.issue', required=True, index=True |
| `sequence` | Integer | default=10 |
| `method` | Selection | required=True, tracking=True, default='five_whys' |
| `description` | Text | required=True |
| `is_primary` | Boolean | tracking=True |
| `analyst_id` | Many2one | comodel_name='res.users', required=True, tracking=True, default=lambda |
| `date_analysis` | Date | required=True, tracking=True, default=fields.Date.context_today |
| `state` | Selection | required=True, tracking=True, default='draft' |
| `company_id` | Many2one | comodel_name='res.company', store=True, related='issue_id.company_id', index=True |
| `why_1` | Char | — |
| `why_2` | Char | — |
| `why_3` | Char | — |
| `why_4` | Char | — |
| `why_5` | Char | — |
| `ishikawa_category` | Selection | — |
| `fmea_severity` | Integer | — |
| `fmea_occurrence` | Integer | — |
| `fmea_detection` | Integer | — |
| `fmea_rpn` | Integer | store=True, compute='_compute_fmea_rpn' |
| `action_ids` | One2many | comodel_name='ls.capa.action' |

### Public methods

- **`create(self, vals_list)`** `@api.model_create_multi`
  Allocate the root cause reference from the sequence.
- **`action_confirm(self)`** 
  Confirm the analysis so it can gate the Action Planning step.
- **`action_reset_to_draft(self)`** 
  Return a confirmed analysis to draft for further investigation.

### Internal methods

- `_compute_fmea_rpn(self)` `@api.depends('fmea_severity', 'fmea_occurrence', 'fmea_detection')`
  Compute the Risk Priority Number for FMEA analyses.
- `_check_fmea_ratings(self)` `@api.constrains('method', 'fmea_severity', 'fmea_occurrence', 'fmea_detection')`
  Restrict FMEA ratings to the documented 1 to 10 scale.
- `_check_five_whys(self)` `@api.constrains('method', 'why_1')`
  Require the first Why on Five Whys analyses.
- `_check_ishikawa(self)` `@api.constrains('method', 'ishikawa_category')`
  Require a diagram category on Ishikawa analyses.

---

## `ls.capa.close.wizard`

*Class* `LsCapaCloseWizard` — `wizards/capa_close_wizard.py`

Collect the closure summary and close the CAPA in one step.

- `_description` = 'CAPA Closure Wizard'

### Fields

| Field | Type | Key attributes |
|---|---|---|
| `issue_id` | Many2one | comodel_name='ls.capa.issue', required=True, readonly=True |
| `issue_reference` | Char | readonly=True, related='issue_id.name' |
| `action_count` | Integer | readonly=True, related='issue_id.action_count' |
| `effectiveness_count` | Integer | readonly=True, related='issue_id.effectiveness_count' |
| `closure_summary` | Text | required=True |

### Public methods

- **`default_get(self, fields_list)`** `@api.model`
  Pre-fill the wizard from the CAPA in context.
- **`action_confirm_close(self)`** 
  Write the summary onto the CAPA and close it.

---

