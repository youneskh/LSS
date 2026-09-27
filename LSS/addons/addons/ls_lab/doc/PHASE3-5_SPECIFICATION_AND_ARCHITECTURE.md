# PHASE 3 — FUNCTIONAL SPECIFICATION · PHASE 4 — TECHNICAL SPECIFICATION · PHASE 5 — ARCHITECTURE REVIEW

**Module:** `ls_lab` — Laboratory Management · Odoo 19 Community Edition

---

# PHASE 3 — FUNCTIONAL SPECIFICATION

## 3.1 Functional description

`ls_lab` implements a quality-control laboratory system in four connected domains:

1. **Controlled masters** — test methods and product specifications, each with an approval
   lifecycle, immutability once approved, and explicit version succession.
2. **Sample lifecycle** — registration against an approved specification, automatic
   generation of the test list, result capture, second-person review, approval, reporting.
3. **Non-conformance** — automatic OOS creation on a failing result, two-phase investigation,
   authorised retest/resample, conclusion and product disposition.
4. **Stability and reporting** — stability studies with configurable time points that generate
   pull samples, and Certificates of Analysis derived from approved results.

## 3.2 Menus and navigation

Root menu **Laboratory** (`ls_lab_menu_root`).

| Path | Action | Notes |
|------|--------|-------|
| Laboratory → Samples → Sample Register | `ls_lab_action_sample` | All non-cancelled samples |
| Laboratory → Samples → Sample Receipt | `ls_lab_action_sample_receipt` | Domain `state = received` |
| Laboratory → Tests → Test Methods | `ls_lab_action_test_method` | |
| Laboratory → Tests → Test Results | `ls_lab_action_test_result` | |
| Laboratory → Specifications → Product Specifications | `ls_lab_action_specification` | |
| Laboratory → Specifications → OOS / OOT | `ls_lab_action_oos` | |
| Laboratory → Stability → Stability Studies | `ls_lab_action_stability_study` | |
| Laboratory → Stability → Stability Samples | `ls_lab_action_stability_sample` | Domain `sample_type = stability` |
| Laboratory → Reports → Certificates of Analysis | `ls_lab_action_coa` | |
| Laboratory → Reports → Test Result Analysis | `ls_lab_action_test_result_analysis` | Pivot + graph |
| Laboratory → Configuration → Storage Conditions | `ls_lab_action_storage_condition` | Manager only |

## 3.3 State machines

### 3.3.1 Test method (`ls.lab.test_method`)

```
draft ──submit──> review ──approve──> approved ──obsolete──> obsolete
  ^                  |                    |
  └────reset─────────┘                    └──revise──> (new draft version)
```

### 3.3.2 Specification (`ls.lab.specification`) — identical lifecycle to test method.

### 3.3.3 Sample (`ls.lab.sample`)

```
received ─> in_progress ─> testing ─> results_recorded ─> reviewed ─> approved ─> reported
     └──────────────────── cancel (any state before approved) ───────────> cancelled
```

### 3.3.4 Test result (`ls.lab.test_result`)

```
draft ──enter──> entered ──review──> reviewed
```

### 3.3.5 OOS (`ls.lab.oos`)

```
open ─> phase1 ─> phase1_done ─┬─(no_lab_error)─> phase2 ─> concluded ─> closed
                               └─(lab_error)────────────────> concluded ─> closed
any state before closed ──> cancelled
```

### 3.3.6 Stability study (`ls.lab.stability_study`)

```
draft ─> approved ─> ongoing ─> completed
                        └─────> terminated
```

### 3.3.7 Time point (`ls.lab.stability_timepoint`)

```
planned ─> sampled ─> tested ─> completed
   └─────> missed
```

### 3.3.8 CoA (`ls.lab.coa`)

```
draft ─> issued ─> superseded
   └──> cancelled
```

## 3.4 Business rules

