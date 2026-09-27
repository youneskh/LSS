# Life Sciences — Electronic Signatures (`ls_electronic_signature`)

Electronic signatures for Odoo 19 Community Edition, designed to **support**
an organisation's implementation of FDA 21 CFR Part 11 Subpart B and Subpart C.

> **This module does not make any organisation compliant with any regulation.**
> Compliance depends on the organisation's procedures, its computer system
> validation, its training, and its ongoing monitoring. The module supplies
> technical controls that an organisation may cite as part of its own
> compliance case. No certification of any kind is claimed or implied.

## What it does

| Capability | Regulatory driver |
|---|---|
| Records printed name, date and time, and meaning with every signature | 21 CFR 11.50(a) |
| Reproduces those three items in printed and on-screen output | 21 CFR 11.50(b) |
| Binds each signature to the signed content with a SHA-256 hash chain | 21 CFR 11.70 |
| Refuses to reuse or reassign a signer identity; blocks deletion of signers | 21 CFR 11.100(a) |
| Presents a binding statement that the signer must acknowledge | 21 CFR 11.100(c) |
| Requires identification code **and** password to sign | 21 CFR 11.200(a)(1) |
| Permits password-only signing inside one continuous session, when configured | 21 CFR 11.200(a)(1)(i) |
| Forces both components again once the session lapses | 21 CFR 11.200(a)(1)(ii) |
| Refuses a signature executed under another person's identification code | 21 CFR 11.200(a)(2) |
| Logs every attempt and alerts the security unit immediately on refusal | 21 CFR 11.300(d) |
| Locks out an identification code after repeated failures | 21 CFR 11.300(d) |

## Architecture in one paragraph

A signature is an **append-only** row in `ls.signature.log`. It cannot be
modified or deleted through the ORM, by any security group, or by direct SQL —
a PostgreSQL trigger refuses `UPDATE` and `DELETE` on the table. Each row stores
a canonical JSON serialisation of exactly what was signed, the SHA-256 digest of
that serialisation, and a chain digest binding it to the previous signature of
the same company. Removing, inserting or altering an entry is therefore
detectable by walking the chain, which a daily scheduled action does
automatically.

## Making a model signable

```python
class LsDeviation(models.Model):
    _name = "ls.deviation"
    _inherit = ["ls.signature.mixin"]

    # Declare the payload explicitly. An explicit list is stable across
    # upgrades; a derived list changes whenever a field is added and would
    # silently invalidate existing signatures.
    _ls_signature_field_whitelist = ("name", "state", "root_cause", "disposition")
```

Then create a policy under **Electronic Signatures → Configuration → Signature
Policies** to state where signatures are required.

To reproduce the manifestation in a QWeb report:

```xml
<t t-call="ls_electronic_signature.signature_manifestation">
    <t t-set="signatures" t-value="doc.ls_signature_ids"/>
</t>
```

## Installation

Requires Odoo 19.0 Community and PostgreSQL. No Python packages beyond the
Odoo runtime. See `doc/06_installation_configuration.md`.

The companion module `ls_electronic_signature_test` supplies a signable
fixture model and the integration test suite. **Do not install it in
production.**

## Known verification obligations

Two items must be confirmed against the target Odoo 19.0 build before the
module is used in a validated environment. Both are documented in
`doc/13_validation_report.md`:

1. **OQ-CRED-001** — the password verification entry point in `res.users` is a
   private Odoo API whose exact signature could not be verified from official
   documentation for 19.0. The adapter in `tools/credentials.py` detects the
   convention at run time and fails loudly rather than silently denying access.
2. **OQ-VIEW-001** — the `<chatter/>` element and the settings `<app>`/`<block>`
   /`<setting>` elements used in the views must render on the target build.

## Licence

AGPL-3. See `LICENSE`.
