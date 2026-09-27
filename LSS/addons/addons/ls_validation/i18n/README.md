# Translations

This directory intentionally contains no `.pot` or `.po` file.

The translation template must be produced by the Odoo toolchain from the
installed module so that every translatable string, including those generated
by the framework, is exported with the correct references:

```bash
odoo-bin -d <database> -u ls_validation \
    --i18n-export=ls_validation/i18n/ls_validation.pot \
    --modules=ls_validation --stop-after-init
```

Language files are then created from the template, for example:

```bash
msginit -i ls_validation.pot -o fr.po -l fr_FR
```

A template written by hand would be incomplete and would silently diverge from
the source code, which is why none is shipped here.
