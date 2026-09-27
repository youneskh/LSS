# Audit runtime campaign (revision 3)

Run from the project root, in PowerShell:

    powershell -ExecutionPolicy Bypass -File .\audit_campaign\run_campaign.ps1

Options: `-SkipCoverage` (saves ~45 min), `-Cleanup` (drops all t_c_* / t_ls_* scratch databases at the end).

What it does, all on NEW scratch databases (t_c_*); the production database is only read:

| Step | Covers |
|---|---|
| 1 | List of modules installed in odooClaude_ls_DB (read only) |
| 2 | F-05: install delivery + stock_delivery |
| 3 | Co-installation of the 23 ls_ modules |
| 4 | Per module: install WITH demo data, upgrade (-u) on that data, uninstall |
| 5 | Probe tests (addons/ls_audit_probe): stock workflows plain and audited, F-01, F-03, F-06, F-07, F-09, F-11, F-13, F-14, F-16, F-17, F-24, F-27, F-35, F-36 |
| 6 | Performance of the audit-trail hooks on stock validation; 2-thread concurrency (F-10) |
| 7 | Line coverage of each module's own test suite |

Nothing under addons\ is modified. The probe module is test code only and must never be installed in production.

## Changes made during the 2026-09-25 remediation

See `REMEDIATION_REPORT_2026-09-25.md` (section 7) at the project root.

* The addons path of the campaign uses `/mnt/test-addons` (test-only module
  `ls_electronic_signature_test`) instead of `/mnt/found-addons`, which is no
  longer mounted.
* Four probes were adapted where their set-up encoded the defective
  behaviour (F-01, F-09, F-11, F-27); the assertions that detect the defects
  are unchanged.
* `scripts/perf_concurrency.py` also runs each concurrency test through
  `odoo.service.model.retrying`, the retry loop of the Odoo server, and
  reuses the audit rules of an earlier run (one rule per model, F-38).
* New scripts, all run with `odoo shell` on a scratch database:
  `scripts/esign_concurrency.py` (concurrent electronic signatures, F-10),
  `scripts/compile_reports.py` (compiles every QWeb template of the `ls_*`
  modules) and `scripts/render_reports.py` (renders every `ls_*` report for up
  to three records).
