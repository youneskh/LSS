# Developer Manual

## 1. Reading order

1. `docs/00_verification_and_limitations.md` — what is proven and what is not.
2. `docs/04_technical_specification.md` — models and fields.
3. `models/ls_complaint.py` — the state machine and its guards.
4. `docs/api_documentation.md` — the public method surface.

## 2. Code conventions in force

- AGPL-3 header on every file.
- Maximum line length 88, no tabs, no trailing whitespace — enforced by the
  delivered checker.
- Docstring on every class and every method, with `:param:` and `:raises:` where
  relevant.
- Every user-facing string wrapped in `_()`, with named interpolation
  (`%(name)s`) rather than positional.
- `@api.model_create_multi` on every `create` override.
- Constraints raise `ValidationError`; lifecycle refusals raise `UserError`.
- No `sudo()` in production code.
- No `TODO`, `FIXME` or commented-out code — enforced by the checker.

## 3. Extension points

### 3.1 The CAPA bridge — the intended first extension

`ls_complaint` deliberately does not depend on a CAPA module. It exposes:

| Field | Role |
|---|---|
| `capa_required` | The complaint requires a CAPA |
| `capa_justification` | Why |
| `capa_reference` | The identifier of the CAPA record, mandatory before Resolution |

When `ls_capa` exists, write `ls_complaint_capa` depending on both:

```python
class LsComplaint(models.Model):
    _inherit = "ls.complaint"

    capa_id = fields.Many2one(comodel_name="ls.capa.issue", copy=False)

    @api.depends("capa_id")
    def _compute_capa_reference(self):
        for record in self:
            record.capa_reference = record.capa_id.name or False

    def action_create_capa(self):
        """Create a CAPA issue from the complaint and link it."""
        self.ensure_one()
        self._ensure_state(("investigation", "capa_required"), _("Create CAPA"))
        capa = self.env["ls.capa.issue"].create({
            "name": _("From complaint %(name)s", name=self.name),
            "description": self.root_cause_summary or self.description,
        })
        self.capa_id = capa
        return capa
```

Do not modify `ls_complaint` to add the dependency: the bridge module is the
supported pattern.

### 3.2 Extending a selection

```python
class LsComplaintResolution(models.Model):
    _inherit = "ls.complaint.resolution"

    resolution_type = fields.Selection(
        selection_add=[("quarantine", "Market Quarantine")],
        ondelete={"quarantine": "set default"},
    )
```

### 3.3 Adding a precondition to a transition

Override the transition and call `super()` after the additional check:

```python
def action_start_resolution(self):
    """Refuse the resolution while a returned sample is unexamined."""
    for record in self:
        if record.sample_available and not record.sample_received_date:
            raise UserError(_("The returned sample has not been received."))
    return super().action_start_resolution()
```

### 3.4 Extending the closure preconditions

Override `_check_can_close`, which is called both by `action_close` and by
`action_open_close_wizard`, so a single override covers the wizard too.

### 3.5 Changing the freeze whitelist

`POST_CLOSURE_WRITABLE_FIELDS` in `models/ls_complaint.py` lists the fields that
remain writable after closure. Extend it in a subclass rather than editing it,
and record the change: it weakens a control.

## 4. The candidate kanban view — NOT DELIVERED, NOT VERIFIED

No kanban view ships with the module because the Odoo 18+ kanban template API
could not be confirmed offline (risk R-09). If the target instance uses the
`card` template name, the following is a starting point. **Validate it on the
target instance before adding it to the manifest; a wrong kanban architecture
prevents the module from loading.**

```xml
<record id="ls_complaint_view_kanban" model="ir.ui.view">
    <field name="name">ls.complaint.kanban</field>
    <field name="model">ls.complaint</field>
    <field name="arch" type="xml">
        <kanban default_group_by="state">
            <field name="state"/>
            <templates>
                <t t-name="card">
                    <div class="oe_kanban_details">
                        <strong><field name="name"/></strong>
                        <div><field name="summary"/></div>
                        <div><field name="product_id"/></div>
                        <div><field name="severity"/></div>
                    </div>
                </t>
            </templates>
        </kanban>
    </field>
</record>
```

## 5. Running the tests

```bash
odoo-bin -d <db> -i ls_complaint --test-enable --stop-after-init \
         --log-level=test
odoo-bin -d <db> -u ls_complaint --test-tags /ls_complaint --stop-after-init
```

`tests/common.py` provides `_create_complaint`, `_bring_to_investigation`,
`_approve_investigation`, `_add_done_resolution`, `_create_user` and
`_create_lot`. Reuse them rather than duplicating fixtures.

`_create_user` links a user to a group through `res.groups.users` rather than
through the user's groups field, because that field's name is version-sensitive.
`_create_lot` inspects `_fields` before writing product tracking attributes, for
the same reason. Keep both patterns.

## 6. Running the delivered static checks

The two checker scripts used in Phase 8 are delivered in `tools/`:

```bash
python3 tools/static_check.py
python3 tools/extra_check.py
```

Edit the `MODULE` constant at the top of each script to point at the deployed
location. Run `flake8`, `pylint` and `pylint-odoo` in addition as soon as an
environment with network access is available; they were never executed here.

## 7. Model reference summary

| Model | Records | Frozen when |
|---|---|---|
| `ls.complaint` | master record | `state in ('closed', 'cancelled')` |
| `ls.complaint.investigation` | root cause analysis | `state in ('approved', 'rejected')` |
| `ls.complaint.adverse_event` | vigilance | `state == 'closed'` |
| `ls.complaint.resolution` | actions | `state in ('done', 'cancelled')` |
| `ls.complaint.category` | configuration | never |
| `ls.complaint.close.wizard` | transient | — |
| `ls.complaint.cancel.wizard` | transient | — |

## 8. Pitfalls

1. Do not add a business control only in a view. Every view condition here
   mirrors a server-side check; the view is a convenience.
2. Do not store a date-relative flag. `is_overdue` and `is_report_overdue` are
   non-stored with a `search` method for that reason.
3. Do not bypass `action_close` by writing `state` directly: the closure
   preconditions live in the method.
4. Do not hard-code a regulatory deadline. Add a configuration field instead.
5. Do not use `sudo()` to work around a record rule. Fix the rule.
