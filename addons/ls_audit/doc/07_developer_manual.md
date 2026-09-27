# 07 — Developer Manual

---

## 1. Layout

```
ls_audit/
├── __manifest__.py
├── models/          11 persistent models
├── wizards/          3 transient models + their views
├── views/           11 view files + menus
├── security/        groups, ACL csv, record rules
├── data/            sequences, categories, mail templates, crons
├── report/          report actions + QWeb templates
├── demo/            demo data
├── tests/           common fixture + 10 test modules
├── i18n/            translation template
├── static/          icon and description page
└── doc/             this documentation set
```

Manifest load order is dependency order: security → data → wizards → views →
report. Menus load last because they reference actions.

---

## 2. Odoo 19 API changes this module depends on

Verified before use. Getting any of these wrong prevents installation.

| Concern | Odoo ≤18 | Odoo 19 |
|---|---|---|
| Group category | `res.groups.category_id` | `res.groups.privilege_id` → `res.groups.privilege`, which carries `category_id` |
| User groups | `res.users.groups_id` | `res.users.group_ids` |
| List view root | `<tree>` | `<list>`; `view_mode` uses `list,form` |
| Chatter | `<div class="oe_chatter">…` | `<chatter/>` |
| Conditional attributes | `attrs="{'invisible': [...]}"` | `invisible="expression"` directly |
| `ir.rule` groups | `groups` | `groups` — **unchanged** |

Deliberately **not** used because the Odoo 19 behaviour could not be
verified:

- `ir.cron.numbercall` and `doall`. Omitted; the framework default applies.
- The ORM recursion helper (`_check_recursion` / `_has_cycle`). Replaced by an
  explicit ancestor walk in `ls_audit_area.py`, which depends only on
  documented ORM behaviour.
- Kanban view templates. No kanban views are shipped.

When you extend this module, verify version-sensitive APIs before use and
document the check at the call site. That convention is why the module
installs at all.

---

## 3. Architecture

### 3.1 Layering

```
Configuration   type, area, auditor, finding category, checklist
      ↓ referenced by
Workflow        program → schedule → response / finding / report
      ↑ driven by
Wizards         checklist load, finding response, cancel
```

Configuration never depends on workflow. Workflow models reference
configuration read-only, except that `ls.audit.checklist` refuses a reset to
draft once an audit has used it.

### 3.2 Copy-on-load

The single most important design decision.

When a checklist is loaded, `ls.audit.checklist.line.name` is **copied** into
`ls.audit.response.name` rather than related through a foreign key. A related
field would mean that editing a template retroactively changed what a past
audit asked — which would destroy the evidentiary value of the record.

Covered by `test_template_change_does_not_alter_executed_audit`. Do not
"optimise" this into a related field.

### 3.3 Locking

Models with a final state override `write()` and `unlink()`:

```python
allowed_fields = {"active", "message_follower_ids", "message_ids",
                  "activity_ids"}
if not set(vals) <= allowed_fields:
    locked = self.filtered(lambda r: r.state in FINAL_STATES)
    if locked:
        raise UserError(...)
```

The allowance exists so that a closed record can still be archived and
followed. Extend `allowed_fields` only for genuinely non-substantive fields.

### 3.4 Impartiality

Implemented as `@api.constrains`, not as onchange warnings, so they hold
against direct ORM writes, imports and scripts — not just the UI.

| Constraint | Model |
|---|---|
| Team ∩ auditees = ∅ | `ls.audit.schedule._check_auditor_independence` |
| No auditor owns an audited area | `ls.audit.schedule._check_auditor_not_area_owner` |
| Auditee ≠ raiser | `ls.audit.finding._check_auditee_not_raiser` |
| Verifier ≠ auditee | `ls.audit.finding.action_verify_and_close` |
| Preparer ≠ reviewer, ≠ approver | `ls.audit.report` |

The last two are in action methods rather than constraints because they
concern the identity of the acting user (`self.env.user`), which is not a
stored field and so cannot be checked by a constraint.

### 3.5 Searchable computed fields

