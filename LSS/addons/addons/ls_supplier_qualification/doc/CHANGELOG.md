# Changelog

All notable changes to `ls_supplier_qualification` are recorded here.
The format follows Keep a Changelog; the project uses Odoo version strings.

## 19.0.1.0.1 — 2026-09-25

Remediation of the independent audit of 2026-09-25 (report AUDIT_REPORT_FINAL_2026-09-25.md; details in REMEDIATION_REPORT_2026-09-25.md at the project root).

- F-01: the qualification status shown on contacts and purchase orders is computed with superuser rights; the hidden fields carry `groups=`.
- F-13: the purchase control uses the dossier of the order company; the partner status depends on the company context.
- F-36: `criticality`, `requalification_interval_months` and the wizard fields are precomputed; the static default that overrode the category interval is removed.
- F-24: `_check_company_auto` on template lines. F-28: counters without the stock module and inclusive period end.
- An assessment can be reviewed by a second assessor; adverse review decisions must be justified when the review is completed; the approved-supplier filter accepts the Odoo 19 operators.
- Reports: three templates no longer fail to compile (t-field on table cells, t-field without a field path).
- F-27: the viewer role implies Internal User. F-23: `@api.ondelete` deletion guards. Tests ported (F-40).

## [19.0.1.0.0] — 2026-07-26

First release.

### Added

**Configuration**
- `ls.supplier.standard`: reference framework designations. 13 shipped.
- `ls.supplier.category`: supplier categories carrying the qualification rules
  (criticality, assessment and audit requirements, requalification, audit and
  review intervals). 10 shipped.
- `ls.supplier.criterion`: reusable assessment criteria across 12 domains, with
  weight and mandatory flag. 32 shipped, original wording.
- `ls.supplier.assessment.template` and its lines: questionnaires with their
  own scale, mandatory minimum and Pass/Conditional thresholds. 2 shipped.

**Qualification**
- `ls.supplier.qualification`: the dossier, with a nine-state lifecycle, a
  computed list of unmet prerequisites, a derived risk level, and next audit
  and review dates.
- `ls.supplier.material`: explicit qualified scope with its own validity and a
  four-state lifecycle.

**Evaluation**
- `ls.supplier.assessment` and `ls.supplier.assessment.line`: weighted scoring
  with rules frozen at creation, a mandatory-criterion override forcing Fail,
  mandatory comments on low scores, and a second-person review step.
- `ls.supplier.audit` and `ls.supplier.audit.finding`: an eight-state audit
  workflow and a six-state finding workflow, with severity levels, a response
  deadline derived from a company setting, and closure blocked while any
  finding is open.

**Monitoring**
- `ls.supplier.performance`: four-indicator scorecard with company weights
  frozen on the record and an A–D rating.
- `ls.supplier.review`: periodic review whose decision is written onto the
  dossier.
- `ls.supplier.signature`: append-only decision log with a SHA-256 chain and a
  verification action that detects out-of-application modification.

**Integration**
- `res.company` and `res.config.settings`: governance, purchase control and
  scorecard settings.
- `res.partner`: qualification status exposed on the contact, computed per
  company and searchable.
- `purchase.order`: qualification check at confirmation with three levels and
  an optional qualified-scope check.

**Operations**
- Three daily scheduled actions: approval validity, audit and review due dates,
  qualified-scope validity.
- Three mail templates: approval, expiry warning, audit report issued.
- Three QWeb PDF reports: dossier, assessment, audit.
- Five sequences: SQ, SA, SAU, SP, SR.

**Security**
- Three groups: Supplier Viewer, Supplier Assessor, Supplier Manager.
- 44 access-rights lines; the signature log grants no write to any group.
- 13 global multi-company record rules and 4 ownership refinements.

**Quality**
- 141 automated tests across 14 modules.
- `tools/static_check.py`: 18 offline consistency checks with no dependency
  beyond `lxml`.
- `tools/extract_pot.py`: offline translation extraction, 511 entries.
- 15 documentation files covering the ten delivery phases and the manuals.

### Known limitations

- Signing confirms intent by retyping a login; it does not re-authenticate the
  signer. See `doc/02_regulatory_analysis.md` §2.4.
- The framework mapping is an architectural recommendation, not a verified
  clause-by-clause mapping.
- The published ANPP requirements for supplier qualification could not be
  verified; the module makes no statement about their content.
- Automatic delivery counters require `purchase_stock`; without it the counters
  are entered manually.
- The test suite and the standard linters were not executed in the build
  environment. See `doc/12_test_report.md` §7.1 and
  `doc/13_static_analysis_report.md` §8.1.
