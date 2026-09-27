# DEVELOPER MANUAL

Module: `ls_training`

---

## 1. Orientation

Read in this order:

1. `verification_notes.md` — what is verified and what is not
2. `technical_specification.md` — data model and method inventory
3. `architecture_review.md` §5 — why the training matrix is not a SQL view

The single most important design constraint: **this module was written
without a running Odoo 19 instance.** Five API assumptions are documented
and unverified. Do not assume the code has been proven correct at runtime.

## 2. Layout

```
models/      8 model files, one per model, named after it
wizards/     3 transient models in 2 files
views/       9 view files, one per model plus menus
security/    groups, ACL, record rules (+ documented alternate)
data/        sequences, parameter, cron, mail template
report/      2 QWeb reports and their actions
tests/       9 files, shared fixture in common.py
doc/         phase documentation
```

## 3. Conventions

| Rule | Applied |
|------|---------|
| Line length | ≤ 79 characters |
| Docstrings | Every module, class and method — 264/264 |
| Naming | Models `ls.training.*`; tables `ls_training_*`; fields on `hr.employee` prefixed `ls_training_` |
| Translation | All user-facing exception messages wrapped in `_()` |
| Create overrides | `@api.model_create_multi`, iterate `vals_list` |
| Counters | `_read_group` with `__count`, never per-record `len()` |
| Raw SQL | None in shipped code |
| JavaScript | None |

## 4. Key invariants — do not break these

### 4.1 Attendance outcome is derived, never typed

`ls.training.attendance.result` is computed from `attended`, `score`,
`course.requires_assessment` and `course.pass_score`. Making it writable
would destroy the audit property that an outcome can be reconstructed from
its inputs. If you need a manual override, add a separate justified
override field and keep the derivation intact.

### 4.2 Certifications are append-only

`unlink()` always raises. Renewal creates a new record. `course_version` is
frozen at creation. Do not add an update path that mutates historical
certifications.

### 4.3 Closed evidence is frozen

`ls.training.session.write` blocks header changes when `state == "done"`.
`ls.training.attendance.write` and `unlink` block when the session is done.
These guards are in the ORM overrides, not in the views, so they hold for
RPC and script access too. Keep them there.

### 4.4 Requirement resolution has one implementation

`ls.training.requirement._get_requirements_for_employee` and
`_get_target_employees` are the only places that resolve a population.
Three callers depend on them. Do not duplicate the domain logic.

## 5. Public API

### `ls.training.certification`

```python
_get_expiry_warning_days() -> int
```
Reads `ls_training.expiry_warning_days`. Returns 30 on missing,
non-numeric or negative values.

```python
_prepare_from_attendance(attendance) -> dict
```
Builds certification values from one passing attendance. Override this to
add fields to auto-issued certifications.

```python
_cron_refresh_certification_state() -> int
_cron_send_expiry_reminders() -> int
```
Scheduled entry points. Both return counts, which makes them testable.

### `ls.training.requirement`

```python
_get_target_employees() -> hr.employee recordset       # single record
_get_requirements_for_employee(employee) -> recordset  # @api.model
```

### `ls.training.matrix.wizard`

```python
_get_scope_employees() -> hr.employee recordset
_prepare_matrix_lines(employees) -> list[dict]
```
Override `_prepare_matrix_lines` to add columns to the matrix.

## 6. Extending the module

Create a bridge module depending on `ls_training` and the other party.
Never patch `ls_training` in place.

### Electronic signature on session closure

```python
class LsTrainingSession(models.Model):
    _inherit = "ls.training.session"

    def action_close(self):
        """Require a signature before closing the session."""
        for record in self:
            record._request_signature()   # from ls_electronic_signature
        return super().action_close()
```

### Linking courses to controlled documents

```python
class LsTrainingCourse(models.Model):
    _inherit = "ls.training.course"

    document_id = fields.Many2one(
        comodel_name="ls.document.document",
        string="Controlled Training Material",
    )
```

### Manager escalation on overdue training

```python
class LsTrainingCertification(models.Model):
    _inherit = "ls.training.certification"

    @api.model
    def _cron_escalate_overdue(self):
        """Notify managers of certifications expired beyond tolerance."""
        overdue = self.search([("state", "=", "expired")])
        # group by employee.parent_id and send one digest per manager
        return len(overdue)
```

Register it as a new `ir.cron` in your bridge module's data files.

### Adding a matrix column

```python
class LsTrainingMatrixLine(models.TransientModel):
    _inherit = "ls.training.matrix.line"

    grace_days = fields.Integer(string="Grace Period")


class LsTrainingMatrixWizard(models.TransientModel):
    _inherit = "ls.training.matrix.wizard"

    def _prepare_matrix_lines(self, employees):
        """Add the requirement grace period to each matrix line."""
        values_list = super()._prepare_matrix_lines(employees)
        requirements = self.env["ls.training.requirement"]
        for values in values_list:
            requirement = requirements.browse(values["requirement_id"])
            values["grace_days"] = requirement.grace_days
        return values_list
```

## 7. Testing

Run:

```bash
odoo-bin -c odoo.conf -d <db> -u ls_training \
         --test-enable --test-tags /ls_training --stop-after-init
```

All test classes inherit `tests/common.py::LsTrainingCommon`, which builds
two companies, three employees, one competency, two approved courses and
one session. Helpers:

```python
cls._create_attendance(session, employee, attended=True, score=0.0)
cls._run_session_to_done(session)   # confirm → start → close
```

Tests are tagged `post_install, -at_install` because they need a fully
loaded registry, including record rules.

**The suite has never been executed.** Expect to fix defects on the first
run. Add a regression test for each one.

## 8. Migration considerations

If migrating from a future version:

| Concern | Note |
|---------|------|
| Model names | Stable; no rename planned |
| State selections | Adding a state is safe; removing one requires a migration script |
| `course_version` on certifications | Never recompute this — it is deliberately frozen historical data |
| `state` on certifications | Stored but derived; safe to recompute via the cron method |
| `result` on attendance | Stored but derived; recomputing changes nothing if inputs are intact |
| Record rules | Re-verify the `ir.rule` group field name — see `verification_notes.md` §2 |

## 9. Known technical debt

| Item | Detail |
|------|--------|
| Matrix query pattern | O(employees × courses) searches. Replace with a SQL view once the Odoo 19 `hr` schema is confirmed, keeping `ls.training.matrix.line` as the interface |
| Reminder deduplication | No "last reminded" field; the job re-sends daily |
| Trainer qualification | Not enforced; anyone can be named trainer |
| Segregation of duties | One Manager can both submit and approve a course |
| `.pot` file | Generated by a helper script, not by Odoo's exporter; regenerate before translating |
