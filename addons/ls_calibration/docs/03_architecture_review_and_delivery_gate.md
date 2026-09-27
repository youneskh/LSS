# ls_calibration — Architecture Review, Deviations and Delivery Gate

Phases 5, 8 and 10 of the development framework.

---

# PHASE 5 — ARCHITECTURE REVIEW

## 5.1 Layering

The module sits in Layer 3 (Life Sciences Core) of the suite architecture and
depends only on Layer 1 (`base`, `mail`). It declares no dependency on any
other Layer 3 module. This is deliberate: a Layer 3 module that hard-depends on
its siblings cannot be deployed incrementally, and a missing sibling blocks
installation outright.

Integration with siblings is delivered through **documented extension points**
rather than dependencies:

| Extension point | Field | Sibling module that would consume it |
|---|---|---|
| Equipment master link | `ls.calibration.instrument.external_equipment_reference` | A `maintenance` bridge module |
| Calibration procedure | `ls.calibration.plan.procedure_reference`, `ls.calibration.record.procedure_reference` | `ls_document_management` |
| Corrective action | `ls.calibration.oot.capa_reference` | `ls_capa` |
| Affected batches | `ls.calibration.oot.affected_batches` | `ls_pharma` / `stock` |

A bridge module replaces the text field with a `Many2one` by inheriting the
model. No change to this module is required.

## 5.2 SOLID assessment

| Principle | Assessment |
|---|---|
| Single responsibility | Each model owns one concept. Tolerance algebra lives only on `ls.calibration.point`; result aggregation only on `ls.calibration.record`; impact assessment only on `ls.calibration.oot`. |
| Open / closed | State machines are declared as data (`*_STATE_TRANSITIONS` in `constants.py`) and consumed by a generic `_assert_transition`. A subclass extends the map rather than editing the guard. |
| Liskov substitution | No model narrows a parent's contract. `write` overrides refuse operations on locked records, which is a documented precondition of the model, not a violated base-class guarantee. |
| Interface segregation | The four security groups are graduated; a technician is never granted approval rights in order to obtain data-entry rights. |
| Dependency inversion | Models depend on the constants module, never on each other's internals. `ls.calibration.reading` reads acceptance limits through `related` fields, not by recomputing point logic. |

## 5.3 DRY and KISS

Every selection list, state transition map and numeric default has exactly one
definition, in `models/constants.py`. Tolerance conversion exists once, in
`LsCalibrationPoint._get_absolute_tolerance`, and both the stored limits and
the runtime `is_within_tolerance` helper use it. Interval arithmetic exists
once, keyed by `INTERVAL_UOM_TO_RELATIVEDELTA_KEY`.

Deliberate simplicity: no custom JavaScript, no OWL components, no custom
widgets, no SQL views, no controllers. Every behaviour is expressed through the
standard ORM and standard view types.

## 5.4 Upgrade safety

| Concern | Treatment |
|---|---|
| Removed Odoo 19 APIs | `models.Constraint` instead of `_sql_constraints`; `<list>` instead of `<tree>`; `<chatter/>` instead of the chatter div; `_compute_display_name` instead of `name_get`; `_read_group` instead of `read_group`. All banned patterns are enforced by the static checker. |
| Unverified APIs | Not used at all. See the deviations register below. |
| Data files | `noupdate="1"` on sequences, crons and record rules so that a module upgrade does not overwrite a customer's tuning. |
| Computed field storage | `store=True` used only where search or grouping requires it. |
| Framework private methods | `_check_recursion` / `_has_cycle` avoided; the category cycle check walks the parent chain explicitly. |

## 5.5 Performance

| Concern | Treatment |
|---|---|
| Counting related records | `_compute_instrument_count` uses `_read_group` with a single aggregate query rather than a per-record `search_count`. |
| Indexes | `index=True` on every foreign key used in a domain and on `code`, `name`, `serial_number`, `state`, `scheduled_date`. |
| Batch creation | `_generate_records_until` accumulates a single `values_list` and issues one `create` call. |
| Unbounded loops | `MAX_GENERATED_RECORDS_PER_PLAN` caps generation at 500 records per plan per run. |
| Recomputation | Date-dependent statuses are refreshed by a scheduled action rather than being recomputed on every read. |

