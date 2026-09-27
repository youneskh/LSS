# API DOCUMENTATION

Module: `ls_training` · 11 model classes · 124 fields · 88 methods

External access uses Odoo's standard RPC interface. This document lists the
models, their public methods and their contracts.

---

## 1. Models

| Technical name | Type | Purpose |
|----------------|------|---------|
| `ls.training.competency` | Model | Competency master data |
| `ls.training.course` | Model | Course master data with approval lifecycle |
| `ls.training.session` | Model | Scheduled delivery of a course |
| `ls.training.attendance` | Model | One employee's presence and outcome in a session |
| `ls.training.certification` | Model | Issued qualification, append-only |
| `ls.training.competency.assessment` | Model | Assessed competence evidence |
| `ls.training.requirement` | Model | Rule stating who must hold which course |
| `ls.training.matrix.wizard` | TransientModel | Matrix scope and generation |
| `ls.training.matrix.line` | TransientModel | One generated matrix cell |
| `ls.training.session.register.wizard` | TransientModel | Bulk registration |
| `hr.employee` | Inherited | Training tab, counters and compliance |

## 2. Workflow methods

All raise `odoo.exceptions.UserError` when the guard fails.

### `ls.training.course`

| Method | Guard | Effect |
|--------|-------|--------|
| `action_submit_review()` | state = draft | → review |
| `action_approve()` | state = review | → approved |
| `action_set_obsolete()` | state = approved, no open session | → obsolete |
| `action_reset_to_draft()` | state ≠ draft | → draft |
| `action_view_sessions()` | — | returns act_window filtered on the course |
| `action_view_certifications()` | — | returns act_window filtered on the course |

### `ls.training.session`

| Method | Guard | Effect |
|--------|-------|--------|
| `action_confirm()` | state = draft, ≥ 1 attendance | → confirmed |
| `action_start()` | state = confirmed | → in_progress |
| `action_close()` | state = in_progress, no pending outcome | issues certifications, → done |
| `action_cancel()` | state ≠ done | → cancelled |
| `action_reset_to_draft()` | state = cancelled | → draft |
| `action_open_register_wizard()` | — | returns the wizard action |
| `action_view_certifications()` | — | returns act_window |

### `ls.training.certification`

| Method | Guard | Effect |
|--------|-------|--------|
| `action_revoke()` | not already revoked | opens the revocation dialog |
| `action_confirm_revoke()` | `revocation_reason` set | sets `revoked`, status → revoked |

### `ls.training.competency.assessment`

| Method | Guard | Effect |
|--------|-------|--------|
| `action_confirm()` | state = draft, `evidence` set | → confirmed, record becomes read-only |

### `ls.training.attendance`

| Method | Effect |
|--------|--------|
| `action_mark_attended()` | sets `attended = True` |
| `action_mark_absent()` | sets `attended = False`, `score = 0.0` |

## 3. Business methods

### `ls.training.certification`

```python
@api.model
_get_expiry_warning_days() -> int
```
Returns the configured warning window. Falls back to 30 when the parameter
is missing, non-numeric or negative.

```python
@api.model
_prepare_from_attendance(attendance) -> dict
```
Builds the certification values for one passing attendance record.
Overriding point for bridge modules.

```python
@api.model
_cron_refresh_certification_state() -> int
```
Recomputes stored status on all non-revoked certifications. Returns the
count processed.

```python
@api.model
_cron_send_expiry_reminders() -> int
```
Queues one reminder per certification in `expiring` or `expired` status
whose employee has a work email. Returns the count queued.

### `ls.training.requirement`

```python
_get_target_employees() -> hr.employee          # ensure_one
@api.model
_get_requirements_for_employee(employee) -> ls.training.requirement
```

### `ls.training.matrix.wizard`

```python
_get_scope_employees() -> hr.employee
_prepare_matrix_lines(employees) -> list[dict]
action_generate() -> dict                       # act_window
```

### `ls.training.session.register.wizard`

