# ls_capa — Developer Manual

---

## 1. Odoo 19 API notes

Odoo 19 introduced breaking changes in the areas this module uses. Each
was verified against official Odoo 19.0 documentation before coding.

| Area | Odoo 19 | Older |
|---|---|---|
| List view root | `<list>` | `<tree>` |
| Chatter | `<chatter>` element | `<div class="oe_chatter">` |
| Kanban card | `<t t-name="card">` | `<t t-name="kanban-box">` |
| Group category | `privilege_id` → `res.groups.privilege` | `category_id` on `res.groups` |

Using the older form of any of these breaks the module: `<tree>` and
`category_id` raise at load, `kanban-box` silently renders an empty
kanban.

**Open point.** Whether `res.users.groups_id` is renamed to `group_ids`
in Odoo 19 could not be confirmed from official documentation. Secondary
sources report the `groups_id` rename cascading across `ir.actions.*`,
`ir.ui.view` and `ir.ui.menu`. Production code in this module never
references the field. `tests/common.py::_user_groups_field` resolves it
from the model registry at runtime, and the CI workflow probes the Odoo
source to report the actual name. Do not hard-code either variant.

## 2. Layout

```
ls_capa/
├── __manifest__.py
├── models/          capa_category, capa_issue, capa_root_cause,
│                    capa_action, capa_effectiveness
├── wizards/         capa_close_wizard
├── security/        groups, ACLs, record rules
├── data/            sequences, cron, default categories
├── demo/            demonstration data
├── views/           one file per model, plus menus
├── report/          QWeb PDF action and templates
├── tests/           common.py plus seven test modules
└── docs/            this documentation set
```

The layout follows the Odoo 19 coding guidelines: security split into
`ir.model.access.csv`, `<module>_groups.xml` and `<model>_security.xml`;
views split per model and suffixed `_views.xml`; menus extracted to
`<module>_menus.xml`.

## 3. Model map

See `API_REFERENCE.md`, which is generated from the AST by
`docs/gen_api_reference.py` and cannot drift from the code.

```
ls.capa.category ──< ls.capa.issue ──< ls.capa.root_cause
                                   ├─< ls.capa.action >── project.task
                                   └─< ls.capa.effectiveness ──> ls.capa.issue
```

The effectiveness check points back at `ls.capa.issue` through
`new_capa_id` to record follow-up escalation.

## 4. State machine

`CAPA_STATES` in `models/capa_issue.py` is the single source of truth
for statuses. Two helpers implement every transition:

- `_check_transition(expected_states)` raises `UserError` when a record
  is in the wrong source state.
- `_set_state(new_state)` writes the state and posts a chatter note.

Each public `action_*` method calls `_check_transition`, applies its own
gate, then calls `_set_state`. To add a gate, extend the relevant
`action_*` method — never bypass it in a view.

Gates live in the model layer so they apply to RPC and import as well as
the UI.

## 5. Extension points

**Add a field.** Inherit normally:

```python
class LsCapaIssue(models.Model):
    _inherit = "ls.capa.issue"

    my_field = fields.Char(tracking=True)
```

**Add a gate.** Override the transition and call `super()`:

```python
def action_verify(self):
    for record in self:
        if not record.my_field:
            raise UserError(_("My field is required before verifying."))
    return super().action_verify()
```

**Integrate with `ls_qms`.** Do not add the dependency to this module.
Create a bridge module `ls_qms_capa` depending on both, and reparent the
menu there. See architectural decision AD-01 in `README.rst`.

**Trigger a CAPA from another module:**

```python
self.env["ls.capa.issue"].create({
    "title": "...",
    "description": "...",
    "source": "deviation",
    "source_reference": self.name,
    "capa_type": "corrective",
    "severity": "major",
    "owner_id": self.env.user.id,
})
```

## 6. Conventions

- PEP 8, 79-column limit, enforced by `.flake8`.
- Docstrings on every class and method, with `:param:`, `:return:` and
  `:rtype:` on methods. Type information is conveyed this way rather
  than through annotations, consistent with Odoo core style.
- All user-facing strings wrapped in `_()` with named `%(placeholder)s`
  interpolation, never positional or f-string interpolation, so
  translators can reorder.
- `@api.model_create_multi` on every `create` override.
- No raw SQL. No `sudo()` except for reading `ir.config_parameter`.

## 7. Testing

```bash
odoo-bin -d <db> -i ls_capa --test-enable --stop-after-init
```

`tests/common.py` provides `CapaCommon` with fixtures and builders
(`_make_issue`, `_make_root_cause`, `_make_action`,
`_make_effectiveness`) plus `_advance_to_in_progress` and
`_advance_to_verified` for driving the state machine.

Tests are tagged `post_install` and `-at_install` because they depend on
the security groups being loaded.

When adding a feature, add tests for the happy path, each failure mode
of every gate, and the access rights of each affected group.

## 8. Local quality checks

```bash
pre-commit run --all-files
flake8 .
pylint --rcfile=.pylintrc $(find . -name "*.py")
python3 docs/gen_api_reference.py   # after any model change
```

The CI workflow in `.github/workflows/ci.yml` runs all of these plus
installation, the test suite, a 95% coverage threshold and an upgrade
test.
