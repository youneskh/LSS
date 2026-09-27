# User Manual

This manual is organised by role. Each section describes what that role does
day to day, and names the rule that will stop them if a precondition is not
met.

## A. Production Manager

### A.1 Plan a batch

Pharmaceutical ▸ Batches ▸ Manufacturing Batches ▸ New.

Choose the product. If the product is marked as pharmaceutical, its unit,
theoretical yield, yield limits and shelf life are proposed onto the batch.
Set the batch type: bulk or intermediate, packaging, or finished product. A
reference such as `BAT/2026/00014` is assigned on save.

The yield limits matter: a yield outside them will later block release until
an investigation is referenced. They come from the master production record
under 21 CFR 211.186(b)(6).

### A.2 Start and complete manufacturing

**Start Production** moves the batch to In Production and stamps the start
time.

Record the actual yield before pressing **Complete Manufacturing**. The
system refuses to complete without one, because 21 CFR 211.103 requires
actual yields to be determined at the conclusion of each phase. On
completion, the system records you as the person who manufactured the batch,
which means you will not be able to take the release decision on it.

If the yield falls outside its limits, a message is posted on the batch and
the investigation flag is raised.

### A.3 Submit for quality review

**Submit for QA Review** requires at least one batch record. The system
refuses otherwise.

## B. Production Operator

### B.1 Record components

On the batch, the Components tab. For each component record the product, the
lot or its reference, the quantity and unit, and where relevant the assay,
which produces the compensated quantity.

Record who charged the component and who verified it. **These must be two
different people.** Where an automated system performed the charge, tick
Automated Charge instead; the verification requirement is then suspended,
which is the exemption in 21 CFR 211.101(d).

### B.2 Record equipment

The Equipment tab. Record each item of major equipment, its identifier, the
operation it performed, the reference of its cleaning record and who verified
the cleaning, with the period of use.

### B.3 Execute the batch record

Pharmaceutical ▸ Batches ▸ Batch Records.

Before execution can start, the master production record must be identified
by reference and version, and someone must be recorded as having checked it,
with a date. This is the reproduction check of 21 CFR 211.188(a).

**Start Execution**, then work through the tabs:

| Tab | What to record |
|---|---|
| Processing Steps | For each step, the value observed, who performed it and who checked it. Mark significant steps as such. |
| In-Process and Laboratory Controls | The acceptance criterion, the result, and the unit. Conformity is computed for numeric results. |
| Line Clearance | One entry before use and one after use, each with the area, the previous product, the performer and the verifier. |
| Labelling Reconciliation | Quantities issued, used, returned and destroyed. The difference and its acceptability are computed. |
| Samples | Every sample taken, with its type. Reserve samples are counted separately. |
| Discrepancies | Anything unexplained. See B.4. |
| Containers and Closures | The description and the result of the examination. |

**Complete Execution** requires every step to be either done or marked not
applicable.

### B.4 Raise a discrepancy

On the Discrepancies tab, open a new line. Give it a title, a classification
and a description of what was observed.

An open discrepancy blocks the approval of the record. To close it you need
an investigation, a written conclusion and a follow-up, and where the
investigation extended to other batches, the scope of that extension. All
four are required by 21 CFR 211.192 and the system enforces them.

## C. Quality Assurance

### C.1 Review a batch record

Open the record in the Under Review state. Check the open discrepancy count,
the non-conforming control count and the unreconciled labelling count shown
on the form.

**Approve** is refused if any discrepancy is open, and refused if you are the
person who completed the execution. **Reject** requires a written review
conclusion.

### C.2 Record a release decision

From a batch under review, **Record Release Decision**.

The wizard shows an advisory system evaluation of what the recorded data
show. It is advisory only: it never ticks a box for you. Each of the eight
confirmations is an assertion you are making.

| Confirmation | Regulatory basis |
|---|---|
| Batch production and control records reviewed and approved | 21 CFR 211.192 |
| All discrepancies investigated and closed with written conclusion | 21 CFR 211.192 |
| Actual yield within the established percentage limits | 21 CFR 211.103, 211.192 |
| Component charge-in verified by a second person | 21 CFR 211.101(c), (d) |
| Finished product laboratory results conform to specification | 21 CFR 211.165 |
| Labelling quantities reconciled | 21 CFR 211.125, 211.188(b)(8) |
| Reserve samples collected and retained | 21 CFR 211.170 |
| Batch covered by the written stability testing programme | 21 CFR 211.166 |

