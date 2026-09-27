# Developer Manual

**Module:** `ls_medical_plastics` · **Target:** Odoo 19.0 Community Edition

---

## 1. Directory layout

```
ls_medical_plastics/
├── __init__.py
├── __manifest__.py
├── constants.py                  All selection vocabularies and thresholds
├── README.md
├── models/                       13 model files
├── wizards/                      3 wizards with their views
├── security/                     Groups, 41-line ACL, 12 record rules
├── data/                         Sequences, scrap reasons, scheduled actions
├── views/                        8 view files plus the menu structure
├── report/                       2 report actions, 2 QWeb templates
├── tests/                        Shared fixture plus 9 test modules
├── static/description/           Icon and module description page
└── doc/                          This documentation set
```

---

## 2. Conventions applied

### 2.1 Odoo 19 API

| Convention | Applied |
|---|---|
| `models.Constraint` replaces `_sql_constraints` | Yes, throughout |
| `<list>` replaces `<tree>` | Yes |
| `_compute_display_name` replaces `name_get` | Yes |
| `self.env._()` for translations | Yes |
| `stock.lot` (not `stock.production.lot`) | Yes |
| `@api.model_create_multi` on `create` | Yes |

### 2.2 Centralised vocabularies

Every selection list, threshold and digit specification lives in
`constants.py`. Models, wizards and tests import from it. Adding a value to a
selection is a one-line change in one file.

### 2.3 Percentage fields

`reject_rate` and `recycled_content` hold values from **0 to 100**, not ratios.
They are therefore rendered as plain float fields. The `percentage` widget must
**not** be applied to them: it expects a 0-to-1 ratio and would display a value
a hundred times too small.

---

## 3. Immutability patterns

Three distinct mechanisms are used; do not confuse them.

### 3.1 Append-only readings

`ls.mp.injection_molding.reading` overrides `write` to reject every field
except an explicit allow list, and overrides `unlink` to reject unconditionally.

```python
_SYSTEM_WRITABLE_FIELDS = frozenset({"in_tolerance", "company_id"})
```

The allow list exists because the ORM must be able to write stored computed
fields. Keep it minimal: anything added to it becomes mutable.

`is_superseded` is deliberately **not stored**, because storing it would force
the ORM to write to an append-only record whenever a correction is captured. A
`search` method translates domain lookups onto the inverse One2many instead.

### 3.2 Frozen closed runs

`ls.mp.injection_molding.write` rejects any change once the state is `closed`.
`unlink` permits deletion only in `draft` and `cancelled`.

### 3.3 Criteria snapshotting

`create` on the reading model calls `line._snapshot_values()` and copies the
specification's acceptance criteria onto the reading. Extending the criteria
means extending both `_snapshot_values` and the reading model's frozen fields.

---

## 4. Extension points

The module deliberately depends only on native Odoo modules. Integration with
the wider suite is designed to be added by a bridge module.

| Field | Intended replacement |
|---|---|
| `ls.mp.injection_molding.deviation_reference` (Char) | Many2one to a deviation model |
| `ls.mp.component.specification_reference` (Char) | Many2one to a controlled document |
| `ls.mp.component.drawing_reference` (Char) | Many2one to a controlled document |
| `ls.mp.material.grade.regulatory_reference` (Text) | Structured regulatory references |
| `ls.mp.tool.qualification_date` (Date) | Many2one to a validation protocol |

A bridge module should add the relational field alongside the existing Char
field and migrate the data, rather than replacing it, so no reference is lost.

### 4.1 Adding a monitoring frequency

1. Add the value to `MONITORING_FREQUENCIES` in `constants.py`.
2. If it must be verified before production starts, add it to
   `STARTUP_REQUIRED_FREQUENCIES`.

`_missing_startup_parameters` reads that tuple, so no method changes.

### 4.2 Adding a tool lifecycle state

1. Add the value to `TOOL_STATES`.
2. Add an action method following the existing pattern: validate the source
   state for every record, then write.
3. If production must be blocked in the new state, no change is needed —
   `TOOL_PRODUCTION_STATE` names the single state in which production is
   allowed.

---

## 5. Testing

```bash
odoo -d <database> -i ls_medical_plastics --test-enable --stop-after-init
odoo -d <database> -u ls_medical_plastics --test-tags /ls_medical_plastics
```

Tests derive from `MedicalPlasticsCommon`, which builds a complete moulding
context: five users at different roles, two material grades, a released
component, a four-cavity tool in service and an approved three-parameter
specification.

Users are created with `new_test_user`, which resolves groups by XML
identifier. This avoids depending on the name of the field holding group links
on `res.users`, which could not be verified for Odoo 19.

Helper methods on the fixture: `_create_run`, `_add_material`,
`_capture_startup_readings`, `_run_to_completed`.

**These tests have never been executed.** See `TEST_REPORT.md`.

---

## 6. Static analysis

An offline checker ships alongside the module in `tools/static_check.py`. It
uses only `ast`, `lxml` and the standard library, because the preparation
environment has no network access and therefore no `flake8` or `pylint-odoo`.

It verifies Python syntax, XML well-formedness, manifest completeness and load
order, view field references, XML reference resolution, ACL model coverage and
group references, button method existence, a PEP 8 subset, absence of
placeholder tokens, absence of raw SQL, and report template resolution.

```bash
python3 tools/static_check.py path/to/ls_medical_plastics
```

`tools/negative_control.py` validates the checker itself by injecting sixteen
deliberate faults and asserting that each is detected. **Run it after modifying
the checker.** During development it exposed two checks that silently passed
everything; both were repaired.

The checker lives outside the module directory on purpose: its source contains
the literal marker strings it searches for, so scanning itself would produce
false positives.

### Known blind spots

It cannot resolve fields inside inline sub-views — it skips them rather than
guess — it cannot validate view attribute semantics, and it cannot confirm that
any Odoo API used actually exists in Odoo 19.
