# User Manual — `ls_medical_device`

## 1. The device register

The device record is the anchor: every regulatory artefact attaches to exactly
one device.

### Creating a device

Devices → Device Register → New. The reference is allocated automatically.

Record the identification (name, model reference, Basic UDI-DI, nomenclature
code), the economic operators (manufacturer, authorised representative), the
risk class, and the intended purpose as it appears in the labelling and
instructions for use.

The characteristic flags — implantable, sterile, measuring, reusable surgical,
software, custom-made — drive several derived obligations:

- **Implantable** sets the documentation retention to 15 years instead of 10
  (MDR Article 10(8)) and marks periodic reports for submission to the
  notified body (MDR Article 86(2)).
- The risk class drives the periodic report type and interval, whether a
  notified body is required, and whether the PMCF evaluation report must be
  updated annually (MDR Article 61(11)).

### The device life cycle

```
draft → development → conformity assessment → on market → suspended → withdrawn
                ↑______________|                    ↕______________|
                  (rework)                            (resume)
```

| Transition | Precondition |
|---|---|
| draft → development | none |
| development → conformity assessment | intended purpose recorded |
| conformity assessment → development | none (rework path) |
| conformity assessment → on market | approved technical documentation, and a certificate in issued or valid status where the class requires a notified body |
| on market → suspended | none |
| suspended → on market | none |
| on market or suspended → withdrawn | none |

Every transition requires the **Regulatory Affairs** or **Manager** access
level. The *Change Status with Justification* button opens a wizard that
forces a justification to be captured at the moment of the change, and writes
it to the record and its message history.

Placing a device on the market is deliberately gated on evidence being present
in the system. A device cannot silently claim market status without approved
documentation behind it.

## 2. UDI assignments

Devices → UDI Assignments.

Record one entry per identifier and packaging level. MDR Article 27(1)
requires a UDI to be assigned to the device and to all higher levels of
packaging.

- **Basic UDI-DI** groups devices sharing the same intended purpose, risk
  class and essential design characteristics (MDR Annex VI Part C).
- **UDI-DI** identifies a specific device model at a packaging level.
- The **production identifier** flags record which UDI-PI components apply:
  lot number, serial number, manufacturing date, expiry date, software
  version.

Selecting an issuing entity of *Other* requires an explanatory note, so that
an entity outside the designated list is never recorded silently.

Life cycle: draft → assigned → published → obsolete. *Published* means the
identifier was submitted to a UDI database; record the database name, the
submission date and the reference returned.

## 3. Risk management

Risk Management → Risk Management Files.

A file follows the ISO 14971:2019 process for one device. Record the scope,
the risk acceptability policy from the risk management plan, and the standard
reference.

Each risk records the full chain the standard requires: hazard → sequence of
events → hazardous situation → harm, with the affected party.

- **Initial** severity and probability produce the initial risk index (their
  product).
- The **control option** follows the priority order of the standard:
  inherently safe design, then protective measures, then information for
  safety.
- **Residual** severity and probability produce the residual index. A residual
  risk worse than the initial risk is rejected.
- Where a control measure introduces a new hazard, this must be declared and
  described.
- The **residual acceptability** is the recorded decision. The matrix proposes
  a value; the user decides and justifies it.

The file reports how many risks are unacceptable, how many have unverified
controls, and the highest residual index. A file cannot be approved without an
overall benefit-risk conclusion.

Once a file leaves draft, its risks are locked. Create a new version instead —
duplicating a file increments the version and returns it to draft.

## 4. Clinical evaluation

Clinical → Clinical Evaluations.

The record follows the evaluation through its stages: the plan (scope, the
GSPRs requiring clinical data, intended clinical benefits, target population,
acceptance criteria, literature search protocol), the evidence, the appraisal
and analysis, and the conclusion.

- Claiming **equivalence** requires the demonstration to be recorded.
- Where **no clinical investigation** was performed, a justification is
  required.
- Where **PMCF is not applicable**, a justification is required.

### PMCF evaluation reports

Clinical → PMCF Evaluation Reports.

One report per period, recording the activities performed, data collected,
findings, any new risks, any off-label use observed, and the benefit-risk
conclusion. For class III and implantable devices the report must be updated
at least annually (MDR Article 61(11)); the next update due date is derived
and displayed.

## 5. Technical documentation

Regulatory → Technical Documentation.

Creating a record seeds its sections from the template configured for the
selected annex. Each section records where the underlying evidence is held —
this module is an index and a completeness control, not a document store.

- Marking a section **complete** requires an evidence reference.
- Marking a section **not applicable** requires a justification. MDR Annex II
  point 4 requires an explanation where a general safety and performance
  requirement does not apply.
- The record reports how many mandatory sections remain unaddressed.

Sections lock once the record leaves draft.

## 6. CE marking

Regulatory → CE Marking.

One record per conformity assessment route and certificate. A route other than
self-declaration requires a notified body.

Life cycle: draft → submitted → issued → valid, with suspended, withdrawn and
expired as further states.

Record the certificate number, issue date and expiry date. MDR Article 56(2)
provides that a certificate is valid for the period it indicates, not
exceeding five years. The record shows the days remaining and flags expiry;
the daily scheduled action moves expired certificates to the expired status.

Record separately the EU declaration of conformity number and date, and the
date the CE marking was affixed.

## 7. Post-market surveillance

### Surveillance plans

Post-Market Surveillance → Surveillance Plans.

The plan records the information sources monitored, the collection process,
the indicators and thresholds, the analysis and communication methods, the
corrective action process, the traceability tools, and the referenced
procedures of the quality system.

A plan must either include a PMCF plan reference or justify its absence.

Approval requires five elements to be recorded: information sources,
collection process, referenced procedures, corrective action process and
traceability tools. Note that **submission** for review checks only the status;
the content gate applies at **approval**.

### Periodic reports

Post-Market Surveillance → Periodic Reports.

The report type follows the risk class: a post-market surveillance report
under Article 85 for class I, a periodic safety update report under Article 86
for classes IIa, IIb and III.

Record the signals for the period (complaints, serious incidents, non-serious
incidents, field safety corrective actions), the sales volume and user
population estimate, the trend analysis, the main PMCF findings, the
preventive and corrective actions, and the benefit-risk determination.

Declaring a trend signal requires a description. MDR Article 88 requires
reporting a statistically significant increase in the frequency or severity of
incidents that are not serious incidents.

*Open Reporting Period* creates draft reports in bulk. The period start is
derived per device from the end of the last approved report, or from the
market placement date where no approved report exists.

## 8. Monitoring

Monitoring → Overdue Post-Market Reports lists devices whose next periodic
report has passed its due date. Monitoring → Expired Certificates lists
certificates past their validity period.

The daily scheduled action raises a to-do activity on each affected device.

## 9. Approval and segregation of duties

Every controlled record follows: draft → under review → approved, with
superseded and cancelled as terminal states.

- Approval requires the **Regulatory Affairs** or **Manager** level.
- **An approver may not approve a record they authored.**
- Approved records cannot be deleted. Cancel them instead, so the record is
  preserved.
- Content locks once a record leaves draft. Create a new version.

These checks run inside the model methods, not only in the views, so they
apply to imports and integrations as well as to interactive use.
