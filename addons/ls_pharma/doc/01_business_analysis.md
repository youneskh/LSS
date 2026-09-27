# Phase 1 — Business Analysis

## 1.1 Business objectives

| # | Objective |
|---|---|
| BO-1 | Hold, for every manufactured batch, the production and control record that a regulated manufacturer must prepare, in a single place and in a form that survives an inspection |
| BO-2 | Prevent a batch from being distributed before the quality unit has reviewed the records and recorded a decision |
| BO-3 | Make the decision of the quality unit permanent, attributable and tamper evident |
| BO-4 | Enforce, in the data layer, the separations of duty that written procedures require, so that they cannot be bypassed through the interface or the API |
| BO-5 | Hold the qualification state of every active ingredient and excipient, so that only qualified materials are charged into a batch |
| BO-6 | Plan and follow stability studies on the frequencies published by ICH, and surface a significant change when it occurs |
| BO-7 | Produce unique identifiers whose serial numbers cannot be deduced, and follow them into shipping containers |
| BO-8 | Follow the preparation of a marketing authorisation dossier section by section |

## 1.2 Business requirements

| # | Requirement | Objective |
|---|---|---|
| BR-1 | Each batch carries components, their lots, their quantities and who charged and verified each of them | BO-1 |
| BR-2 | Each batch carries the major equipment used and the reference of its cleaning record | BO-1 |
| BR-3 | Actual yield is compared against theoretical yield and against established percentage limits | BO-1, BO-2 |
| BR-4 | A yield outside its limits raises a flag that blocks release until an investigation reference is recorded | BO-2 |
| BR-5 | A batch cannot reach review without at least one batch record | BO-2 |
| BR-6 | A batch record cannot be approved while a discrepancy remains open | BO-2 |
| BR-7 | The person who executed a record cannot approve it | BO-4 |
| BR-8 | The person who manufactured a batch cannot decide on its release | BO-4 |
| BR-9 | A component charged by one person is verified by a second, unless an automated system performed the charge | BO-4 |
| BR-10 | A release decision can never be modified or deleted after it is recorded | BO-3 |
| BR-11 | A release decision carries a digest that detects modification of its stored values | BO-3 |
| BR-12 | Materials move through draft, qualified, restricted and obsolete states | BO-5 |
| BR-13 | A material of animal origin cannot be qualified without the reference of its supplier statement | BO-5 |
| BR-14 | A stability schedule is proposed from the study duration and the storage conditions | BO-6 |
| BR-15 | Overdue time points are flagged daily without human intervention | BO-6 |
| BR-16 | A serial number is drawn from a cryptographically strong source, never from a sequence | BO-7 |
| BR-17 | A product code is rejected unless its modulo-10 check digit is correct | BO-7 |
| BR-18 | A dossier can be populated from a reusable Common Technical Document structure | BO-8 |

## 1.3 Stakeholders

| Stakeholder | Interest |
|---|---|
| Production operator | Executes the batch record, charges components, records values |
| Production manager | Plans batches, starts and completes manufacturing, submits records |
| Quality assurance | Reviews and approves records, investigates discrepancies, decides on release |
| Regulatory affairs | Prepares and follows dossiers, holds the marketing authorisation data |
| Qualified person or equivalent | Accountable for the release decision |
| Inspector or auditor | Reads the records; needs them complete, attributable and unaltered |
| System administrator | Installs, configures, backs up, and manages user rights |

## 1.4 User roles

The module ships six groups. Their rights are listed in
`doc/10_administrator_manual.md`.

| Group | Role |
|---|---|
| Viewer | Reads the pharmaceutical data of its companies |
| Production Operator | Executes batch records and records production data |
| Production Manager | Plans batches and drives the production states; implies Operator |
| Quality Assurance | Approves records and decides on release; **does not** imply Operator |
| Regulatory Affairs | Prepares dossiers and holds product regulatory data |
| Manager | Configures the module; implies the other groups |

The quality role deliberately does not inherit the production role. The
independence of the quality unit is therefore visible in the role model
itself, not only in the guards written into the models.

## 1.5 User stories

