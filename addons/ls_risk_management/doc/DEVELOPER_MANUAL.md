# Developer Manual

## 1. Layout

```
ls_risk_management/
├── models/          9 persistent models, 1 abstract mixin, constants
├── wizards/         6 transient models and their views
├── security/        groups, ACLs (35 lines), record rules (9)
├── views/           list, form and search views; menus
├── report/          2 QWeb PDF reports
├── data/            sequences, cron, taxonomy, example matrix
├── demo/            demonstration data
├── tests/           161 tests in 8 modules plus shared fixtures
├── i18n/            offline-generated translation template
├── doc/             this documentation set
├── static_check.py         offline static analyser
├── negative_controls.py    22 fault injections validating the analyser
├── tools_generate_data.py  generates the cross-referenced data XML
└── tools_generate_docs.py  generates the API reference and the .pot
```

## 2. Model map

```
ls.risk.matrix ─┬─ ls.risk.matrix.level   (severity and probability scales)
                └─ ls.risk.matrix.cell    (band + acceptability per pair)
                        ▲
                        │ evaluated against
ls.risk.category ──▶ ls.risk.register ─┬─ ls.risk.assessment
                                       └─ ls.risk.mitigation ──▶ (new risk)
                        ▲
                        │ raised from
ls.risk.fmea ──▶ ls.risk.fmea.line
```

`ls.risk.role.mixin` is inherited by the five models carrying approvals.

## 3. Conventions applied

| Convention | Applied |
|---|---|
| `models.Constraint` for SQL constraints | 22 constraints; `_sql_constraints` is rejected by the static checker |
| `<list>` rather than `<tree>` | Enforced by the static checker |
| `<chatter/>` rather than `<div class="oe_chatter">` | 5 form views |
| `_compute_display_name` rather than `name_get` | 8 models |
| `self.env._()` rather than the bare `_()` | Enforced by the static checker |
| `_read_group` rather than `read_group` | 2 aggregations |
| `res.groups.privilege` with `privilege_id` | `security/ls_risk_security.xml` |
| Complete docstrings with `:param:`/`:return:`/`:raise:` | Every method |

## 4. Extension points

### 4.1 Linking a risk to any record

```python
risk.write({
    "linked_model_id": env["ir.model"]._get("your.model").id,
    "linked_res_id": record.id,
})
```

The display name of the target is deliberately never computed in this module,
so no access rule of the target model is bypassed. `action_open_linked_record`
opens it under the target model's own rules.

### 4.2 Re-parenting the menu under a Quality root

```xml
<record id="menu_ls_risk_root_reparent" model="ir.ui.menu">
    <field name="id" ref="ls_risk_management.menu_ls_risk_root"/>
    <field name="parent_id" ref="your_module.menu_quality_root"/>
</record>
```

### 4.3 Adding a risk type or category

`RISK_TYPES` in `models/constants.py` is a plain list; extend it by
`selection_add` in an inheriting module. Categories are data, so no code
change is needed.

### 4.4 Hooking the workflow

Override any `action_*` method and call `super()`. All of them return `True`
or an action dictionary and operate on multi-record sets.

## 5. What not to do

- **Do not hardcode acceptability thresholds.** They belong on
  `ls.risk.matrix`. ISO 14971:2019 requires the organisation to establish
  them; the module must never assume them.
- **Do not treat `ordinal_index` as a risk measure.** It is the product of two
  ordinal ranks, supplied for sorting only. Acceptability comes from the
  matrix cell. Ordinal values are not on a ratio scale, so their product has
  no metric meaning.
- **Do not add detection to `ls.risk.assessment`.** It is an FMEA construct.
- **Do not weaken the segregation-of-duties checks.** They are the reason the
  approvals are meaningful.

## 6. Tooling

```
python3 static_check.py        # must report no findings
python3 negative_controls.py   # must report 22/22
python3 tools_generate_data.py # regenerate data XML after editing the generator
python3 tools_generate_docs.py # regenerate the API reference and the .pot
```

Never edit `data/ls_risk_category_data.xml`,
`data/ls_risk_matrix_data.xml`, `doc/API_REFERENCE.md` or
`i18n/ls_risk_management.pot` by hand; edit the generator and re-run it.

## 7. Testing

```
odoo-bin -d TESTDB -i ls_risk_management --test-enable \
         --test-tags /ls_risk_management --stop-after-init
```

Tests derive from `tests/common.RiskCommon`, which builds three role-separated
users, a second company, and an approved square matrix whose corner cells
exercise every acceptability branch. Users are created with `new_test_user`
and group **external identifiers**, so the suite does not depend on the name
of the groups field of `res.users`.
