# 02 — Regulatory Analysis

**Phase gate: PASS**, with the explicit limitation recorded in section 2.5.

## 2.1 Position on compliance

This module **supports** the implementation of deviation-handling processes.
It does not confer, certify or guarantee compliance with any framework.
Compliance depends on written procedures, computerised system validation,
personnel training and an operating quality system, none of which is software.

No article, clause or section number appears anywhere in the module source
unless it was verified against a primary source during construction.

## 2.2 Verified requirements that shaped the design

### 21 CFR 211.100(b) — Written procedures; deviations

Verified text: written production and process control procedures shall be
followed and documented at the time of performance, and **any deviation from
the written procedures shall be recorded and justified**.

Design consequence: a `justification` field exists on every deviation and is
mandatory for a planned deviation, enforced by `_check_planned_justification`.
The field is surfaced in the form under a heading naming the regulation and is
printed in the PDF report.

### 21 CFR 211.192 — Production record review

Verified requirements and their direct implementation:

| Verified requirement | Implementation |
|---|---|
| Any unexplained discrepancy, **including a percentage of theoretical yield outside the established limits**, shall be thoroughly investigated | Supplied deviation type "Yield Discrepancy" whose description names this requirement; the type is flagged `requires_disposition` |
| Investigation applies **whether or not the batch has already been distributed** | No field or state conditions the investigation on distribution status |
| The investigation **shall extend to other batches of the same drug product and other drug products** that may be associated | `other_batches_lot_ids` many2many plus a mandatory `extension_rationale`; `action_disposition` refuses to proceed without the rationale, so the extension decision must be recorded even when the conclusion is that none was needed |
| A **written record** of the investigation shall be made **including the conclusions and follow-up** | `conclusion` and `followup` fields, both mandatory in the close wizard; both printed in the PDF report |

This section is the single strongest driver of the module's design. The
common inspection finding against 211.192 is failure to extend the
investigation beyond the affected batch, which is why the extension rationale
is a hard gate rather than an optional note.

### 21 CFR 211.160(a)

Verified that deviations from laboratory control mechanisms must likewise be
recorded and justified. Accommodated through the "QC Laboratory" category and
the same justification field; no laboratory-specific behaviour is implemented,
because laboratory OOS handling is out of scope and belongs to `ls_lab`.

### Algeria — ANPP

Verified: the Agence nationale des produits pharmaceutiques is the competent
authority; it operates BPF (good manufacturing practice) certification and
regulatory inspection of pharmaceutical establishments. **Décret exécutif
n° 22-247 du 30 juin 2022** is the instrument setting the good manufacturing
practice rules for pharmaceutical products for human use.

Design consequence: none specific. The module is designed against the general
GMP expectation that deviations are recorded, investigated, dispositioned and
closed, which is common to GMP regimes.

## 2.3 Frameworks named in the suite specification but NOT implemented against

The suite specification maps `ls_deviation` to ANPP, GMP, ISO 9001, ISO 13485,
ISO 22716 and EU MDR. This module makes **no clause-level claim** against any
of them, because:

- ISO standards are copyrighted documents that were not consulted. Clause
  numbers repeated from a secondary source would be unverified assertions.
- EU GMP chapter and annex numbering was not consulted.

Regulatory Affairs must complete the clause-level mapping against the actual
standard texts. The module is structured so that this is a documentation
exercise rather than a code change: the process steps it enforces (record,
justify, classify, assess impact, investigate, extend, disposition, decide
CAPA, conclude, follow up, close) are the steps these frameworks generally
require.

## 2.4 How the module supports implementation

| Process expectation | Mechanism |
|---|---|
| Prompt recording | Records are created directly in `reported`; there is no draft state in which an unreported deviation can be parked |
| Traceable record | Sequence-generated reference; deletion blocked past `reported`; cancellation requires a reason |
| Attributability | Reporter, owner, QA reviewer, impact assessor, disposition approver and closer are each stored as distinct users with timestamps |
| Contemporaneous evidence | Occurrence, detection and recording timestamps with a chronology constraint |
| Segregation of duties | Disposition approval and closure restricted to the Manager (QA) group |
| Evidence of investigation | Structured RCA method, mandatory findings and root cause before completion |
| Justified disposition | Mandatory justification on every disposition; approver and approval date stamped |
| Timeliness | Severity-derived closure targets, overdue computation, daily notification, justified extensions only |
| Transition history | Append-only `ls.deviation.stage.log` blocked from write and unlink for every user including the superuser |

## 2.5 Explicit limitation

The mapping in section 2.2 is verified. The mapping in section 2.3 is **not
performed**. Anyone using this document as validation input must treat section
2.3 as an open action, not as evidence.

Furthermore, Odoo's native `tracking=True` change history is used for field
history. This is a functional change log. It is **not** a validated 21 CFR
Part 11 audit trail: it is not cryptographically protected, and the module
performs no identity re-verification at approval points. Part 11 capability
requires `ls_electronic_signature` and `ls_audit_trail`, which do not exist.
