# Deviation Register

Every departure from the Life Sciences Suite functional specification, from
the master prompt's development framework, or from a common Odoo practice, is
recorded here with its reason and its consequence. A deviation is recorded
whether or not it was avoidable.

## D-1 — No dependency on other suite modules

**Specification says:** `ls_pharma` depends on `ls_qms`, `ls_validation`,
`mrp` and `stock`.

**What was built:** dependencies on `base`, `mail`, `product`, `stock` and
`mrp` only.

**Reason:** neither `ls_qms` nor `ls_validation` was present in the build
environment. Declaring a dependency on a module that is not installed aborts
installation of this one. A module that cannot be installed is of no use to
anybody.

**Consequence:** the quality-system links that those modules would provide
are not present. The discrepancy model carries `external_reference` as the
extension point, and `doc/11_developer_manual.md` shows how a site that has
those modules bridges to them in a small local module.

## D-2 — No inheritance of standard product and company views

**Common practice:** expose new fields by inheriting the standard form.

**What was built:** standalone list, form and search views owned entirely by
this module, reached from Pharmaceutical ▸ Materials ▸ Pharmaceutical
Products and Pharmaceutical ▸ Configuration ▸ Company Settings.

**Reason:** inheriting requires naming an XML identifier owned by another
module. Searching for `product.product_template_form_view`,
`product.product_template_tree_view` and `base.view_company_form` against
Odoo 19 returned only community forum posts from versions 14 to 17, which is
not verification. An unresolved `ref` aborts installation of the whole
module.

**Consequence:** the pharmaceutical fields do not appear on the standard
product and company forms. They remain ordinary fields, so a site that has
verified the identifiers for its own build adds an inheriting view locally
without changing this module.

## D-3 — No kanban view and no JavaScript

**Framework asks for:** dashboards, and JavaScript files among the outputs.

**What was built:** graph and pivot views, and no JavaScript at all.

**Reason:** the Odoo 19 kanban root template API and the Owl component
conventions of this version could not be verified. A broken kanban view
breaks the action that opens it.

**Consequence:** no card-based overview. The pivot and graph views cover the
analytical need; the list views cover the operational one.

## D-4 — Demo data limited to master data

**Framework asks for:** demo data.

**What was built:** two active ingredients and four excipients, and nothing
else.

**Reason:** two independent ones. Every richer record needs an external
identifier that could not be verified, being a demo product or a unit of
measure. And a release decision written as an XML record would bypass the
guards that this module exists to enforce, leaving a decision and a batch in
states that contradict each other.

**Consequence:** a fresh installation with demo data shows master data only.
The full scenario is built instead by the test suite, which creates its
records through the ORM and finds a unit of measure by searching.

## D-5 — Sub-sections of CTD 2.6, 2.7, 4.2 and 5.3 not shipped

**What was built:** 108 template sections covering the five modules, the
sub-structure of 2.3 and the sub-structure of 3.2 down to the fourth level.

**Reason:** the headings of those four branches are defined in ICH M4S and
ICH M4E, which were not consulted. Worse, the two documents that *were*
consulted disagree on 2.7: the granularity table of M4(R4) shows six
sub-sections while M4Q lists five titles. Assigning numbers to titles under
that disagreement would be a guess presented as a fact.

**Consequence:** a regulatory affairs team adds those branches under
Configuration ▸ CTD Section Template. The reason is written into the data
file itself, so it travels with the artefact.

## D-6 — ICH storage conditions limited to the general case

**What was built:** the four general-case conditions of ICH Q1A(R2).

**Reason:** the guideline states the refrigerated, frozen and
semi-permeable-container conditions together with product-specific
qualifications that a data record cannot carry without distorting them.

**Consequence:** a manufacturer adds those conditions as configuration, with
the reference of the guidance it is following.

## D-7 — Cron records omit the call-count fields

**What was built:** `ir.cron` records that set the name, the model, the code,
the user, the interval and the active flag, and nothing else.

**Reason:** the names of the fields governing the number of remaining calls
and the catch-up behaviour in Odoo 19 could not be verified, and a daily job
does not need them.

**Consequence:** none expected. If the target build requires those fields,
the records will still install, because the fields carry defaults.

## D-8 — Global record rules with no group restriction

**What was built:** twenty-two global `ir.rule` records providing
multi-company isolation.

**Reason:** the name of the group field on `ir.rule` in Odoo 19 could not be
verified, and `ir.rule.global` is computed and must never be written
explicitly.

**Consequence:** isolation is by company only. Per-group row filtering, if a
site needs it, is added locally.

## D-9 — `flake8`, `pylint` and `pylint-odoo` not run

**Framework requires:** the module passes all three.

**Reason:** no network access in the build environment, so they could not be
installed.

**Consequence:** the requirement is unmet. A purpose-built checker covers
part of the same ground, and the gap is recorded in the delivery gate and in
the outstanding qualification activities.

## D-10 — Tests written but never executed

**Framework requires:** minimum 95 per cent coverage.

**Reason:** no Odoo runtime and no PostgreSQL server in the build
environment.

**Consequence:** the coverage requirement is unmet and undemonstrable here.
**No coverage figure and no pass rate is claimed anywhere.** Running the
suite is activity OQ-1 in the validation report.

## D-11 — The translation template is not a server export

**What was built:** a 847-message template produced by an offline extractor.

**Reason:** the canonical export needs a running server.

**Consequence:** the template is faithful but may be incomplete. The file
says so in its own header, and the developer manual gives the command to
regenerate it from a live instance.

## D-12 — Documentation as a phase-gate set rather than an OCA `readme/`

**Common practice:** OCA modules ship fragments in a `readme/` directory.

**What was built:** a single `README.md` and a nineteen-document `doc/` set.

**Reason:** a validated environment needs each phase gate to be a separate
controlled document with its own verdict.

**Consequence:** the module does not match the OCA documentation layout. It
matches the framework that commissioned it.

## D-13 — Reports depend on layout templates resolved at render time

**What was built:** two QWeb reports calling `web.external_layout` and
`web.html_container`.

**Reason:** there is no way to render a report without those or an equivalent
layout, and writing a private layout would diverge from every other report in
the system.

**Consequence:** a mismatch in the target build surfaces on the first print
rather than at installation. Recorded as residual risk RR-2 and as activity
OQ-4.

## D-14 — The Algerian corpus is reference-level only

**Specification says:** the module supports ANPP requirements.

**What was built:** nothing derived from any Algerian text.

**Reason:** six instruments were located by reference during this work, but
their full texts were never read. Building controls from a title and a date
would be invention.

**Consequence:** **no ANPP or BPF support is claimed.** The references are
listed in `doc/02_regulatory_analysis.md` section 2.5 so that a regulatory
affairs function can obtain the texts and perform the mapping itself.