| # | Rule | Enforcement |
|---|------|-------------|
| BRU-01 | An approved test method cannot be modified on any controlled field. | `write()` guard, `UserError` |
| BRU-02 | An approved specification cannot be modified on any controlled field. | `write()` guard |
| BRU-03 | Specification lines cannot be added, changed or removed once the specification is approved. | `create`/`write`/`unlink` guards on the line model |
| BRU-04 | A specification may only reference approved test methods. | `@api.constrains` |
| BRU-05 | At most one approved specification per (product, spec type, company). | `@api.constrains` |
| BRU-06 | A sample must reference an approved specification. | `@api.constrains` |
| BRU-07 | Result lines are generated from the specification; they cannot be created manually on an approved sample. | `create` guard |
| BRU-08 | `evaluation` is computed from the specification line and is never writable. | computed stored, no editable widget |
| BRU-09 | A result cannot be entered on a sample in state `received`, `approved`, `reported` or `cancelled`. | `action_enter` guard |
| BRU-10 | The reviewer of a result must differ from its analyst. | `@api.constrains` |
| BRU-11 | A sample may only move to `results_recorded` when all mandatory results are entered. | action guard |
| BRU-12 | A sample may only move to `reviewed` when all mandatory results are reviewed. | action guard |
| BRU-13 | The sample reviewer must differ from every result analyst on that sample. | `@api.constrains` |
| BRU-14 | The sample approver must differ from the sample reviewer. | `@api.constrains` |
| BRU-15 | A sample cannot be approved while an OOS on it is not closed. | action guard |
| BRU-16 | A non-conforming result automatically creates an OOS record on entry. | `action_enter` |
| BRU-17 | A retest result cannot be created unless the OOS carries a retest authorisation. | `create` guard on `ls.lab.test_result` |
| BRU-18 | Retest authorisation requires a justification and an authorising user, stamped at authorisation time. | action guard |
| BRU-19 | An OOS cannot be closed without `final_conclusion` and `product_disposition`. | action guard |
| BRU-20 | The OOS QA approver must differ from the investigator. | `@api.constrains` |
| BRU-21 | Phase II may only be started when Phase I concluded `no_lab_error`. | action guard |
| BRU-22 | A CoA may only be issued from a sample in state `approved`. | action guard |
| BRU-23 | An issued CoA is frozen; corrections require a new version that supersedes it. | `write()` guard |
| BRU-24 | A time point sample may only be generated for a study in state `ongoing`. | wizard guard |
| BRU-25 | `scheduled_date` is derived from study start date plus interval months. | computed stored |
| BRU-26 | Cancelling a sample requires a recorded reason. | wizard, mandatory field |
| BRU-27 | Marking a time point `missed` requires notes. | action guard |
| BRU-28 | `is_oot` cannot be set without `oot_justification`. | `@api.constrains` |
| BRU-29 | Scheduled actions never change a state; they post messages only. | cron implementation |
| BRU-30 | Numeric criteria require the values their criterion type needs; `range` requires `min <= max`. | `@api.constrains` |

## 3.5 Notifications and scheduled actions

All three are **notification-only**. None writes a regulated field.

| Cron | Interval | Behaviour |
|------|----------|-----------|
| `ls_lab_cron_stability_timepoint_due` | daily | For studies in state `ongoing`, posts one message per study listing planned time points whose `scheduled_date` falls within the notice horizon or is past. |
| `ls_lab_cron_sample_overdue` | daily | Posts a message on each sample whose `due_date` has passed and which is not approved, reported or cancelled. |
| `ls_lab_cron_method_review_due` | weekly | Posts a message on approved test methods whose approval date is older than `ls_lab.method_review_interval_months` (system parameter, default 24). |

## 3.6 Reports

| Report | Model | Output |
|--------|-------|--------|
| Certificate of Analysis | `ls.lab.coa` | QWeb PDF — header, product/lot identification, reportable result table with acceptance criteria, conclusion, issuer and date, explicit non-Part-11 signature notice. |
| OOS Investigation Report | `ls.lab.oos` | QWeb PDF — result reference, Phase I checklist and findings, Phase II findings and root cause, authorisations, conclusion and disposition. |

## 3.7 Dashboards, KPIs, views

| View type | Models |
|-----------|--------|
| list | all ten models |
| form | all ten models |
| search | sample, test_method, specification, test_result, oos, stability_study, coa, storage_condition |
| kanban | sample (grouped by state) |
| pivot | test_result |
| graph | test_result, oos |

KPIs available through pivot/graph: result count by evaluation, OOS count by conclusion and by product, sample count by state and type.

## 3.8 Search views — filters and Group By

Every search view places Group By filters inside a **bare `<group>`** element, per the
verified Odoo 19 RNG (see `API_VERIFICATION_RECORD.md` §4). No `expand` attribute and no
`string` attribute is used on any `<group>` anywhere in this module.

## 3.9 Wizards

