# CONFIGURATION GUIDE — `ls_lab`

The module ships **no** master data. Everything below must be configured before
the laboratory can operate. This is deliberate: shipping storage conditions or
acceptance limits would embed a guideline version your organisation may not be
operating under.

Configure in this order — each step depends on the one before it.

---

## Step 1 — Assign security groups

Settings → Users & Companies → Users.

| Role | Group |
|------|-------|
| Reads laboratory data only | Laboratory Viewer |
| Registers samples, records results | Laboratory Analyst |
| Performs second-person review, investigates | Laboratory Reviewer |
| Approves, closes investigations, issues certificates | Laboratory Manager |

Groups imply one another, so assign only the highest applicable role.

**Segregation of duties requires at least three distinct users** to complete a
sample: one to record results, a second to review, a third to approve. A
two-person laboratory can complete review but not approval, because the approver
may not be the reviewer. Plan role coverage before go-live.

---

## Step 2 — Storage conditions

Laboratory → Configuration → Storage Conditions.

| Field | Guidance |
|-------|----------|
| Name, Code | Your internal designation. The code must be unique. |
| Temperature, tolerance | The nominal value and permitted deviation. |
| Relative humidity, tolerance | On a 0–100 scale. |
| Light condition | Protected from light, ambient, controlled exposure, or not specified. |
| Reference | Free text pointing at the internal procedure or guideline that defines the condition. No guideline content is stored. |

Define one record per condition your stability programme and sample storage use.

---

## Step 3 — Test methods

Laboratory → Tests → Test Methods.

1. Create the method: name, technique, **result type**, default unit, decimal
   places.
2. Record its validation status and validation reference.
3. Submit for review, then approve as a Laboratory Manager.

**Result type drives everything downstream:**

| Result type | Analyst records | Usable criterion types |
|-------------|-----------------|------------------------|
| Numeric | A number | Range, minimum, maximum, informative |
| Text | Free text | Text match, informative |
| Pass / Fail | A selection | Pass/Fail, informative |

An approved method is frozen. Correcting it requires **Create Revision**, which
produces a new draft version.

---

## Step 4 — Specifications

Laboratory → Specifications → Product Specifications.

1. Create the specification: name, product, **specification type**.
2. Add one line per test, choosing the approved method and the criterion.
3. Submit for review, then approve.

Criterion types:

| Type | Requires | Conforms when |
|------|----------|---------------|
| Between Min and Max | both bounds | min ≤ value ≤ max (inclusive) |
| Not Less Than | minimum | value ≥ minimum |
| Not More Than | maximum | value ≤ maximum |
| Text Match | expected text | case-insensitive, whitespace-trimmed match |
| Pass / Fail | — | the recorded value is Pass |
| Informative Only | — | never evaluated; records a value without judging it |

Per-line flags:

- **Mandatory** — the sample cannot reach Results Recorded until this line has a
  result, and cannot reach Reviewed until it is reviewed.
- **Show On CoA** — the line appears on the Certificate of Analysis.

**Only one approved specification may exist per product and specification type.**
Make the existing version obsolete before approving a replacement.

---

## Step 5 — System parameters

Settings → Technical → System Parameters.

| Parameter | Default | Effect |
|-----------|---------|--------|
| `ls_lab.timepoint_notice_days` | `14` | Horizon in days for the stability time point due notice. |
| `ls_lab.method_review_interval_months` | `24` | Age after which an approved method is reported as due for periodic review. Set to `0` to disable. |

Neither parameter is a regulatory value. Both are organisational policy.

---

## Step 6 — Scheduled actions

Settings → Technical → Scheduled Actions.

| Action | Default interval | Behaviour |
|--------|------------------|-----------|
| Laboratory: notify due stability time points | daily | Posts a message on each ongoing study listing due or overdue time points. |
| Laboratory: notify overdue samples | daily | Posts a message on each sample past its due date. |
| Laboratory: notify test methods due for review | weekly | Posts a message on approved methods older than the review interval. |

**All three are notification-only.** None changes a state. Adjust or deactivate
intervals freely — no regulated behaviour depends on them.

---

## Step 7 — Stability studies

Laboratory → Stability → Stability Studies.

1. Create the study: product, lot, batch details, study type, storage condition,
   container closure, specification, protocol reference.
2. Add time points. Each carries a label, an **interval in months** and an
   optional window in days. The scheduled date is derived from the study start
   date plus the interval.
3. Approve the protocol, then start the study. A start date is required, because
   every due date derives from it.

The module ships no time point schedule. Enter the intervals from your approved
stability protocol.

---

## Configuration checklist

- [ ] Users assigned to groups, with at least three distinct users for the full
      sample path
- [ ] Storage conditions defined
- [ ] Test methods created and approved
- [ ] Specifications created, populated and approved
- [ ] System parameters reviewed
- [ ] Scheduled action intervals reviewed
- [ ] A test sample registered end to end on a non-production database
- [ ] Part 11 signature limitation read and accepted by Quality
