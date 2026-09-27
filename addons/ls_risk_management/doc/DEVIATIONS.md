# Declared Deviations from the Functional Specification

Reference: *Life Sciences Suite - Functional Specification, Odoo 19 Community
Edition, version 1.0, July 2026*, section 7.16 and section 15.3.

Every difference between that specification and what was built is listed
below with its rationale. No deviation is silent.

---

## D-01 Dependencies reduced to `base` and `mail`

**Specification** Section 15.3 lists `ls_risk_management` as depending on
`ls_qms`.

**Built** `depends = ["base", "mail"]`.

**Rationale** `ls_qms` is a suite module, not part of the Odoo 19 Community
addons path. Declaring it would make installation fail on any database that
does not already carry it, which is the normal case for a module delivered on
its own. This repeats the pattern applied consistently across the suite.

**Compensating design** Integration is provided by an extension point rather
than a dependency: `ls.risk.register.linked_model_id` (`ir.model`) plus
`linked_res_id` (integer), with `action_open_linked_record` to navigate. A
module that provides `ls_qms` can relate its records to risks without this
module changing.

**Residual limitation** No automatic linkage to QMS records exists out of the
box. A thin bridge module is required.

---

## D-02 `mail` added as a dependency

**Specification** Does not list `mail`.

**Built** `mail` is a dependency.

**Rationale** GxP records require attributable, contemporaneous change
history. `mail.thread` supplies field-level tracking and an immutable message
log; `mail.activity.mixin` supplies the review activities used by the
scheduled action. Re-implementing either would duplicate core functionality,
contrary to the DRY and "use inheritance wherever possible" requirements of
the development framework. `mail` ships with Odoo Community.

---

## D-03 Root menu created rather than reusing a Quality menu

**Specification** Section 7.16 places the menus under `Quality → Risk
Management`.

**Built** A dedicated `Risk Management` root menu (`menu_ls_risk_root`).

**Rationale** The `Quality` root menu is provided by `ls_qms`, which is not a
dependency (D-01). Referencing a menu that may not exist would raise a
`ParseError` at installation.

**Compensating design** A module that provides the Quality root menu can
re-parent `menu_ls_risk_root` by view inheritance without modifying this
module.

---

## D-04 `ls.risk.register` implemented as one record per risk

**Specification** Lists a model named `ls.risk.register` alongside a menu
called "Risk Register".

**Built** One record of `ls.risk.register` is one identified risk. The
"register" is the list view over the model.

**Rationale** The specification's own feature list for the model is "Identify
risks across products and processes", which is a per-risk activity. A
container model holding a collection would add a level of indirection with no
stated requirement behind it.

---

## D-05 Models added beyond the four specified

**Specification** Lists four models: `ls.risk.register`,
`ls.risk.assessment`, `ls.risk.mitigation`, `ls.risk.fmea`.

**Built** Nine persistent models plus one abstract mixin and six transient
wizards.

**Added models and why each is required**

| Model | Required by | Rationale |
|---|---|---|
| `ls.risk.matrix` | Specified feature "Risk Matrix - Risk prioritization matrix" | ISO 14971:2019 requires the organisation to establish objective acceptability criteria and does not prescribe levels. Criteria must therefore be reviewable, approvable, version-controlled **data**, not code. |
| `ls.risk.matrix.level` | Same | Holds the ordinal severity and probability scales with their objective definitions. |
| `ls.risk.matrix.cell` | Same | Holds the acceptability decision per severity/probability pair. |
| `ls.risk.category` | Specified feature "Risk Identification across products and processes" | A configurable taxonomy under change control, rather than a hardcoded selection list. |
| `ls.risk.fmea.line` | Specified feature "FMEA Support" | An FMEA worksheet is inherently a table of failure modes; a header without rows cannot represent one. |
| `ls.risk.role.mixin` | Development framework requirements on DRY and security | Provides one implementation of the Risk Manager assertion used by nine workflow methods. |

---

## D-06 Detectability excluded from the ISO 14971 assessment path

**Specification** Does not distinguish the two rating systems.

**Built** `ls.risk.assessment` carries severity and probability only.
Detection lives on `ls.risk.fmea.line`.

**Rationale** ISO 14971:2019 estimates risk from the severity of harm and the
probability of its occurrence. Detection is an FMEA construct. Mixing them
would misrepresent the standard's method. Both paths are provided; they are
kept structurally separate and can be joined through
`ls.risk.fmea.line.risk_id`.

---

## D-07 No kanban view

**Specification** Does not require one.

**Built** List, form and search views only.

**Rationale** The Odoo 19 kanban card template API could not be verified in
this session. Shipping an unverified view definition risks a template error at
runtime. Consistent with earlier modules in the suite.

---

## D-08 `cancelled` states added throughout

**Specification** Does not list cancelled states.

**Built** `cancelled` exists on the risk, assessment, control measure and
FMEA state machines, always with a mandatory recorded reason.

**Rationale** In a regulated environment a reversed decision must be recorded,
not deleted. Deletion is additionally blocked by overridden `unlink` methods
once a record leaves draft.

---

## D-09 Risk management plan and risk management file not implemented

**Specification** Does not list them.

**Built** Not implemented.

**Rationale** ISO 14971:2019 clauses 4.4 and 4.5 concern a risk management
plan and a risk management file. Implementing them properly requires
controlled document management, which is the scope of
`ls_document_management`, not this module.

**Stated plainly** This module does **not** provide a risk management plan or
a risk management file. The `reference_document` field on `ls.risk.matrix`
records the identifier of the external plan that defines the acceptability
criteria. Organisations must maintain the plan and the file elsewhere.

---

## D-10 No electronic signature

**Specification** Section 14 does not map `ls_risk_management` to 21 CFR
Part 11.

**Built** Approvals record the acting user and a timestamp on the record and
in the chatter. There is no re-authentication and no signature manifestation.

**Stated plainly** The approvals in this module are **not** 21 CFR Part 11
electronic signatures. Where signed approvals are required, integrate
`ls_electronic_signature`.
