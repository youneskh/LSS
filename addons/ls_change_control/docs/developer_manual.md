# Developer Manual

Module: `ls_change_control` | Odoo 19.0 Community

## 1. Design rules of this module

1. **The state machine is code, not configuration.** States are a fixed `Selection`, not a stage model. An administrator cannot alter a regulated workflow at run time.
2. **Guards live in one place.** `_get_blocking_reasons` is used both by the transition guards and by the `blocking_reasons` field shown to the user. There is never a guard implemented twice.
3. **Workflow writes go through `sudo()`.** In Odoo, `sudo()` sets the superuser flag while keeping the real user on the environment, so message tracking still attributes the change to the person who acted. `env.su` cannot be set from an RPC context, which makes it a reliable gate.
4. **Never gate integrity on the context.** The context is supplied by the client and can be forged. `_check_system_fields` tests `env.su`, never a context key.
5. **No raw SQL.** Nowhere in the module.
6. **No Enterprise dependency.** No Enterprise module, view type or source code.

## 2. Odoo 19 specifics used

| Construct | Note |
|-----------|------|
| `<list>` | The root element of a list view. `<tree>` is the previous name |
| `<chatter/>` | The chatter element. The `oe_chatter` div is obsolete |
| `models.Constraint(definition, message)` | Class attribute replacing `_sql_constraints` |
| `<t t-name="card">` | The root kanban template |
| Inline Python in `invisible`, `readonly`, `required` | `attrs` and `states` were removed |
| `_compute_display_name` | Replaces `name_get` |
| `@api.model_create_multi` | Required on `create` |

`static_check.py` fails the build if any of the obsolete forms reappears.

## 3. Model map

```
ls.change_control.category ──< ls.change_control.approval_template
        │                              │
        │ impact_area_ids (m2m)        │ template of
        ▼                              ▼
ls.change_control.impact_area   ls.change_control.approval
        │                              ▲
        │ assessed in                  │ approval_ids
        ▼                              │
ls.change_control.assessment >── ls.change_control.request ──< ls.change_control.implementation
                                       │
                                       └──< ls.change_control.verification
res.company ── four ls_cc_ configuration fields
```

## 4. Extension points

### 4.1 Electronic signature

`ls.change_control.approval._apply_signature(meaning)` returns the values
written with the decision. Override it to apply a stronger signing procedure
before the decision is recorded.

```python
class Approval(models.Model):
    _inherit = "ls.change_control.approval"

    def _apply_signature(self, meaning):
        values = super()._apply_signature(meaning)
        # Perform the signing procedure here and enrich the values.
        return values
```

Raising an exception in the override cancels the decision entirely, because
the whole transition runs in one transaction.

### 4.2 Additional transition guards

`ls.change_control.request._get_blocking_reasons()` returns the list of
outstanding items. Adding an entry blocks the transition **and** displays the
reason to the user, with no other change.

```python
class Request(models.Model):
    _inherit = "ls.change_control.request"

    def _get_blocking_reasons(self):
        reasons = super()._get_blocking_reasons()
        if self.state == "impact_assessment" and self.gmp_impact \
                and not self.risk_assessment_reference:
            reasons.append(_("A risk assessment reference is required."))
        return reasons
```

### 4.3 Extending the closed selection lists

The approval roles and the action types are deliberately closed so that the
matrix of a site is deterministic. Extend them with `selection_add`.

```python
class ApprovalTemplate(models.Model):
    _inherit = "ls.change_control.approval_template"

    approval_role = fields.Selection(
        selection_add=[("hse", "Health, Safety and Environment")],
        ondelete={"hse": "cascade"},
    )
```

The same addition must be applied to `ls.change_control.approval`.

### 4.4 Behaviour without code

Most of the behaviour is driven by the category and by the company parameters.
Before writing an override, check whether a configuration change achieves the
same result.

## 5. Integration with the rest of the suite

The functional specification lists `ls_qms` and `ls_validation` as dependencies
of this module. Those modules do not exist; the specification describes them as
architectural recommendations. Declaring a dependency on software that does not
exist would make the module uninstallable, so the dependencies are `base`,
`mail` and `hr` only.

Integration is prepared through the following points. Each is a text field
today and becomes a relational field in a bridge module when the target module
exists.

| Point | Field | Target module |
|-------|-------|---------------|
| Risk assessment | `request.risk_assessment_reference` | `ls_risk_management` |
| Corrective action after an ineffective change | `verification.follow_up_reference` | `ls_capa` |
| Evidence of an implementation action | `implementation.evidence_reference` | `ls_document_management` |
| Signature procedure | `approval._apply_signature` | `ls_electronic_signature` |
| Menu placement | `menu_ls_change_control_root` | `ls_qms` |

A bridge module re-parents the root menu with a single override:

```xml
<menuitem id="ls_change_control.menu_ls_change_control_root"
          parent="ls_qms.menu_quality_root"/>
```

## 6. Coding standards applied

| Rule | Enforcement |
|------|-------------|
| Maximum line length 88 characters | `static_check.py` |
| No trailing whitespace, no tabs, final newline | `static_check.py` |
| Docstring on every module, class and public method | `static_check.py` |
| No TODO, FIXME or XXX | `static_check.py` |
| No dead code, no commented out code | Manual review, no occurrence |
| `_description` on every model | `static_check.py` |
| Every model covered by access rights | `static_check.py` |
| Every declared manifest file exists, every XML file is declared | `static_check.py` |
| Every external identifier reference resolves | `static_check.py` |

`static_check.py` is not a substitute for flake8, pylint-odoo and the Odoo test
runner. It performs the checks that are possible without an Odoo runtime.

## 7. Running the checks

```bash
python3 static_check.py ls_change_control

odoo-bin -d <test-db> -i ls_change_control --test-enable \
         --test-tags /ls_change_control --stop-after-init --log-level=test

flake8 --max-line-length=88 ls_change_control
pylint --load-plugins=pylint_odoo -e odoolint ls_change_control
```

The last two require the corresponding packages, which were not installable in
the environment where this module was built.

## 8. Adding a test

Inherit `ChangeControlCommon` from `tests/common.py`, which provides seven
users covering every group, a category with two impact areas and two approval
roles, and helpers to bring a request to any state:
`_create_request`, `_prepare_review`, `_to_impact_assessment`,
`_complete_assessments`, `_grant_approvals`, `_to_approved`,
`_add_implementation`, `_add_verification`.

Tag every class `post_install`, `-at_install`, because the module data must be
fully loaded before the workflow can be exercised.
