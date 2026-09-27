# Translations

No `.pot` template and no `.po` file is delivered.

Generating a translation template requires a running Odoo instance, which was
not available when this module was produced. Rather than hand-write a `.pot`
file that could not be verified against the actual extracted strings, the
generation command is given instead.

## Producing the template

```bash
odoo-bin -c odoo.conf -d <database> -i ls_complaint --stop-after-init
odoo-bin -c odoo.conf -d <database> \
         --i18n-export=ls_complaint/i18n/ls_complaint.pot \
         --modules=ls_complaint --stop-after-init
```

## Adding a language

```bash
cp i18n/ls_complaint.pot i18n/fr.po
# translate fr.po, then
odoo-bin -c odoo.conf -d <database> --i18n-import=i18n/fr.po \
         --language=fr_FR --stop-after-init
```

## What is translatable

- Every Python string passed through `_()`.
- Every `string`, `help`, `placeholder`, `confirm` and `title` attribute in the
  views, and the field labels derived from the models.
- `name` and `description` on `ls.complaint.category`, which carry
  `translate=True` and are therefore translatable **per record**, not only per
  source string.
- The two mail templates, through the standard `mail.template` translation
  mechanism.
