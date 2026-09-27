# Phase 3 — Functional Specification

## 3.1 Navigation

Root menu **Pharmaceutical**, visible to the Viewer group and above.

| Menu | Submenu | Opens |
|---|---|---|
| Batches | Manufacturing Batches | `ls.pharma.batch` (list, form, graph, pivot) |
| Batches | Batch Records | `ls.pharma.batch_record` |
| Batches | Batch Release | `ls.pharma.batch.release`, read only |
| Batches | Open Discrepancies | `ls.pharma.batch_record.discrepancy`, filtered to not closed |
| Materials | APIs | `ls.pharma.api`, filtered to qualified |
| Materials | Excipients | `ls.pharma.excipient`, filtered to qualified |
| Materials | Pharmaceutical Products | `product.template`, filtered to pharmaceutical |
| Stability | Stability Studies | `ls.pharma.stability_study` |
| Stability | Stability Samples | `ls.pharma.stability.sample` |
| Stability | Time Points | `ls.pharma.stability.timepoint` |
| Serialization | Serial Numbers | `ls.pharma.serialization` |
| Serialization | Aggregation | `ls.pharma.aggregation` |
| Serialization | Generate Serial Numbers | The generation wizard (Production Manager and above) |
| Regulatory | CTD Dossiers | `ls.pharma.ctd_dossier` |
| Reports | Batch Yield Analysis | Pivot and graph on batches, excluding planned and cancelled |
| Reports | Stability Results | List of results across studies |
| Configuration | Storage Conditions | `ls.pharma.stability.condition` (Manager) |
| Configuration | CTD Section Template | Template sections (Manager) |
| Configuration | Company Settings | The four pharmaceutical company settings (Manager) |

## 3.2 State machines

### 3.2.1 Batch — `ls.pharma.batch`

```
draft ──start──▶ in_process ──complete──▶ manufactured ──quarantine──▶ quarantine
                                              │                            │
                                              └────submit_review───────────┤
                                                                           ▼
                                                                     under_review
                                                                           │
                                                          release wizard ──┤
                                                                           ▼
                                                                 released │ rejected
draft, in_process ──cancel──▶ cancelled ──set_draft──▶ draft
```

| Transition | Guard |
|---|---|
| start | State is draft |
| complete | State is in_process **and** actual yield is above zero |
| quarantine | State is manufactured or under_review |
| submit_review | State is manufactured or quarantine **and** at least one batch record exists |
| release wizard | State is under_review |
| cancel | State is draft or in_process |

### 3.2.2 Batch record — `ls.pharma.batch_record`

```
draft ──start_execution──▶ in_execution ──complete_execution──▶ completed
        ──submit_review──▶ under_review ──approve──▶ approved
                                        ──reject───▶ rejected
completed, under_review ──return_to_execution──▶ in_execution
```

| Transition | Guard |
|---|---|
| start_execution | The master record has been checked, dated and attributed |
| complete_execution | Every step is done or marked not applicable |
| approve | No open discrepancy **and** the approver is not the executor |
| reject | A written review conclusion is present |

### 3.2.3 Other state machines

| Model | States |
|---|---|
| Step | pending, in_progress, done, not_applicable |
| Discrepancy | open, under_investigation, closed |
| Material | draft, qualified, restricted, obsolete |
| Stability study | draft, scheduled, ongoing, completed, terminated |
| Time point | scheduled, pulled, tested, completed, out_of_specification, missed |
| Stability sample | stored, pulled, consumed, discarded |
| Serialised unit | generated, commissioned, aggregated, shipped, decommissioned, destroyed, sampled, returned |
| Container | draft, packed, shipped, disaggregated |
| Dossier | draft, in_preparation, ready, submitted, deficiency, approved, withdrawn |
| Dossier section | not_started, in_preparation, ready, submitted, deficiency, complete |

## 3.3 Approval workflow

Release is the only multi-party approval in the module and runs as follows.

1. Production completes manufacturing. The system stamps the user who did so
   into `user_manufactured_id`.
2. Production submits the batch for review. The system refuses if no batch
   record exists.
3. The quality unit approves each batch record. The system refuses if the
   approver executed the record or if a discrepancy is open.
