# Phase 4 — Technical Specification

## 4.1 Module layout

```
ls_electronic_signature/
├── __init__.py, __manifest__.py, README.md, LICENSE
├── tools/        hashing.py, credentials.py          pure functions, no ORM
├── models/       meaning, policy, session, log, attempt,
│                 integrity_check, request, mixin, res_config_settings
├── wizards/      ls_signature_wizard.py (+ decline wizard) and its views
├── security/     groups, ir.model.access.csv, record rules
├── data/         config parameters, meanings, crons, mail templates
├── demo/         demonstration users
├── views/        one file per model, plus menus
├── report/       manifestation template, certificate template, report action
├── tests/        unit tests (no signable model required)
├── i18n/         translation template location — see i18n/README.md
├── static/description/  icon.png, index.html
└── doc/          phases 1-10 and the manuals

ls_electronic_signature_test/    signable fixture model + integration tests
```

`tools/` contains no Odoo model and imports no ORM object beyond exceptions and
the translation helper. It is unit-testable in isolation, which is what makes
the hashing rules cheap to re-qualify.

## 4.2 Dependencies

| Dependency | Kind | Justification |
|---|---|---|
| `base` | Odoo Community, LGPLv3 | Users, groups, companies, sequences, `ir.model`. |
| `mail` | Odoo Community, LGPLv3 | Mail templates for the §11.300(d) notification, and chatter/tracking on requests. |

No Enterprise module. No external Python package: `hashlib`, `json`, `datetime`,
`decimal`, `inspect`, `ast`, `re` and `logging` are all standard library.

This adds `mail` to the dependency stated in the suite specification (§15.3,
`base` only). The addition is deliberate: §11.300(d) requires reporting "in an
immediate and urgent manner", which cannot be delivered without a mail
transport, and `mail` is Community.

## 4.3 Manifest

Version `19.0.1.0.0` (OCA convention: Odoo series then module semantic
version). Licence AGPL-3, permissible because every dependency is LGPLv3.
`application = True`; `auto_install = False`. Data files are ordered so that
security precedes data, data precedes reports, and views precede menus.

## 4.4 Models

| Model | Kind | Purpose |
|---|---|---|
| `ls.signature.meaning` | Model | Controlled vocabulary for §11.50(a)(3). |
| `ls.signature.policy` | Model | Where signatures are required, how many, by whom. |
| `ls.signature.session` | Model | Continuous period of controlled system access. |
| `ls.signature.log` | Model | **Append-only evidence.** |
| `ls.signature.attempt` | Model | Append-only security log for §11.300(d). |
| `ls.signature.integrity.check` | Model | Stored result of a chain verification. |
| `ls.signature.request` | Model | Routable work item. Inherits `mail.thread`, `mail.activity.mixin`. |
| `ls.signature.mixin` | AbstractModel | Capability added to signable models. |
| `ls.signature.wizard` | TransientModel | The signing dialog. |
| `ls.signature.decline.wizard` | TransientModel | Refusal with justification. |
| `res.config.settings` | TransientModel (inherit) | Settings. |

### 4.4.1 `ls.signature.log` — field reference

| Field | Type | Notes |
|---|---|---|
| `name` | Char | `ESIG/%08d` from the chain sequence. |
| `chain_sequence` | Integer | Contiguous per company from 1. |
| `company_id` | Many2one res.company | `restrict`. Chain scope. |
| `user_id` | Many2one res.users | `restrict` — blocks login recycling, §11.100(a). |
| `signer_name` | Char | §11.50(a)(1). Snapshot. |
| `signer_login` | Char | Snapshot. |
| `signed_at` | Datetime | §11.50(a)(2). UTC. |
| `meaning_id` | Many2one | `restrict`. |
| `meaning_code`, `meaning_name` | Char | §11.50(a)(3). Snapshots. |
| `res_model`, `res_id` | Char, Integer | The signed record. |
| `res_model_name`, `res_name` | Char | Labels, snapshots. |
| `payload_json` | Text | Canonical serialisation of what was signed. |
| `record_hash`, `previous_hash`, `chain_hash` | Char(64) | §11.70. |
| `hash_algorithm` | Char | Recorded so evidence remains interpretable. |
| `reason` | Text | Mandatory for some meanings. |
| `policy_id`, `request_id`, `session_id` | Many2one | `restrict`. |
| `authentication_method` | Selection | `full` / `single` — §11.200(a)(1). |
| `ip_address`, `user_agent` | Char | Execution context. |
| `is_current` | Boolean, computed, not stored | Live comparison against the record. |

