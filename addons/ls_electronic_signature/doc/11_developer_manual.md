# Developer Manual

## 1 Making a model signable

```python
from odoo import fields, models

class LsDeviation(models.Model):
    _name = "ls.deviation"
    _description = "Deviation"
    _inherit = ["ls.signature.mixin"]

    # MANDATORY IN PRACTICE. See section 2.
    _ls_signature_field_whitelist = (
        "name", "state", "classification", "root_cause", "disposition",
    )

    name = fields.Char(required=True)
    state = fields.Selection([...])
```

Add to the form view:

```xml
<header>
    <button name="action_ls_sign" type="object" string="Sign" class="btn-primary"/>
    <button name="action_ls_request_signature" type="object" string="Request Signature"/>
</header>
<div class="oe_button_box">
    <button name="action_ls_view_signatures" type="object" class="oe_stat_button"
            icon="fa-pencil-square-o">
        <field name="ls_signature_count" widget="statinfo" string="Signatures"/>
    </button>
</div>
<div class="alert alert-warning" role="alert"
     invisible="ls_signature_count == 0 or ls_signature_current">
    This record changed after its most recent signature.
</div>
```

## 2 Always declare the payload whitelist

If you omit `_ls_signature_field_whitelist`, the mixin derives the payload from
every stored field except audit columns and binary types. That default exists so
the mixin is never undefined, **not** because it is a good choice.

Adding any field to a model that uses the derived payload changes the payload
composition. Every existing signature then recomputes to a different digest,
`is_current` becomes false everywhere at once, and every policy that depended on
those signatures silently stops being satisfied. You will discover it when
production halts.

Rule: **declare the whitelist, and treat changing it as a change requiring
impact assessment.** Adding a field to the whitelist invalidates existing
signatures by design — that is correct behaviour, but it must be a decision, not
an accident.

## 3 What the mixin gives you

| Member | Kind | Purpose |
|---|---|---|
| `ls_signature_ids` | computed M2m | Signatures on this record, chain order. |
| `ls_signature_count` | computed Integer | For the smart button. |
| `ls_last_signature_id` | computed M2o | Most recent signature. |
| `ls_signature_current` | computed Boolean | Whether the latest signature still covers the content. |
| `_ls_signature_enabled` | class attribute | Marker. Policies, requests and the wizard refuse models without it. |
| `_ls_signature_fields()` | method | Ordered payload field names. Override for computed inclusion. |
| `_ls_signature_field_value(name)` | method | Canonical value of one field. Override for special types. |
| `_ls_signature_payload(meaning, signed_at, signer)` | method | The full payload. Override only with strong reason. |
| `_ls_applicable_policies(trigger)` | method | Policies governing this record. |
| `_ls_satisfying_signatures(policy)` | method | Signatures currently satisfying a policy. |
| `_ls_check_policy_satisfied(policy)` | method | Raises `UserError` when short. |
| `action_ls_sign()` / `action_ls_request_signature()` / `action_ls_view_signatures()` | actions | Form buttons. |

## 4 Enforcing a signature from your own code

Transition policies are enforced automatically in `write`. To enforce at a point
the ORM cannot see — inside a button, for example:

```python
def action_release(self):
    """Release the record, requiring the approval signatures first."""
    for record in self:
        for policy in record._ls_applicable_policies():
            record._ls_check_policy_satisfied(policy)
        record.with_context(ls_signature_bypass=True).write({"state": "released"})
    return True
```

`ls_signature_bypass` suppresses the `write` check. Use it **only** after you
have verified satisfaction yourself, as above. Setting it to skip a check you
have not performed removes the control entirely.

## 5 Reproducing the manifestation in a report

21 CFR 11.50(b) requires the manifestation in any human readable form. In every
QWeb report of a signable model:

```xml
<t t-call="ls_electronic_signature.signature_manifestation">
    <t t-set="signatures" t-value="doc.ls_signature_ids"/>
</t>
```

## 6 The canonicalisation contract

`tools/hashing.py` defines the rules normatively. They are a **contract, not an
implementation detail**: changing any of them invalidates every digest ever
computed by this module.

The payload carries `"schema": 1`. A future change must increment it and keep
the old code path, so historical signatures continue to verify under the rules
that produced them. Do not change the rules in place.

Never place binary content in a payload — `canonical_dumps` rejects `bytes`
outright. Reduce an attachment to its own SHA-256 digest and put that digest in
the payload instead.

## 7 The credential adapter

`tools/credentials.verify_password(user, password) -> bool`.

It raises `CredentialApiError` when the host Odoo build exposes an unrecognised
password API. **Never catch that and report it as a wrong password.** Doing so
hides a system defect behind a routine user error and pushes the signer toward a
spurious lockout. The wizard logs it as `system_error`, which is a distinct
outcome in the attempt log precisely so the two are never confused.

The Odoo method behind it is private and its signature has changed across
releases; that is why it is isolated here rather than called from the wizard.

## 8 Things you must not do

| Do not | Because |
|---|---|
| Call `ls.signature.log.create` outside the wizard | You would bypass lockout, identity, authorisation and reason checks. The identity fields are overwritten anyway. |
| Try to `write` or `unlink` a signature | Refused at four independent layers. There is no supported route. |
| Add an HTTP controller that creates signatures | It would bypass the control sequence. The module deliberately has none. |
| Store a password anywhere | Passwords exist only as a transient wizard field. |
| Store a raw session identifier | Only the keyed digest is stored. |
| Use `t-raw` in a template | Use `t-out`, which escapes. |
| Build SQL by concatenation | Every `cr.execute` uses parameter binding. |
| Use `eval` on a domain | Use `ast.literal_eval`, as the policy model does. |

## 9 Extending the module

Adding a meaning or a policy is **data**, not code. Adding an authentication
factor means extending `tools/credentials.py` and adding a value to
`authentication_method`; note that adding a selection value to an append-only
model affects only future rows, which is why the field is a `Selection` and not
a relation.

## 10 Running the tests

```bash
odoo-bin -c odoo.conf -d <db> -i ls_electronic_signature_test \
  --test-enable --test-tags ls_signature --stop-after-init
```

All tests carry the `ls_signature` tag and are `post_install`. Integration tests
requiring a signable model live in `ls_electronic_signature_test`, because a
production module must not carry a model with no business purpose.
