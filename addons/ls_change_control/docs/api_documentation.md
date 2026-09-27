# API Documentation

Module: `ls_change_control` | Public Python methods and their contracts

The module exposes **no HTTP controller and no REST endpoint**. It is reached
through the standard Odoo external API (`/xmlrpc/2` or the JSON API of the
release in use), which applies the access rights and the record rules of the
calling user, and through the Python methods below in a server side context.

## 1. `ls.change_control.request`

### 1.1 Transitions

| Method | Signature | Allowed from | Caller | Raises |
|--------|-----------|--------------|--------|--------|
| `action_submit_review` | `() -> True` | `draft` | Requester of the record, or manager | `AccessError` if the caller is neither; `UserError` if the state is wrong |
| `action_start_assessment` | `() -> True` | `under_review` | Manager | `AccessError`, `UserError` when an item is outstanding |
| `action_reset_draft` | `() -> True` | `under_review` | Manager | `AccessError`, `UserError` |
| `action_start_implementation` | `() -> True` | `approved` | Manager | `AccessError`, `UserError` when no action is planned |
| `action_verify` | `() -> True` | `implementation` | Manager | `AccessError`, `UserError` when an item is outstanding |
| `action_close` | `(closure_statement: str) -> True` | `verified` | Manager | `AccessError`, `UserError` when the statement is empty |
| `action_reject` | `(reason: str) -> True` | `under_review`, `impact_assessment` | Manager or an assigned approver | `AccessError`, `UserError` when the reason is empty |
| `action_cancel` | `(reason: str) -> True` | `draft`, `under_review`, `impact_assessment`, `approved` | Manager | `AccessError`, `UserError` when the reason is empty |

All transitions are multi-record: they apply to the whole recordset, and a
failure on one record rolls the whole call back.

### 1.2 Internal transition

`_try_approve() -> True` moves to `approved` every record of the set that is in
`impact_assessment` and has no outstanding item. It is called by the approval
lines; records that are not ready are silently left untouched, which is why it
must not be used as a user facing action.

### 1.3 Query helpers

| Method | Returns |
|--------|---------|
| `_get_blocking_reasons()` | `list[str]`, empty when the next transition is allowed. Single record only |
| `_is_verification_required()` | `bool`, combining the company parameter and the category. Single record only |

### 1.4 Generation helpers

| Method | Effect |
|--------|--------|
| `_generate_assessments()` | Creates one assessment per selected impact area that has none. Idempotent |
| `_generate_approvals()` | Creates one approval per approval template line of the category that has none. Idempotent |

### 1.5 Scheduled action entry points

All three are `@api.model` and return `True`.

| Method | Selects |
|--------|---------|
| `_cron_remind_pending_approvals` | Pending approvals of requests in `impact_assessment`, older than the reminder delay of their company, not already reminded today |
| `_cron_remind_overdue_implementations` | Requests in `approved` or `implementation`, planned implementation date passed, not implemented |
| `_cron_remind_due_verifications` | Requests in `implementation`, planned verification date reached, verification required, no completed verification |

### 1.6 Window actions

`action_view_assessments`, `action_view_approvals`,
`action_view_implementations`, `action_view_verifications` return a window
action filtered on the record. `action_open_close_wizard`,
`action_open_reject_wizard`, `action_open_cancel_wizard` return the decision
wizard action. All are single record.

### 1.7 ORM overrides

| Method | Behaviour added |
|--------|-----------------|
| `create` | Allocates the reference from the sequence of the company; subscribes the requester |
| `write` | Applies `_check_system_fields`, `_check_content_fields` and `_check_writer` before writing |
| `unlink` | Refuses any record whose state is not `draft` |
| `copy_data` | Resets reference, state and request date, and drops the child records |

### 1.8 Integrity checks

| Method | Raises when |
|--------|-------------|
| `_check_system_fields(vals)` | A workflow field is written and `env.su` is not set |
| `_check_content_fields(vals)` | A frozen content field is written on a submitted request |
| `_check_writer(vals)` | A non technical field is written on a submitted request by a non manager |
| `_check_manager()` | The current user does not hold the manager group |
| `_check_state(expected)` | A record of the set is not in one of the expected states |

## 2. `ls.change_control.assessment`

| Method | Contract |
|--------|----------|
| `action_complete()` | Completes the assessments. Requires: state `draft`, parent in `impact_assessment`, caller is the assessor or a manager, a written assessment, and required actions when the impact is not `none`. Raises `UserError` or `AccessError` |

`write` refuses the workflow fields outside `env.su`, and refuses any business
field on a completed assessment. `unlink` refuses a completed assessment.

## 3. `ls.change_control.approval`

| Method | Contract |
|--------|----------|
| `action_approve()` | Records a favourable decision, then calls `_try_approve` on the parent requests |
| `action_reject()` | Records an unfavourable decision, then rejects each parent request once. Requires a non empty comment |
| `_apply_signature(meaning)` | Returns the decision metadata. **Extension point** for `ls_electronic_signature` |
| `_notify_approver(reminder=False)` | Sends the approval mail and schedules a to-do; stamps `date_reminder` when `reminder` is true |
| `_check_can_decide()` | Raises unless the state is `pending`, the parent is in `impact_assessment` and the caller is the assigned approver |

`write` refuses the decision fields outside `env.su`, and refuses any write on a
decided approval. `unlink` refuses a decided approval.

## 4. `ls.change_control.implementation`

| Method | Contract |
|--------|----------|
| `action_start()` | `pending` to `in_progress`. Parent must be `approved` or `implementation`; caller is the responsible person or a manager |
| `action_done()` | To `done`. Requires a non empty `evidence_reference`. Stamps `date_done` and `done_by_id` |
| `action_cancel()` | To `cancelled`. Manager only. Requires `cancellation_reason` to have been recorded first |

`write` refuses the workflow fields outside `env.su`, and refuses any write on a
closed action. `unlink` refuses an action that is not `pending`.

## 5. `ls.change_control.verification`

| Method | Contract |
|--------|----------|
| `action_complete_effective()` | Completes with result `effective` |
| `action_complete_not_effective()` | Completes with result `not_effective`. Requires `follow_up_required` |
| `_complete(result)` | Shared implementation. Requires the parent in `implementation`, the caller to be the verifier or a manager, and a non empty conclusion |

`write` refuses the workflow fields outside `env.su`, and refuses any write on a
completed verification. `unlink` refuses a completed verification.

## 6. `ls.change_control.category`

| Method | Returns |
|--------|---------|
| `get_verification_delay(company)` | The category delay when it is non zero, otherwise the company default, never negative. Single record only |

## 7. `ls.change_control.decision_wizard`

| Method | Contract |
|--------|----------|
| `action_confirm()` | Applies the decision by delegating to `action_close`, `action_reject` or `action_cancel` of the request, then closes the dialog |

## 8. Calling the module from an external client

```python
import xmlrpc.client

common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

request_id = models.execute_kw(
    db, uid, password,
    "ls.change_control.request", "create",
    [{
        "title": "Replace the filter of the purified water loop",
        "category_id": category_id,
        "current_situation": "The filter is a 0.22 micrometre cartridge.",
        "proposed_change": "Replace it with an equivalent cartridge.",
        "justification": "The current reference is discontinued.",
    }],
)

models.execute_kw(
    db, uid, password,
    "ls.change_control.request", "action_submit_review", [[request_id]],
)
```

**An external client cannot write the state, a decision or a decision date.**
Those fields are refused outside superuser mode, which an external session
never reaches. The only way to move a request through its lifecycle is to call
the transition methods, which apply every guard.