| Wizard | Purpose |
|--------|---------|
| `ls.lab.sample_cancel_wizard` | Cancel a sample with a mandatory reason. |
| `ls.lab.stability_pull_wizard` | Create the pull sample for a stability time point. |
| `ls.lab.signature_wizard` | Record signature intent (user, timestamp, meaning) before approval or CoA issue. Carries the explicit limitation notice. |

**PHASE 3 GATE: PASS**

---

# PHASE 4 — TECHNICAL SPECIFICATION

## 4.1 Module architecture

```
ls_lab/
├── __init__.py, __manifest__.py
├── models/       10 model files + __init__.py
├── wizard/        3 wizard files + __init__.py
├── security/      ls_lab_security.xml, ir.model.access.csv
├── views/         9 view files + menus
├── data/          ir_sequence_data.xml, ir_cron_data.xml
├── report/        report actions + 2 QWeb templates
├── tests/         8 test files + __init__.py
├── i18n/          ls_lab.pot
├── doc/           phase documents and manuals
├── tools/         static_check.py, negative_control.py, retrofit_scan.py
└── static/description/icon.png
```

## 4.2 Dependencies

`'depends': ['base', 'mail', 'product', 'stock', 'uom']`

| Dependency | Justification |
|------------|---------------|
| `base` | Core. |
| `mail` | `mail.thread` and `mail.activity.mixin` on the seven business models; `message_post` for cron notices. |
| `product` | `product.product` on specification, sample, study, CoA. |
| `stock` | `stock.lot` on sample and study (verified model name). |
| `uom` | `uom.uom` on methods, specification lines, results, samples (verified present in Community). |

**Not depended upon, deliberately:**

- `quality` — **verified absent from Odoo 19 Community** (see verification record §7).
- `maintenance` — present in Community, but not required; instrument linkage is by reference.
- any `ls_*` suite module — they may not be installable at install time; all cross-module
  references are free-text (`capa_reference`, `validation_reference`, `instrument_reference`).

No external Python package beyond Odoo's own runtime is required. `dateutil.relativedelta`
is used and is part of Odoo's declared runtime dependencies.

## 4.3 Models

| Model | Purpose | Mail thread |
|-------|---------|-------------|
| `ls.lab.storage_condition` | Storage condition master (configuration) | no |
| `ls.lab.test_method` | Analytical method register | yes |
| `ls.lab.specification` | Product specification header | yes |
| `ls.lab.specification_line` | One acceptance criterion | no |
| `ls.lab.sample` | Sample lifecycle | yes |
| `ls.lab.test_result` | One test result | yes |
| `ls.lab.oos` | OOS/OOT investigation | yes |
| `ls.lab.stability_study` | Stability study | yes |
| `ls.lab.stability_timepoint` | Study time point | no |
| `ls.lab.coa` | Certificate of Analysis | yes |

A complete, AST-generated field inventory is provided in `doc/API_REFERENCE.md`. It is
generated from source so it cannot drift from the code.

## 4.4 Constraints

**SQL constraints** use `models.Constraint` exclusively (verified Odoo 19 mechanism; core
uses it). `_sql_constraints` is not used anywhere and is rejected by the static checker.

| Model | Constraint |
|-------|-----------|
| `ls.lab.storage_condition` | `UNIQUE(code)` |
| `ls.lab.test_method` | `UNIQUE(code, version)` |
| `ls.lab.specification` | `UNIQUE(code, version)` |
| `ls.lab.sample` | `UNIQUE(name)` |
| `ls.lab.oos` | `UNIQUE(name)` |
| `ls.lab.stability_study` | `UNIQUE(name)` |
| `ls.lab.coa` | `UNIQUE(name, version)` |
| `ls.lab.test_result` | `CHECK` on non-negative sequence |
| `ls.lab.stability_timepoint` | `CHECK (interval_months >= 0)` |

Python constraints implement BRU-04, 05, 06, 10, 13, 14, 20, 28, 30.

## 4.5 Security model

**Privilege:** one `res.groups.privilege` record, `ls_lab_privilege`, category
`base.module_category_manufacturing` — verified field `privilege_id` on `res.groups`.

**Groups** (`implied_ids` chain): viewer ← analyst ← reviewer ← manager.

**ACL matrix** (`ir.model.access.csv`): every model carries four rows.

