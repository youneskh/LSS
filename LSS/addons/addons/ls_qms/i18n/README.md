# Translations

No translation template is shipped with this module.

A `.pot` file must be produced by the Odoo export, from a database where the
module is installed:

```bash
odoo-bin -d <database> --modules=ls_qms --i18n-export=i18n/ls_qms.pot \
  --stop-after-init
```

A hand written `.pot` would carry source line references that do not
correspond to the source files, which is fabricated data. It is therefore not
provided.
