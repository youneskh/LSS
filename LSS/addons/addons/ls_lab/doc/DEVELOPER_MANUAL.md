# DEVELOPER MANUAL — `ls_lab`

---

## 1. Odoo 19 conventions this module follows

Every item below was verified against `github.com/odoo/odoo` branch `19.0` during
the build. Evidence is in `API_VERIFICATION_RECORD.md`. Follow them when
extending.

| Do | Not |
|----|-----|
| `<list>` | `<tree>` |
| `<chatter/>` | `<div class="oe_chatter">` |
| `models.Constraint` | `_sql_constraints` |
| `_compute_display_name` | `name_get` |
| `res.users.group_ids` | `groups_id` |
| `ir.ui.menu.group_ids` | `groups_id` |
| `ir.rule.groups` | `group_ids` |
| `res.groups.privilege_id` | `category_id` |
| `stock.lot` | `stock.production.lot` |
| `uom.uom` | free-text unit strings |
| `self.env._()` | bare `_()` import |
| `ir.cron` without `numbercall`/`doall` | either field |

### The search-view `<group>` rule

Odoo 19 ships **no `view.rng`**. It ships one RNG per view type. Search views are
validated; form views are not.

In `common.rng`, `<group>` permits: `position`, `groups`, `colspan`, `rowspan`,
`fill`, `height`, `width`, `name`, `color`, `invisible`, `col`. **Neither
`expand` nor `string`.**

```xml
<!-- search view: bare group, as Odoo 19 core writes it -->
<group>
    <filter name="group_by_state" string="Status" domain="[]"
            context="{'group_by': 'state'}"/>
</group>

<!-- form view: string is fine here, because forms are not RNG-validated -->
<group string="Identification">
    <field name="code"/>
</group>
```

`tools/static_check.py` enforces the allow-list inside search views only.

---

## 2. Module layout

```
ls_lab/
├── models/    10 concrete models + 2 abstract mixins
├── wizard/    3 transient models
├── security/  groups, privilege, record rules, ACL
├── views/     9 view files + menus
├── data/      sequences, scheduled actions
├── report/    2 report actions + 2 QWeb templates
├── tests/     8 suites + shared fixture
├── tools/     static checker, negative control, retrofit scanner, RNG schemas
└── doc/       phase documents and manuals
```

---

## 3. Extension points

### 3.1 Protecting additional fields on approval

`LsLabControlledMixin.write()` reads `_CONTROLLED_FIELDS` from the record, so an
inheriting module extends the protected set without touching the guard:

```python
class LsLabTestMethod(models.Model):
    _inherit = "ls.lab.test_method"

    my_field = fields.Char()

    _CONTROLLED_FIELDS = LsLabTestMethod._CONTROLLED_FIELDS + ("my_field",)
```

### 3.2 Adding a criterion type

Conformity is decided in exactly one place:
`ls.lab.specification_line._evaluate()`. Add the selection value and extend the
method:

```python
class LsLabSpecificationLine(models.Model):
    _inherit = "ls.lab.specification_line"

    criterion_type = fields.Selection(
        selection_add=[("my_type", "My Criterion")],
        ondelete={"my_type": "cascade"},
    )

    def _evaluate(self, result_numeric, result_text, result_boolean):
        self.ensure_one()
        if self.criterion_type == "my_type":
            return "conform" if ... else "non_conform"
        return super()._evaluate(result_numeric, result_text, result_boolean)
```

Return one of `pending`, `conform`, `non_conform`, `informative`. Nothing else
needs changing: the sample verdict, investigation raising and CoA conclusion all
derive from this return value.

### 3.3 Making a model signable

Inherit the signature mixin and implement the target action:

```python
class MyModel(models.Model):
    _inherit = ["ls.lab.signed.mixin", "mail.thread"]

    def _signature_target_action(self):
        return self.action_do_the_thing()
```

Then add the model to `SIGNABLE_MODELS` in `wizard/ls_lab_signature_wizard.py`.
The allow-list is deliberate: it prevents the generic wizard being pointed at
arbitrary models.

### 3.4 Bridging to other suite modules

Cross-module links are free-text by design (`capa_reference`,
`validation_reference`, `instrument_reference`), because declaring a sibling
suite module as a dependency blocks installation when it is absent.

A bridge module is the correct place to add real relations:

```python
class LsLabOos(models.Model):
    _inherit = "ls.lab.oos"

    capa_id = fields.Many2one("ls.capa.issue", string="CAPA")
```

Bridges should depend on **both** modules and ship separately.

---

## 4. Conventions used throughout

- **Business rules are numbered.** Every guard and constraint cites its rule
  (BRU-nn) in the docstring or message. Rules are defined in
  `PHASE3-5_SPECIFICATION_AND_ARCHITECTURE.md` §3.4.
- **Guards raise `UserError`; invariants raise `ValidationError`.** Guards
  express "not now"; constraints express "never".
- **Messages name the record and the reason.** Never a bare "Operation not
  allowed".
- **Actions are ordinary methods**, so they can be overridden.
- **No raw SQL.** Enforced by the static checker.
- **Docstrings on every method**, first line imperative.
- **No commented-out code, no placeholder markers.** Enforced by the checker.

---

## 5. State machines

Each model exposes `_assert_state(expected, action_label)`. Call it first in any
action:

```python
def action_something(self):
    """Do the thing, from the right state only."""
    self._assert_state("reviewed", "Something")
    return self.write({"state": "done"})
```

---

## 6. Scheduled actions

Crons in this module are **notification-only**. If you add one, keep it so: post
messages or create activities, never write a regulated field. This is BRU-29 and
is covered by tests that assert states are unchanged after a cron run.

---

## 7. Testing

```bash
odoo -d <db> -i ls_lab --test-enable --test-tags /ls_lab --stop-after-init
```

The fixture in `tests/common.py` creates five users because most rules under test
are segregation-of-duties rules that a single user cannot exercise. Use
`with_user()` deliberately; a test that passes because everything ran as the
superuser is testing nothing.

---

## 8. Before submitting a change

```bash
python3 tools/static_check.py .          # expect 0 findings
python3 tools/negative_control.py .      # expect 25/25
flake8 . && pylint --load-plugins=pylint_odoo .
```

If you change the checker, add a seeded fault to `negative_control.py` for the
new check. A check with no negative control is a check nobody has verified.