| # | As a | I want to | So that |
|---|---|---|---|
| US-1 | production manager | plan a batch against a product and a manufacturing order | production has an authorised target |
| US-2 | operator | execute a batch record step by step and record each value | the record reflects what was actually done |
| US-3 | operator | record who charged and who verified each component | the second-person verification is evidenced |
| US-4 | production manager | record the actual yield and see it compared with the theoretical yield | a yield discrepancy is visible immediately |
| US-5 | quality assurance officer | see every open discrepancy on a record before approving it | nothing unexplained is approved |
| US-6 | quality assurance officer | record a release decision through a checklist tied to its regulatory basis | the reason for each confirmation is auditable |
| US-7 | quality assurance officer | verify later that a decision has not been altered | the record is trustworthy |
| US-8 | stability coordinator | generate a testing schedule from the study duration | the plan follows the published frequencies |
| US-9 | stability coordinator | be told when a time point falls due and is not pulled | the study does not silently lapse |
| US-10 | packaging manager | generate unpredictable serial numbers for a batch | the units carry a compliant unique identifier |
| US-11 | packaging manager | aggregate units into a case and a pallet | the shipment can be traced downwards |
| US-12 | regulatory affairs officer | load the Common Technical Document structure into a new dossier | preparation starts from the published organisation |
| US-13 | auditor | print a batch record and a release certificate | the evidence can be handed over |

## 1.6 Use cases

| # | Use case | Primary actor | Outcome |
|---|---|---|---|
| UC-1 | Plan a batch | Production manager | A batch in the planned state with its yield expectations |
| UC-2 | Execute a batch record | Operator | Steps, controls, clearances, labelling and samples recorded |
| UC-3 | Raise and close a discrepancy | Operator, quality assurance | A written investigation, conclusion and follow-up |
| UC-4 | Review and approve a record | Quality assurance | An approved record attributed to a reviewer |
| UC-5 | Decide on release | Quality assurance | An append-only decision and a batch state change |
| UC-6 | Verify a decision later | Auditor | A recomputed digest compared with the stored one |
| UC-7 | Qualify a material | Quality assurance | A material moved to the qualified state |
| UC-8 | Plan a stability study | Stability coordinator | A generated schedule of time points |
| UC-9 | Record a stability result | Analyst | A conform or non-conform result at a time point |
| UC-10 | Generate serial numbers | Packaging manager | Serialised units carrying a GS1 element string |
| UC-11 | Aggregate a container | Packaging manager | A packed container with its units marked aggregated |
| UC-12 | Prepare a dossier | Regulatory affairs | Sections tracked from not started to complete |

## 1.7 Functional scope

In scope: batch manufacturing records, batch release, material master data,
stability studies, GS1 identification and aggregation, dossier tracking, the
printed batch record and release certificate, the six-group security model,
multi-company isolation, and two scheduled actions.

## 1.8 Out of scope

| Item | Reason |
|---|---|
| Electronic signatures under 21 CFR Part 11 | The controls of that Part are not implemented; a site that needs them obtains them elsewhere |
| Barcode symbol rendering | Requires a symbology encoder |
| Electronic submission packaging | Requires a validated publishing tool |
| Laboratory instrument integration | Belongs to a laboratory information system |
| Environmental monitoring | A separate module of the suite |
| Deviation and CAPA workflows | Separate modules of the suite; this module holds a discrepancy record and an external reference field that points at them |
| Equipment calibration | A separate module of the suite |
| Document control | A separate module of the suite; this module holds document references, not documents |

## 1.9 Risks

| # | Risk | Mitigation |
|---|---|---|
| R-1 | The module is taken for a compliance guarantee | Stated in the README, in every report and on the printed certificate |
| R-2 | The integrity digest is taken for an electronic signature | Stated on the form, on the certificate and in the model docstring |
| R-3 | An unverified Odoo 19 identifier breaks installation | No view of another module is inherited; every external reference is declared and checked |
| R-4 | Tests never executed hide a defect | Declared in the delivery gate; the receiving team executes them before qualification |
| R-5 | A separation of duty is bypassed through the API | Every separation is enforced in the model, not in the view |
| R-6 | Regulatory text is paraphrased inaccurately | Every provision cited is traced to a fetched source in `doc/02_regulatory_analysis.md` |
| R-7 | The printed record is taken for the complete batch record | The printout names, in its closing note, what it does not carry |

## 1.10 Success criteria

| # | Criterion | Met |
|---|---|---|
| SC-1 | Every business requirement BR-1 to BR-18 is implemented in a model, not only in a view | Yes |
| SC-2 | Every regulatory citation resolves to a source that was actually read | Yes |
| SC-3 | The module installs without depending on any other suite module | Designed for it; **not demonstrated**, see the delivery gate |
| SC-4 | The static checker reports no finding and is itself validated by fault injection | Yes |
| SC-5 | Every deviation from the suite specification is declared with its reason | Yes, in `doc/15_deviation_register.md` |
| SC-6 | No claim of test coverage is made without measurement | Yes, none is made |

## Gate verdict

**PASS.** The analysis is complete and every requirement is traceable to an
objective and to a later implementation artefact. The one open point, SC-3,
is carried forward into the delivery gate rather than closed here.