```python
_get_candidate_employees() -> hr.employee
action_register() -> dict                       # act_window back to session
```

## 4. Computed field semantics

| Field | Stored | Depends on |
|-------|--------|-----------|
| `attendance.result` | yes | attended, score, course assessment settings |
| `session.attendee_count` / `passed_count` / `failed_count` | yes | attendance lines and their result |
| `certification.date_expiry` | yes, writable | date_granted, course validity |
| `certification.state` | yes | date_expiry, revoked — **plus today's date, refreshed by cron** |
| `certification.days_to_expiry` | no | date_expiry |
| `assessment.date_next` | yes, writable | date_assessment, competency interval |
| `assessment.is_acquired` | yes | level vs competency minimum |
| `requirement.target_employee_count` | no | job, department, employee, company |
| `hr.employee.ls_training_compliance_rate` | no | requirements and certifications — **date-sensitive** |

`certification.state` is stored but time-dependent. Any integration reading
it must accept that it is accurate as of the last cron run.

## 5. RPC examples

### Create and approve a course

```python
import xmlrpc.client

common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

course_id = models.execute_kw(db, uid, password,
    "ls.training.course", "create", [{
        "name": "GMP Fundamentals",
        "duration_hours": 4.0,
        "validity_months": 12,
        "requires_assessment": True,
        "pass_score": 80.0,
    }])

models.execute_kw(db, uid, password,
    "ls.training.course", "action_submit_review", [[course_id]])
models.execute_kw(db, uid, password,
    "ls.training.course", "action_approve", [[course_id]])
```

### Run a session end to end

```python
session_id = models.execute_kw(db, uid, password,
    "ls.training.session", "create", [{
        "course_id": course_id,
        "date_start": "2026-08-01 08:00:00",
        "date_end": "2026-08-01 12:00:00",
    }])

models.execute_kw(db, uid, password,
    "ls.training.attendance", "create", [{
        "session_id": session_id,
        "employee_id": employee_id,
        "attended": True,
        "score": 92.0,
    }])

for action in ("action_confirm", "action_start", "action_close"):
    models.execute_kw(db, uid, password,
                      "ls.training.session", action, [[session_id]])
```

### Query training gaps

```python
gaps = models.execute_kw(db, uid, password,
    "ls.training.certification", "search_read",
    [[["state", "in", ["expiring", "expired"]]]],
    {"fields": ["employee_id", "course_id", "date_expiry", "state"]})
```

### Read an employee's compliance

```python
data = models.execute_kw(db, uid, password,
    "hr.employee", "read", [[employee_id]],
    {"fields": ["name",
                "ls_training_required_count",
                "ls_training_compliant_count",
                "ls_training_compliance_rate"]})
```

Note: compliance fields are non-stored computes. They can be **read** but
not **searched** or grouped.

## 6. Error behaviour over RPC

| Exception | Raised when |
|-----------|-------------|
| `UserError` | A workflow guard fails, or a forbidden delete/edit is attempted |
| `ValidationError` | A Python constraint fails |
| `IntegrityError` | A SQL constraint fails (duplicate code, reference, or negative capacity) |
| `AccessError` | The user lacks the ACL right or the record is outside their record rules |

Notable RPC-visible behaviours:

- `ls.training.certification.unlink` **always** raises `UserError`.
- Writing `attended` or `score` on attendance of a closed session raises
  `UserError`.
- Creating attendance on a closed or cancelled session raises `UserError`
  **after** the record is created and rolled back — wrap in a savepoint if
  you are batching.

## 7. Report generation

| Report XML ID | Model |
|---------------|-------|
| `ls_training.ls_training_certificate_report_action` | `ls.training.certification` |
| `ls_training.ls_training_employee_record_report_action` | `hr.employee` |

Render via the standard report controller:

```
GET /report/pdf/ls_training.ls_training_certificate_document/<id>
GET /report/pdf/ls_training.ls_training_employee_record_document/<id>
```
