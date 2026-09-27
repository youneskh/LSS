# API Documentation

Module: `ls_supplier_qualification` · Odoo 19 Community Edition

---

## 1. Access

The module declares **no HTTP controller and no web service**. Every operation
is a public ORM method, reachable through the standard Odoo external API
(XML-RPC or JSON-RPC) and from other modules.

Access rights and record rules apply to every call. There is no path that
bypasses them, with one designed exception: `ls.supplier.signature.sign()`
elevates internally to write the log, on a model no group can write to.

## 2. Module-level constants

Import these rather than repeating literals.

| Constant | Module |
|----------|--------|
| `STATE_SELECTION`, `APPROVED_STATES`, `EDITABLE_HEADER_STATES` | `models.ls_supplier_qualification` |
| `CRITICALITY_SELECTION` | `models.ls_supplier_category` |
| `CRITERION_DOMAIN_SELECTION` | `models.ls_supplier_criterion` |
| `MATERIAL_TYPE_SELECTION`, `MATERIAL_STATE_SELECTION` | `models.ls_supplier_material` |
| `ASSESSMENT_TYPE_SELECTION`, `ASSESSMENT_STATE_SELECTION`, `RESULT_SELECTION` | `models.ls_supplier_assessment` |
| `AUDIT_TYPE_SELECTION`, `AUDIT_STATE_SELECTION`, `AUDIT_OUTCOME_SELECTION`, `FINDING_SEVERITY_SELECTION`, `FINDING_STATE_SELECTION` | `models.ls_supplier_audit` |
| `PERFORMANCE_STATE_SELECTION`, `RATING_SELECTION` | `models.ls_supplier_performance` |
| `REVIEW_TYPE_SELECTION`, `REVIEW_STATE_SELECTION`, `REVIEW_DECISION_SELECTION` | `models.ls_supplier_review` |
| `SIGNATURE_MEANING_SELECTION` | `models.ls_supplier_signature` |
| `PO_CONTROL_SELECTION` | `models.res_company` |

## 3. `ls.supplier.qualification`

### Transitions

| Method | Returns | Raises |
|--------|---------|--------|
| `action_start_assessment()` | `True` | `UserError` if not draft |
| `action_start_audit()` | `True` | `UserError` if not under assessment or pending approval |
| `action_submit_for_approval()` | `True` | `UserError` listing every unmet prerequisite |
| `action_requalify()` | `True` | `UserError` if not expired or suspended |
| `action_reset_to_draft()` | `True` | `UserError` if approved or disqualified |

### Decision helpers

**`_get_blocking_reasons()`** → `list[str]`
Unmet prerequisites for submission, as translated strings. Empty means ready.
Single record. The extension point for adding a prerequisite.

**`_apply_approval(decision, conditions, expiry_date, reason, login)`** → `None`
Writes the approval, appends the signature entry, posts to the chatter and
queues the notification. `decision` is `"approved"` or `"conditional"`.
Raises `UserError` on a segregation-of-duties conflict. Called by the wizard;
callable directly by a module that implements its own approval interface.

**`_check_segregation_of_duties(user)`** → `None`
Raises `UserError` when `user` produced assessment or audit evidence on this
dossier and `company_id.ls_enforce_sod` is set.

### Scheduled actions

| Method | Returns |
|--------|---------|
| `_cron_check_expiry()` | Number of dossiers moved to Expired |
| `_cron_check_due_dates()` | Number of activities created |

Both are `@api.model` and safe to call repeatedly.

### Notable fields

`state`, `criticality`, `risk_level`, `expiry_date`, `expiry_status`,
`days_to_expiry`, `is_ready_for_approval`, `blocking_reasons`,
`latest_assessment_score`, `latest_assessment_result`,
`latest_performance_rating`, `open_critical_finding_count`,
`open_major_finding_count`, `next_audit_date`, `next_review_date`.

## 4. `ls.supplier.assessment`

| Method | Effect |
|--------|--------|
| `action_load_template()` | Replaces the lines with the template criteria. Draft only. |
| `action_start()` | Draft → In Progress. Requires at least one line. |
| `action_done()` | In Progress → Completed. Requires comments on low scores and a conclusion. Appends an `authored` signature. |
| `action_review()` | Completed → Reviewed. Enforces segregation of duties. Appends a `reviewed` signature. |
| `action_cancel()`, `action_reset_to_draft()` | Cancellation and return to draft. |

Result fields: `total_weighted_score`, `total_max_weighted_score`,
`score_percent`, `mandatory_failed_count`, `finding_count`, `result`.

Frozen rule fields: `max_score_per_criterion`, `mandatory_min_score`,
`pass_threshold`, `conditional_threshold`.