**Known cost:** `_compute_calibration_dates` filters `record_ids` in Python
rather than issuing a targeted search. For an instrument with a very large
number of calibration records this loads them all. Acceptable at expected data
volumes (tens of records per instrument over a lifetime); noted rather than
optimised away, because a premature `search` per record would be worse in the
common batch case.

**PHASE 5 GATE: PASS**

---

# DEVIATIONS REGISTER

Every departure from the Life Sciences Suite Functional Specification v1.0
section 7.10, with its rationale.

## D-1 — Dependencies reduced from `maintenance`, `ls_qms` to `base`, `mail`

**Specification:** `ls_calibration` depends on `maintenance` and `ls_qms`.

**Delivered:** depends on `base` and `mail`.

**Rationale.** Whether the Odoo 19 `maintenance` application ships in Community
Edition **could not be verified from official documentation**. The application
is documented in the Odoo 19 user documentation, but the edition in which it
ships is not stated there. Declaring a module that is absent makes installation
fail outright. `ls_qms` is a sibling suite module whose presence in the target
database cannot be assumed.

**Consequence.** The instrument register is a first-class model of this module
rather than an extension of `maintenance.equipment`. Sites running the
Maintenance application will hold the same physical asset in two places until a
bridge module is written; `external_equipment_reference` exists to correlate
them in the interim.

## D-2 — Additional models beyond the four in the specification

**Specification models:** `ls.calibration.instrument`, `ls.calibration.plan`,
`ls.calibration.record`, `ls.calibration.certificate`.

**Additional models delivered:**

| Model | Why it is required |
|---|---|
| `ls.calibration.instrument.category` | The specification's own feature list requires an "Instrument Register — master list of measuring instruments". A register without classification cannot be filtered or governed by family-level defaults. |
| `ls.calibration.point` | The specification requires "As-Found/As-Left Readings" and "Out-of-Tolerance Management". Neither is expressible without a per-point acceptance criterion. |
| `ls.calibration.reading` | The as-found and as-left values are a set per record, not a scalar. A one-to-many is the only correct structure. |
| `ls.calibration.standard` | ISO 13485 clause 7.6 and 21 CFR 820.72 both require calibration against traceable standards. Without this model, the traceability requirement cannot be met. |
| `ls.calibration.oot` | The specification lists "Out-of-Tolerance Management: Handle OOT events" as a feature. ISO 13485 clause 7.6 requires assessing the validity of previous measurements. A workflow with an assessment and a disposition is required; a boolean flag would not satisfy it. |

## D-3 — Fourth security group added

**Specification groups:** Calibration Manager, Calibration Technician,
Calibration Viewer.

**Delivered:** Viewer, Technician, **Approver**, Manager.

**Rationale.** The module enforces segregation of duties between the performer
and the approver of a calibration. With only three groups, the approver role
would have to be the Manager, which would force every approver to also hold
master-data and deletion rights. The Approver group grants review and approval
without configuration rights.

## D-4 — `cancelled` states added to three state machines

The specification gives no state machine for this module. States
`ls.calibration.record.cancelled`, `ls.calibration.plan.closed` and
`ls.calibration.instrument.retired` are terminal states that preserve a
reversed or ended item rather than deleting it. This follows the pattern
established across the suite: a reversed decision is recorded, not erased.

## D-5 — Record rules are global rather than group-scoped

**Rationale.** The name of the many-to-many field linking `ir.rule` to
`res.groups` in Odoo 19 **could not be verified from official documentation**.
All shipped rules are therefore global and used only for multi-company
isolation. Role-based restriction is delivered by `ir.model.access.csv` and by
ORM-level checks in Python, neither of which depends on the unverified name.

