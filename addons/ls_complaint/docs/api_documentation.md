# API Documentation

## 1. Scope

The module exposes **no HTTP controller and no web service of its own**.
Integration uses the standard Odoo external API (XML-RPC or JSON-RPC) against
the seven models below and the methods listed in section 4.

Every call is subject to the access rights and the record rules of the
authenticating user. There is no service account bypass and no `sudo()` path.

## 2. Models

| Technical name | Kind | Purpose |
|---|---|---|
| `ls.complaint` | persistent | Complaint master record and state machine |
| `ls.complaint.category` | persistent | Configuration: classification and time targets |
| `ls.complaint.investigation` | persistent | Root cause analysis |
| `ls.complaint.adverse_event` | persistent | Vigilance record |
| `ls.complaint.resolution` | persistent | Action taken |
| `ls.complaint.close.wizard` | transient | Closure data collection |
| `ls.complaint.cancel.wizard` | transient | Cancellation data collection |

Field-by-field reference: `docs/04_technical_specification.md` section 4.

## 3. Creating a complaint externally

```python
import xmlrpc.client

url, db, username, password = "https://…", "…", "…", "…"
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

complaint_id = models.execute_kw(
    db, uid, password,
    "ls.complaint", "create",
    [{
        "summary": "Chipped tablets",
        "description": "Several tablets chipped on the edge.",
        "channel": "portal",
        "complainant_type": "pharmacy",
        "partner_id": 42,
        "product_id": 17,
        "lot_name": "L-2026-0043",
        "quantity_complained": 4.0,
        "category_id": 3,
        "owner_id": 8,
    }],
)
```

The reference is assigned by the server; do not send `name`.

## 4. Public method surface

Transitions raise `odoo.exceptions.UserError` when a precondition is not met.
Data rules raise `odoo.exceptions.ValidationError`. Over XML-RPC both surface as
faults carrying the message.

### `ls.complaint`

| Method | Arguments | Purpose |
|---|---|---|
| `create` | vals_list | Assign the complaint reference from the company sequence. |
| `write` | vals | Protect the content of complaints that reached a final state. |
| `copy_data` | default=… | Reset regulated data when duplicating a complaint. |
| `action_start_assessment` | — | Move the complaint from Received to Assessment. |
| `action_start_investigation` | — | Move the complaint from Assessment to Investigation. |
| `action_skip_investigation` | — | Move to Resolution without investigation, with justification. |
| `action_mark_capa_required` | — | Declare that a CAPA record must be raised for this complaint. |
| `action_start_resolution` | — | Move the complaint to the Resolution state. |
| `action_open_close_wizard` | — | Open the closure wizard for the current complaint. |
| `action_open_cancel_wizard` | — | Open the cancellation wizard for the current complaint. |
| `action_close` | closure_summary, reviewer, customer_notified=… | Close the complaint after the wizard collected the closure data. |
| `action_cancel` | reason | Cancel the complaint with a documented reason. |
| `action_reset_to_received` | — | Return a cancelled complaint to the Received state. |
| `action_view_investigations` | — | Open the investigations of the current complaint. |
| `action_view_resolutions` | — | Open the resolutions of the current complaint. |
| `action_view_adverse_events` | — | Open the adverse events of the current complaint. |
| `_cron_notify_overdue_complaints` | limit=… | Schedule a to-do activity on every overdue open complaint. |

### `ls.complaint.category`

| Method | Arguments | Purpose |
|---|---|---|
| `action_view_complaints` | — | Open the complaints of the current category. |

### `ls.complaint.investigation`

| Method | Arguments | Purpose |
|---|---|---|
| `create` | vals_list | Assign the investigation reference from the company sequence. |
| `write` | vals | Freeze approved and rejected investigations. |
| `action_start` | — | Move the investigation from Draft to In Progress. |
| `action_complete` | — | Move the investigation from In Progress to Completed. |
| `action_approve` | — | Approve a completed investigation. |
| `action_reject` | reason=… | Reject a completed investigation with a documented reason. |

### `ls.complaint.adverse_event`