`is_overdue` is computed and non-stored, with a `_search_is_overdue`
companion so that domains push into SQL. If you add a similar flag, add the
search method too, or list views will load every record into memory.

Signature is `_search_is_overdue(self, operator, value)` with **no**
`@api.model` decorator.

---

## 4. Extending

Create a new module depending on `ls_audit`. Never edit this one.

### 4.1 Adding a field

```python
class LsAuditFinding(models.Model):
    _inherit = "ls.audit.finding"

    capa_id = fields.Many2one("ls.capa.action", string="CAPA")
```

If the field must be writable on a locked record, extend `allowed_fields`
through a `write()` override — and think hard about whether it should be.

### 4.2 Extending a transition

```python
def action_verify_and_close(self):
    result = super().action_verify_and_close()
    # your logic
    return result
```

Call `super()` first so the module's own controls run before yours.

### 4.3 Adding a constraint

```python
@api.constrains("area_ids", "auditor_ids")
def _check_my_rule(self):
    for audit in self:
        if ...:
            raise ValidationError(_("..."))
```

### 4.4 The CAPA bridge

The intended integration point. `ls.audit.finding.capa_reference` is free
text today. A bridge module should add a `Many2one`, keep the text field for
historical records, and extend `action_verify_and_close` to require the linked
CAPA to be closed.

---

## 5. Conventions

| Concern | Convention |
|---|---|
| Models | `ls.audit.<thing>` |
| Files | One model per file, named after it |
| Line length | 79 characters |
| Docstrings | **Every** class and function. 254 of 254 currently |
| Type hints | Not used — Odoo recordsets are not usefully typed; docstrings carry `:rtype:` |
| Translations | `_()` on every user-facing string, with named `%(placeholders)s` |
| XML ids | `<type>_ls_audit_<thing>`, e.g. `view_ls_audit_finding_form` |
| Sequences | `_order` uses stored, indexed fields only |

### 5.1 Do not order by a Selection to get severity

`ls.audit.finding._order` sorts on `category_id`, which resolves through the
comodel's own `_order` of `sequence, name`. Ordering on the `severity`
Selection would sort the stored strings alphabetically — critical,
improvement, major, minor, observation — which is not severity order. The
comment at the `_order` line says so; leave it there.

---

## 6. Testing

`tests/common.py` provides `AuditCommon` with four **distinct** users, so the
fixture satisfies the impartiality constraints. Helpers:

| Helper | Does |
|---|---|
| `_create_audit(**overrides)` | Valid audit in `planned` |
| `_load_checklist(audit, checklist)` | Runs the load wizard |
| `_bring_audit_to_in_progress(audit)` | Load, schedule, start |
| `_create_finding(audit, category, **overrides)` | Valid draft finding |
| `_create_report(audit, **overrides)` | Valid draft report |

All tests are `@tagged("post_install", "-at_install")`.

```bash
odoo-bin -d test_db -i ls_audit --test-enable --test-tags /ls_audit \
         --log-level=test --stop-after-init
```

When you add a control, add a test that proves it **refuses** the invalid
case. A test that only proves the happy path does not test a control.

---

## 7. Offline validation harness

`validate_module.py` (shipped beside the module, not inside it) runs the
checks that are possible without an Odoo installation:

1. Python syntax and docstring coverage.
2. XML well-formedness.
3. Manifest coherence — declared files exist; files on disk are declared.
4. XML identifier resolution, including `ref()` inside `eval`.
5. ACL integrity — header, columns, resolvable models and groups, no
   duplicate id, **every model covered**.
6. PEP 8 subset — line length, tabs, trailing whitespace, final newline, CRLF.
7. Odoo 19 regressions — `<tree>`, `attrs=`, `states=`,
   `res.groups.category_id`, writes to `ir.rule.global`, `res.users.groups_id`.
8. Forbidden markers — TODO, FIXME, XXX.

It is not a substitute for running Odoo. It catches the class of error that
prevents installation, which is the class you cannot otherwise catch offline.

Regenerate the API reference and translation template after any change:

```bash
python3 gen_api_doc.py
python3 extract_pot.py
python3 validate_module.py
```
