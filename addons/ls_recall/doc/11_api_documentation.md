# API Documentation

Module: `ls_recall`
All models are reachable over XML-RPC and JSON-RPC subject to the same
access rights and record rules as the user interface.

---

## `ls.recall.plan`

| Method | Signature | Effect |
|--------|-----------|--------|
| `action_submit_review` | `()` → `True` | draft → under_review |
| `action_approve` | `()` → `True` | under_review → approved; stamps approver and time. Raises `ValidationError` without a procedure or deputy. |
| `action_reject` | `()` → `True` | under_review → draft |
| `action_set_obsolete` | `()` → `True` | approved → obsolete; archives the record |
| `action_new_revision` | `()` → window action | Copies at version n+1 in draft, retires version n |
| `action_view_executions` | `()` → window action | Lists recalls under the plan |
| `_cron_check_mock_recall_due` | `()` → `int` | Model method. Raises activities on plans whose rehearsal is due. Returns the number of plans found. |

## `ls.recall.execution`

### Workflow

| Method | Signature | Gate |
|--------|-----------|------|
| `action_initiate` | `()` → `True` | Reason and lots present; for real actions also classification, depth and hazard evaluation |
| `action_trace_and_start` | `()` → `True` | Tracing produces at least one consignee line |
| `action_start_communication` | `()` → `True` | At least one communication sent or acknowledged |
| `action_start_effectiveness` | `()` → `True` | Planned checks ≥ required |
| `action_open_close_wizard` | `()` → window action | Record is in effectiveness_check |
| `action_cancel` | `()` → window action | Record is not already finalised |
| `action_reset_to_planned` | `()` → `True` | State is initiated and no related record exists |

All raise `odoo.exceptions.UserError` when the gate is not met.

### Operations

| Method | Signature | Effect |
|--------|-----------|--------|
| `action_trace_distribution` | `()` → `True` | Rebuilds consignee lines from stock movements. Idempotent for user-entered quantities. Raises on a finalised record. |
| `action_generate_effectiveness_checks` | `()` → `True` | Creates one planned check per uncovered consignee line |
| `action_view_lines` / `action_view_communications` / `action_view_effectiveness` / `action_view_reports` | `()` → window action | Open related records |

### Extension points

| Method | Returns |
|--------|---------|
| `_evaluate_closure_gates()` | `list[(bool, str)]` — one entry per closure check |
| `_scan_move_lines()` | `(dict, float)` — `{(partner_id, lot_id): {"quantity": float, "picking_ids": set}}` and the unattributable quantity |
| `_required_effectiveness_checks(consignee_count)` | `int` — consignees to contact, rounded up |
| `_assert_transition(target_state)` | `None`; raises `UserError` |
| `_register_authority_notification(notification_date)` | `None`; sets the notification flag and date |
| `_cron_monitor_open_recalls()` | `int` — number of recalls an activity was raised on |

### Selected fields

| Field | Type | Note |
|-------|------|------|
| `state` | selection | planned, initiated, in_progress, communication, effectiveness_check, closed, cancelled |
| `action_type` | selection | recall, market_withdrawal, stock_recovery, fsca, mock_recall |
| `classification` | selection | not_classified, class_i, class_ii, class_iii |
| `depth` | selection | wholesale, retail, consumer_user |
| `effectiveness_level` | selection | a, b, c, d, e |
| `qty_distributed`, `qty_accounted`, `qty_outstanding`, `reconciliation_rate` | float, stored compute | Derived from consignee lines |
| `consignee_count`, `response_rate`, `effectiveness_required_count`, `effectiveness_coverage` | stored compute | |
| `is_mock` | boolean, stored compute | True for rehearsals |
| `authority_notified` | boolean, readonly | Set by the communication model |

## `ls.recall.line`

| Method | Effect |
|--------|--------|
| `action_mark_notified` | Sets notified and stamps the date |

Status is a stored compute over notification, response and quantities,
evaluated in the order discrepancy → reconciled → responded → notified →
pending.

## `ls.recall.communication`

| Method | Gate |
|--------|------|
| `action_approve` | Draft; body present; content confirmations complete for notices |
| `action_mark_sent` | Approved; content confirmations still complete. Marks recipient lines notified; an authority notification updates the recall header. |
| `action_acknowledge` | Sent |
| `action_cancel` | Not sent |

## `ls.recall.effectiveness`

| Method | Gate |
|--------|------|
| `action_perform` | Planned, and an outcome is set. Stamps user and time; marks the consignee line as having responded. |
| `action_escalate` | Planned or performed. Marks escalated and creates the next attempt. |

## `ls.recall.report`

| Method | Gate |
|--------|------|
| `action_review` | Draft; summary present |
| `action_approve` | Reviewed; approver differs from reviewer. Freezes twelve figures. |
| `action_submit` | Approved; at least one recipient named |

## `stock.lot`

| Field / method | Note |
|----------------|------|
| `ls_recall_open` | Boolean compute — lot is named in a real, non-finalised action. Computed through `sudo` so it is readable without a recall role. |
| `ls_recall_count` | Integer compute — number of real actions naming the lot |
| `action_view_ls_recalls` | Window action listing them |

## Wizards

| Model | Method | Returns |
|-------|--------|---------|
| `ls.recall.initiate.wizard` | `action_create_recall` | Window action on the created recall |
| `ls.recall.close.wizard` | `action_confirm` | `{"type": "ir.actions.act_window_close"}` |

## Example — creating and initiating over XML-RPC

```python
import xmlrpc.client

url, db, username, password = "http://localhost:8069", "prod", "user", "***"
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

recall_id = models.execute_kw(db, uid, password,
    "ls.recall.execution", "create", [{
        "action_type": "recall",
        "product_id": 42,
        "lot_ids": [(6, 0, [17, 18])],
        "classification": "class_ii",
        "depth": "retail",
        "reason": "Out-of-specification dissolution result.",
        "health_hazard_evaluation": "<p>Assessed as class II.</p>",
    }])

models.execute_kw(db, uid, password,
                  "ls.recall.execution", "action_initiate", [[recall_id]])
models.execute_kw(db, uid, password,
                  "ls.recall.execution", "action_trace_distribution",
                  [[recall_id]])

gates = models.execute_kw(db, uid, password,
                          "ls.recall.execution", "_evaluate_closure_gates",
                          [[recall_id]])
```

Errors surface as XML-RPC faults carrying the `UserError` or
`ValidationError` message.
