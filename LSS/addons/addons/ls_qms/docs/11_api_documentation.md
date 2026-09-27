# 11 — API Documentation

Only methods intended to be called by other code are listed. Compute methods,
constraint methods and default methods are documented in the source.

## 1. `ls.qms.document.mixin`

| Method | Signature | Returns | Raises |
|---|---|---|---|
| `action_submit_for_review` | `(self)` | `True` | `UserError` on a forbidden transition or an incomplete document |
| `action_approve` | `(self)` | `True` | `UserError` on a forbidden transition, a missing group, or self approval |
| `action_publish` | `(self)` | `True` | `UserError` on a forbidden transition or a missing group |
| `action_set_obsolete` | `(self)` | `True` | `UserError` outside the group Manager |
| `action_reset_to_draft` | `(self)` | `True` | `UserError` outside the group Manager |
| `ls_qms_reject` | `(self, reason)` | `True` | `UserError` on an empty reason or a forbidden transition |
| `create_new_revision` | `(self, reason_for_change, date_effective=None)` | the new revision, single recordset | `UserError` on an empty reason or a non published source |
| `action_open_new_revision_wizard` | `(self)` | action dictionary | none |
| `action_open_reject_wizard` | `(self)` | action dictionary | none |
| `action_open_attachments` | `(self)` | action dictionary | none |
| `_ls_qms_documents_due_for_review` | `(self, lead_days=None)` | recordset of the current model | none |
| `_cron_document_review_reminder` | `(self)` | integer, activities created | none |
| `_ls_qms_document_models` | `(self)` | list of model names present in the registry | none |
| `_ls_qms_content_fields` | `(self)` | set of field names | none |
| `_ls_qms_signature_hook` | `(self, meaning)` | `True` in this module | none in this module |

## 2. `ls.qms.objective`

| Method | Signature | Returns | Raises |
|---|---|---|---|
| `action_start` | `(self)` | `True` | `UserError` outside the state draft |
| `action_close_achieved` | `(self)` | `True` | `UserError` outside the state in progress |
| `action_close_not_achieved` | `(self)` | `True` | `UserError` outside the state in progress |
| `action_cancel` | `(self)` | `True` | `UserError` on an already cancelled objective |
| `action_reset_to_draft` | `(self)` | `True` | none |
| `action_view_measurements` | `(self)` | action dictionary | none |
| `_expected_progress` | `(self, today)` | float, percentage of the period elapsed | none |
| `_cron_objective_monitoring` | `(self)` | integer, activities created | none |

Module level function:

```python
compute_achievement_rate(direction, baseline, target, current, tolerance)
```

Returns a float, floored at zero, not capped above one hundred. Returns zero
when the denominator of the applicable formula is zero. The four formulas are
tabulated in `03_functional_specification.md`, section 4.

## 3. `ls.qms.quality_record`

| Method | Signature | Returns | Raises |
|---|---|---|---|
| `action_confirm` | `(self)` | `True` | `UserError` outside the state draft |
| `action_archive_record` | `(self)` | `True` | `UserError` outside the state confirmed |
| `action_dispose` | `(self)` | `True` | `UserError` outside the group Manager, outside the state archived, or before the retention date |
| `action_open_attachments` | `(self)` | action dictionary | none |
| `_cron_retention_review` | `(self)` | integer, activities created | none |

## 4. `ls.qms.parameter.mixin`

| Method | Signature | Returns |
|---|---|---|
| `_get_int_parameter` | `(self, key, fallback)` | integer, the fallback when the stored value is absent, not a number, or negative |
| `_get_bool_parameter` | `(self, key, fallback)` | boolean, the fallback when the stored value is absent or unrecognised |

## 5. Wizards

| Model | Method | Effect |
|---|---|---|
| `ls.qms.new.revision.wizard` | `action_create_revision` | Calls `create_new_revision` and returns an action opening the new revision |
| `ls.qms.reject.wizard` | `action_reject` | Calls `ls_qms_reject` and closes the dialog |

Both read `active_model` and `active_id` from the context in `default_get`
and raise a `UserError` when the context is absent or names a model that is
not a controlled document.