**Consequence.** A site needing row-level restriction beyond company isolation
(for example, a technician seeing only their own department's instruments) must
add rules after installation, once the field name is confirmed against the
running instance.

## D-6 — No kanban view and no dashboard client action

**Rationale.** The Odoo 19 kanban card template API and the dashboard view
architecture **could not be verified from official documentation**. Shipping an
unverified template risks a view parse error that blocks installation.
Pivot, graph and calendar views are shipped instead; all three use view
architectures confirmed in the Odoo 19 documentation.

## D-7 — `ir.cron` records omit `numbercall`, `doall` and `nextcall`

**Rationale.** The presence of these fields in Odoo 19 **could not be verified
from official documentation**. Omitting a field with a framework default is
always safe; writing a removed field is not. `nextcall` carries a default in
the framework.

## D-8 — Electronic signatures and hash-chained audit trail not implemented

Stated in the manifest, in the regulatory analysis and here. Approval on a
calibration record is a user identity plus a timestamp plus a tracked chatter
message. It is **not** a 21 CFR Part 11 electronic signature and does not carry
a signature meaning or a re-authentication step. Sites requiring these must
deploy `ls_electronic_signature` and `ls_audit_trail`.

---

# PHASE 8 — STATIC ANALYSIS

## 8.1 What was run

| Tool | Available | Result |
|---|---|---|
| `python3 -m py_compile` | Yes | **PASS** — every `.py` file compiles |
| `lxml.etree.parse` | Yes | **PASS** — 17 of 17 XML files well-formed |
| `tools/static_check.py` | Yes (written for this module) | **PASS** — 0 errors, 0 warnings |
| `flake8` | **No** — no network, no pip install | **NOT RUN** |
| `pylint` | **No** | **NOT RUN** |
| `pylint-odoo` | **No** | **NOT RUN** |
| `black` / `isort` | **No** | **NOT RUN** |
| `xmllint` | **No** — binary absent | Substituted by `lxml` parsing |

## 8.2 The custom checker and its validation

`tools/static_check.py` implements twelve check families using only `ast`,
`csv`, `re`, `pathlib` and `lxml`. Its output is only trustworthy if it can be
shown to fail on bad input, so it ships with negative controls:

```
$ python3 tools/static_check.py --self-test
  negative control [PASS] python syntax
  negative control [PASS] xml syntax
  negative control [PASS] tree tag
  negative control [PASS] attrs attribute
  negative control [PASS] sql constraints
  negative control [PASS] placeholder token
  negative control [PASS] raw sql
  negative control [PASS] bare except
  negative control [PASS] trailing whitespace
  negative control [PASS] bare placeholder marker
  negative control [PASS] unresolved menu action
  negative control [PASS] unresolved groups attribute
  positive control [PASS] clean file produces no error
```

Twelve deliberately broken modules are written to a temporary directory and the
checker is asserted to detect each fault. The positive control confirms that a
clean file — including the legitimate constant `NEW_SEQUENCE_PLACEHOLDER` —
produces no finding, so the rules were not merely weakened until they went
quiet.

**Two false positives were found and corrected during this build**, which is
itself evidence the checker was exercised rather than assumed:

1. The `<field name="arch">` wrapper of an `ir.ui.view` was being treated as a
   field of the target model. Fixed by skipping the architecture root.
2. `NEW_SEQUENCE_PLACEHOLDER` was matching the `PLACEHOLDER` marker rule. Fixed
   with an identifier-boundary regex, and a new negative control was added to
   prove a bare `PLACEHOLDER` is still caught.

## 8.3 Checks that could not be performed offline

| Check | Why not |
|---|---|
| PEP 8 in full | Only line length, trailing whitespace and tabs are checked. Naming, complexity and import ordering are not. |
| Odoo-specific lint (`pylint-odoo`) | Not installable. Its rules on manifest keys, translation style and deprecated methods are partially replicated by hand in the custom checker. |
| Cyclomatic complexity | No tool available. |
| Security lint (`bandit`) | Not installable. Mitigated by the raw-SQL ban and the absence of controllers, `eval` and `exec`. |

**PHASE 8 GATE: PASS**, with the explicit scope limitation that "static
analysis clean" means "clean under the checks that could be run", not "clean
under flake8 and pylint-odoo".

---

# PHASE 10 — FINAL VALIDATION AND DELIVERY GATE

## 10.1 Verdict

> ### CONDITIONAL PASS
>
> The module is complete, internally consistent and statically clean. It has
> **never been installed against a running Odoo 19 instance**, and its tests
> have **never been executed**. It must not be deployed to a regulated
> production environment until the qualification tasks in §10.4 are complete.

## 10.2 What has been verified

| Claim | Evidence |
|---|---|
| Every Python file compiles | `python3 -m py_compile` over 26 files (24 module + 2 tooling scripts) |
| Every XML file is well-formed | `lxml.etree.parse` over 17 files |
| Custom static checks are clean | `tools/static_check.py`: 0 errors, 0 warnings |
| The checker detects the faults it claims to | 12 negative controls, 1 positive control, all passing |
| Every view field exists on its model | Static checker rule 4, AST-derived field inventory |
| Every `ref`, menu action, `groups` and `t-call` resolves | Static checker rules 5 and the attribute-reference check |
| Every model has ACL coverage for every group | Static checker rules 6 and 7 |
| Every cron targets an existing method | Cross-check script, 3 of 3 |
| Every report action targets an existing template | Cross-check script, 2 of 2 |
| Every demo-data field exists on its model | Cross-check script, 17 records |
| No removed Odoo 19 API is used | Static checker rule 9 |
| No placeholder, no raw SQL, no bare except | Static checker rule 10 |
| Odoo 19 API choices are correct | Verified against official Odoo 19 documentation; see §10.3 |

## 10.3 API verification status

| API | Status | Source |
|---|---|---|
| `models.Constraint(...)` replaces `_sql_constraints` | **Verified** | Odoo 19 tutorial, *Chapter 10: Constraints* |
| `<list>` is the list-view root element | **Verified** | Odoo 19 reference, *View architectures* |
| `<chatter/>` element with the `mail.thread` mixin | **Verified** | Odoo 19 reference, *Mixins and Useful Classes* |
| `res.groups.privilege` with `privilege_id` | **Verified** | Odoo 19 tutorial, *Restrict access to data* |
| `self.env._('literal', named=param)` | **Verified** | Odoo 19 *Coding guidelines*; named placeholders also required by pylint-odoo |
| `post_init_hook` takes `env` | **Verified** | Odoo 19 reference, *Module Manifests* |
| Maintenance application exists in Odoo 19 | **Verified** | Odoo 19 user documentation |
| Maintenance ships in **Community** Edition | **NOT VERIFIED** | Engineered around — see D-1 |
| `ir.rule` groups field name | **NOT VERIFIED** | Engineered around — see D-5 |
| `res.users` groups field name | **NOT VERIFIED** | Engineered around — `has_group()` and `new_test_user()` |
| Kanban card and dashboard template API | **NOT VERIFIED** | Engineered around — see D-6 |
| `ir.cron` field stability | **NOT VERIFIED** | Engineered around — see D-7 |

## 10.4 What has NOT been verified — outstanding qualification tasks

The receiving team must complete all of the following before regulated use.

### Installation Qualification (IQ)

| # | Task |
|---|---|
| IQ-1 | Install the module into a clean Odoo 19.0 Community database and confirm it installs without error. |
| IQ-2 | Confirm all 11 models are created and all 40 ACL lines load. |
| IQ-3 | Confirm the 4 security groups and the `res.groups.privilege` record are created. |
| IQ-4 | Confirm all 4 sequences and all 3 scheduled actions are created. |
| IQ-5 | Confirm all 17 XML data files load and every menu renders. |
| IQ-6 | Upgrade the module over itself and confirm no data loss and no duplicated records. |
| IQ-7 | Uninstall and confirm clean removal. |

### Operational Qualification (OQ)

| # | Task |
|---|---|
| OQ-1 | Execute the full test suite: `odoo -d <db> -i ls_calibration --test-enable --test-tags /ls_calibration`. Record the pass/fail count. |
| OQ-2 | Measure test coverage with `coverage run`. The suite specification targets 95 %; **no coverage figure is claimed here because none was measured**. |
| OQ-3 | Run `flake8`, `pylint` and `pylint-odoo` and remediate findings. |
| OQ-4 | Verify each of the 28 business rules in `docs/01_analysis_and_functional_spec.md` §3.3 manually. |
| OQ-5 | Verify all four state machines by walking every declared transition and confirming every undeclared transition is refused. |
| OQ-6 | Verify segregation of duties with three distinct real users. |
| OQ-7 | Render both QWeb reports to PDF and confirm layout and content. |
| OQ-8 | Trigger each of the three scheduled actions manually and confirm behaviour. |
| OQ-9 | Verify multi-company isolation with two companies and a multi-company user. |
| OQ-10 | Confirm whether `maintenance` is present; if so, evaluate building the bridge module. |
| OQ-11 | Confirm the `ir.rule` groups field name on the running instance and add group-scoped rules if row-level restriction is required. |

### Performance Qualification (PQ)

| # | Task |
|---|---|
| PQ-1 | Load the register with a representative instrument population and measure list-view and search response. |
| PQ-2 | Generate a full year of schedule from all approved plans and measure the wizard's run time. |
| PQ-3 | Execute a complete calibration cycle with real users against the site's own SOPs. |
| PQ-4 | Confirm the calibration status of a real overdue instrument is reported correctly after the daily cron runs. |

### Computer System Validation

| # | Task |
|---|---|
| CSV-1 | Produce a User Requirements Specification and trace it to this module's business requirements. |
| CSV-2 | Perform a risk assessment for the intended use. |
| CSV-3 | Determine whether 21 CFR Part 11 applies. If it does, deploy `ls_electronic_signature` and `ls_audit_trail`; **this module alone does not satisfy Part 11**. |
| CSV-4 | Write the SOPs governing instrument registration, calibration execution, review, approval and out-of-tolerance handling. |
| CSV-5 | Train users and record the training. |
| CSV-6 | Produce the validation summary report. |

## 10.5 Compliance checklist

| # | Item | Status |
|---|---|---|
| 1 | Installs successfully | **UNVERIFIED** — never installed |
| 2 | Upgrades successfully | **UNVERIFIED** |
| 3 | Follows official Odoo module architecture | **PASS** |
| 4 | Follows OCA conventions where applicable | **PASS** — AGPL-3, `19.0.x.y.z` version, module-prefixed XML IDs, no core modification |
| 5 | Does not modify Odoo core | **PASS** |
| 6 | Uses inheritance rather than replacement | **PASS** — `mail.thread`, `mail.activity.mixin` |
| 7 | Follows MVC separation | **PASS** — no business logic in views, no presentation in models |
| 8 | Follows ORM best practice | **PASS** — no raw SQL, batched creates, `_read_group` for aggregation |
| 9 | Prevents SQL injection | **PASS** — no raw SQL anywhere |
| 10 | Prevents XSS | **PASS** — no controllers, no `t-raw`, no custom JavaScript |
| 11 | Validates user input | **PASS** — 31 constraints (14 SQL, 17 Python) across 11 models |
| 12 | Respects access rights | **PASS** — 40 ACL lines, 4 graduated groups |
| 13 | Respects record rules | **PASS** — 9 global multi-company rules |
| 14 | No placeholders, no dead code, no TODO | **PASS** — enforced by the static checker |
| 15 | Complete docstrings | **PASS** — enforced by the static checker |
| 16 | Tests written | **PASS** — 5 test modules, 11 test classes, 112 test methods |
| 17 | Tests executed | **FAIL — NOT RUN.** No Odoo runtime available. |
| 18 | Coverage ≥ 95 % | **NOT MEASURED.** No figure is claimed. |
| 19 | flake8 / pylint-odoo clean | **NOT RUN** |
| 20 | Fully documented | **PASS** — 5 documents in `docs/`, README, module description |

## 10.6 Statement

Items 17, 18 and 19 are failures against the framework's own quality gates, and
they are reported as failures rather than presented as passes. They cannot be
remedied in a build environment without an Odoo runtime, a PostgreSQL server or
network access. They are the first three tasks the receiving team must perform.

**FINAL GATE: CONDITIONAL PASS.**
