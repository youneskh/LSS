# Deviations Register — `ls_environmental_monitoring`

Every departure from the Life Sciences Suite Functional Specification, and every
design decision taken to work around an unverifiable fact, is recorded here with
its rationale. Nothing is left implicit.

---

## A. Deviations from the suite specification

### A1. Module dependencies reduced to `base` and `mail`

**Specification says:** `ls_environmental_monitoring` depends on `ls_qms` and
`ls_deviation`.

**Delivered:** depends on `base` and `mail` only.

**Rationale:** declaring a dependency on a module that is not present in the
target database prevents installation outright. Each suite module is delivered
as a separately installable package with no guarantee about which siblings are
installed, or in what order. Integration is provided instead through extension
points that a sibling module can override.

**Consequence:** the module installs standalone. Where the specification implies
integration, the following extension points are provided:

| Intended integration | Extension point |
|---|---|
| Deviation record raised from an excursion | `ls.env.excursion.action_create_external_record()`, overridable; `external_reference` field for the identifier |
| Corrective action linked to an excursion | Same extension point |
| Quality management document references | Free-text `reference_document` and `source_reference` fields on grades, methods, plans and limits |

**Risk accepted:** a sibling module must be written to use these hooks. Without
one, the link between an excursion and a deviation record is a manually entered
reference rather than a database relation.

---

### A2. Nine models added beyond the four named in the specification

**Specification names:** `ls.env.sampling_point`, `ls.env.sample`,
`ls.env.result`, `ls.env.trend`.

**Delivered:** those four, plus `ls.env.grade`, `ls.env.area`,
`ls.env.parameter`, `ls.env.method`, `ls.env.limit`, `ls.env.plan`,
`ls.env.plan.line`, `ls.env.excursion` and `ls.env.trend.line`.

**Rationale:** the specification's own feature list for this module requires
capabilities that the four named models cannot carry. Specifically, the
specification lists "Alert Limits", "Monitoring Schedule" and "Out-of-Limit
Management" as required features. Each needs a record of its own:

| Specified feature | Model added | Why a model was needed |
|---|---|---|
| Alert Limits | `ls.env.limit` | Thresholds must be versioned and approved independently of the point they apply to, so a past evaluation remains reconstructable |
| Monitoring Schedule | `ls.env.plan`, `ls.env.plan.line` | A schedule must be approvable and versioned; storing frequency on the sampling point would make the schedule uncontrolled |
| Out-of-Limit Management | `ls.env.excursion` | An out-of-limit event has its own lifecycle, owner and closure, distinct from the result that triggered it |
| Trend Analysis | `ls.env.trend.line` | An analysis produces one row per point and parameter; these cannot be held on the analysis header |
| (supporting configuration) | `ls.env.grade`, `ls.env.area`, `ls.env.parameter`, `ls.env.method` | Sampling points must reference a location, a classification, a measured characteristic and a method; hard-coding any of these would prevent configuration |

---

### A3. Three security groups, matching the specification exactly

**Specification names:** Environmental Manager, Environmental Technician,
Environmental Viewer.

**Delivered:** `group_ls_env_manager`, `group_ls_env_technician`,
`group_ls_env_viewer`.

**Note:** no fourth group was added. Review and approval, which some sites would
assign to a dedicated reviewer role, are carried by the manager role, enforced
in Python by `ls.env.sample._check_manager_role()`.

---

## B. Decisions taken because a fact could not be verified

The Truth Protocol requires that unverifiable facts are not guessed. In each
case below, the code was engineered so that the unverified fact is never relied
upon.

### B1. `res.groups` link to `res.groups.privilege` — omitted

**Status:** the `res.groups.privilege` model is **verified** to exist in Odoo 19
from the official documentation tutorial "Restrict access to data". The **name
of the field** on `res.groups` that links to it is **not verified**; secondary
sources report `privilege_id`, but the official reference page could not be
retrieved (it returns navigation content only).

**Decision:** the link is omitted entirely. The three groups are created with a
name and a comment only.

**Consequence:** the roles appear without a grouping heading on the user form.
This is cosmetic.

**Residual risk:** if `privilege_id` turns out to be a *required* field on
`res.groups` in Odoo 19, group creation would fail at install time. This was
judged less likely than the alternative failure mode, because the corresponding
field has been optional in every prior version. **The receiving team should
confirm this at Installation Qualification.**

**Remedy if the field name is confirmed:** add
`<field name="privilege_id" ref="..."/>` to `security/ls_env_groups.xml` after
creating a `res.groups.privilege` record.

---

### B2. `res.groups` implied group relationships — omitted

**Status:** the field name for implied groups in Odoo 19 is **not verified**.

**Decision:** no implication is declared. Each of the three roles carries its
own complete set of access control list rows in `ir.model.access.csv`.

**Consequence:** 46 access rows instead of roughly half that number. A user must
be assigned the role they need; a manager does not inherit viewer rows, but is
granted equivalent access directly.

---

### B3. `ir.rule` group restriction — avoided by using global rules only

**Status:** the field name linking an `ir.rule` to groups in Odoo 19 is **not
verified**. Odoo 19 is known to have renamed several group fields.

**Decision:** all thirteen record rules are **global** rules, which apply to
every user and therefore never reference a group. They implement multi-company
isolation only.

