# RELEASE NOTES — `ls_lab` 19.0.1.0.0

**Release date:** 2026-08-07
**Target:** Odoo 19 Community Edition
**Status:** CONDITIONAL PASS — statically verified, not live-executed

---

## Summary

First release of Laboratory Management for the Life Sciences Suite. Delivers QC
laboratory operation from sample receipt to Certificate of Analysis, with
specification-driven result evaluation and a two-phase OOS investigation.

## Highlights

**Result integrity by construction.** Conformity is computed from the approved
specification and is not writable through any view. An analyst can record a
value; an analyst cannot record a verdict.

**Frozen controlled masters.** Approved methods and specifications cannot be
edited, only superseded. A result recorded months ago remains evaluable against
exactly the criteria that applied when it was taken.

**Segregation of duties in the ORM.** The reviewer of a result cannot be its
analyst; the approver of a sample cannot be its reviewer; the closer of an
investigation cannot be its investigator. These are Python constraints, not
hidden buttons.

**Authorisation before retest.** A retest result cannot be created until the
investigation carries a retest authorisation with a written justification and an
authorising user.

## What is new for the suite

This is the first module built with verified access to Odoo 19 source. Several
facts that earlier modules engineered around are now settled, and one defect class
was positively identified — the search-view `<group expand="0" string="...">`
construct that passes offline checking and fails at install. See
`doc/API_VERIFICATION_RECORD.md` and run `tools/retrofit_scan.py` against the
other modules.

## Upgrade notes

None — first release.

## Before production use

1. Install on a non-production Odoo 19 database and record the outcome in
   `doc/TEST_REPORT.md`.
2. Execute the test suite and record pass/fail and coverage.
3. Run `flake8`, `pylint` and `pylint-odoo`.
4. Configure storage conditions, test methods and specifications — none are
   shipped.
5. Read the Part 11 limitation in the README before relying on signatures.
