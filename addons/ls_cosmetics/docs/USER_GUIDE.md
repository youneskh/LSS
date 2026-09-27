# User Guide

Seven workflows, in the order you will normally perform them.

---

## 1. Load your annex data

**Cosmetics → Ingredients → Annex Restrictions**

This register ships empty by design. Annexes II to VI of Regulation (EC)
No 1223/2009 are amended several times a year, so the module does not embed a
snapshot that would be stale and would look authoritative.

For each entry you rely on, record:

| Field | What to enter |
|---|---|
| Annex | II (prohibited), III (restricted), IV (colorants), V (preservatives), VI (UV-filters) |
| Reference Number | The entry number as published |
| Substance Name | The name as published |
| Has Numeric Limit | Tick only where the annex states a maximum concentration |
| Maximum Concentration | The published figure, in % w/w |
| Source Reference | Which consolidated text you took it from |
| Consolidation Date | The consolidation date of that text |
| Label Wording | Any wording the annex requires on the label |

An Annex II entry cannot carry a numeric limit — a prohibited substance has
no permitted concentration, and the model refuses the combination.

**Until an ingredient is linked to an annex entry, its status reads
"not evaluated".** That is not the same as compliant, and the module will
never say compliant on the strength of missing data.

---

## 2. Build the ingredient register

**Cosmetics → Ingredients → Ingredient Register**

One record per substance. The INCI name recorded here is what will appear on
the label, so enter it exactly as it should be printed.

Flags that change labelling behaviour:

- **Nanomaterial** — appends `(nano)` to the label token, per Art. 19(1)(g).
- **Perfume Component** — the substance is listed as `parfum` or `aroma`
  rather than by name. Record the composition code and supplier; Annex I
  Part A §1 asks for them.
- **Requires Individual Listing** — overrides the perfume term where an annex
  entry requires the substance to be named individually.
- **Impurity** / **Processing Aid** — excluded from the label list entirely,
  per Art. 19(1)(g)(i) and (ii). A substance cannot be both.
- **CMR** — requires a category (1A, 1B or 2) when ticked.

Link the applicable annex entries on the **Annex Entries** tab. Linking an
Annex II entry marks the ingredient as prohibited, which the register shows in
red.

---

## 3. Create a formulation

**Cosmetics → Products → Product Formulations**

Add one line per substance with its concentration in **% w/w**. The total must
come to 100 % before the formulation can be submitted for review.

The **Annex Status** column on each line reports one of:

| Status | Meaning |
|---|---|
| Not evaluated | No annex entry is linked to this ingredient |
| Within limit | Concentration is at or below the recorded limit |
| Over limit | Concentration exceeds the recorded limit — blocking |
| Prohibited | An Annex II entry is linked — blocking |
| Manual review | An entry applies but states no numeric limit; read the conditions |

Two flags on the **Use and Population** tab drive later gating: *intended for
children under three* and *exclusively for external intimate hygiene*. Both
trigger a mandatory specific assessment in the safety report.

**Submit for Review**, then a *different* user approves. The submitter cannot
approve their own formulation. A formulation with any blocking finding cannot
be approved at all.

Once approved, the composition is frozen. To change it, use **Create New
Version**: the composition is copied into a fresh draft, and the current
version is marked superseded only when the new one is approved.

---

## 4. Write the safety report

**Cosmetics → Safety → Safety Assessments**

The form reproduces Annex I exactly.

**Part A** — ten sections, all mandatory. You cannot start Part B until every
one of the ten is documented, because Part B §3 requires the reasoning to be
based on the Part A descriptions. If you try, the module names the sections
that are still empty.

**Part B** — conclusion, labelled warnings, reasoning, and the assessor's
credentials. The specific assessments for children under three and for
external intimate hygiene are required whenever the linked formulation
carries the corresponding flag.

**Approval.** Fill in *Assessor User Account* with the user account of the
qualified person named in section B4. Only that user can press **Approve as
Safety Assessor** — anyone else is refused, including a regulatory manager.
This keeps the record of who signed Part B accurate.

Set a **Next Review Date**. Article 10(1)(c) requires the report to be kept up
to date; a daily scheduled action posts a reminder on the chatter once the
date passes, and the reports appear under **Reports → Safety Reports Due for
Review**.

---

## 5. Substantiate your claims

**Cosmetics → Regulatory → Product Claims**

Enter the claim's exact wording. On the **Common Criteria** tab, work through
the six criteria of Commission Regulation (EU) No 655/2013. Each needs both a
tick and a written justification — a tick alone will not let the claim be
approved.

Where you tick **Evidential Support**, record the evidence on the **Evidence**
tab: experimental studies, consumer perception tests, or published
information. Studies and perception tests must record the number of subjects.
Evidence cannot be dated in the future.

For a "not tested on animals" claim, tick **Article 20(3) claim** and record
the declarations obtained from the manufacturer and every supplier.

As with formulations, the user who starts substantiation cannot approve.

---

## 6. Produce the label

**Cosmetics → Regulatory → Labelling**

One field per Article 19(1) particular. Press **Generate Ingredient List** to
build particular (g) from the approved formulation — do not type it. The
wizard previews the result and lets you choose the two colorant options
Article 19(1)(g) permits: listing colorants last, and adding the `+/-` marker
for a shade range.

The 30-month rule is enforced: if you state a minimum durability above 30
months, the module requires a period after opening instead of a date.

**Approve** lists every missing particular if any are absent. Once approved,
the label is frozen and the ingredient list can no longer be regenerated.

---

## 7. Assemble the Product Information File

**Cosmetics → Regulatory → Product Information Files**

One page per Article 11(2) item. **Activate** refuses while any applicable
item is missing, and names what is missing. It also refuses if the linked
safety report is not approved, or concludes that the product is not safe, or
if any attached claim is unapproved.

**The retention clock.** When the last batch has been placed on the market,
enter that date in *Last Batch Placed on the Market* and press **Enter
Retention Period**. The retention end date is computed as that date plus ten
years, per Article 11(1). The file cannot be archived before then, and cannot
be deleted at all once it has left draft.

A daily scheduled action posts a notice when the ten years elapse. It never
archives the file itself — ending the retention of a regulatory dossier is a
decision for a person, and the module records decisions rather than making
them.

### Algerian prior authorisation

**Cosmetics → Regulatory → Algerian Prior Authorisations**

Tick the sixteen dossier items; submission is refused while any is missing.
Register the deposit receipt to start the 45-day decision period — the deposit
receipt is not itself an authorisation. Overdue dossiers show in red and
receive a chatter notice. A refusal cannot be recorded without its reason.
