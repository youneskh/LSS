# Administrator Manual

Module: `ls_supplier_qualification` · Odoo 19 Community Edition
Audience: Application administrator, IT, quality systems administrator

---

## 1. Security model

### 1.1 Groups

| Group | Technical name | Grants |
|-------|----------------|--------|
| Supplier Viewer | `group_ls_supplier_viewer` | Read on every model of the module. |
| Supplier Assessor | `group_ls_supplier_assessor` | Viewer, plus create and write on dossiers, scope, assessments, audits, findings and performance. No delete. No configuration. No approval. |
| Supplier Manager | `group_ls_supplier_manager` | Assessor, plus configuration, delete, approval, status changes and review decisions. |

Groups are cumulative through `implied_ids`. Assign one group per person.

**No group is granted to new users automatically.** This is deliberate: access
to qualification records should be the result of a decision that can be
evidenced, not a side effect of creating a user. Assign groups through
**Settings → Users & Companies → Users**, and record the assignment in your own
user-management procedure.

### 1.2 What each group cannot do

| Attempt | Viewer | Assessor | Manager |
|---------|--------|----------|---------|
| Read qualification records | yes | yes | yes |
| Create or edit a dossier | no | yes | yes |
| Delete a dossier | no | no | yes, and only while it is a draft |
| Create a category, criterion or template | no | no | yes |
| Approve, suspend, disqualify | no | no | yes |
| Edit a colleague's assessment | no | no | yes |
| Write in the signature log | no | no | no |

The last row is not a group setting. **No group holds write, create or unlink
on `ls.supplier.signature`.** Entries are written by the application itself.
There is no interface, and no permission, that lets a person create or alter a
signature entry by hand.

### 1.3 Record rules

Thirteen global multi-company rules restrict every company-scoped model to
`company_id in company_ids`. They carry no group, which makes them global: they
apply to administrators too.

Four ownership rules refine write access for assessors: an assessor may modify
assessments where they are the assessor, and audits where they are the lead
auditor or a team member. Managers hold a parallel unrestricted rule; because
rules of different groups combine with OR, a manager is never blocked by the
assessor rule.

## 2. The signature log

### 2.1 What it holds

One append-only entry per decision, carrying: sequence number, timestamp,
signer, login typed at signing, meaning, justification, the model and id of the
signed record, a JSON snapshot of the signed values, the previous entry's
hash and this entry's SHA-256 hash.

Entries are created when an assessment is completed or reviewed, an audit
report is issued, an audit or a finding is closed, a dossier is approved,
suspended, reinstated or disqualified, and a periodic review is completed.

### 2.2 Verifying integrity

The chain covers all entries of one company in sequence order. Each hash is
computed over the previous hash plus a canonical form of the entry's content,
so altering any entry breaks every hash after it.

Run **Monitoring → Signature Log**, then the *Verify Signature Chain* server
action. A green notification means the chain is consistent. A red one lists the
sequence numbers that do not match.

Run this verification on a defined schedule — for example monthly and before
any inspection — and keep the result. A failure means the database was modified
outside the application; investigate it as a data-integrity incident, not as a
software bug.

### 2.3 Scope limits you must document

The signature log records who, when, what and why, and detects alteration. It
**does not re-authenticate the signer** at the moment of signing: the wizard
asks the signer to retype their own login, which confirms intent within an
already-open session.

If your quality system requires a second identification component at signing,
cover it by other documented means until `ls_electronic_signature` is
available. Practical compensating controls:

* a short session inactivity timeout, so an unattended session cannot be used;
* two-factor authentication at login, enabled in Odoo for the users who approve;
* a written procedure forbidding shared or unattended sessions;
* periodic review of the signature log against the approvals actually decided.

State in your validation documentation which of these you rely on. The module
makes the limit visible in the approval dialog rather than hiding it.

## 3. Scheduled actions

| Action | Frequency | Effect |
|--------|-----------|--------|
| Check approval validity | Daily | Expires elapsed approvals; raises reminder activities and queues e-mails for approvals expiring within the reminder lead time. |
| Check audit and review due dates | Daily | Raises activities for periodic audits and reviews falling due. |
| Check qualified scope validity | Daily | Suspends qualified scope lines whose own validity has elapsed. |

