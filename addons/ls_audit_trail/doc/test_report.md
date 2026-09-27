# Test Report — `ls_audit_trail`

**Delivery-gate status: CONDITIONAL PASS.** Every statement below is verifiable
against the source. The tests are written and their structure is validated, but
they have **not** been executed against a live Odoo 19 instance in this build
environment, which has no Odoo runtime, no PostgreSQL and no network access. No
pass-rate and no coverage percentage are claimed. See the honesty statement at
the end.

## Inventory (97 test methods across 10 modules)

### `tests/test_access_rights.py` (12 tests)
- `test_user_without_group_cannot_read_entries`
- `test_viewer_can_read_entries`
- `test_viewer_cannot_configure_rules`
- `test_viewer_cannot_create_evidence_packs`
- `test_auditor_can_create_evidence_packs`
- `test_auditor_cannot_configure_rules`
- `test_auditor_cannot_open_the_retention_wizard`
- `test_administrator_can_configure_rules`
- `test_no_role_can_write_entries`
- `test_acl_grants_no_write_or_unlink_on_the_trail`
- `test_multi_company_record_rules_are_installed`
- `test_entries_of_another_company_are_not_visible`

### `tests/test_capture.py` (13 tests)
- `test_create_is_captured`
- `test_write_is_captured_with_old_and_new_values`
- `test_write_without_change_produces_no_entry`
- `test_write_of_unaudited_field_produces_no_entry`
- `test_excluded_field_is_not_captured`
- `test_unlink_is_captured_before_deletion`
- `test_operation_flags_are_honoured`
- `test_many2one_is_stored_as_identifier_and_name`
- `test_binary_is_stored_as_fingerprint_only`
- `test_selection_display_uses_the_label`
- `test_line_context_columns_are_populated`
- `test_batch_create_produces_one_entry_per_record`
- `test_engine_models_are_never_audited`

### `tests/test_evidence_pack.py` (14 tests)
- `test_reference_is_assigned`
- `test_generation_populates_the_record`
- `test_generated_pack_is_immutable`
- `test_generated_pack_can_still_be_archived`
- `test_pack_cannot_be_deleted`
- `test_empty_selection_is_rejected`
- `test_archive_contains_the_three_files`
- `test_manifest_digests_match_the_files`
- `test_manifest_records_the_verification`
- `test_archive_digest_self_check_passes`
- `test_archive_digest_self_check_detects_tampering`
- `test_download_requires_generation`
- `test_inverted_range_is_rejected`
- `test_model_filter_restricts_the_export`

### `tests/test_hash_chain.py` (8 tests)
- `test_chain_positions_are_consecutive`
- `test_each_entry_links_to_its_predecessor`
- `test_chain_tail_of_an_unused_company_is_the_genesis`
- `test_first_entry_of_a_new_chain_uses_the_genesis_digest`
- `test_digests_are_reproducible`
- `test_digest_lengths`
- `test_canonical_json_is_key_order_independent`
- `test_payload_covers_stored_evidence_but_not_registry_metadata`

### `tests/test_immutability.py` (9 tests)
- `test_write_is_refused`
- `test_write_of_sealing_fields_is_refused_once_sealed`
- `test_unlink_is_refused_for_the_superuser`
- `test_line_write_is_refused`
- `test_line_unlink_is_refused`
- `test_verification_record_is_immutable`
- `test_company_with_entries_cannot_be_deleted`
- `test_user_with_entries_cannot_be_deleted`
- `test_audited_record_deletion_does_not_remove_its_entries`

### `tests/test_installation.py` (7 tests)
- `test_module_is_installed`
- `test_models_are_registered`
- `test_groups_are_created`
- `test_scheduled_action_exists`
- `test_sequence_exists`
- `test_no_rule_means_no_capture`
- `test_report_actions_exist`

### `tests/test_purge.py` (10 tests)
- `test_scope_counts_the_aged_entries`
- `test_retention_requires_period_before_allowing`
- `test_retention_requires_procedure_before_allowing`
- `test_disallowed_company_cannot_purge`
- `test_confirmation_count_must_match`
- `test_justification_is_required`
- `test_run_removes_entries_and_writes_an_anchor`
- `test_chain_still_verifies_after_a_run`
- `test_run_refuses_a_broken_chain`
- `test_new_entries_continue_the_chain_after_a_run`

