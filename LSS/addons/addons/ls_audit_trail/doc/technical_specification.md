# Technical Specification — `ls_audit_trail`

## 1. Architecture

The module has three architectural parts.

**The interception layer** (`models/base_audit.py`) extends the abstract Odoo
model `base`, from which every model inherits. It overrides `create`, `write`
and `unlink` to capture audited operations. Extending `base` is the supported
mechanism for cross-model behaviour and is used by Odoo's own `web` addon;
monkey-patching `BaseModel` at import time was rejected as not upgrade-safe.

**The engine** (`models/ls_audit_trail_log.py`, `ls_audit_trail_log_line.py`)
snapshots values, writes entries, seals them into the per-company hash chain,
and verifies chains. It owns all serialisation via `tools/serialization.py` and
all constants via `tools/constants.py`.

**The governance surface** — rules (`ls_audit_trail_rule.py`), verifications
(`ls_audit_trail_verification.py`), evidence packs
(`ls_audit_trail_evidence_pack.py`), company configuration (`res_company.py`),
and the two wizards — is what users interact with.

## 2. Performance of the interception layer

Every ORM write in the database passes through the layer. When a model is not
audited, the added cost is: one check of `_abstract`/`_transient`, one membership
test against a frozenset, one `registry.ready` check, and one lookup in a
registry-level `ormcache`. No SQL is issued for an unaudited model. The cache is
invalidated only when a rule is created, written or unlinked.

## 3. Hash chain

- One chain per `company_id`.
- `payload_digest = SHA-256(canonical_json(payload))`, where the payload
  contains every stored, immutable value of the entry including the display
  snapshots, but excludes registry-resolved metadata (field label, field type)
  and any related record's display name.
- `hash_current = SHA-256(payload_digest + "|" + previous_hash_current)`.
- The first entry of a chain uses `GENESIS_DIGEST` (64 zeros) as its previous
  digest.
- Positions are assigned under `pg_advisory_xact_lock(namespace, company_id)`,
  released automatically at transaction end, so two concurrent transactions
  cannot claim the same position.
- `env.flush_all()` is called before reading the chain tail with SQL, so a
  second capture in the same transaction sees the first capture's committed row.

## 4. Immutability

`write` on the log permits only the sealing fields and only while the entry is
unsealed; once `hash_current` is set, every write is refused. `unlink` on the
log and both `write`/`unlink` on the line are refused unconditionally, for every
user including the superuser. Entries are therefore removable only by the
retention wizard, which uses parameterised SQL `DELETE` after writing an anchor.
Keeping the ORM path unconditionally closed means no future code path deletes
entries silently.

## 5. Retention (the only removal path)

Preconditions, all enforced: the company allows retention runs; a retention
period in days is set; a procedure reference is recorded; only `data` entries
older than the period are in scope; the operator confirms the exact count and
provides a justification; and the chain must verify *before* removal. The removed
range is replaced by an `anchor` entry recording the removed positions, their
count, the SHA-256 of their concatenated chain digests, and the justification.
Verification then reconciles the head of a chain against anchors, so an
undocumented head truncation is still detected.

## 6. Value representation

Two representations per captured value (`tools/serialization.py`):

- **technical** — locale-independent, hashed and compared exactly. Relations →
  ids; binary → `sha256:<digest>;bytes:<n>` (content never copied); boolean →
  `true`/`false`.
- **display** — human-readable, shown and exported, never the sole basis of a
  digest but included as a stored snapshot within the payload.

## 7. Declared deviations from the suite specification

Each deviation is deliberate and justified, per the suite's deviation-logging
practice.

1. **Menu placement.** The specification places the audit trail under a
   top-level *Security* menu. Odoo Community has no such top-level menu; the
   nearest location (Settings ▸ Technical ▸ Security) is visible only to system
   administrators and would hide the trail from the viewer and auditor roles,
   who are intentionally not administrators. A dedicated top-level *Audit Trail*
   menu is used instead.

2. **Added models.** The specification lists `ls.audit_trail.log` and
   `ls.audit_trail.evidence_pack`. The implementation adds
   `ls.audit_trail.rule` (configuration must live somewhere and per-model
   rules are the safe way to bound capture), `ls.audit_trail.log.line`
   (field-level tracking requires a child row per field, as the spec's own
   "old value / new value / user / timestamp" feature demands), and
   `ls.audit_trail.verification` (a durable, immutable record of each integrity
   check is itself evidence). Two transient wizards are added for verification
   and retention.

3. **No dependency on other suite modules.** The manifest depends only on
   `base` and `mail`. Declaring a dependency on a suite module that is not
   present would block installation. Cross-module use is achieved by auditing
   any model by name, so no compile-time dependency is needed.

4. **No `_sql_constraints`.** Odoo 19 removed `_sql_constraints`; the module
   uses `models.Constraint`, consistent with the rest of the suite.

## 8. Points that could not be verified for Odoo 19

These were engineered around rather than guessed.

- **`res.users` groups field name** (`group_ids` vs `groups_id`). Not used
  directly: group membership is tested with `user.has_group(...)`, and tests
  build users with `new_test_user(..., groups="<xml_id>")`.
- **`ir.rule` groups field name.** Not used: the multi-company rules are global
  (no group), which is the Odoo convention for company scoping. The computed
  flag marking a rule global is never written and is not asserted by name in a
  test; the *behaviour* is asserted instead.
- **`res.groups` group-classification field.** Not used: no category is assigned
  to the three groups; only `name` and `implied_ids` are set.
- **`ir.cron` optional fields** (historically `numbercall`, `doall`). Not set;
  only fields whose presence is established are written in the cron data.

## 9. Files

- `models/` — the engine, the governance models, the company extension, the
  interception layer.
- `wizards/` — verify and retention wizards.
- `tools/` — `constants.py`, `serialization.py` (no Odoo import; unit-testable).
- `security/` — groups, ACL CSV, multi-company record rules.
- `views/`, `report/`, `data/`, `demo/` — UI, PDF templates, cron/sequence,
  demonstration rule.
- `tests/` — eleven test modules (see `doc/test_report.md`).
- `devtools/static_check.py` — offline static checker (not part of the
  importable module; excluded from the package).
