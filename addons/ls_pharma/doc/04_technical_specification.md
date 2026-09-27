# Phase 4 — Technical Specification

## 4.1 Module architecture

```
ls_pharma/
├── __init__.py, __manifest__.py
├── constants.py          selections, regulatory citations, GS1 and ICH constants
├── gs1.py                pure GS1 functions, no ORM dependency
├── static_check.py       offline static checker, shipped for re-use
├── models/               26 model files
├── wizards/              3 transient models and their forms
├── security/             groups, 143 access rules, 22 record rules
├── data/                 sequences, ICH conditions, CTD template, crons
├── demo/                 master data with no external identifier
├── report/               2 report actions, 2 QWeb templates
├── views/                10 view files and the menu file, loaded last
├── tests/                11 test modules
├── i18n/                 translation template
├── doc/                  this documentation set
└── static/description/   the module icon
```

Two design rules shape the layout. First, anything that can be a pure
function is one: `gs1.py` imports nothing from Odoo, which is why it can be
tested in isolation and reused by other modules of the suite. Second, every
regulatory citation lives in `constants.py` or in a model docstring, never
duplicated in a view or a report; the release certificate reads the checklist
from the constants through `get_checklist_report_lines`.

## 4.2 Dependencies

Declared: `base`, `mail`, `product`, `stock`, `mrp`.

`mail` supplies the chatter and the activity mixin. `product` supplies the
product on which a batch, a study and a dossier hang. `stock` supplies the
lot and the warehouse. `mrp` supplies the manufacturing order and the bill of
materials that a batch may point at.

No dependency is declared on any module of the Life Sciences Suite. The
reason is recorded in `doc/15_deviation_register.md`.

No external Python package is required beyond the Odoo runtime and the
standard library. `gs1.py` uses `secrets` and `string`; the models use
`hashlib` and `dateutil.relativedelta`, both of which the Odoo runtime
already requires.

## 4.3 Models

Twenty-six persistent models, one abstract mixin and three transient models.
The complete inventory of fields, constraints and methods is generated from
the source into `doc/12_api_reference.md`. The grouping is:

| Group | Models |
|---|---|
| Materials | `ls.pharma.material.mixin` (abstract), `ls.pharma.api`, `ls.pharma.excipient` |
| Batch | `ls.pharma.batch`, `.batch.component`, `.batch.equipment`, `.batch.coproduct` |
| Batch record | `ls.pharma.batch_record`, `.step`, `.control`, `.clearance`, `.labeling`, `.sample`, `.discrepancy` |
| Release | `ls.pharma.batch.release` |
| Stability | `ls.pharma.stability.condition`, `.stability_study`, `.stability.timepoint`, `.stability.sample`, `.stability.result` |
| Serialisation | `ls.pharma.serialization`, `ls.pharma.aggregation` |
| Regulatory | `ls.pharma.ctd_dossier`, `ls.pharma.ctd.section` |
| Extensions | `product.template`, `res.company` |
| Wizards | release, stability schedule, serial generation |

The abstract mixin exists so that an active ingredient and an excipient share
their pharmacopoeial standard, their manufacturers, their retest period and
their qualification state without either model inheriting the other. Both the
model name required by the suite specification and the separate excipient
menu are satisfied without duplicated code.

## 4.4 Constraints

Database constraints use `models.Constraint`, which replaced `_sql_constraints`
in Odoo 19. They cover uniqueness of a material code per company, of a batch
reference per company, of a dossier reference per company, of a storage
condition code, of a serial number per product code and company, and of a
Serial Shipping Container Code.

Python constraints implement the business rules of section 3.4 of the
functional specification. Every rule that expresses a separation of duty or a
regulatory precondition is a Python constraint or a guard inside an action
method, never a view attribute alone, so that it holds for the API as well as
for the interface.

## 4.5 Compute and onchange methods

Stored computes: yield percentage and the yield investigation flag; the
reconciliation difference and its acceptability; conformity of a numeric
control or result; the counters on records, batches, studies and dossiers;
the GS1 element strings; the release checklist completeness and the integrity
verification.

Onchange methods propose values without imposing them: selecting a product
proposes its unit, yield expectations and shelf life onto a batch; entering a
manufacturing date and a shelf life proposes an expiry date.

## 4.6 Security model

Six groups under one `res.groups.privilege` record: Viewer, Production
Operator, Production Manager, Quality Assurance, Regulatory Affairs, Manager.
Quality Assurance implies Viewer only, never Operator.

The access file holds 143 rules covering 26 models. It was generated from an
explicit permission matrix by `tools/generate_acl.py` rather than typed, so
that a model can never be forgotten. The release model carries
`perm_unlink=0` for every group, which agrees with the hard block in the
model.

Twenty-two record rules give multi-company isolation with the domain
`['|', ('company_id', '=', False), ('company_id', 'in', company_ids)]`. They
are global rules, so they do not name a group field whose name in Odoo 19
could not be verified. Two categories are excluded and the exclusion is
documented inside the rules file: the shared storage conditions, which carry
no company field, and the three transient wizards, which the framework
already restricts to their creator.

## 4.7 Views

Ten view files plus the menu file, which is loaded last because every menu
refers to an action declared elsewhere. Odoo 19 syntax throughout: `<list>`
rather than `<tree>`, `<chatter/>` rather than a chatter div, and direct
`invisible`, `readonly` and `required` expressions rather than `attrs`.

No view of another module is inherited. The consequence and the reason are in
the deviation register.

## 4.8 Reports

Two QWeb reports, each declared as an `ir.actions.report` bound to its model.
Both call `web.external_layout` and `web.html_container`. Those two
identifiers are resolved by QWeb at render time rather than at installation
time, so a mismatch would surface on the first print rather than on install.
This is recorded as a residual risk in the validation report.

## 4.9 Data files

| File | Content |
|---|---|
| `data/ir_sequence_data.xml` | Five sequences, company independent |
| `data/ls_pharma_stability_condition_data.xml` | The four ICH Q1A(R2) general-case conditions |
| `data/ls_pharma_ctd_section_template_data.xml` | 108 template sections generated from ICH M4(R4) and M4Q |
| `data/ir_cron_data.xml` | Two daily scheduled actions |

All four are loaded with `noupdate="1"`, so a manufacturer's edits survive a
module upgrade.

The cron records deliberately do not set the fields that govern the number of
remaining calls or the catch-up behaviour, because their names in Odoo 19
could not be verified and they are not needed for a daily job.

## 4.10 Demo data

Master data only, and no external identifier anywhere. The reason is written
into the demo file itself and summarised in the deviation register: every
richer demo record would need either an unverified external identifier or a
state transition that a static XML record would bypass.

## 4.11 Scheduled jobs

Both crons call a model method by name in a `code` action, so neither depends
on a server action record. Both are executed by a test on an empty data set,
because a scheduled action that raises on an empty database would fill the
server log daily.

## 4.12 Translation structure

`i18n/ls_pharma.pot` holds 847 messages. It was produced by an offline
extractor rather than by the Odoo export, and the file says so in its own
header. Regenerating it from a live instance is a one-line command and is
recommended before translation work starts.

## Gate verdict

**PASS.** Every artefact described here exists, and the static checker
verifies the parts of this specification that are machine checkable: field
existence, reference resolution, manifest completeness and access coverage.