**Consequence:** role separation is enforced by access control lists at model
level and by Python checks at transition level, not by record rules. This is
adequate for the roles defined, because no role needs to see a *subset* of the
records of a model — the distinctions are all about what may be done, not what
may be seen.

**Note:** the `global` field on `ir.rule` is computed by Odoo and is never
written explicitly by this module.

---

### B4. `ir.ui.menu` group restriction — omitted

**Status:** the field name in Odoo 19 is **not verified**.

**Decision:** no menu item declares a group.

**Consequence:** menu visibility follows the access control lists. A user with
no read access to a model does not see its menu entry. A user with read access
to every model, such as a viewer, sees every menu; attempting a write action
they lack rights for produces an access error rather than a hidden button.

---

### B5. `res.users` groups field — avoided in code and tests

**Status:** the field name is **not verified**; secondary sources report a
rename from `groups_id` to `group_ids`.

**Decision:** the field is never referenced. Group membership is tested with
`user.has_group('module.group_xml_id')` and test users are created with
`new_test_user(env, login=..., groups=...)`.

---

### B6. `ir.cron` optional fields — not written

**Status:** the presence and behaviour of `numbercall` and `doall` on `ir.cron`
in Odoo 19 is **not verified**.

**Decision:** only `name`, `model_id`, `state`, `code`, `interval_number`,
`interval_type` and `active` are written on the two cron records.

**Consequence:** the jobs use whatever defaults Odoo 19 applies for the fields
not written. Both jobs are idempotent, so a repeated or missed run is not
harmful: sample generation skips dates already generated, and the overdue
notification posts a message that is additive.

---

### B7. `<chatter/>` element — used, carried forward from the suite convention

**Status:** `<chatter/>` replacing `<div class="oe_chatter">` was established as
the suite convention for Odoo 18 and later and is applied consistently across
the preceding modules of this suite. It was **not re-verified** against official
Odoo 19 documentation during this work.

**Decision:** used, for consistency with the rest of the suite.

**Residual risk:** if the element name is wrong, the affected form views fail to
load and the module fails to install. This is the single highest-severity
unverified item in the delivery and **must be checked first at Installation
Qualification.**

**Remedy:** the seven `<chatter/>` occurrences are confined to form views and
can be removed or replaced without touching any model code. Field tracking would
continue to operate; only the inline display of the message log would be lost.

---

### B8. `self.env._()` translation call — used, carried forward

**Status:** reported as the Odoo 19 coding guideline and applied consistently
across the preceding modules of this suite. Not re-verified during this work.

**Decision:** used throughout, for consistency.

**Remedy if incorrect:** replace with `from odoo import _` and `_(...)`. This is
a mechanical substitution.

---

## C. Design decisions taken on compliance grounds

### C1. No numeric limit values are shipped

No grade, parameter or limit record is included in the module data. Shipping
example thresholds into a regulated system risks their being mistaken for
approved acceptance criteria. `data/ls_env_parameter_data.xml` is deliberately
empty and explains why.

### C2. Limits are versioned, not edited

Approving a replacement limit supersedes its predecessor. The thresholds of an
approved limit cannot be changed, and an approved limit cannot be deleted.

### C3. Results carry their own copy of the criteria applied

Each result stores the thresholds used at the moment of evaluation. A historical
evaluation therefore remains readable even if the limit record is later revised
or archived. This is verified by
`test_result_evaluation.test_snapshot_survives_a_later_limit_revision`.

### C4. Approved records are frozen; correction is by amendment

An approved sample cannot be modified except for its notes. A result on an
approved sample is amended through a route that requires a reason, records the
author and timestamp, and preserves the original value. A result may be amended
once; a further correction requires a new investigation.

### C5. Excursions are cancelled, never deleted

`ls.env.excursion.unlink()` always raises. An excursion is evidence that a
breach occurred.

### C6. Segregation of duties is enforced at ORM level, not in the interface

| Rule | Enforced in |
|---|---|
| A limit is approved by someone other than its author | `ls.env.limit.action_approve` |
| A plan is approved by someone other than its author | `ls.env.plan.action_approve` |
| A sample is reviewed by someone other than the results author | `ls.env.sample.action_review` |
| A sample is approved by someone other than the results author | `ls.env.sample.action_approve` |
| Review and approval require the manager role | `ls.env.sample._check_manager_role` |
| An excursion is closed by someone other than its owner | `ls.env.excursion.close` |

### C7. Strict comparison at the threshold boundary

A value exactly equal to a threshold is reported as compliant, matching the
usual reading of a limit expressed as "not more than". This is documented in
`evaluation.is_breach` and verified by two dedicated tests. Organisations
requiring the opposite convention must configure the threshold accordingly.

### C8. Trend direction is descriptive and refuses thin data

Direction compares the mean of the later half of a series with the mean of the
earlier half. Below six values, or where the earlier-half mean is zero, the
result is reported as insufficient data rather than a figure the data cannot
support. The user interface states that this is not a significance test.

### C9. Statistics that are undefined are flagged, not reported as zero

Each statistic on a trend line is paired with an availability flag. A standard
deviation over a single value is reported as unavailable rather than as zero.

### C10. `widget="percentage"` applied only to a ratio field

`exceedance_ratio` is stored as a ratio in the interval from zero to one, which
is what the `percentage` widget expects. It is not a value from zero to one
hundred.
