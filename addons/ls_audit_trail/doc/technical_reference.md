# Technical Reference — `ls_audit_trail`

This reference is generated from the module source with the Python `ast`
module, so it reflects the code exactly. It lists every model, its stored
and computed fields, and its public and audit-engine methods.

# Package `models`

## `base (extension)`
Defined in `models/base_audit.py` as `Base`.

**Overridden ORM methods:** `create`, `write`, `unlink`

**Public methods:** `create`, `write`, `unlink`

**Audit-engine methods:** `_ls_audit_plan`

## `ls.audit_trail.evidence_pack`
*Audit Trail Evidence Pack*
Defined in `models/ls_audit_trail_evidence_pack.py` as `LsAuditTrailEvidencePack`.

**Fields**

| Field | Type |
|-------|------|
| `name` | Char |
| `state` | Selection |
| `active` | Boolean |
| `purpose` | Text |
| `company_id` | Many2one |
| `date_from` | Datetime |
| `date_to` | Datetime |
| `model_names` | Char |
| `user_ids` | Many2many |
| `entry_count` | Integer |
| `line_count` | Integer |
| `first_sequence` | Integer |
| `last_sequence` | Integer |
| `pack_digest` | Char |
| `verification_id` | Many2one |
| `verification_result` | Selection |
| `attachment_id` | Many2one |
| `generated_by` | Many2one |
| `generated_on` | Datetime |

**Overridden ORM methods:** `create`, `write`, `unlink`

**Public methods:** `create`, `write`, `unlink`, `action_generate`, `action_download`, `action_verify_archive`

**Audit-engine methods:** `_ls_entry_domain`, `_ls_entry_payloads`, `_ls_build_csv`, `_ls_build_manifest`

## `ls.audit_trail.log`
*Audit Trail Entry*
Defined in `models/ls_audit_trail_log.py` as `LsAuditTrailLog`.

**Fields**

| Field | Type |
|-------|------|
| `sequence_number` | Integer |
| `company_id` | Many2one |
| `entry_type` | Selection |
| `event_datetime` | Datetime |
| `user_id` | Many2one |
| `user_login` | Char |
| `remote_addr` | Char |
| `model_name` | Char |
| `model_id` | Many2one |
| `res_id` | Integer |
| `res_name` | Char |
| `operation` | Selection |
| `line_ids` | One2many |
| `line_count` | Integer |
| `payload_digest` | Char |
| `hash_prev` | Char |
| `hash_current` | Char |
| `purged_from_sequence` | Integer |
| `purged_to_sequence` | Integer |
| `purged_entry_count` | Integer |
| `purged_aggregate_digest` | Char |
| `purge_reason` | Text |

**Overridden ORM methods:** `write`, `unlink`

**Public methods:** `write`, `unlink`, `action_open_audited_record`

**Audit-engine methods:** `_ls_audit_config_for`, `_ls_clear_audit_config_cache`, `_ls_eligible_field_names`, `_ls_snapshot`, `_ls_remote_addr`, `_ls_context_values`, `_ls_record_company_id`, `_ls_capture`, `_ls_safe_display_name`, `_ls_payload`, `_ls_lock_chain`, `_ls_chain_tail`, `_ls_seal`, `_ls_verify_chain`, `_ls_check_chain_head`, `_ls_cron_verify_chain`

## `ls.audit_trail.log.line`
*Audit Trail Field Change*
Defined in `models/ls_audit_trail_log_line.py` as `LsAuditTrailLogLine`.

**Fields**

| Field | Type |
|-------|------|
| `log_id` | Many2one |
| `field_name` | Char |
| `old_value_technical` | Text |
| `new_value_technical` | Text |
| `old_value_display` | Text |
| `new_value_display` | Text |
| `company_id` | Many2one |
| `event_datetime` | Datetime |
| `model_name` | Char |
| `res_id` | Integer |
| `res_name` | Char |
| `operation` | Selection |
| `user_id` | Many2one |
| `sequence_number` | Integer |
| `field_label` | Char |
| `field_type` | Char |

**Overridden ORM methods:** `write`, `unlink`

**Public methods:** `write`, `unlink`

## `ls.audit_trail.rule`
*Audit Trail Rule*
Defined in `models/ls_audit_trail_rule.py` as `LsAuditTrailRule`.

**Fields**

| Field | Type |
|-------|------|
| `name` | Char |
| `active` | Boolean |
| `model_id` | Many2one |
| `model_name` | Char |
| `company_id` | Many2one |
| `log_create` | Boolean |
| `log_write` | Boolean |
| `log_unlink` | Boolean |
| `field_ids` | Many2many |
| `excluded_field_ids` | Many2many |
| `entry_count` | Integer |
| `note` | Text |

**Overridden ORM methods:** `create`, `write`, `unlink`

**Public methods:** `create`, `write`, `unlink`, `action_view_entries`

## `ls.audit_trail.verification`
*Audit Trail Integrity Verification*
Defined in `models/ls_audit_trail_verification.py` as `LsAuditTrailVerification`.

**Fields**

| Field | Type |
|-------|------|
| `name` | Char |
| `company_id` | Many2one |
| `date_from` | Datetime |
| `date_to` | Datetime |
| `executed_on` | Datetime |
| `executed_by` | Many2one |
| `source` | Selection |
| `entries_checked` | Integer |
| `result` | Selection |
| `first_failure_log_id` | Many2one |
| `first_failure_sequence` | Integer |
| `details` | Text |

**Overridden ORM methods:** `write`, `unlink`

**Public methods:** `write`, `unlink`

**Audit-engine methods:** `_ls_run`, `_ls_notify_failure`

## `res.company (extension)`
Defined in `models/res_company.py` as `ResCompany`.

**Fields**

| Field | Type |
|-------|------|
| `ls_audit_retention_days` | Integer |
| `ls_audit_allow_purge` | Boolean |
| `ls_audit_retention_procedure` | Char |
| `ls_audit_entry_count` | Integer |

# Package `wizards`

## `ls.audit_trail.purge.wizard`
*Audit Trail Retention Run*
Defined in `wizards/ls_audit_trail_purge_wizard.py` as `LsAuditTrailPurgeWizard`.

**Fields**

| Field | Type |
|-------|------|
| `company_id` | Many2one |
| `retention_days` | Integer |
| `purge_allowed` | Boolean |
| `procedure_reference` | Char |
| `cutoff_datetime` | Datetime |
| `entry_count` | Integer |
| `first_sequence` | Integer |
| `last_sequence` | Integer |
| `confirm_entry_count` | Integer |
| `justification` | Text |

**Public methods:** `action_execute`

**Audit-engine methods:** `_ls_scope_domain`, `_ls_check_preconditions`

## `ls.audit_trail.verify.wizard`
*Verify Audit Trail Integrity*
Defined in `wizards/ls_audit_trail_verify_wizard.py` as `LsAuditTrailVerifyWizard`.

**Fields**

| Field | Type |
|-------|------|
| `company_id` | Many2one |
| `scope` | Selection |
| `window_days` | Integer |
| `date_from` | Datetime |
| `date_to` | Datetime |
| `entry_estimate` | Integer |

**Public methods:** `action_verify`

**Audit-engine methods:** `_ls_resolved_range`
