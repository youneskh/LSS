# Administrator Manual

## 1 Responsibilities this module does not discharge

State these in your validation file as organisational controls, because the
software cannot enforce them:

| Requirement | Obligation |
|---|---|
| 21 CFR 11.100(b) | Verify each individual's identity before issuing an account. |
| 21 CFR 11.100(c) | Submit the written certification to the FDA. Configure the binding statement to match it. |
| 21 CFR 11.300(b) | Password aging and periodic review — platform and procedure. |
| 21 CFR 11.300(c) | Loss management for compromised credentials. |
| 21 CFR 11.200(a)(3) | Administration such that misuse requires two-person collaboration. |
| Named accounts | Shared accounts destroy attribution. Software cannot detect them. |

## 2 Roles

| Role | Grants | Notably does not grant |
|---|---|---|
| Signer | Execute signatures; own history; requests | Others' signatures; the security log |
| Viewer | All signatures and requests | Attempts, sessions, integrity checks |
| Auditor | Attempts, sessions, integrity checks | Any write on evidence |
| Manager | Meanings, policies, settings; close sessions | **Any write or delete on any signature or attempt** |
| Security Unit | Receives §11.300(d) alerts | — |

The escalation grants breadth of visibility and configuration authority; it
never grants the ability to alter what happened. Verify after any upgrade:

```sql
SELECT a.name, g.name, a.perm_write, a.perm_unlink
  FROM ir_model_access a
  JOIN ir_model m ON m.id = a.model_id
  LEFT JOIN res_groups g ON g.id = a.group_id
 WHERE m.model IN ('ls.signature.log','ls.signature.attempt');
```
Every `perm_write` and `perm_unlink` must be false. `test_install.py` asserts
this automatically.

## 3 System parameters

| Key | Default | Effect |
|---|---|---|
| `ls_electronic_signature.session_idle_minutes` | 15 | Continuous-period idle timeout. |
| `ls_electronic_signature.max_failed_attempts` | 3 | Lockout threshold. |
| `ls_electronic_signature.lockout_minutes` | 15 | Lockout window. |
| `ls_electronic_signature.credential_api_mode` | `auto` | Password verification convention. |
| `ls_electronic_signature.binding_statement` | empty | Statement shown to signers. |
| `ls_electronic_signature.attempt_isolated_cursor` | `1` | **Must be `1` in production.** |
| `ls_electronic_signature.db_immutability_trigger` | set at install | `installed` or `absent`. Read-only fact. |

**`attempt_isolated_cursor` is the parameter to watch.** The test suite sets it
to `0`. If a production database is ever seeded from a validation database,
verify it is `1`, or a refused attempt will be rolled back with its transaction
and the §11.300(d) evidence lost.

## 4 Scheduled actions

| Action | Interval | Consequence if disabled |
|---|---|---|
| Verify hash chain | Daily | Tampering goes undetected until someone verifies manually. |
| Close idle signing sessions | 15 min | Sessions stay open past the idle timeout, weakening §11.200(a)(1)(ii). |
| Expire overdue requests | Hourly | Requests remain pending past their deadline. |

Treat disabling any of them as a change requiring impact assessment.

## 5 Responding to a failed integrity check

A *failed* result means the recorded signature history is not internally
consistent. Treat it as a suspected data integrity event.

1. **Do not delete the failing record.** It is evidence.
2. Open a deviation.
3. Open the integrity check; note the first divergence and the messages.
4. Determine the cause. The realistic causes, in order of likelihood:
   - a partial or out-of-step database restore (sequence gap);
   - direct database manipulation (the trigger was disabled or bypassed);
   - storage corruption.
5. Confirm whether the trigger is present:
   ```sql
   SELECT tgname, tgenabled FROM pg_trigger
    WHERE tgrelid = 'ls_signature_log'::regclass AND NOT tgisinternal;
   ```
   `tgenabled` must be `O`. A value of `D` means the trigger was disabled
   deliberately, which is itself a finding.
6. Review PostgreSQL logs and the operating system audit trail for the period.
7. Assess the product impact of any signature whose integrity cannot be
   demonstrated.

## 6 Responding to a misuse alert

An alert names the identification code submitted, the authenticated session
user, the outcome, the record, the time and the source address.

| Outcome | Interpretation |
|---|---|
| `identity_mismatch` | Someone tried to sign under another person's code. **Highest concern.** |
| `invalid_password` | Repeated occurrences suggest guessing. Isolated ones are usually typing errors. |
| `not_authorised` | An attempt to apply a meaning or satisfy a policy outside the person's role. |
| `locked_out` | Attempts continued after the threshold. |

Investigate under your security procedure and record the outcome. The attempt
records are permanent and cannot be edited or deleted by anyone.

## 7 Users who leave

**Archive, never delete.** Deletion is refused at database level for any user
who has signed, because reissuing a login would breach 21 CFR 11.100(a).
Archiving stops further signing and leaves every past signature intact and
attributable.

## 8 Backup, restore and retention

The chain spans the whole `ls_signature_log` table. Back up and restore the
database as a unit; restoring that table alone will produce sequence gaps that
verification reports as failures. Run a chain verification immediately after any
restore and file the result.

**Uninstalling drops the signature log and every signature in it.** Where those
are GxP records within a retention period, uninstallation is a
records-destruction event requiring authorisation under your retention
procedure. Export first.

## 9 Upgrade checklist

1. Take a full backup and verify the chain before starting.
2. Upgrade in a validation environment first.
3. Run the test suite; attach the output to the change record.
4. Run OQ-CRED-001 and OQ-VIEW-001 (see `07_test_report.md` §7.6).
5. Confirm the ACL invariant query in §2 still returns no writable row.
6. Confirm the immutability trigger is present and enabled.
7. Confirm `attempt_isolated_cursor` is `1`.
8. Verify the chain again after the upgrade.
