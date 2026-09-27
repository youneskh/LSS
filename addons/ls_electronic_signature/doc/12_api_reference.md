# API Reference

Public surface only. Members not listed are internal and may change.

## `tools.hashing`

| Member | Signature | Returns |
|---|---|---|
| `HASH_ALGORITHM` | constant | `"sha256"` |
| `HASH_HEX_LENGTH` | constant | `64` |
| `GENESIS_HASH` | constant | 64 ASCII zeroes |
| `normalise_value(value)` | any → JSON-safe | Raises `TypeError` for `bytes` and unknown types |
| `canonical_dumps(payload)` | dict → bytes | Canonical UTF-8 JSON |
| `sha256_hex(data)` | bytes → str | 64-char lowercase hex |
| `digest_payload(payload)` | dict → str | Record digest |
| `chain_digest(previous_hash, record_hash)` | str, str → str | Raises `ValueError` on malformed operands |

## `tools.credentials`

| Member | Signature | Notes |
|---|---|---|
| `CredentialApiError` | exception (`UserError`) | Configuration fault, **not** an authentication failure |
| `SUPPORTED_MODES` | constant | `("auto", "credential", "password")` |
| `resolve_mode(env)` | env → str | Raises `CredentialApiError` on an unknown parameter value |
| `verify_password(user, password)` | recordset, str → bool | `False` for wrong password; raises for API fault |

## `ls.signature.mixin`

See `11_developer_manual.md` §3 for the full member table.

## `ls.signature.log`

| Method | Signature | Purpose |
|---|---|---|
| `create(vals_list)` | override | Pins signer identity, builds the chain. |
| `write(vals)` | override | Always raises `UserError`. |
| `unlink()` | override | Always raises `UserError`. |
| `verify()` | → dict keyed by id | `{"chain_ok", "payload_ok", "messages"}` per signature. |
| `verify_chain(company)` | `@api.model` → dict | `{"entries_checked", "passed", "first_divergence_id", "messages"}`. |
| `action_verify()` | action | Raises on divergence, otherwise a success notification. |
| `action_open_signed_record()` | action | Opens the signed record. |

## `ls.signature.policy`

| Method | Purpose |
|---|---|
| `_policies_for_model(model_name, trigger=None)` | Active policies for a model. |
| `is_applicable_to(record)` | Whether the domain matches. |
| `_get_domain()` | Parsed applicability domain. |

## `ls.signature.meaning`

| Method | Purpose |
|---|---|
| `is_available_to(user)` | Subset of `self` the user may apply. |

## `ls.signature.session`

| Method | Purpose |
|---|---|
| `_current_token_hash()` | Digest of the caller's web session, or `False`. |
| `is_continuous(user, token_hash)` | Whether a continuous period is in force. |
| `register_signature(user, token_hash)` | Open or extend a session. |
| `_cron_close_idle_sessions()` | Scheduled action. |

## `ls.signature.attempt`

| Method | Purpose |
|---|---|
| `record(values, notify=False)` | Write an attempt, optionally alerting. Uses an independent cursor unless disabled. |
| `is_locked_out(login)` | Whether the code is currently blocked. |
| `_security_unit_recipients()` | Comma-separated e-mail list of the security unit. |

## `ls.signature.integrity.check`

| Method | Purpose |
|---|---|
| `run(company, trigger="manual")` | Verify a chain and store the result. |
| `_cron_verify_all_companies()` | Scheduled action. |
| `action_run_now()` | Verify the active company now. |

## `ls.signature.request`

| Method | Purpose |
|---|---|
| `action_send()` / `action_open_wizard()` / `action_decline()` / `action_cancel()` | Lifecycle. |
| `_mark_signed(signature)` | Close on signature. |
| `_cron_expire_requests()` | Scheduled action. |

## External API note

Every method above is reachable through the standard Odoo external API under the
same access rights as the user interface. The module adds no HTTP controller and
no separate service endpoint, deliberately: an endpoint able to create a
signature outside the wizard would bypass the control sequence.
