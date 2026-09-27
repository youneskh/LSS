# Configuration Guide

**Module:** `ls_medical_plastics`

Configuration must be performed in the order below, because each step depends
on the previous one.

---

## Step 1 — Assign roles

**Settings → Users & Companies → Users**

Assign exactly one Medical Plastics role per user. Roles imply one another, so
assigning Manager also grants Engineer, Technician, Operator and Viewer.

| Role | Give to |
|---|---|
| Viewer | Staff who need visibility without data entry |
| Operator | Moulding machine operators |
| Tool Technician | Tool room staff |
| Engineer | Process and tooling engineers |
| Manager | Production and quality management |

**Segregation of duties depends on this step.** If one person holds Manager and
performs the moulding, the system will still block them from reviewing their own
run, but the organisation gains nothing from the control if that is the only
person available. Plan role coverage so that a second competent person exists
for review and approval.

---

## Step 2 — Review the scrap reason catalogue

**Medical Plastics → Configuration → Scrap Reasons**

Twenty-one reasons are shipped as a starting point, using standard injection
moulding defect terminology. They are **not** a regulatory classification.

Confirm three things:

1. The reasons match the defect taxonomy actually used on site. Rename, archive
   or add as required.
2. The **Start-up / Purge Scrap** flag is set on exactly those reasons that
   represent material discarded while reaching stable production. These are
   excluded from the quality reject rate.
3. The **Requires Investigation** flag reflects the site deviation procedure.

Reasons are shipped without a company, making them shared. Set a company to
restrict a reason to one plant.

---

## Step 3 — Register material grades

**Medical Plastics → Configuration → Material Grades**

For each resin or masterbatch:

1. Enter the grade name, internal code and polymer type.
2. Link the **Inventory Product** used to purchase it.
3. Set **Direct Drug Contact** where the moulded part contacts the medicinal
   product. This makes a lot reference mandatory on every consumption line.
4. Enter the **Consumption Unit** label used when recording consumption.
5. Populate **Regulatory / Compendial References** from the organisation's own
   controlled sources. **This field ships empty by design** — the module does
   not pre-populate regulatory references it cannot verify.
6. Set the qualification status. Only *Qualified* and *Conditionally Qualified*
   grades can be consumed by a run. Conditional qualification requires the
   conditions to be recorded in the qualification notes.

---

## Step 4 — Register components

**Medical Plastics → Products → Components**

1. Link the inventory **Product**.
2. Choose the **Component Category**. Categories forming part of a container
   closure system automatically set the *Primary Packaging* flag.
3. Set **Criticality**. The module stores this classification; it does not
   derive it. It must come from the organisation's risk assessment.
4. Add the **Approved Material Grades**, then set the primary grade — which must
   be one of them.
5. Enter drawing and specification references.
6. Click **Release**. A component cannot be released without at least one
   approved material grade, and a run cannot start against a component that is
   not released.

---

## Step 5 — Register tools

**Medical Plastics → Tools → Tool Register**

1. Enter the tool name and type. The tool code is assigned automatically.
2. Set the **Cavity Count**. Cavity records are created automatically. The count
   can be increased later but **never reduced**, because produced parts remain
   traceable to a cavity.
3. Add the **Components Produced**. A run and a specification can only cite a
   tool declared as producing that component.
4. Set the **Opening Shot Count** for a tool transferred in from elsewhere. This
   becomes read-only once runs have been recorded.
5. Configure maintenance intervals. Set the shot interval, the month interval,
   or both; zero disables that rule. With both set, whichever falls due first
   drives the status.
6. Set the qualification date and, if periodic requalification applies, the
   requalification interval.
7. Click **Qualify**, then **Place In Service**.

---

## Step 6 — Create the moulding parameter specification

**Medical Plastics → Production → Moulding Parameters**

1. Select the component and tool. Leave the work centre empty for a
   specification valid on any machine, or set it to bind the specification to
   one machine. A machine-specific specification takes precedence.
2. Add one line per process parameter: code, name, unit label, minimum, target
   and maximum.
3. Flag the parameters classified as **critical**. A critical parameter out of
   tolerance at start-up **blocks production from starting**.
4. Set the **Monitoring Frequency**. Parameters set to *At Setup Only* or
   *At Start-up Verification* must carry a recorded value before the run can
   leave start-up verification.
5. Optionally set a periodic review interval.
6. **Submit For Review** → a second person clicks **Record Review** → a third
   person clicks **Approve**.

The author cannot review or approve; the reviewer cannot approve. **Three
distinct users are required** to complete the workflow.

---

## Step 7 — Verify the scheduled actions

**Settings → Technical → Scheduled Actions**

| Action | Default frequency | Purpose |
|---|---|---|
| Medical Plastics: check tool maintenance and requalification | Daily | Posts a message on tools that are overdue |
| Medical Plastics: check moulding specification periodic review | Weekly | Posts a message on specifications due for review |

Adjust the frequency to the site's needs. Both are safe to run more often.
