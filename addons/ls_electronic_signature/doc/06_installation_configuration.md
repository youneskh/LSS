# Installation and Configuration Guide

## 1 Prerequisites

- Odoo **19.0 Community Edition**
- PostgreSQL, with the Odoo database role owning its schema (required to create
  the immutability trigger; installation proceeds without it but records the
  fact — see §4)
- A configured outgoing mail server. **Without one the §11.300(d) notification
  cannot be delivered.** The attempt is still recorded and a warning is logged.
- `wkhtmltopdf`, for the signature certificate PDF

No additional Python packages.

## 2 Installation

```bash
cp -r ls_electronic_signature /path/to/addons/
odoo-bin -c odoo.conf -u base --stop-after-init          # refresh the app list
odoo-bin -c odoo.conf -i ls_electronic_signature --stop-after-init
```

Then, in the interface, activate developer mode and confirm under
**Apps** that the module state is *Installed*.

The test fixture module is installed **only** on validation and development
databases:

```bash
odoo-bin -c odoo.conf -i ls_electronic_signature_test --stop-after-init
```

## 3 Post-installation verification

Run the four checks below and record the outcome in the installation
qualification record.

| # | Check | Expected |
|---|---|---|
| IQ-1 | **Settings → Electronic Signatures → Database Immutability Trigger** | `installed` |
| IQ-2 | `SELECT tgname FROM pg_trigger WHERE tgrelid='ls_signature_log'::regclass AND NOT tgisinternal;` | returns `ls_signature_log_immutable_trg` |
| IQ-3 | **Configuration → Signature Meanings** | seven meanings present |
| IQ-4 | **Settings → Technical → Scheduled Actions**, filter "Electronic Signatures" | three actions, all active |

If IQ-1 reports `absent`, the database role could not create the trigger.
Database-level immutability is then **not** in force. Either grant the privilege
and re-run `-u ls_electronic_signature`, or record the reduced protection as an
accepted risk in the validation file. The ACL, ORM and cryptographic layers
remain active in either case.

## 4 Configuration sequence

### 4.1 Assign roles

**Settings → Users & Companies → Users**, then per user set the *Life Sciences*
role. Preconditions that software cannot enforce and the organisation must
satisfy:

- Every account is **named**. Shared accounts destroy attribution and breach
  21 CFR 11.100(a).
- Identity is verified before an account is issued — 21 CFR 11.100(b).
- Password aging and loss management are operated at platform and procedure
  level — 21 CFR 11.300(b) and (c). This module does not provide them.

At least one user must hold **Security Unit** *and* have an e-mail address, or
the §11.300(d) notification has no recipient.

### 4.2 Record the binding statement

**Settings → Electronic Signatures → Binding Statement.** Enter wording that
matches the certification your organisation has submitted under
21 CFR 11.100(c). The signer must acknowledge it at every signature. Leaving it
empty uses a generic default, which is unlikely to match your certification.

### 4.3 Review the meanings

**Configuration → Signature Meanings.** Seven are supplied, covering the four
examples named in §11.50(a)(3). Restrict a meaning to a group where only
certain roles may apply it — for example, restrict `APPROVED` to Quality
Assurance. Archive rather than delete any meaning you do not use: deletion is
refused once a signature references it.

Multi-company: the supplied meanings belong to the main company only. Create
your own set for each additional company.

### 4.4 Define the policies

**Configuration → Signature Policies.** For each controlled operation:

| Field | Guidance |
|---|---|
| Model | Must inherit the signature mixin, or creation is refused. |
| Trigger | *Field transition* to block a lifecycle step; *Manual* to define expectations without blocking. |
| Controlled Field / Target Value | For example `state` → `released`. |
| Meaning | The meaning that counts toward this policy. |
| Signatures Required | 2 or more for dual control. |
| Distinct Signers | Leave enabled, or one person can satisfy a dual-control policy alone. |
| Authorised Signers | Groups whose members may satisfy the policy. |
| Applicability Domain | Restrict to a subset, e.g. `[('quantity', '>', 100)]`. |
| Require Full Credentials | **Leave enabled** unless you have documented a justification against 21 CFR 11.200(a)(1)(i). |

### 4.5 Tune the controls

| Setting | Default | Guidance |
|---|---|---|
| Continuous Session Timeout | 15 min | Shorter is stricter. Applies only where a policy permits reduced components. |
| Failures Before Lockout | 3 | |
| Lockout Duration | 15 min | |
| Password Verification API | Detect automatically | Change only if qualification test OQ-CRED-001 shows a convention must be pinned. |

## 5 Embedding the manifestation in your reports

21 CFR 11.50(b) requires the manifestation in **any** human readable form. Add
to every QWeb report of a signable model:

```xml
<t t-call="ls_electronic_signature.signature_manifestation">
    <t t-set="signatures" t-value="doc.ls_signature_ids"/>
</t>
```

Omitting this from a report that is printed and filed leaves a §11.50(b) gap
that the module cannot detect for you.

## 6 Backup and restore

The signature chain spans the whole `ls_signature_log` table. Restoring that
table alone from an older backup, or restoring it out of step with the rest of
the database, produces sequence gaps that chain verification will report as a
failure. Back up and restore the database as a unit. A restore is a change
requiring impact assessment.

## 7 Monitoring

| What | Where | Cadence |
|---|---|---|
| Chain verification results | Monitoring → Integrity Checks | Daily; investigate any *failed* result as a suspected data integrity event |
| Refused attempts | Monitoring → Signature Attempts, *Possible Unauthorised Use* | Per procedure |
| Stale signatures | Signature Log, filter `is_current = False` | Before release decisions |
| Overdue requests | Signature Requests, *Overdue* | Per procedure |

## 8 Uninstalling

Uninstalling **drops the signature log and every signature it holds.** Where
those signatures are GxP records subject to a retention period, uninstallation
is a records-destruction event and must be authorised under your record
retention procedure. Export the evidence first.
