# Demonstration scenarios

These scripts create the demonstration records shown in the handbook
screenshots. They drive the **real workflows** of the LS modules (the same
methods as the buttons) with separate demonstration users, so that the
segregation-of-duties controls apply.

They were run once, in file-name order, on a scratch database where the 22 LS
modules had been installed with demonstration data:

```sh
for f in docs/sop_handbook/scenarios/[1-9]*.py; do
  cat docs/sop_handbook/scenarios/00_common.py "$f" | \
    odoo-bin shell -c odoo.conf -d <scratch_db> --no-http
done
```

Never run them on a production database. The users created have the
logins `demo.analyst`, `demo.reviewer`, `demo.manager`, `demo.operator`
and `demo.operator2`, with the login as password.
