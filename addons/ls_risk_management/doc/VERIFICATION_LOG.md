# Verification Log

## Life Sciences Suite - Risk Management (`ls_risk_management`)

This log exists because the Absolute Truth Protocol governing this suite
requires every claim to be sourced or explicitly flagged as unverified. It
records what was checked, against what source, and what remains unproven.

Verification was performed on 30 July 2026.

---

## 1. Odoo 19 platform facts

### 1.1 Verified against official Odoo documentation

| Fact | Source | Applied in |
|---|---|---|
| SQL constraints are declared with `models.Constraint(definition, message)` as a class attribute; `_sql_constraints` is no longer the mechanism | Odoo 19.0 developer tutorial, *Chapter 10: Constraints* (`odoo.com/documentation/19.0/developer/tutorials/server_framework_101/10_constraints.html`) | 22 constraints across 8 models |
| `models.Index()` also exists in Odoo 19 | Odoo 19 release commentary (secondary source, corroborating) | Not used; `index=True` on fields used instead |
| A model inheriting `mail.thread` renders its chatter with the `<chatter/>` element in the form view | Odoo 19.0 developer reference, *Mixins and Useful Classes* (`.../reference/backend/mixins.html`) | 5 form views |
| Security groups attach to an `ir.module.category` through the `res.groups.privilege` model, referenced from `res.groups` by `privilege_id` | Odoo 19.0 developer tutorial, *Restrict access to data* (`.../developer/tutorials/restrict_data_access.html`) | `security/ls_risk_security.xml` |
| The ACL model grants access through a `group_id` field; an empty `group_id` grants the ACL to every user | Odoo 19.0 developer reference, *Security in Odoo* | `security/ir.model.access.csv`, 35 lines |
| A record rule with no group specified is **global**, and global rules combine with a logical AND | Odoo 19.0 developer reference, *Security in Odoo* | All 9 record rules |
| The global status of a rule is a **computed** field derived from its groups | Odoo 19.0 developer reference, *Security in Odoo* | Never written in data files |

### 1.2 Not verified - engineered around

| Fact | Why it could not be verified | Mitigation actually implemented |
|---|---|---|
| Name of the groups field on `ir.rule` in Odoo 19 | The official Odoo 19 security reference describes the field only as "the res.groups to which access is granted (or not)" without naming it. A direct fetch of that page returned navigation content only. A secondary source reports `groups_id` was renamed to `group_ids`, but this is not an official source. | **All record rules in this module are global.** Role separation is delivered by ACLs (whose `group_id` field *is* confirmed) and by ORM-level checks in `ls.risk.role.mixin`. No `ir.rule` groups field is written anywhere. |
| Name of the groups field on `res.users` in Odoo 19 | Same page limitation; secondary sources report a rename from `groups_id` to `group_ids`. | `res.users.has_group('<xmlid>')` is used instead, in `_ensure_risk_manager`. Tests create users with `new_test_user(..., groups='<xmlid>,<xmlid>')`, which takes external identifiers rather than a field name. |
| Whether the base-model helper for cycle detection is `_check_recursion` or `_has_cycle` in Odoo 19 | Neither name appears in retrievable Odoo 19 documentation. | `ls.risk.category._check_category_recursion` walks the ancestry explicitly with a bounded loop. No base-model helper is called. |
| Stability of the `ir.cron` fields `numbercall` and `doall` in Odoo 19 | Not documented in retrievable Odoo 19 material. | Both fields are **omitted** from `data/ir_cron_data.xml`. Only long-established fields are set: `name`, `model_id`, `state`, `code`, `interval_number`, `interval_type`, `active`. |
| The Odoo 19 kanban card template API (`<t t-name="card">`) | Not verified in this session. | **No kanban view is shipped.** List, form and search views only. This matches the decision taken in earlier modules of this suite. |
| Whether `ir.sequence.next_by_code` resolves a company-specific sequence in preference to a company-independent one | Behaviour is expected from the ORM but is not stated in retrievable Odoo 19 documentation. | Company-independent sequences are shipped. The behaviour is listed as an operational qualification item in `VALIDATION_REPORT.md`. Numbering still works if the behaviour differs; only per-company numbering would be affected. |
| Presence of the `mail.mail_activity_data_todo` external identifier | Long established in Odoo, but not confirmed for 19 from an official page. | Resolved with `self.env.ref(..., raise_if_not_found=False)`. When absent, the scheduled action posts a chatter message instead of scheduling an activity. Both branches are reachable and neither raises. |