All three are idempotent. Running them twice on the same day changes nothing
the second time: expiry is a one-way transition, and activity creation is
guarded by a duplicate check on the summary text.

If the crons are stopped, approvals stop expiring **in the system**; they do
not stop expiring in reality. Monitor that the Odoo cron worker runs.

## 4. Company configuration

Every setting in **Settings → Supplier Qualification** is stored on
`res.company`. In a multi-company database, set them per company; there is no
inheritance between companies.

Changing performance weights or thresholds affects new evaluations only.
Existing evaluations keep the values frozen on them.

Changing the purchase control level takes effect at the next confirmation. Plan
the move from *Warn* to *Block*: run the *Not Approved* filter on the dossier
list first and clear the backlog.

## 5. Multi-company

| Aspect | Behaviour |
|--------|-----------|
| Dossiers | Belong to one company. One live dossier per supplier per company. |
| Configuration | Categories, criteria and templates belong to one company. |
| Standards | Shared across companies. |
| Sequences | Shared, with no company. Numbering is continuous across companies. |
| Signature log | Per company. Each company has its own chain, verified separately. |
| Partner status fields | Computed for the company of the reading user and deliberately not stored, so one company's status never appears in another. |

## 6. Data retention

The module refuses deletion where a record is evidence:

| Record | Deletable |
|--------|-----------|
| Dossier | Draft only. |
| Assessment | Draft or cancelled only. |
| Audit | Draft or cancelled only. |
| Performance evaluation | Not once confirmed. |
| Periodic review | Not once completed. |
| Signature entry | Never. |

Archiving (`active = False`) is available on dossiers, categories, criteria,
templates and standards. Archive rather than delete.

**Uninstalling the module drops every one of these tables, including the
signature log.** Treat uninstallation as records destruction: export the dossier
reports and the signature log, and take a full backup, before proceeding.

## 7. Backup and restore

Nothing in this module changes standard Odoo backup practice, with two points
worth stating:

* The signature chain is verified in place. A restore from backup restores a
  consistent chain; it does not need re-signing.
* If you restore an older backup over a newer database, signature entries
  created in between are lost, and their absence is not detectable by the chain
  verification, because the chain that remains is internally consistent. Record
  restores in your incident log.

## 8. Monitoring

| What to watch | Where | Why |
|---------------|-------|-----|
| Failed scheduled actions | Settings → Technical → Scheduled Actions | A stopped cron means approvals stop expiring in the system. |
| Signature chain verification | Signature Log → Verify Signature Chain | Detects out-of-application modification. |
| Approvals expiring | Qualification → Expiring Approvals | The operational early warning. |
| Dossiers pending approval | *Pending Approval* filter | Work waiting on a manager. |
| Audits with open findings | *With Open Findings* filter | Audits that cannot be closed yet. |
| Suppliers rated C or D | *Action Required* filter on performance | Suppliers needing intervention. |

## 9. Troubleshooting

| Symptom | Cause | Resolution |
|---------|-------|-----------|
| "Segregation of duties" error on approval | The approver assessed or led the audit on this dossier. | Have another manager approve, or disable the rule per company as a documented decision. |
| "The login you entered does not match" | Typo, or a different user is signed in. | Retype the login of the connected user. |
| Dossier cannot be submitted | A prerequisite is unmet. | Read the blue banner on the form; it lists exactly what is missing. |
| Audit cannot be closed | A finding is still open. | Close every finding first. |
| Purchase order refused | Control level *Block* and the supplier is not approved. | Approve the supplier, or lower the level. |
| A user sees no records | Company mismatch or no group. | Check allowed companies and group assignment. |
| Chain verification fails | The table was modified outside Odoo. | Investigate as a data-integrity incident. Identify who had database access and when. |
| Delivery counters button errors | `purchase_stock` not installed. | Install it, or enter counters manually. |

## 10. Routine administrative tasks

| Task | Frequency |
|------|-----------|
| Verify the signature chain and keep the result | Monthly, and before any inspection |
| Confirm the three scheduled actions ran | Weekly |
| Review the *Expiring Approvals* list | Weekly |
| Review group assignments against your user-management procedure | Quarterly |
| Review configuration (categories, criteria, thresholds) under change control | Annually |
| Export dossier reports for archiving | Per your retention procedure |
