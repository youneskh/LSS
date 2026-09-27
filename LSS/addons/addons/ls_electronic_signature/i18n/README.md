# Translations

No `.pot` template is committed to this module, deliberately.

A `.pot` file records the source file and line of every translatable string. A
hand-authored template carries references that do not correspond to the real
extraction positions, and translators and reviewers then work from wrong
locations. That is a defect, not a deliverable.

Generate the template from a database where the module is installed:

```bash
odoo-bin -c odoo.conf -d <database> \
  --i18n-export=i18n/ls_electronic_signature.pot \
  --modules=ls_electronic_signature \
  --stop-after-init
```

Then create a language file:

```bash
cp i18n/ls_electronic_signature.pot i18n/fr.po   # then translate
```

Every user-facing string in the module is wrapped in `_()` or declared on a
field marked `translate=True`, so the extraction is complete.

## Strings that must not be translated casually

- The **binding statement** is configuration, not a translatable literal,
  because its wording must match the certification submitted to the agency under
  21 CFR 11.100(c). Configure it per company and per language deliberately.
- **Signature meaning codes** are stable technical identifiers and are not
  translatable. Only the meaning *name* is.
- Values already recorded in a signature — `meaning_name`, `signer_name` — are
  historical snapshots stored as plain text. Changing a translation never
  changes what a past signature says, which is the intended behaviour.
