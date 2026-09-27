# RELEASE NOTES — 19.0.1.0.0

Module: Life Sciences Training Management (`ls_training`)
Platform: Odoo 19.0 Community Edition
Date: July 2026
Status: **Beta — for validation environments only**

---

## Read this before installing

This is a first release that has **never been installed or executed**. It
was developed without access to an Odoo 19 runtime. Before using it
anywhere that matters:

1. Read `doc/verification_notes.md` in full.
2. Install on a scratch database.
3. Run the test suite and fix what fails.

`doc/verification_notes.md` §2 describes the one known API uncertainty that
can block installation, together with the one-line fix.

## What this module does

Manages training and competence for regulated Life Sciences environments:

- **Controlled courses.** Material is versioned and must be approved before
  it can be delivered.
- **Sessions.** Schedule, register attendees in bulk, record presence and
  scores, close in one action.
- **Automatic certification.** Closing a session issues certifications to
  everyone who passed, freezing the course version in force at that moment.
- **Expiry management.** Certifications expire on schedule, statuses
  refresh nightly, and affected employees are emailed inside a configurable
  warning window.
- **Training requirements.** State that a job position, department or named
  employee must hold a course.
- **Training matrix.** See every employee/course cell as valid, expiring,
  expired or not trained. Filter to gaps.
- **Competency assessments.** Evidence that someone can do the job, kept
  separate from evidence that they attended a class.
- **Printable records.** A certificate per qualification, and a one-page
  training record per employee.

## Design decisions you should know about

**Outcomes are derived, not typed.** A trainer records presence and score;
the system derives pass or fail. Nobody can type a result directly, so any
outcome can be reconstructed from its inputs.

**Absence is not failure.** An employee who did not attend stays *Pending*,
and Pending blocks session closure. Remove them from the attendee list and
register them on a later session.

**Certifications cannot be deleted.** Ever, by anyone, including
Managers. Revocation with a written reason is the only withdrawal path.

**Closed sessions are frozen.** After closure the course, dates, trainer,
attendance and scores are permanently immutable. Check before clicking.

**Renewal adds, never overwrites.** A refresher creates a new certification;
the old one remains and lapses on its own date.

## What this module does not do

It does **not** implement FDA 21 CFR Part 11. There is no electronic
signature and no field-level audit trail. Do not represent this module as
Part 11 compliant. See `doc/regulatory_analysis.md` §3.5.

It implements nothing ANPP-specific, because ANPP training-record
requirements could not be verified from official sources. See
`doc/regulatory_analysis.md` §3.4.

Also out of scope in this release: Odoo eLearning integration, links to
controlled SOP documents, training cost management, trainer qualification
enforcement, and survey-based examinations. Each is documented with the
reason and the intended integration point.

## Requirements

| Item | Value |
|------|-------|
| Odoo | 19.0 Community |
| Dependencies | `base`, `mail`, `hr` |
| Extra Python packages | None |
| Custom JavaScript | None |

## Upgrade path

None — this is the first release.

## Known issues

| # | Issue | Workaround |
|---|-------|------------|
| 1 | Test suite never executed | Run it before use |
| 2 | `ir.rule` group field name unverified | Swap to the shipped alternate file if install fails |
| 3 | `_sql_constraints`, `<chatter/>`, `ir.cron` fields, `hr.employee` field locations unverified | Remediation documented per item |
| 4 | Matrix generation is query-heavy on large populations | Bounded at 20 000 lines; narrow the scope |
| 5 | Compliance rate cannot be searched or grouped | Use the matrix wizard |
| 6 | Reminders repeat daily and do not escalate to managers | Reduce cron frequency, or extend |
| 7 | Employees with no linked user see no training data | Populate Related User on every employee |

## Support

Report issues with the Odoo version, the full traceback, and steps to
reproduce.
