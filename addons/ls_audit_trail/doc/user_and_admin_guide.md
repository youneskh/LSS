# User and Administrator Guide — `ls_audit_trail`

## For everyone (Viewer)

### Reading the trail

**Audit Trail ▸ Audit Log** lists recorded changes, newest first, filtered to
the last 30 days by default. Each row shows the chain position, the event time
(UTC), the user, the model and record, the operation, and how many fields
changed. Open a row to see, per field, the label, the value before and the value
after the change. Retention-anchor rows are highlighted and show a Retention Run
tab instead of field changes.

Use the search filters for today / last 7 / last 30 days, for a specific
operation, or to see only your own operations. Group by model, user, operation,
entry type or event day.

**Audit Trail ▸ Field Changes** presents the same information one row per changed
field, convenient for scanning a single field across many records.

**Audit Trail ▸ Audit Dashboard** shows the activity as a graph and a pivot.

You see only the chains of the companies you belong to.

## For auditors

### Verifying integrity on demand

**Audit Trail ▸ Integrity ▸ Verify Now** opens a wizard. Choose a scope:

- *Recent window* — the last N days (default 7).
- *Explicit range* — between two dates you set.
- *Complete chain* — everything; note the estimated entry count, as a full
  verification of a large chain takes time.

The wizard recomputes each entry's digests and compares them to the stored
values. The outcome is written to an immutable **Integrity Verification** record,
whether it passes or fails. A failure is a data-integrity finding to be handled
through your deviation process.

### Producing an evidence pack

**Audit Trail ▸ Evidence Packs ▸ New**. Set the company, the date range,
optionally a comma-separated model filter and a set of users, and a purpose.
Press **Generate**. The module runs an integrity verification over the range,
then builds a sealed ZIP containing:

- `audit_entries.json` — the entries with every digest, in canonical JSON;
- `audit_entries.csv` — one row per field change, for a spreadsheet;
- `manifest.json` — the selection, the counts, the SHA-256 of each file, and the
  verification outcome.

The record stores the SHA-256 of the whole archive. Once generated, the pack is
immutable (you can still archive it). Use **Download Archive** to obtain the ZIP,
**Verify Archive Digest** to confirm a stored archive still matches its recorded
digest, and **Print Cover Sheet** for a PDF summary with paper signature lines.

## For administrators

### Deciding what is audited

**Audit Trail ▸ Configuration ▸ Audit Rules**. Create a rule per model:

- Choose the model and the operations to capture.
- Leave **Audited Fields** empty to capture every stored field except the
  technical ones, or list exactly the fields you want.
- Use **Excluded Fields** to keep specific fields out even in all-field mode
  (for example a large or confidential field).
- Record a **Justification** for the scope.

Keep scopes narrow. Every captured field adds volume to the trail, and a
narrower scope is easier to review and to defend.

You cannot audit the audit engine's own models, abstract models or transient
models — the rule form rejects them.

### Configuring retention (on the company)

Open the company form (**Settings ▸ Companies**, or the multi-company selector)
and find **Audit Trail Retention**:

- **Retention (days)** — the minimum age an entry must reach before it may be
  removed. Zero means nothing may ever be removed.
- **Retention Procedure Reference** — the controlled number of your approved
  records-retention procedure.
- **Allow Retention Runs** — you cannot enable this without both a period and a
  procedure reference; the form enforces that.

### Running a retention run

**Audit Trail ▸ Configuration ▸ Retention Run**. The wizard shows the cut-off
derived from the period and how many entries are in scope. To proceed you must
type the exact count and a justification. The run first verifies the chain (it
refuses to proceed on an already-broken chain), writes a retention anchor
capturing what was removed and why, and only then deletes the aged rows. The
surviving chain, anchor included, remains verifiable, and the removal is itself
recorded as evidence. This action is logged to the server log.

## The scheduled integrity check

A scheduled action, **Audit Trail: Verify Integrity**, runs daily and verifies
the recent window (configurable via the `ls_audit_trail.verification_window_days`
system parameter, default 7) of every company chain, recording one verification
per company. If a check fails, the audit administrators are notified and the
failure is written to the server log; the immutable verification record is the
authoritative evidence either way.

## Good practice

- Audit deletions on any model where a removed record would matter.
- To have an auditable record of *why* a stored computed field changed, audit
  the fields it depends on rather than the computed field itself.
- Review integrity verifications periodically, as Annex 11 §9 expects.
- Treat any failed verification as a deviation, not a nuisance.
