# Developer Manual

Module: `ls_recall`

---

## 1. Design intent

Two ideas explain most of the code.

**A state is a claim about evidence.** Each forward transition asserts
that the evidence the next phase presupposes already exists — a reason,
traced consignees, a sent communication, planned checks. This is why
transitions live in methods with gates rather than in a status field a
user can set. The state is therefore a factual claim, not a label.

**Finalised records are evidence.** Sent communications, approved
reports and closed actions are refused at `write()`, not merely made
readonly in a view, so an RPC caller is bound by the same rule.

## 2. Extension seams

Override these rather than patching the models:

| Method | Model | Purpose |
|--------|-------|---------|
| `_scan_move_lines` | execution | Change or supplement the source of distribution data. The only place `stock` internals are touched. |
| `_evaluate_closure_gates` | execution | Add or remove a closure check. Returns `[(bool, label), ...]`. |
| `_required_effectiveness_checks` | execution | Change the sampling arithmetic. |
| `_workflow_writable_fields` | execution | Widen what stays writable after finalisation. |
| `_allowed_writes_when_controlled` | plan | Same, for approved plans. |
| `_quantity_precision` | line | Change the float comparison tolerance. |

### Example: adding a closure gate

```python
class LsRecallExecution(models.Model):
    _inherit = "ls.recall.execution"

    def _evaluate_closure_gates(self):
        """Add a check that the CAPA reference is filled."""
        results = super()._evaluate_closure_gates()
        if not self.is_mock:
            results.append(
                (bool(self.capa_reference), self.env._("A CAPA is referenced"))
            )
        return results
```

### Example: tracing from an external distribution system

```python
class LsRecallExecution(models.Model):
    _inherit = "ls.recall.execution"

    def _scan_move_lines(self):
        """Merge ERP movements with the external distribution log."""
        traced, unassigned = super()._scan_move_lines()
        for row in self._fetch_external_shipments():
            key = (row["partner_id"], row["lot_id"])
            entry = traced.setdefault(key, {"quantity": 0.0, "picking_ids": set()})
            entry["quantity"] += row["quantity"]
        return traced, unassigned
```

## 3. Connecting to a suite quality module

The module deliberately does not depend on `ls_qms` or `ls_complaint`
(deviation D-01). To connect it later, write a bridging module that:

1. depends on `ls_recall` and the quality module;
2. re-parents `menu_ls_recall_root` under the quality root menu;
3. adds many2one fields alongside `defect_reference` and
   `capa_reference` and migrates the text values;
4. optionally adds a closure gate requiring the linked CAPA to be open.

None of this requires changing `ls_recall`.

## 4. Conventions used

| Convention | Note |
|------------|------|
| One model per file, named after the model | |
| Selections in `constants.py` | Each annotated `[REG]` with a citation or `[OPS]` |
| `self.env._()` | Rather than importing `_` |
| `@api.model_create_multi` | On every create override |
| Docstrings everywhere | Enforced mechanically by `static_checks.py` |
| Line length ≤ 88 | Enforced for Python only |
| `models.Constraint` | Odoo 19 replacement for `_sql_constraints` |

## 5. Running the checks

```
python3 static_checks.py path/to/ls_recall
```

Validates Python syntax, XML well-formedness, manifest/disk agreement,
view field references against model fields, button methods, XML id
references, the access rights CSV, style and docstrings. It exits
non-zero on any error.

It is not a substitute for `flake8` and `pylint-odoo`; run those too
when you have them.

## 6. Adding a field: checklist

1. Declare it on the model with a docstring-worthy `help`.
2. If it is a selection with a regulatory basis, put the values in
   `constants.py` with the citation.
3. If it must be frozen after a state, add it to the relevant
   restriction set.
4. Add it to the view.
5. Add a test.
6. Run `static_checks.py`.

## 7. Model reference summary

| Model | Order | Inherits | Company field |
|-------|-------|----------|---------------|
| `ls.recall.plan` | `code desc, id desc` | mail.thread, mail.activity.mixin | own |
| `ls.recall.execution` | `decision_date desc, id desc` | mail.thread, mail.activity.mixin | own |
| `ls.recall.line` | `execution_id, partner_id, lot_id` | — | related, stored |
| `ls.recall.communication` | `execution_id, sent_date desc, id desc` | mail.thread | related, stored |
| `ls.recall.effectiveness` | `execution_id, partner_id, attempt_number, id` | — | related, stored |
| `ls.recall.report` | `execution_id, report_date desc, id desc` | mail.thread | related, stored |
