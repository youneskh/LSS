# Release Notes - version 19.0.1.0.0

Module: Life Sciences - Change Control (`ls_change_control`)
Platform: Odoo 19.0 Community Edition
Date: 2026-07-24
Licence: AGPL-3.0 or later

## Summary

First release. The module manages the complete lifecycle of a controlled
change in a regulated life sciences organisation: request, review, impact
assessment, approval, implementation, effectiveness verification and closure.

## What is in this release

* Nine state lifecycle matching section 7.6 of the Life Sciences Suite specification.
* Change categories driving the impact areas to assess, the approval matrix and the deadlines.
* One impact assessment record per impact area, with a mandatory written rationale.
* Approval matrix with 11 named roles, recording for each decision the approver, the date and time in UTC and the meaning of the signature.
* Implementation actions with 12 explicit types and a mandatory evidence reference.
* Effectiveness verification with acceptance criteria defined in advance.
* Change Control Record report in PDF.
* Three daily reminders: pending approvals, late implementations, due verifications.
* Four security groups, 23 access rights lines, 7 record rules with multi-company isolation.
* 14 impact areas and 10 categories delivered as a starting configuration.

## Installation

```bash
odoo-bin -d <database> -i ls_change_control --stop-after-init
```

Full procedure in `docs/installation_guide.md`. Installation alone does not make
the module usable: proceed to `docs/configuration_guide.md`.

## Compatibility

| Item | Value |
|------|-------|
| Odoo | 19.0 Community Edition only |
| Dependencies | `base`, `mail`, `hr` |
| Additional Python packages | None |
| Enterprise modules | None, and none may be required |

## Upgrade

Not applicable: this is the first release. Future upgrades will preserve the
site configuration, because all data files are declared `noupdate`.

## Important notices

### Verification status

**The module was never installed and its 121 tests were never executed.** The
build environment had no Odoo runtime, no database and no network access. What
was verified is 170 static checks with zero error, and the conformance of every
Odoo 19 construct used against the official Odoo documentation.

The module is delivered **ready for qualification, not qualified**. Read
`docs/validation_report.md` before deploying.

### Regulatory compliance

This module **supports** the implementation of a change control process. It
does not achieve, guarantee or certify compliance with any regulatory
framework. Compliance depends on the procedures of the organisation, the
validation of the system in its intended use, the training of personnel and the
quality management system.

### Electronic signatures

The module records the identity, the date and time in UTC and the meaning of
each decision, and makes decisions immutable. It does **not** re-authenticate
the signer at the moment of signing. An organisation subject to the electronic
signature requirements of FDA 21 CFR Part 11 cannot satisfy them with this
module alone.

## Deviations from the suite specification

Five deviations, all stated and justified in `docs/validation_report.md`
section 6. The most significant: the module does not depend on `ls_qms` and
`ls_validation`, because those modules do not exist.

## Next steps for the receiving organisation

1. Installation qualification on a clean Odoo 19.0 Community instance.
2. Execution of the 121 automated tests.
3. Measurement of coverage.
4. Execution of `flake8` and `pylint-odoo`.
5. Operational qualification through the interface.
6. Configuration and its approval by the quality unit.
7. Standard operating procedure and training.