| Model | viewer | analyst | reviewer | manager |
|-------|--------|---------|----------|---------|
| storage_condition | r | r | r | rwcd |
| test_method | r | r | r | rwcd |
| specification | r | r | r | rwcd |
| specification_line | r | r | r | rwcd |
| sample | r | rwc | rwc | rwcd |
| test_result | r | rwc | rwc | rwcd |
| oos | r | r | rwc | rwcd |
| stability_study | r | r | rwc | rwcd |
| stability_timepoint | r | r | rwc | rwcd |
| coa | r | r | r | rwcd |
| 3 wizards | — | rwc | rwc | rwcd |

**Record rules.** Because `ir.rule.groups` is now verified, group-restricted rules are used
where they add value, alongside global multi-company rules:

| Rule | Scope | Domain |
|------|-------|--------|
| multi-company (7 rules) | global | `['|', ('company_id','=',False), ('company_id','in',company_ids)]` |
| analyst own-sample write scope | `ls_lab_group_analyst` | read all; documented in admin manual |

## 4.6 Data files

`data/ir_sequence_data.xml` — six sequences, `noupdate="1"`.
`data/ir_cron_data.xml` — three crons, `noupdate="1"`, **no `numbercall`, no `doall`**
(verified removed).

**No demo data of regulatory significance is shipped.** No storage conditions, no time points,
no specifications, no acceptance limits.

## 4.7 Translation

`i18n/ls_lab.pot` generated offline from source via AST + lxml extraction. All user-facing
strings use `self.env._()` (verified Odoo 19 translation accessor).

**PHASE 4 GATE: PASS**

---

# PHASE 5 — ARCHITECTURE REVIEW

## 5.1 Odoo architecture conformance

| Check | Verdict | Evidence |
|-------|---------|----------|
| Standard module layout | PASS | §4.1 |
| No core modification | PASS | no `_inherit` of core models except mixins |
| Mixins used for chatter | PASS | `mail.thread`, `mail.activity.mixin` |
| Business logic in models, not views | PASS | views declare buttons only |
| No raw SQL | PASS | enforced by static checker |
| ORM used for all reads/writes | PASS | `_read_group` used where grouping is needed |
| Odoo 19 element set | PASS | `<list>`, `<chatter/>`, bare `<group>`, `models.Constraint` |

## 5.2 SOLID / DRY / KISS

- **Single responsibility** — each model owns one concept; investigation logic is not mixed
  into the result model beyond raising the OOS.
- **Open/closed** — the immutability guard is driven by a per-model `_CONTROLLED_FIELDS`
  tuple, so subclassing modules extend the protected set without editing the guard.
- **DRY** — the freeze guard, the sequence assignment and the version-succession helper are
  each implemented once in `ls_lab_mixin.py` and reused.
- **KISS** — no metaprogramming, no dynamic model creation, no monkey patching.

## 5.3 Separation of concerns

| Layer | Responsibility |
|-------|----------------|
| Models | state, constraints, computations, guards |
| Wizards | user-supplied justifications and confirmations |
| Views | presentation and button wiring |
| Reports | rendering only; no computation |
| Crons | notification only |

## 5.4 Upgradeability

- No stored computed field depends on a value that cannot be recomputed from stored data.
- Sequences and crons are `noupdate="1"` so customer configuration survives upgrade.
- No column renames; no data migration required for a first release.
- Selection values use stable technical keys; labels are translatable.

## 5.5 Extensibility

- `_CONTROLLED_FIELDS` extension point (§5.2).
- `_evaluate_result()` is a single, overridable method — an industry module can add a new
  criterion type by extending it.
- All actions are ordinary methods and can be overridden.

## 5.6 Findings

| # | Finding | Severity | Resolution |
|---|---------|----------|------------|
| AR-01 | Generic signature wizard dispatches by `res_model`/`res_id`. | Medium | Target models must implement `action_signature_apply`; both do, and the static checker verifies method existence. |
| AR-02 | `evaluation` stored computed field depends on the specification line, which is frozen once approved — so recomputation is stable. | Low | Accepted; documented. |
| AR-03 | `is_oot` is user-asserted, not statistically derived. | Medium | Explicitly out of scope (§1.8); mandatory justification; stated in user manual. |
| AR-04 | CoA reads results at print time rather than snapshotting them. | Low | Acceptable because the source sample is frozen at `approved`. Documented in the validation report as a design decision. |

**PHASE 5 GATE: PASS** — four findings, none blocking, all resolved or explicitly accepted.