## 5. `ls.supplier.audit` and `ls.supplier.audit.finding`

Audit: `action_plan`, `action_start`, `action_draft_report`,
`action_issue_report`, `action_register_response`, `action_close`,
`action_cancel`, `action_reset_to_draft`, `action_view_findings`.

Finding: `action_register_response`, `action_agree_action`,
`action_mark_implemented`, `action_verify`, `action_close`, `action_cancel`.

Counters on the audit: `critical_count`, `major_count`, `minor_count`,
`observation_count`, `open_finding_count`, `finding_count`.

## 6. `ls.supplier.material`

`action_qualify`, `action_suspend`, `action_reject`, `action_reset_to_draft`.
`_cron_check_material_expiry()` → number of lines suspended.

## 7. `ls.supplier.performance`

`action_confirm`, `action_cancel`, `action_reset_to_draft`,
`action_compute_delivery_counters`.

`action_compute_delivery_counters` raises `UserError` when the record is not a
draft, or when `stock.move.purchase_line_id` and
`purchase.order.line.date_planned` are unavailable. It never guesses.

## 8. `ls.supplier.review`

`action_collect_evidence`, `action_done`, `action_cancel`.
`_apply_decision()` writes the decision onto the dossier; override it to change
what a decision does.

## 9. `ls.supplier.signature`

**`sign(record, meaning, reason=False, login=False, payload=None)`** →
`ls.supplier.signature`
Appends one entry. `record` is any singleton; the dossier back-reference is
resolved automatically. `payload` is a dict frozen as JSON. `@api.model`.

**`verify_chain(company=None)`** → recordset
Recomputes the chain and returns the entries whose stored digest no longer
matches. Empty means consistent. `@api.model`.

**`action_verify_chain()`** → client action
Verifies the active company chain and returns a notification.

**`_compute_hash(previous_hash, values)`** → `str`
The SHA-256 primitive. `@api.model`.

`write()` and `unlink()` raise `UserError` unconditionally.

## 10. `res.partner`

**`ls_get_qualification_blocking_message(products=None)`** → `str`
Empty string when nothing blocks a purchase; otherwise a translated message
naming the issue: no dossier, not approved, expired, or products outside the
qualified scope. `products` is an optional `product.product` recordset, checked
only when `company.ls_po_check_scope` is set. The extension point for changing
the purchase policy.

Fields, all non-stored and company-aware: `ls_qualification_id`,
`ls_qualification_state`, `ls_qualification_expiry_date`,
`ls_is_approved_supplier` (searchable), `ls_qualification_count`.

## 11. `purchase.order`

**`_ls_check_supplier_qualification()`** → `None`
Applies the company policy. Posts to the chatter at *Warn*, raises `UserError`
at *Block*, does nothing at *No control*. Called from `button_confirm()`.

Fields: `ls_qualification_id`, `ls_qualification_state`,
`ls_qualification_warning`.

## 12. Example: create and approve through RPC

```python
import xmlrpc.client

url, db, user, pwd = "http://localhost:8069", "prod", "quality", "***"
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, user, pwd, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

def call(model, method, *args, **kwargs):
    """Shorthand for execute_kw."""
    return models.execute_kw(db, uid, pwd, model, method, list(args), kwargs)

category = call("ls.supplier.category", "search",
                [("code", "=", "API")], limit=1)[0]
dossier = call("ls.supplier.qualification", "create", [{
    "partner_id": partner_id,
    "category_id": category,
}])

call("ls.supplier.qualification", "action_start_assessment", [dossier])

# ... create and complete an assessment, qualify a scope line ...

reasons = call("ls.supplier.qualification", "read", [dossier],
               fields=["blocking_reasons", "is_ready_for_approval"])
if reasons[0]["is_ready_for_approval"]:
    call("ls.supplier.qualification", "action_submit_for_approval", [dossier])
```

Approval itself goes through the wizard, so that the login confirmation and the
signature entry are not bypassed:

```python
wizard = call("ls.supplier.approve.wizard", "create", [{
    "qualification_id": dossier,
    "decision": "approved",
    "expiry_date": "2029-07-26",
    "reason": "Initial qualification approved on assessment SA/2026/00001.",
    "signature_login": user,
}])
call("ls.supplier.approve.wizard", "action_confirm", [wizard])
```

## 13. Errors a caller must handle

| Exception | When |
|-----------|------|
| `UserError` | Invalid transition, unmet prerequisite, segregation-of-duties conflict, login mismatch, deletion of a retained record, missing `purchase_stock` fields. |
| `ValidationError` | Constraint violation: duplicate live dossier, incoherent dates, out-of-range score or percentage, missing conditions or justification. |
| `AccessError` | The user lacks the right, or a record rule excludes the record. |
