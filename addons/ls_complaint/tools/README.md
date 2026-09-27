# Substitute static analysis

`flake8`, `pylint` and `pylint-odoo` could not be executed when this module was
produced: they are not installed in the build environment and the network is
disabled. These two scripts were written and executed instead, so that the claim
made in `docs/07_static_analysis_report.md` can be reproduced.

They are a **substitute**, not a replacement. Run the three real linters as soon
as an environment with network access is available.

```bash
python3 tools/static_check.py   # style, manifest, refs, ACL, view/field coherence
python3 tools/extra_check.py    # removed-API detection, duplicate ids, t-field checks
```

Both scripts expect the module at `/home/claude/ls_complaint`; edit the `MODULE`
constant at the top of each file to point at the deployed location.

Exit code 0 means no error was found.