A release is refused if any confirmation is missing, if a record is
unapproved, if the yield flag is raised with no investigation reference, if
there is no expiry date, or if you manufactured the batch. A rejection needs
only a statement.

**The decision is permanent.** It can never be edited or deleted. If it was
wrong, that fact is itself part of the record; record the correction through
your deviation procedure.

### C.3 Verify a decision later

Open the decision and press **Verify Integrity**. The system recomputes the
SHA-256 digest over the stored values and compares it with the digest stamped
at the time. A mismatch means the stored values differ from those covered by
the digest.

This is not an electronic signature under 21 CFR Part 11. It detects
modification; it does not authenticate a signer.

### C.4 Qualify materials

Pharmaceutical ▸ Materials ▸ APIs or Excipients.

A material moves through Draft, Qualified, Restricted and Obsolete. A
material of animal origin cannot reach Qualified without the reference of its
supplier statement on transmissible spongiform encephalopathy. An obsolete
material is archived and cannot be returned to draft.

## D. Stability Coordinator

Pharmaceutical ▸ Stability ▸ Stability Studies.

Create the study with its product, protocol reference, packaging description,
start date, duration and storage conditions. **Generate Schedule** opens a
wizard that previews the proposed time points before writing anything.

The proposal follows ICH Q1A(R2): for the long term condition, every three
months over the first year, every six months over the second and annually
thereafter; for the accelerated condition a minimum of three points; for the
intermediate condition a minimum of four. A twenty-four month long term
series is therefore months 0, 3, 6, 9, 12, 18 and 24.

At each time point, **Pull Samples**, record the results, then **Mark
Tested** and **Complete**. A result outside its limits is flagged; ticking
Significant Change on a result marks the whole study.

A daily job flags time points whose scheduled date has passed and which have
not been pulled. Completing a study requires every point to be settled and a
written conclusion, because 21 CFR 211.166 requires the results to be used in
determining storage conditions and expiration dates.

## E. Packaging Manager

### E.1 Generate serial numbers

Pharmaceutical ▸ Serialization ▸ Generate Serial Numbers.

Choose the batch, confirm the product code, batch number and expiry date, and
give a quantity and a serial length. The product code is refused unless it is
a valid fourteen-digit key with a correct modulo-10 check digit, and the
expiry date must be in the future.

Serial numbers are drawn from a cryptographically strong random source, never
from a counter, because Article 4 of Regulation (EU) 2016/161 requires that
the value not be possible to deduce.

Each unit carries an element string of the form
`(01)product code(21)serial(10)batch(17)YYMMDD`.

### E.2 Commission and aggregate

Commission the units. Then create a container with its Serial Shipping
Container Code, choose its level, attach the units or smaller containers, and
**Pack**. Packing is refused if the container is empty or holds an
uncommissioned unit. Disaggregation returns the units to commissioned.

## F. Regulatory Affairs

Pharmaceutical ▸ Regulatory ▸ CTD Dossiers.

Create the dossier with its product, type, authority and version, then **Load
CTD Structure** to copy in the shipped Common Technical Document sections.
The structure comes from ICH M4(R4) and ICH M4Q.

Assign a responsible person and a due date per section. A section cannot be
declared ready without a document reference. The dossier cannot be marked
ready while any section is unready, cannot be approved without an
authorisation number, and cannot be deleted once submitted.

Note that the sub-sections of 2.6, 2.7, 4.2 and 5.3 are not shipped. Their
headings come from ICH M4S and M4E, which were not consulted when the
template was written, so shipping numbered guesses would have been wrong. Add
them under Configuration ▸ CTD Section Template.

## G. Printing

| Print | From |
|---|---|
| Batch Production and Control Record | The batch record form |
| Batch Release Certificate | The release decision form |

The printed batch record names, in its closing note, the items that it does
not carry. It is not a substitute for the complete batch record of the
manufacturer.
