# ADMINISTRATOR MANUAL — `ls_lab`

For system administrators, quality unit staff and validation engineers.

---

## 1. Security architecture

### Groups

Declared in `security/ls_lab_security.xml` under the `res.groups.privilege`
record `ls_lab_privilege`.

```
ls_lab_group_manager  implies  ls_lab_group_reviewer
                      implies  ls_lab_group_analyst
                      implies  ls_lab_group_viewer
```

Assign only the highest applicable group.

### ACL matrix

`security/ir.model.access.csv`, 49 rows. Every model carries a row for all four
groups. `r` = read, `w` = write, `c` = create, `d` = delete.

| Model | Viewer | Analyst | Reviewer | Manager |
|-------|--------|---------|----------|---------|
| storage_condition | r | r | r | rwcd |
| test_method | r | r | r | rwcd |
| specification | r | r | r | rwcd |
| specification_line | r | r | r | rwcd |
| sample | r | rwc | rwc | rwcd |
| test_result | r | rwc | rwc | rwcd |
| oos | r | r | rwc | rwcd |
| stability_study | r | r | rwc | rwcd |
| stability_timepoint | r | r | rwc | rwcd |
| coa | r | r | r | rwcd |

### Record rules

Ten global multi-company rules, one per model with a company scope, plus one
group-scoped rule on samples for the analyst role. Multi-company rules are
**global** so they apply to administrators too.

### Segregation of duties

Enforced at the ORM layer by Python constraints and action guards, not by hiding
buttons. Bypassing the interface does not bypass the rule.

| Rule | Enforcement |
|------|-------------|
| Result reviewer ≠ result analyst | `_check_reviewer_segregation` on `ls.lab.test_result` |
| Sample reviewer ≠ any result analyst | `_check_reviewer_segregation` on `ls.lab.sample` |
| Sample approver ≠ sample reviewer | `_check_approver_segregation` on `ls.lab.sample` |
| OOS closer ≠ investigator | `_check_approver_segregation` on `ls.lab.oos` and the `action_close` guard |

**Staffing consequence.** Completing one sample end to end requires **three
distinct users**. Verify role coverage, including holiday and shift cover, before
go-live. There is no override.

---

## 2. Data integrity controls

| Control | Mechanism |
|---------|-----------|
| Conformity cannot be asserted by a user | `evaluation` is a stored computed field with no editable widget anywhere |
| Approved masters cannot be edited | `write()` guard driven by `_CONTROLLED_FIELDS` |
| Approved specification criteria cannot change | create, write and unlink guards on `ls.lab.specification_line` |
| Reviewed results cannot be changed | `write()` guard on protected value fields |
| Records carrying data cannot be deleted | `unlink()` guards; investigations can never be deleted |
| Retest requires prior authorisation | `create()` guard on `ls.lab.test_result` |
| Every cancellation carries a reason | mandatory wizard field or action guard |
| Change history | `mail.thread` tracking on all seven business models |

**Tracked fields.** Fields declared `tracking=True` produce chatter entries on
change. This is Odoo's message-based history, not a tamper-evident audit trail
with a hash chain. If your validation requires the latter, deploy the suite's
audit trail module and assess whether its coverage extends to these models.

---

## 3. System parameters

Settings → Technical → System Parameters.

| Parameter | Default | Effect |
|-----------|---------|--------|
| `ls_lab.timepoint_notice_days` | `14` | Notice horizon for due stability time points. |
| `ls_lab.method_review_interval_months` | `24` | Age at which an approved method is reported due for review. `0` disables. |

Neither is a regulatory value; both are organisational policy. Changing them
changes only notification behaviour.

---

## 4. Scheduled actions

| Action | Model | Method | Default |
|--------|-------|--------|---------|
| Notify due stability time points | `ls.lab.stability_study` | `_cron_notify_due_timepoints` | daily |
| Notify overdue samples | `ls.lab.sample` | `_cron_notify_overdue_samples` | daily |
| Notify test methods due for review | `ls.lab.test_method` | `_cron_notify_method_review_due` | weekly |

**All three post messages only.** None writes a state or any regulated field.
This is business rule BRU-29 and is covered by tests. Consequences:

- Deactivating them loses notifications, nothing else.
- They cannot corrupt regulated data.
- They are not part of any validated calculation.

The `ir.cron` records declare no `numbercall` and no `doall`; both were removed
from Odoo and are absent in 19.

---

## 5. Sequences

Six sequences, all `noupdate="1"` so customer configuration survives upgrade.

| Code | Prefix |
|------|--------|
| `ls.lab.test_method` | `LAB/MTH/` |
| `ls.lab.specification` | `LAB/SPC/` |
| `ls.lab.sample` | `LAB/SMP/<year>/` |
| `ls.lab.oos` | `LAB/OOS/<year>/` |
| `ls.lab.stability_study` | `LAB/STB/` |
| `ls.lab.coa` | `LAB/COA/<year>/` |

Changing a prefix affects new records only. Existing references are unchanged.

---

## 6. Electronic signature — scope and limitation

**State this plainly to your quality unit before go-live.**

The signature wizard records:

- the signing user;
- a UTC timestamp;
- the record signed;
- the declared meaning (reviewed, approved, issued, authorised).

It does **not**:

- re-authenticate the user at the moment of signing;
- implement two distinct identification components;
- cryptographically bind the signature to the record;
- prevent a signature being applied from an unattended authenticated session.

**FDA 21 CFR Part 11 compliance is not claimed.** Organisations requiring Part 11
signatures must implement re-authentication at platform level and validate it.
The limitation is displayed in the wizard, on the sample and certificate forms,
and printed on the Certificate of Analysis.

---

## 7. Backup and retention

Laboratory records may be subject to retention requirements. Note in particular:

- **Uninstalling deletes every laboratory record.** Export or archive first and
  follow change control.
- Investigations can never be deleted through the interface, by design.
- Cancelled samples are retained, not removed.
- The module implements no automatic purge or archival job.

Retention scheduling is an organisational responsibility outside this module.

---

## 8. Monitoring

| Signal | Where |
|--------|-------|
| Samples awaiting review or approval | Sample search filters |
| Open investigations | OOS action, default filter Open |
| Overdue samples | Sample filter Overdue, and the daily notice |
| Due stability time points | Time point filters, and the daily notice |
| Conformity rates | Laboratory → Reports → Test Result Analysis (pivot and graph) |
| Investigation outcomes | OOS graph by product and final conclusion |

---

## 9. Verification tooling

Run after every change to the module and before every deployment:

```bash
python3 ls_lab/tools/static_check.py ls_lab        # expect 0 findings
python3 ls_lab/tools/negative_control.py ls_lab    # expect 25/25 detected
python3 ls_lab/tools/retrofit_scan.py /path/to/addons
```

The negative control matters: it is what distinguishes a checker that finds
nothing because there is nothing to find from a checker that finds nothing
because it cannot see.

---

## 10. Known operational limitations

| Limitation | Consequence |
|------------|-------------|
| Not live-tested | Install first on a non-production database. |
| Tests unexecuted | Execute and record before production use. |
| No instrument calibration enforcement | A result can be recorded citing an out-of-calibration instrument. Control by procedure. |
| No statistical trend analysis | Out-of-trend determination is manual. |
| No shelf-life extrapolation | Stability data evaluation happens outside the system. |
| Signature is intent-confirmation only | See section 6. |
| Three distinct users required | See section 1. |
