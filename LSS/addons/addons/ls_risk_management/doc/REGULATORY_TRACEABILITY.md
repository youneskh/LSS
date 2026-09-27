# Regulatory Traceability Matrix

## Scope of this document

This matrix maps clauses of **ISO 14971:2019** to the specific fields,
constraints and methods that support their implementation.

**It is not a compliance claim.** Software alone does not make an organisation
compliant with any framework. Compliance depends on procedures, validation,
training, and the quality system as a whole. No certification against
ISO 14971:2019 or any other standard is claimed, implied or evidenced by this
module.

Clause numbers and titles are taken from the **published table of contents**
of ISO 14971:2019. The normative text of the standard is not publicly
available, was not retrieved, and is not reproduced or paraphrased anywhere in
this module. See `VERIFICATION_LOG.md` section 2.

---

## ISO 14971:2019

| Clause | Clause title | Supported by | Enforcement |
|---|---|---|---|
| 4.4 | Risk management plan | `ls.risk.matrix` with `reference_document`, `state`, `approved_by_id`, `approval_date` | The plan itself lives outside this module (deviation D-09). The acceptability criteria it defines are held here, and must be approved before use. |
| 4.5 | Risk management file | `ls.risk.register` with its `assessment_ids`, `mitigation_ids` and chatter | `unlink` blocked once a risk leaves draft; approved assessments immutable |
| 5.2 | Intended use and reasonably foreseeable misuse | `ls.risk.register.intended_use` | Free text, no enforcement |
| 5.3 | Identification of characteristics related to safety | `ls.risk.register.safety_characteristics` | Free text, no enforcement |
| 5.4 | Identification of hazards and hazardous situations | `ls.risk.register.hazard`, `.sequence_of_events`, `.hazardous_situation`, `.harm` | Four distinct fields, so the chain is recorded rather than collapsed into one description |
| 5.5 | Risk estimation | `ls.risk.assessment.severity_level_id`, `.probability_level_id`, `.estimation_rationale` | `action_confirm` refuses without a rationale and without a resolvable matrix cell |
| 6 | Risk evaluation | `ls.risk.matrix.cell.acceptability`, surfaced as `ls.risk.assessment.acceptability` | Computed from the approved matrix; not editable on the assessment |
| 7.1 | Risk control option analysis | `ls.risk.mitigation.control_option`, `.option_priority`, `.option_analysis` | Measures are ordered by option preference so a less preferred option is visible |
| 7.2 | Implementation of risk control measures | `.implementation_evidence`, `.implementation_verified_by_id`, `.implementation_verification_date` | `action_mark_implemented` refuses without evidence |
| 7.3 | Residual risk evaluation | `ls.risk.register.residual_risk_accepted`, `.residual_risk_accepted_by_id`, `.residual_risk_acceptance_date`, `.residual_risk_justification` | Recorded only through `ls.risk.residual.wizard`, which requires a justification and is restricted to Risk Managers |
| 7.4 | Benefit-risk analysis | `ls.risk.register.benefit_risk_analysis` | The residual wizard **refuses** to accept a `not_acceptable` risk without one |
| 7.5 | Risks arising from risk control measures | `ls.risk.mitigation.introduces_new_risk`, `.new_risk_description`, `.new_risk_id` | A declared new risk must be described; `action_create_new_risk` raises it as a register entry |
| 7.6 | Completeness of risk control | `ls.risk.register.control_completeness_confirmed`, `.control_completeness_by_id`, `.control_completeness_date` | Refused while any control measure is unverified; Risk Manager only |
| 8 | Evaluation of overall residual risk | `ls.risk.register.overall_residual_risk_assessment` | Free text, no enforcement |
| 9 | Risk management review | `ls.risk.assessment` with `assessment_type = 'periodic'` | Approval requires a second person |
| 10.2 | Information collection | `ls.risk.assessment` with `assessment_type = 'post_production'` | Distinct type so post-production input is identifiable |
| 10.3 | Information review | `ls.risk.register.next_review_date`, `.review_interval_months`, `.review_overdue`, and `_cron_notify_review_due` | Daily scheduled action notifies the risk owner |
| 10.4 | Actions | `ls.risk.mitigation` raised from a post-production assessment | Same lifecycle as any other control measure |

---

## Clauses deliberately not supported

| Clause | Why |
|---|---|
| 4.1 Risk management process | An organisational process, not a data structure |
| 4.2 Management responsibilities | Organisational |
| 4.3 Competence of personnel | Scope of `ls_training` |
| 10.1 General | Introductory |

---

## Other frameworks

| Framework | Status in this module |
|---|---|
| **ANPP (Algeria)** | **Not claimed.** Official ANPP publications could not be retrieved. The suite specification's traceability matrix marks `ls_risk_management` as supporting ANPP; that mapping is **not** reproduced here because it could not be verified from official documentation. |
| **ICH Q9** | Not claimed. Not verified from an official source. |
| **ISO 13485:2016** | Not claimed. The clause structure was not verified in this session. |
| **21 CFR Part 11** | Not claimed. No electronic signature is implemented (deviation D-10). |
| **EU MDR 2017/745** | Not claimed. |