---

## 2. Regulatory facts

### 2.1 Verified

| Fact | Source | Consequence for the design |
|---|---|---|
| ISO 14971:2019 clause structure: 4 General requirements (4.1-4.5), 5 Risk analysis (5.1-5.5), 6 Risk evaluation, 7 Risk control (7.1-7.6), 8 Evaluation of overall residual risk, 9 Risk management review, 10 Production and post-production activities (10.1-10.4) | Published table of contents of ISO 14971:2019, reproduced on standards catalogue listings; corroborated by the ISO catalogue entry for the standard | `ISO_14971_CLAUSE_MAP` in `models/constants.py`; field-level mapping in `REGULATORY_TRACEABILITY.md` |
| **ISO 14971:2019 requires the manufacturer to establish objective criteria for risk acceptability but does not itself specify acceptable risk levels** | ISO catalogue entry for ISO 14971:2019 (`iso.org/standard/72704.html`) | This is the single most load-bearing regulatory fact in the module. Acceptability is **configuration data** on `ls.risk.matrix`, never a hardcoded threshold. The shipped example matrix is delivered **unapproved and not default**, so it cannot be used until an organisation reviews and approves it. |
| ISO 14971:2019 covers the full lifecycle from conception to decommissioning, including production and post-production information | ISO catalogue entry | `assessment_type` includes `post_production`; the review cron supports clause 10.3 |
| The 2019 edition places enhanced emphasis on benefit-risk analysis | ISO catalogue entry | `benefit_risk_analysis` field, made mandatory by the residual wizard when acceptability is `not_acceptable` |

### 2.2 Not verified - and therefore not claimed

| Item | Status |
|---|---|
| The **normative text** of ISO 14971:2019 | Not publicly available. It was not retrieved and **no wording of the standard is reproduced or paraphrased as a requirement** anywhere in this module. Only clause numbers and clause titles from the published table of contents are referenced. |
| The three risk control options of clause 7.1 as a normative ordered list | The clause **title** ("Risk control option analysis") is verified. The three option categories implemented in `CONTROL_OPTIONS` are widely published, but their exact normative wording and ordering **could not be verified from official documentation**. They are implemented as a configurable selection with a documented priority, not asserted as a quotation of the standard. |
| ANPP (Algeria) requirements applicable to risk management | **This information could not be verified from official documentation.** Official ANPP publications were not retrievable. No ANPP requirement is claimed, mapped or implied anywhere in this module, notwithstanding the suite specification's traceability matrix. |
| ICH Q9 requirements | Not verified from an official source in this session. ICH Q9 is **not** claimed in the module. |
| The 1-10 severity / occurrence / detection scales and the Risk Priority Number | **Could not be verified as a normative requirement of any standard.** Implemented as an industry convention with organisation-defined thresholds, and labelled as such in the FMEA form view, the FMEA PDF report, and `models/constants.py`. |
| Any statement that this module makes an organisation compliant with anything | Not claimed. The module supports the implementation of processes. Both PDF reports carry an explicit disclaimer to that effect. |

---

## 3. Method

1. Version-sensitive Odoo APIs were searched against `odoo.com/documentation/19.0/...` before any code depending on them was written.
2. Where a documentation fetch returned navigation content rather than substantive text, the fact was declared **unverified** and the code was engineered so as not to depend on it. This happened once, for the `ir.rule` groups field.
3. Regulatory clause numbers were taken only from published tables of contents, never inferred.
4. The static checker (`static_check.py`) was validated with 22 deliberate fault injections (`negative_controls.py`) before its clean result was accepted as meaningful.

---

## 4. Standing limitation

No Odoo runtime and no PostgreSQL instance were available in the build
environment, and package installation was blocked by the absence of network
access from the shell. Consequently the module has **never been installed,
started or executed**. Everything in this log concerns static verification
only. See `VALIDATION_REPORT.md` for the honest delivery gate.