### 4.4.2 Constraints

Odoo 19.0 replaced the `_sql_constraints` list with `models.Constraint`
attributes; this is confirmed by the official 19.0 developer tutorial. All SQL
constraints below use that form.

| Model | Constraint | Definition |
|---|---|---|
| meaning | `_code_company_uniq` | `UNIQUE(code, company_id)` |
| policy | `_signature_count_positive` | `CHECK(required_signature_count >= 1)` |
| session | `_user_token_uniq` | `UNIQUE(user_id, token_hash)` |
| log | `_chain_sequence_uniq` | `UNIQUE(company_id, chain_sequence)` |
| log | `_chain_hash_uniq` | `UNIQUE(chain_hash)` |
| log | `_record_hash_length` etc. | `CHECK(char_length(...) = 64)` ×3 |
| log | `_chain_sequence_positive` | `CHECK(chain_sequence > 0)` |

Python constraints: meaning code format; policy model signability, domain
parseability, domain type, transition completeness and field existence; request
target signability; decline reason non-blank.

### 4.4.3 Immutability, in four independent layers

1. **ACL** — no group holds `perm_write` or `perm_unlink` on `ls.signature.log`
   or `ls.signature.attempt`. Asserted by a test that reads `ir.model.access`.
2. **ORM** — `write()` and `unlink()` raise `UserError` unconditionally,
   defeating `sudo()` as well.
3. **PostgreSQL** — `ls_signature_log_immutable_trg`, a `BEFORE UPDATE OR
   DELETE ... FOR EACH ROW` trigger raising an exception. Installed by
   `init()`. Installation is wrapped: a role lacking privileges gets a logged
   warning and the parameter
   `ls_electronic_signature.db_immutability_trigger = absent`, so the fact is
   recorded rather than assumed. `EXECUTE PROCEDURE` is used in preference to
   `EXECUTE FUNCTION` for the widest PostgreSQL compatibility.
4. **Cryptographic** — even a superuser who disables the trigger and edits the
   row is detected, because the chain no longer verifies.

Because the log can never be updated, every value must be correct at insert.
This is why the signing session is registered *before* the signature row is
created, so `session_id` is part of the insert.

### 4.4.4 Chain construction and concurrency

`_prepare_chain_values` takes `pg_advisory_xact_lock(namespace, company_id)`
before reading the current chain head. The lock is transaction-scoped and
released automatically at commit or rollback. Two concurrent signatures in the
same company therefore serialise, and neither can obtain a duplicate sequence
number or a duplicate predecessor. The `UNIQUE(company_id, chain_sequence)`
constraint is the second line of defence should the lock ever be bypassed.

### 4.4.5 Payload canonicalisation

Normative rules, restated from `tools/hashing.py`: mapping with string keys;
keys sorted by code point; separators `,` and `:` with no whitespace;
`ensure_ascii=False` then UTF-8; datetimes to ISO-8601 with naive values read
as UTC; `Decimal` to its string form so binary floating point never influences a
digest; `bytes` rejected outright; unset values normalised to `null`.

Chain digest: `SHA-256(previous_hash + ":" + record_hash)`. The separator
removes any ambiguity between the two fixed-length operands. Genesis previous
hash: 64 ASCII zeroes.