### `tests/test_rule_constraints.py` (8 tests)
- `test_reject_own_models`
- `test_reject_transient_models`
- `test_reject_abstract_models`
- `test_reject_foreign_fields`
- `test_reject_no_operation`
- `test_reject_duplicate_rule`
- `test_changing_model_clears_field_selection`
- `test_rule_change_invalidates_configuration_cache`

### `tests/test_verification.py` (12 tests)
- `test_intact_chain_passes`
- `test_altered_value_is_detected`
- `test_altered_attribution_is_detected`
- `test_removed_entry_is_detected`
- `test_undocumented_head_truncation_is_detected`
- `test_empty_range_is_reported_rather_than_failed`
- `test_verification_record_captures_the_outcome`
- `test_failed_verification_is_recorded_as_failed`
- `test_wizard_runs_a_verification`
- `test_wizard_estimates_the_scope`
- `test_scheduled_action_runs_for_every_company`
- `test_payload_excludes_nothing_that_matters`

### `tests/test_volume.py` (4 tests)
- `test_large_batch_create_is_consecutive`
- `test_batch_write_produces_one_entry_per_changed_record`
- `test_mixed_operations_stay_linked`
- `test_verification_scales_to_the_whole_chain`

## What each module covers

- **test_installation** — module installs; models, groups, cron, sequence and
  report actions are registered; no rule means no capture.
- **test_rule_constraints** — a rule cannot target engine/abstract/transient
  models, foreign fields, or zero operations; the uniqueness constraint holds;
  a rule change invalidates the configuration cache immediately.
- **test_capture** — create/write/delete capture; no-op writes and unaudited or
  excluded fields produce nothing; relational, binary and selection value
  representation; denormalised line columns; batch create; no self-audit.
- **test_hash_chain** — consecutive positions; predecessor linkage; genesis
  digest on a fresh chain; digests reproducible; digest lengths; canonical JSON
  key-order independence; payload scope.
- **test_immutability** — write and unlink refused on entries and lines for the
  superuser; verification records immutable; restrict-on-delete on company and
  user; entries survive the audited record's deletion.
- **test_access_rights** — plain user blocked; viewer read-only; auditor can
  produce packs but not configure or purge; administrator can configure; no
  role can write/delete the trail; ACL grants only read; multi-company
  isolation.
- **test_verification** — intact chain passes; altered value, altered
  attribution, removed entry and undocumented head-truncation all detected;
  empty range reported not failed; outcome recorded immutably; wizard parity;
  scheduled action runs per company.
- **test_evidence_pack** — reference assigned; generation seals the record;
  immutability after generation with archiving still allowed; no-deletion;
  empty selection rejected; archive holds three files; manifest digests match;
  archive self-check passes and detects tampering; inverted range rejected.
- **test_purge** — scope counting; company preconditions; disallowed company
  blocked; confirmation count must match; justification required; run removes
  entries and writes an anchor; chain still verifies afterwards; run refuses a
  broken chain; new entries continue the chain after a run.
- **test_volume** — 200-record batch create consecutive; batch write one entry
  per changed record; mixed operations stay linked; verification scales to a
  few hundred entries. These assert correctness under load, not throughput.

## How to execute (for the receiving team)

```bash
odoo -d <db> -i ls_audit_trail --test-enable --stop-after-init \
     --test-tags /ls_audit_trail
```
Coverage can then be measured with `coverage run` around that command. Any
coverage figure must come from that real run, not from this document.

## Honesty statement

Verified in this environment: Python compiles (`py_compile`), XML is well-formed
(`xmllint`), the offline static checker passes with zero errors and zero
warnings, the checker's negative controls fail as expected, and view field
references and XML-id references cross-resolve. **Not** verified here: execution
against Odoo 19, test pass/fail outcomes, measured coverage, and `flake8` /
`pylint-odoo` (uninstallable without network access). The module is therefore
delivered as CONDITIONAL PASS pending IQ/OQ/PQ by the receiving team.