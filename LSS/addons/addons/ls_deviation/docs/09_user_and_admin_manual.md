# 09 — User, Administrator and Developer Manual

## Part A — User manual

### A.1 Recording a deviation

Quality Management → Deviations → All Deviations → New.

Mandatory at creation: title, description, deviation type, category,
occurrence date, detection date. The reference is generated on save.

There is **no draft state**. The record exists from the moment it is saved,
and every subsequent edit is tracked in the chatter. This is deliberate: a
draft state would allow a deviation to sit unreported.

Record the description as a factual account — what happened, where, when, how
it was detected. Conclusions belong in the investigation, not here.

If the deviation was authorised in advance, tick **Planned Deviation**. The
justification then becomes mandatory and must be present before saving.

### A.2 Immediate actions

On the Immediate Actions tab, add containment or correction actions with a
responsible person and a deadline. An action cannot be marked Done without
completion evidence. Open actions block closure of the deviation.

### A.3 Assessment

Set the severity. This proposes a target closure date from the configured
interval.

- **Critical** — has or may have an impact on patient safety, product efficacy or regulatory commitments
- **Major** — affects product quality without direct patient safety impact
- **Minor** — no impact on product quality

On the Impact Assessment tab, set the applicable impact flags and write the
rationale supporting them. Assign an investigator.

Press **Complete Assessment**. This is refused without severity, an impact
narrative and an assigned investigator, and it stamps who assessed and when.

### A.4 Investigation

On the Investigation tab, add an investigation record and choose a root cause
analysis method. Press **Start Investigation** on the deviation.

Open the investigation, record findings and root cause, then Start and
Complete it. Completion is refused without both findings and a root cause.

Where no definitive root cause can be established, clear **Root Cause
Determined** and record the most probable cause together with the rationale
for that conclusion in the root cause field.

### A.5 Extension to other batches

Still on the Investigation tab, complete the section headed *Extension to
Other Batches (21 CFR 211.192)*.

List the other lots evaluated, and record the rationale for the scope of the
extension. **The rationale is mandatory even if the conclusion is that no
extension was necessary** — record that determination and why. The deviation
cannot leave the investigation stage without it.

### A.6 Disposition

Where the deviation was assessed as having an impact, at least one product
disposition is required. On the Disposition tab, add a disposition with the
product, lot, quantity, decision and justification.

Available decisions: Use As Is, Rework, Reprocess, Quarantine, Reject,
Destroy, Return to Supplier. A Use As Is decision requires a rationale
demonstrating that quality, safety and efficacy are not adversely affected.

A Deviation Manager approves or rejects it. The proposer cannot approve their
own disposition.

Recording a disposition does **not** move stock. Executing the scrap, rework
or return is a separate inventory transaction.

Press **Proceed to Disposition** on the deviation.

### A.7 CAPA decision and closure

If corrective or preventive action beyond the immediate actions is needed,
press **Require CAPA** and record the rationale.

Press **Close Deviation**. The wizard requires conclusions, follow-up and a
CAPA decision rationale, and a CAPA reference where a CAPA is required. Where
no follow-up is required, record that determination and its rationale rather
than leaving the field empty.

Closure is refused while any immediate action is open or any disposition is
unapproved.

### A.8 Send back, cancel, extend

**Send Back** returns the deviation one step for rework. The reason is
mandatory and is written to the transition log.

**Cancel** voids a deviation raised in error. The record is retained with its
reference; it is never deleted.

**Extend Target Date** is the only way to change a target closure date. The
new date must be later than the current one and the justification is posted to
the chatter.

### A.9 Reporting

Print → Deviation Report produces the complete record including the transition
log. Reporting → Deviation Analysis provides pivot and graph views.

---

## Part B — Administrator manual

### B.1 Roles

| Group | Can |
|---|---|
| Viewer | Read all deviations in their companies |
| Reporter | Create; edit own records while Reported |
| Investigator | Edit any open record; investigate; propose dispositions |
| Manager | Approve/reject dispositions; close; cancel; edit closed records; configure |

Groups are hierarchical; assign only the highest applicable.

### B.2 Records that cannot be destroyed

- A deviation past Reported cannot be deleted by anyone through the UI or ORM.
- The transition log rejects write and unlink for every user including the superuser.

Both are application-level controls. A user with direct PostgreSQL access can
still alter the database; protecting against that is an infrastructure control
outside this module.

### B.3 Monitoring

Use the Overdue filter and the Transition Log view. The daily scheduled action
notifies investigators and QA reviewers of overdue open deviations.

---

## Part C — Developer manual

### C.1 Extending the state machine

Add the state to `STATE_SELECTION` and wire it into `STATE_TRANSITIONS` in
`models/ls_deviation.py`, then add an action method that calls
`_apply_transition`. Guards belong in the action method; the transition map
holds only reachability.

### C.2 Adding an electronic signature

Override `_apply_transition` in a module depending on both `ls_deviation` and
`ls_electronic_signature`. Every state change in the module passes through
this single method, so one override covers the whole workflow.

### C.3 Integrating CAPA

Create `ls_deviation_capa` depending on `ls_deviation` and `ls_capa`. Add a
`capa_id` many2one, make `capa_reference` related to it, and extend
`action_require_capa` to create the CAPA. Do not add the dependency to this
module: it must remain installable on its own.

### C.4 Key API

| Method | Purpose |
|---|---|
| `_apply_transition(target_state, reason)` | Validate, perform and log a transition. Single choke point |
| `_check_transition_allowed(target_state)` | Raise if unreachable from the current state |
| `_log_transition(from_state, to_state, reason)` | Append to the immutable log |
| `_cron_notify_overdue()` | Returns the number of records notified |
| `res.company._ls_deviation_target_days(severity)` | Configured closure interval with documented fallback |

### C.5 Odoo 19 idioms used

`models.Constraint` for SQL constraints; `<list>` root element; `<chatter/>`;
`<t t-name="card">`; `res.groups.privilege` with `privilege_id`;
`_read_group` returning tuples led by the grouping recordset. See
`00_VERIFICATION_STATUS.md` section 3.
