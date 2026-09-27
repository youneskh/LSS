# Developer Manual

Module: `ls_calibration` `19.0.1.0.0`.

## 1. Odoo 19 constructs used

The module targets Odoo 19 only. The following constructs are version
specific and are the ones to adapt on a future migration.

| Construct | Odoo 19 form | Previous form |
|-----------|--------------|---------------|
| Database constraints | `_name = models.Constraint("CHECK(...)", "message")` | `_sql_constraints` list of triples, which no longer works in 19 |
| List views | `<list>` | `<tree>`, renamed in 18 |
| Chatter | `<chatter/>` | `<div class="oe_chatter">`, replaced in 18 |
| View modifiers | `invisible="state != 'draft'"` | `attrs="{'invisible': [...]}"`, removed in 17 |
| Translations | `self.env._("...")` | `from odoo import _`, legacy |
| Record name | `_compute_display_name` | `name_get`, removed in 17 |
| Creation | `@api.model_create_multi` | `@api.model` with a single dict |
| Action mode | `view_mode="list,form"` | `tree,form` |

## 2. Source layout

One model per file, named after the model. The module `__init__.py` imports
`models` and `wizards` only; `tests` is imported by the Odoo test runner.

## 3. Extension points

Extend this module from a separate module. Do not modify it.

| Method | Model | Use |
|--------|-------|-----|
| `_prepare_record_values` | plan | Add values to the records generated from a plan. |
| `_prepare_record_line_values` | plan point | Add values to the lines generated from a test point. |
| `_get_limits` | plan point | Change the computation of the acceptance limits, for instance to add an asymmetric tolerance. |
| `_get_calibration_status` | instrument | Change the status classification. Overriding it changes the compute method, the search method and both scheduled actions at once. |
| `_get_lock_exempt_fields` | record | Add a field that stays writable on an approved record. |
| `_get_recompute_exempt_fields` | record line | Same, on the lines. |
| `_check_ready_for_review` | record | Add a completeness check before submission. |
| `_check_standards_validity` | record | Change the policy on the reference standards. |
| `_get_open_records` | plan | Change what counts as an open record for the generation. |

### Example: link an out-of-tolerance record to a deviation

```python
from odoo import fields, models


class LsCalibrationRecord(models.Model):
    _inherit = "ls.calibration.record"

    deviation_id = fields.Many2one(
        comodel_name="ls.deviation",
        string="Deviation",
    )

    def _check_ready_for_review(self):
        """Require a deviation when the as-found readings are out."""
        super()._check_ready_for_review()
        for record in self:
            if (
                record.as_found_status == "out_of_tolerance"
                and not record.deviation_id
            ):
                raise UserError(
                    self.env._(
                        "A deviation is required on record %s.",
                        record.display_name,
                    )
                )
```

### Example: keep a new field writable after approval

```python
class LsCalibrationRecord(models.Model):
    _inherit = "ls.calibration.record"

    archive_reference = fields.Char()

    @api.model
    def _get_lock_exempt_fields(self):
        """Allow the archive reference to be set after approval."""
        return super()._get_lock_exempt_fields() | {"archive_reference"}
```

## 4. Data integrity design

Three layers, deliberately separated.

| Layer | Enforces | Where |
|-------|----------|-------|
| Database | Uniqueness and value ranges that must never be violated, whatever the entry path | `models.Constraint` |
| ORM | Coherence between records, and immutability of the evidence | `@api.constrains`, `create`, `write`, `unlink` overrides |
| Workflow | Completeness at the moment of a state transition | `action_*` and `_check_*` methods |

A rule is implemented in exactly one layer. Do not duplicate a workflow check
as a constraint: it would block the intermediate states.

### The locking mechanism

`write` on the record compares the keys of `vals` with
`_get_lock_exempt_fields()`. The exempt set contains the message and activity
fields, the one2many to the certificates, and **every stored computed field**.
The stored computed fields are listed because the recomputation engine writes
them, and that write must never be interpreted as a modification of the
evidence. The same reasoning applies to `_get_recompute_exempt_fields` on the
lines.

If you add a stored computed field to one of these models, add it to the
corresponding exempt set, otherwise a recomputation may raise a user error on
an approved record.

## 5. The calibration status

`calibration_status` is computed, not stored, because it depends on the
current date. It is searchable through `_search_calibration_status`, which
reads the candidate instruments and filters them in Python, because the
comparison uses the per-instrument alert lead time.

Consequences for a developer:

* The field can be displayed, filtered and used in an action domain.
* It **cannot** be used in a group by, a pivot axis or an `order`.
* Do not make it stored without also adding a daily recomputation, and
  without accepting that the value is stale between two runs.

## 6. Testing

Nine test modules under `tests/`. `common.py` provides the fixtures: three
users, one instrument, one reference standard and one active plan with two
test points.

`common.py` resolves the name of the users-to-groups many2many field at run
time, because the Odoo 19 rename of `groups_id` to `group_ids` could not be
verified from official documentation. Use `cls._create_user()` rather than
creating users directly.

```
odoo-bin -d <test_db> -i ls_calibration --test-enable --test-tags ls_calibration --stop-after-init
```

Every test class is tagged `post_install` and `-at_install`, because the
tests need the complete registry, the access rights and the reports.

## 7. Static analysis

`tools/static_analysis.py`, delivered beside the module, reproduces the
subset of flake8, pylint-odoo and the OCA hooks that can be implemented with
the standard library: syntax, unused imports, missing docstrings, PEP 8
subset, forbidden markers, Odoo 19 deprecations, XML well-formedness,
manifest completeness, XML identifier resolution and access rights
consistency.

```
python3 tools/static_analysis.py [path/to/ls_calibration]
```

It is a complement to, not a replacement for, flake8 and pylint-odoo, which
must be run in an environment where they can be installed.

## 8. Conventions

* Every class and every method carries a docstring; the static analysis
  enforces it.
* Public methods that a user can trigger are prefixed `action_`.
* Checks are prefixed `_check_`, value builders `_prepare_`, scheduled
  actions `_cron_`.
* No f-string inside a translated message; pass the values as arguments of
  `self.env._`.
* No raw SQL, no `t-raw`, no `sudo()` on business data.
* Maximum line length 88 characters in the Python sources.
