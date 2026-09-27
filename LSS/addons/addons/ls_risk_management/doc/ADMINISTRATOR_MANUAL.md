# Administrator Manual

## 1. Security model

Three layers, deliberately independent.

### 1.1 Access rights

`security/ir.model.access.csv`, 35 lines covering all 16 accessible models.
Viewers read; analysts create and edit operational records; managers
additionally maintain configuration. The residual, closure and cancellation
wizards are **manager-only at ACL level**, so an analyst cannot instantiate
them at all.

### 1.2 Record rules

Nine rules in `security/ls_risk_record_rules.xml`, all **global** and all
scoped to the company:

```
['|', ('company_id', '=', False), ('company_id', 'in', company_ids)]
```

No rule specifies groups. This is a deliberate design decision: the name of
the groups field on `ir.rule` in Odoo 19 could not be verified from official
documentation, and guessing it would produce a parse error at installation.
Role separation is delivered by the other two layers instead. See
`VERIFICATION_LOG.md` section 1.2.

`ir.rule.global` is a computed field and is never written.

### 1.3 ORM-level enforcement

Hiding a button does not stop the method being called through the external
API, a server action or an import. Nine workflow methods therefore assert the
caller's role themselves, through `ls.risk.role.mixin._ensure_risk_manager`,
which uses `res.users.has_group` with an external identifier.

Two segregation-of-duties rules are enforced the same way and apply to
everyone including administrators:

| Rule | Method |
|---|---|
| The assessor cannot approve their own assessment | `ls.risk.assessment.action_approve` |
| The implementation verifier cannot verify effectiveness | `ls.risk.mitigation.action_verify_effectiveness` |
| The FMEA facilitator cannot review or approve their own worksheet | `ls.risk.fmea.action_review`, `.action_approve` |

Provision at least two Risk Managers.

---

## 2. Record integrity

| Control | Where |
|---|---|
| Risks cannot be deleted once assessed | `ls.risk.register.unlink` |
| Assessments cannot be deleted once confirmed | `ls.risk.assessment.unlink` |
| Approved assessments reject changes to the estimation | `ls.risk.assessment.write` |
| Verified control measures reject changes to evidence | `ls.risk.mitigation.write` |
| Cancellation always records a reason | All cancel wizards |
| Field-level change history | `mail.thread` tracking on all main models |

Duplication resets the reference, the state and the workflow evidence, so a
copy cannot inherit another record's approvals.

---

## 3. Scheduled action

*Life Sciences Risk: notify overdue risk reviews*, daily, calling
`ls.risk.register._cron_notify_review_due()`. It schedules a To Do activity
for the risk owner where the activity type is available, and otherwise posts a
chatter message. It writes nothing else and returns the number of risks
notified.

`numbercall` and `doall` are deliberately not set; their presence in Odoo 19
could not be verified.

---

## 4. Sequences

| Code | Prefix | Padding |
|---|---|---|
| `ls.risk.register` | `RISK/%(year)s/` | 5 |
| `ls.risk.assessment` | `RA/%(year)s/` | 5 |
| `ls.risk.mitigation` | `RCM/%(year)s/` | 5 |
| `ls.risk.fmea` | `FMEA/%(year)s/` | 4 |

Shipped company-independent. Confirm per-company numbering behaviour during
operational qualification if you need it.

---

## 5. Data retention

Uninstalling deletes every record created by this module. Cascade deletion
applies from a risk to its assessments and control measures, and from an FMEA
worksheet to its failure modes. Export before any uninstall in a regulated
environment.

---

## 6. Performance notes

- Indexed: `state`, `company_id`, `next_review_date`, `current_risk_level`,
  `current_acceptability`, and every foreign key used in a domain.
- Aggregations use `_read_group`; there is no per-record counting loop.
- No raw SQL anywhere; the static checker enforces this.
- The matrix cell lookup is an in-memory filter over a recordset already
  loaded by the ORM prefetch, so it costs no additional query per assessment.

---

## 7. Backup and change control

Treat the approved risk matrix as controlled configuration. Any change to
acceptability criteria changes the evaluation of every future assessment.
Approved matrices are immutable by design; supersede rather than edit, and
record the change under your change control procedure.
