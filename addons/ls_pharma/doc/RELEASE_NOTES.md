# Release Notes — ls_pharma 19.0.1.0.0

**Released:** 2026-08-01
**Target:** Odoo 19.0 Community Edition
**Licence:** AGPL-3.0 or later

## What this release is

The pharmaceutical manufacturing module of the Life Sciences Suite. It holds
the batch production and control record that a regulated manufacturer must
prepare, enforces the reviews and separations that stand between a
manufactured batch and a distributed one, and adds the stability,
serialisation and dossier records that surround them.

## What this release is not

**It is not a qualified system, and it does not make anyone compliant.** It
is an engineering artefact ready for qualification by the organisation that
will operate it.

Specifically, and stated plainly because it matters:

- The 121 tests shipped with this release **have never been executed.** The
  build environment had no Odoo runtime and no database.
- **No coverage has been measured.** The 95 per cent target set for this work
  is not demonstrated, and nothing in this documentation claims that it is.
- `flake8`, `pylint` and `pylint-odoo` **were not run**; no network access.
- The module **has never been installed** against a live Odoo 19 instance.
- The two reports **have never been rendered.**

What was verified: every Python file compiles, every XML file is well formed,
and a purpose-built static checker reports no finding across twelve check
families. That checker was itself validated by injecting fifteen deliberate
faults and confirming it caught all fifteen.

## Before you deploy

Work through section 13.5 of `doc/13_validation_report.md`. It lists six
installation qualification activities, twelve operational qualification
activities and six performance qualification activities. The first of them is
to run the test suite and record the result.

## Highlights

**The release decision is permanent.** Once recorded it cannot be edited or
deleted, by anyone, including through `sudo`. A SHA-256 digest over its
values lets an auditor detect later modification. This is deliberate: the
decision is the evidence that the quality unit did its work.

**The separations of duty are in the data layer.** They hold for the API as
well as for the interface, because a control that only exists in a view is
not a control.

**Regulatory citations are traceable, one at a time.** Every provision this
module relies upon was read in a primary source, and
`doc/14_regulatory_traceability_matrix.md` maps each one to the field or
guard that supports it and to the test that exercises it. Where no source was
read, no claim is made — which is why the Algerian corpus appears in this
release as a list of references and nothing more.

**Serial numbers are unpredictable by construction.** They come from
`secrets`, never from a counter, because Article 4 of Regulation (EU) 2016/161
requires that the value not be possible to deduce.

## Known issues

| # | Issue |
|---|---|
| 1 | The pharmaceutical fields do not appear on the standard product and company forms. See deviation D-2. |
| 2 | No kanban view. See deviation D-3. |
| 3 | The demo data is master data only. See deviation D-4. |
| 4 | Four branches of the CTD template are not shipped. See deviation D-5. |
| 5 | The translation template is an offline extraction, not a server export. See deviation D-11. |

## Upgrading

Not applicable; this is the first release.

## Support

The module ships its own static checker so that any site can re-verify it
after a local change:

```bash
python3 ls_pharma/static_check.py ls_pharma
```