4. The quality unit opens the release wizard. The wizard shows an advisory
   system evaluation and an eight-point checklist.
5. On confirmation the system creates an append-only decision, stamps a
   SHA-256 digest, and moves the batch to released or rejected.

The system evaluation is advisory only. It reports what the recorded data
show; it never ticks a checklist entry on the user's behalf. Each
confirmation is an assertion made by a person.

## 3.4 Business rules

| # | Rule |
|---|---|
| BB-1 | Percentage of theoretical yield equals actual yield divided by theoretical yield, times one hundred |
| BB-2 | A yield outside the established minimum and maximum percentages raises the investigation flag |
| BB-3 | A batch with the investigation flag raised cannot be released without an investigation reference |
| BB-4 | A batch cannot be released without an expiry date |
| BB-5 | A batch cannot be released while any of its records is unapproved |
| BB-6 | A batch can carry at most one release decision |
| BB-7 | A component charged and verified by the same user is refused, unless the charge was automated |
| BB-8 | A component cannot be both an active ingredient and an excipient |
| BB-9 | Labelling reconciles when issued minus used, returned and destroyed is within the recorded tolerance |
| BB-10 | A numeric control or result conforms when it lies within the limits that are declared present |
| BB-11 | A discrepancy cannot be closed without an investigation, a conclusion and a follow-up, and without the scope where it was extended to other batches |
| BB-12 | A material of animal origin cannot reach the qualified state without a supplier statement reference |
| BB-13 | An expiry date cannot precede the manufacturing date |
| BB-14 | A product code is refused unless it is fourteen digits with a correct modulo-10 check digit |
| BB-15 | A Serial Shipping Container Code is refused unless it is eighteen digits with a correct check digit |
| BB-16 | Serial numbers and batch numbers are refused above twenty characters, the GS1 limit for the variable-length fields |
| BB-17 | A container cannot be packed while empty or while it holds an uncommissioned unit |
| BB-18 | A dossier section cannot be declared ready without a document reference |
| BB-19 | A dossier cannot be approved without an authorisation number |
| BB-20 | A submitted dossier cannot be deleted |

## 3.5 Scheduled actions

| Action | Frequency | Effect |
|---|---|---|
| Flag overdue stability time points | Daily | Sets the overdue flag on scheduled points whose date has passed |
| Notify batches approaching expiry | Daily | Posts a message on released batches within the company alert window |

The alert window is the company setting `pharma_batch_expiry_alert_days`.

## 3.6 Reports

| Report | Model | Content |
|---|---|---|
| Batch Production and Control Record | `ls.pharma.batch_record` | Components, equipment, steps, controls, clearances, labelling, samples, containers, discrepancies, execution and review, and a closing note naming what the printout does not carry |
| Batch Release Certificate | `ls.pharma.batch.release` | Batch, decision, the checklist with its regulatory references read from the constants, the statement, and the digest with its limitation |

## 3.7 Dashboards and analysis

Graph and pivot views on batches give yield by product and by state. A list
view across stability results gives out-of-specification and significant
change counts. No custom JavaScript dashboard is shipped, for the reason
given in the deviation register.

## 3.8 Search, filters and grouping

Every model ships a search view. The filters are listed per model in
`doc/09_user_manual.md`; each one is a state, a flag, a date range or a
relation, and every field named in a filter is verified by the static checker
to exist on its model.

## 3.9 Wizards

| Wizard | Opened from | Purpose |
|---|---|---|
| Batch Release Decision | The batch form, under review | Collects the checklist and the statement, creates the decision |
| Generate Stability Schedule | The study form | Previews the proposed time points before writing them |
| Generate Serial Numbers | The serialisation menu | Draws unique serial numbers for a batch |

## 3.10 Notifications

The module posts messages on the chatter of a batch when a yield falls
outside its limits, when a release decision is recorded, and when a released
batch approaches its expiry date. No email template is shipped, so that a
deployment chooses its own notification policy.

## Gate verdict

**PASS.** Every menu, state, rule, report and wizard described here exists in
the implementation, and every field named in this document was checked
against the models by the static checker.