| Method | Arguments | Purpose |
|---|---|---|
| `create` | vals_list | Assign the adverse event reference from the company sequence. |
| `write` | vals | Freeze closed adverse events. |
| `action_assess` | — | Record the reportability decision and move to Assessed. |
| `action_submit` | — | Record the submission of the report to the competent authority. |
| `action_close` | — | Close the adverse event once every obligation is discharged. |
| `_cron_notify_due_adverse_event_reports` | limit=… | Schedule an activity on reportable events whose deadline passed. |

### `ls.complaint.resolution`

| Method | Arguments | Purpose |
|---|---|---|
| `write` | vals | Freeze resolutions that reached a final state. |
| `action_start` | — | Move the resolution from Draft to In Progress. |
| `action_done` | — | Complete the resolution once evidence is recorded. |
| `action_cancel` | reason=… | Cancel the resolution with a documented reason. |

### `ls.complaint.close.wizard`

| Method | Arguments | Purpose |
|---|---|---|
| `action_confirm` | — | Apply the closure on the related complaint. |

### `ls.complaint.cancel.wizard`

| Method | Arguments | Purpose |
|---|---|---|
| `action_confirm` | — | Apply the cancellation on the related complaint. |


## 5. Typical external sequence

```python
call = lambda model, method, *args: models.execute_kw(
    db, uid, password, model, method, list(args)
)

call("ls.complaint", "action_start_assessment", [complaint_id])
call("ls.complaint", "write", [complaint_id], {
    "severity": "major",
    "complaint_type": "quality_defect",
    "assessment_summary": "Potential process deviation.",
})
call("ls.complaint", "action_start_investigation", [complaint_id])

investigation_ids = call(
    "ls.complaint.investigation", "search",
    [[("complaint_id", "=", complaint_id)]],
)
call("ls.complaint.investigation", "action_start", investigation_ids)
```

`action_close` and `action_cancel` take arguments and are the only two
transitions that do:

```python
call("ls.complaint", "action_cancel", [complaint_id], "Duplicate entry.")
```

`action_close` expects `closure_summary`, `reviewer` and optionally
`customer_notified`. Because `reviewer` is a recordset, external callers should
go through the wizard instead:

```python
wizard_id = call("ls.complaint.close.wizard", "create", {
    "complaint_id": complaint_id,
    "closure_summary": "Root cause corrected.",
    "reviewer_id": 9,
    "effectiveness_confirmed": True,
    "customer_notified": True,
})
call("ls.complaint.close.wizard", "action_confirm", [wizard_id])
```

## 6. Searching

```python
# open complaints past their configured closure target
call("ls.complaint", "search_read",
     [[("is_overdue", "=", True)]],
     {"fields": ["name", "summary", "closure_due_date", "owner_id"]})

# reportable adverse events not yet submitted
call("ls.complaint.adverse_event", "search_read",
     [[("reportable", "=", True), ("state", "in", ["draft", "assessed"])]],
     {"fields": ["name", "complaint_id", "report_due_date"]})
```

`is_overdue` and `is_report_overdue` are computed, non-stored and searchable,
and accept only the `=` and `!=` operators. Any other operator raises a
`UserError`.

## 7. Printing the report externally

```python
call("ir.actions.report", "_render_qweb_pdf",
     "ls_complaint.action_report_ls_complaint", [complaint_id])
```

The exact signature of the rendering method is version-sensitive — see risk
R-08 in `docs/00_verification_and_limitations.md`.

## 8. Error catalogue

| Situation | Exception | Message pattern |
|---|---|---|
| Transition from a wrong state | `UserError` | `Action '<action>' is not allowed for complaints <refs> in their current status.` |
| Missing mandatory information for a transition | `UserError` | `Complaint <ref>: action '<action>' requires the following information: <fields>.` |
| Approval by the investigator | `UserError` | `Investigation <ref> cannot be approved by its own investigator (segregation of duties).` |
| Closure with an open child record | `UserError` | `Complaint <ref>: resolutions <refs> are still open.` |
| Write on a final record | `UserError` | `Complaints <refs> are closed or cancelled and can no longer be modified.` |
| Deletion of a progressed record | `UserError` | `Complaints <refs> cannot be deleted because they left the Received state.` |
| Data rule violation | `ValidationError` | See `docs/04_technical_specification.md` section 5.2 |
| Access denied | `AccessError` | Standard Odoo message |
