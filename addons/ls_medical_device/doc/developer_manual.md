# Developer Manual — `ls_medical_device`

## 1. Layout

```
ls_medical_device/
├── __init__.py, __manifest__.py, hooks.py
├── models/          17 models across 13 modules + constants.py
├── wizards/         2 transient models and their views
├── views/           11 view files + menus.xml
├── report/          3 QWeb reports + report actions
├── security/        groups, ACL csv, record rules
├── data/            sequences, risk classes, evidence sources, section templates
├── demo/            fictitious demonstration records
├── tests/           10 test modules
├── doc/             this documentation set
└── static/description/icon.png
```

## 2. Odoo 19 API decisions applied

| Change | Applied |
|---|---|
| `models.Constraint` replaces `_sql_constraints` | Yes, throughout |
| `<list>` replaces `<tree>` | Yes, in every view |
| `<chatter/>` replaces `<div class="oe_chatter">` | Yes |
| `_compute_display_name` replaces `name_get` | Yes |
| `self.env._()` for translations | Yes |
| `_read_group` replaces `read_group` | Yes |
| `res.groups.privilege` with `privilege_id` | Yes |

### Facts that could not be verified, and how they were engineered around

| Unverified | Mitigation |
|---|---|
| `res.users` groups field name | `user.has_group()` in code; `new_test_user()` in tests |
| `ir.rule` groups field name | Global record rules only; access differentiation via ACL and Python |
| `ir.cron` field set | Created in `post_init_hook` with the value dict filtered against the registry |
| MDR Annex II section 6 title | Shipped as editable template data with the uncertainty documented |

This pattern is deliberate: where a fact could not be confirmed, the code
avoids depending on it rather than guessing.

## 3. Model map

Anchor model `ls.md.device` with one-to-many relations to:

- `ls.md.udi` — UDI assignments
- `ls.md.risk_assessment` → `ls.md.risk_item`
- `ls.md.clinical_evaluation` → `ls.md.pmcf_evaluation`
- `ls.md.technical_file` → `ls.md.technical_file_section`
- `ls.md.ce_marking` → `ls.md.notified_body`
- `ls.md.pms` → `ls.md.pms_report`

Configuration models: `ls.md.device_class`, `ls.md.clinical_evidence_source`,
`ls.md.technical_file_section_template`.

Full field and method inventory: `doc/api_reference.md`, generated from source.

## 4. The controlled-record pattern

Most regulatory models share a pattern worth understanding before extending:

- State: `draft → under_review → approved`, plus `superseded`, `cancelled`
  (`REGULATORY_DOC_STATE_SELECTION`).
- `write()` refuses content changes outside draft, allowing only workflow and
  chatter fields through.
- `unlink()` refuses deletion outside draft; cancellation preserves the record.
- `copy_data()` increments the version and resets approval data.
- `action_approve()` checks the authority and refuses self-approval.

When adding a model to this suite, reuse the pattern rather than reimplementing
it, so the audit behaviour stays uniform.

## 5. Extension points

The module intentionally declares no dependency on other suite modules.
Integrate by inheriting:

```python
class LsMdDevice(models.Model):
    _inherit = "ls.md.device"

    capa_ids = fields.One2many("ls.capa.issue", "device_id", string="CAPA")
```

Suggested integrations:

| Target module | Integration |
|---|---|
| `ls_capa` | Link a periodic report conclusion or an unacceptable residual risk to a CAPA issue |
| `ls_complaint` | Feed complaint counts into the periodic report |
| `ls_document_management` | Replace the free-text evidence reference on documentation sections with a document link |
| `ls_electronic_signature` | Add a signature request to `action_approve` |
| `ls_audit_trail` | Register the controlled models for field-level change capture |
| `ls_risk_management` | Reconcile `ls.md.risk_item` with a suite-wide risk register |

Vigilance reporting under MDR Article 87 is not implemented. The deadlines are
published in `constants.py` (`VIGILANCE_DAYS_SERIOUS_INCIDENT` = 15,
`VIGILANCE_DAYS_PUBLIC_HEALTH_THREAT` = 2,
`VIGILANCE_DAYS_DEATH_OR_DETERIORATION` = 10) for reuse by an integrating
module, so the values are not re-derived.

## 6. Defaults and onchange

`ls.md.pms_report` sets both the report type and the notified body submission
obligation in `create()` as well as in the onchange. An onchange fires only in
the user interface; a record created by the wizard, an import or another
module would otherwise lose the Article 86(2) obligation silently. An explicit
value passed by the caller is never overridden.

Apply the same reasoning when adding derived defaults: if the value carries a
regulatory obligation, it belongs in `create()`, not only in an onchange.

## 7. Static analysis

`check_ls_medical_device.py` performs offline analysis using only the standard
library and `lxml`, because the build environment has no Odoo runtime and no
network access. It checks Python syntax, XML well-formedness, manifest and
disk agreement, package imports, view field and button resolution against the
models, XML ID resolution, ACL coverage, comodel resolution, placeholder
tokens, raw SQL, a PEP 8 subset, docstring presence, `widget="percentage"`
misuse, and the field and action names used in the test package.

The checker is validated by `negative_controls.py`, which injects 16 known
faults into a copy of the module and asserts each is detected. **A checker
that has never failed has not been tested**; run the controls after changing
it.

Limitation: the test-reference check validates *names*, not *semantics*. A
test referencing real fields but asserting a wrong value still passes.

## 8. Coding conventions

- Line length 88; docstrings on every module, class and public method.
- `self.env._()` with named interpolation placeholders.
- Constraints as `models.Constraint`; Python constraints as `@api.constrains`.
- No raw SQL. No `TODO`, `FIXME` or commented-out code.
- Every regulatory value carries a source reference in the comment declaring it.
  If a value cannot be sourced, it is configuration data, not a constant.