Any change to these rules invalidates every existing digest and is therefore a
change requiring impact assessment.

## 4.5 Security model

Groups: Signer → Viewer → Auditor → Manager, each implying the previous;
Security Unit implies Auditor. Manager deliberately does **not** imply any write
right over evidence — the escalation chain grants breadth of visibility and
configuration authority, never the ability to alter what happened.

Record rules. Global rules restrict every model to `company_ids`. Group rules,
which Odoo combines with OR: a plain Signer sees only their own signatures and
sessions and only requests they raised or must answer; Viewer and above see all.

Signers hold `perm_create` on the log — creating a signature is what signing
means. The resulting privilege is closed by `_force_signer_identity`, which
overwrites `user_id`, `signer_name`, `signer_login` and `signed_at` with
server-side values for any non-elevated call. A regression test asserts that a
crafted create attributing a signature to another user is silently corrected to
the caller.

## 4.6 Injection and input handling

- No SQL is built by string concatenation with user data. Every `cr.execute`
  uses parameter binding. The only interpolated values are the module's own
  constant trigger and function names in `init()`.
- Policy domains are parsed with `ast.literal_eval`, never `eval`. A non-list
  or unparseable domain is refused by a constraint. The static analyser
  explicitly checks for `eval` and reports none.
- Reasons and instructions are stored as `Text` and rendered with `t-out`,
  which escapes. No field uses `t-raw`.
- The raw web session identifier is never stored; only a SHA-256 digest keyed
  with `database.secret`.
- Passwords exist only as a transient wizard field and are never written to the
  log, the attempt record, or the server log.

## 4.7 Performance

| Concern | Treatment |
|---|---|
| Chain head lookup | Single indexed query ordered by `chain_sequence` with `LIMIT 1`. |
| Advisory lock scope | Per company, transaction-scoped; does not block other companies. |
| Indexes | `chain_sequence`, `chain_hash`, `record_hash`, `signed_at`, `res_model`, `res_id`, `user_id`, `company_id`, `name`. |
| Mixin signature lookup | One search for the whole recordset, then grouped in Python; no query per record. |
| `is_current` | Not stored, so never recomputed in bulk by the ORM; evaluated only when read. |
| Chain verification cost | O(n) in signatures per company; runs off-peak in a scheduled action. |

## 4.8 Controllers, services, external API

None. The module adds no HTTP controller and no public RPC service. Every
operation is an ORM method reachable through the standard Odoo external API,
subject to the same access rights as the user interface. This is a deliberate
attack-surface decision: an endpoint that could create a signature outside the
wizard would bypass the control sequence in §3.2.1.

## 4.9 Data, demo and translation

Data (`noupdate="1"`, so an upgrade never overwrites site configuration): five
system parameters, the request sequence, seven signature meanings, three
scheduled actions, three mail templates. Demo: four users, one per role. **No
demonstration signature is supplied** — manufacturing one in a data file would
contradict the control the module exists to provide.

Translation: `i18n/` holds no `.pot` in this delivery. Hand-authoring one would
produce source references that do not match the extracted positions, which is a
defect rather than a deliverable. `i18n/README.md` gives the exact
`odoo-bin --i18n-export` command. Every user-facing string is wrapped in `_()`
or marked translatable, so extraction is complete when run.

## 4.10 JavaScript and OWL

**None, deliberately.** The signing dialog is a standard transient-model form.
Custom front-end code is the least stable surface across Odoo releases and the
most expensive to re-qualify under computer system validation; here it would buy
no control that the server does not already enforce. Any client-side check
would in any case have to be duplicated server-side, since the server is the
only trustworthy enforcement point. This is recorded as an architectural
decision, not an omission.

## Gate

**PASS.** Architecture, dependencies, manifest, models, fields, SQL and Python
constraints, security model, injection handling, performance, data files and
the two "none" decisions (controllers, JavaScript) are specified with reasons.
