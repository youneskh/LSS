# API Documentation

Module: `ls_calibration` `19.0.1.0.0`. The module exposes no HTTP controller
and no custom web service. Everything below is reachable through the standard
Odoo external API, XML-RPC and JSON-RPC, subject to the access rights and to
the multi-company record rules.

## 1. Models

| Model | Purpose |
|-------|---------|
| `ls.calibration.instrument` | Instrument register |
| `ls.calibration.plan` | Periodic calibration programme |
| `ls.calibration.plan.point` | Test point of a plan |
| `ls.calibration.record` | Calibration event |
| `ls.calibration.record.line` | Test point result |
| `ls.calibration.certificate` | Calibration certificate |
| `ls.calibration.record.generate` | Generation wizard, transient |
| `ls.calibration.record.reject` | Rejection wizard, transient |

The complete field list is in the technical specification, section 4.4.

## 2. Public methods

### `ls.calibration.instrument`

| Method | Signature | Returns | Raises |
|--------|-----------|---------|--------|
| `action_set_in_service` | `()` on a recordset | `True` | `UserError` if the state is not draft or out of service |
| `action_set_out_of_service` | `()` | `True` | `UserError` if the state is not in service |
| `action_retire` | `()` | `True`, and makes the active plans obsolete | `UserError` if already retired |
| `action_reset_to_draft` | `()` | `True` | `UserError` if not retired |
| `action_view_plans` | `()` on one record | act_window action | |
| `action_view_records` | `()` on one record | act_window action | |
| `action_view_certificates` | `()` on one record | act_window action | |
| `_get_calibration_status` | `(today)` on one record | one of `not_applicable`, `not_scheduled`, `valid`, `due_soon`, `overdue` | |
| `_cron_notify_due_calibrations` | `()` on the model | number of activities scheduled | |

### `ls.calibration.plan`

| Method | Signature | Returns | Raises |
|--------|-----------|---------|--------|
| `action_activate` | `()` | `True` | `UserError` if the state is wrong or there is no test point |
| `action_suspend` | `()` | `True` | `UserError` if not active |
| `action_set_obsolete` | `()` | `True` | `UserError` if already obsolete |
| `action_reset_to_draft` | `()` | `True` | `UserError` if not suspended or obsolete |
| `action_create_calibration_record` | `()` | act_window action on the created records | `UserError` if a plan is not active |
| `action_view_records` | `()` on one record | act_window action | |
| `_add_interval` | `(date_from)` on one record | shifted `date` | |
| `_prepare_record_values` | `()` on one record | `dict` for `ls.calibration.record.create` | |
| `_get_open_records` | `()` on one record | recordset of the non-closed records | |
| `_cron_generate_calibration_records` | `()` on the model | number of records created | |

### `ls.calibration.record`

| Method | Signature | Returns | Raises |
|--------|-----------|---------|--------|
| `action_start` | `()` | `True` | `UserError` if not draft |
| `action_submit_review` | `()` | `True` | `UserError` on any completeness failure |
| `action_approve` | `()` | `True` | `UserError` if not to review, if the caller is not a manager, or if the caller is the performer |
| `action_reject` | `(reason=None)` | `True` | `UserError` if not to review or if the reason is empty |
| `action_cancel` | `()` | `True` | `UserError` if approved or cancelled |
| `action_reset_to_draft` | `()` | `True` | `UserError` if not rejected |
| `action_open_reject_wizard` | `()` on one record | act_window action | |
| `action_view_certificates` | `()` on one record | act_window action | |
| `_check_ready_for_review` | `()` | `None` | `UserError` on failure |
| `_check_standards_validity` | `()` on one record | `None` | `UserError` if a standard is overdue |
| `_get_lock_exempt_fields` | `()` on the model | `set` of field names | |

### `ls.calibration.certificate`

| Method | Signature | Returns | Raises |
|--------|-----------|---------|--------|
| `action_issue` | `()` | `True` | `UserError` if not draft, or if an external certificate has no document |
| `action_supersede` | `()` | `True` | `UserError` if not issued |

### Wizards

| Model | Method | Returns |
|-------|--------|---------|
| `ls.calibration.record.generate` | `action_generate()` | act_window action on the created records; `UserError` when nothing is due or when every due plan already has an open record |
| `ls.calibration.record.reject` | `action_reject()` | `{"type": "ir.actions.act_window_close"}` |

## 3. Integration examples

The examples use XML-RPC. Replace the connection parameters.

### Read the instruments that are overdue

```python
models.execute_kw(
    db, uid, password,
    "ls.calibration.instrument", "search_read",
    [[("calibration_status", "=", "overdue")]],
    {"fields": ["code", "name", "location", "next_calibration_date"]},
)
```

### Create a calibration record from a plan

```python
values = models.execute_kw(
    db, uid, password,
    "ls.calibration.plan", "_prepare_record_values", [[plan_id]],
)
record_id = models.execute_kw(
    db, uid, password, "ls.calibration.record", "create", [values],
)
```

### Record the readings and submit

```python
for line_id, found, left in readings:
    models.execute_kw(
        db, uid, password, "ls.calibration.record.line", "write",
        [[line_id], {"as_found_value": found, "as_left_value": left}],
    )
models.execute_kw(
    db, uid, password, "ls.calibration.record", "action_start", [[record_id]],
)
models.execute_kw(
    db, uid, password, "ls.calibration.record", "action_submit_review",
    [[record_id]],
)
```

### Render the PDF of a calibration record

```python
models.execute_kw(
    db, uid, password, "ir.actions.report", "_render_qweb_pdf",
    ["ls_calibration.report_ls_calibration_record", [record_id]],
)
```

## 4. Integration rules

| Rule | Reason |
|------|--------|
| Never write directly on the `state` field. | The `action_*` methods carry the checks. Writing the state bypasses them, and on an approved record it is refused. |
| Never write on an approved record. | The ORM refuses it; the call returns a `UserError`. |
| Do not compute the due date yourself. | It is derived from the last approved record and from the interval of the plan. |
| Authenticate the integration with its own dedicated user. | Attributability of the records depends on it. The integration user must not hold the manager group unless it is meant to approve. |
| Handle `UserError` explicitly. | Every business rule is reported as a `UserError` with a message intended to be shown to a human. |
