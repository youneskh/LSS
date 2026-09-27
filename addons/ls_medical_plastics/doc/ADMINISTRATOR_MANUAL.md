# Administrator Manual

**Module:** `ls_medical_plastics`

---

## 1. Security model

### 1.1 Role hierarchy

Roles imply one another, so each role holds every capability below it.

```
Manager -> Engineer -> Tool Technician -> Operator -> Viewer
```

### 1.2 Access rights matrix

Forty-one access lines are declared in `security/ir.model.access.csv`.

| Model | Viewer | Operator | Technician | Engineer | Manager |
|---|---|---|---|---|---|
| `ls.mp.material.grade` | R | R | R | RWC | RWCD |
| `ls.mp.component` | R | R | R | RWC | RWCD |
| `ls.mp.tool` | R | R | RW | RWC | RWCD |
| `ls.mp.tool.cavity` | R | R | RWC | RWC | RWCD |
| `ls.mp.tool.maintenance` | R | R | RWC | RWC | RWCD |
| `ls.mp.molding_parameter` | R | R | R | RWC | RWCD |
| `ls.mp.molding_parameter.line` | R | R | R | RWCD | RWCD |
| `ls.mp.scrap.reason` | R | R | R | RWC | RWCD |
| `ls.mp.injection_molding` | R | RWC | RWC | RWC | RWCD |
| `ls.mp.injection_molding.reading` | R | **RC** | **RC** | **RC** | **RC** |
| `ls.mp.injection_molding.material` | R | RWCD | RWCD | RWCD | RWCD |
| `ls.mp.injection_molding.scrap` | R | RWCD | RWCD | RWCD | RWCD |

R = read, W = write, C = create, D = delete.

**Note the reading row.** No role — including Manager — holds write or delete
permission on parameter readings. Append-only behaviour is enforced twice: in
the access control list and in the model's `write` and `unlink` overrides.
Removing one layer does not silently make readings editable, and a test asserts
the access-control layer specifically.

### 1.3 Segregation of duties

These controls are enforced in Python, not merely hidden in the interface, so
they cannot be bypassed through the API, an import or a server action.

| Control | Where enforced |
|---|---|
| Author cannot review a specification | `_check_segregation_of_duties`, `action_review` |
| Author cannot approve a specification | `_check_segregation_of_duties`, `action_approve` |
| Reviewer cannot approve a specification | `_check_segregation_of_duties`, `action_approve` |
| Operator cannot review their own run | `action_review` |
| Setter cannot review their own run | `action_review` |

Completing the specification workflow requires **three distinct users**. Plan
role coverage accordingly, including for holidays and shift patterns.

### 1.4 Record rules

Twelve record rules provide multi-company isolation. **All are global**: they
carry no group restriction and therefore apply to every user.

This is deliberate. A rule attached to a group is combined with other group
rules using a logical OR, so a user holding an extra role could see another
company's records. A global rule is combined with AND and cannot be widened.

The scrap reason rule additionally admits records with no company, so a shared
catalogue remains visible to every company.

---

## 2. Scheduled actions

| Action | Model | Method | Default |
|---|---|---|---|
| Check tool maintenance and requalification | `ls.mp.tool` | `_cron_check_tool_status` | Daily |
| Check moulding specification periodic review | `ls.mp.molding_parameter` | `_cron_check_specification_review` | Weekly |

Both are read-mostly: they recompute stored status fields and post a message on
affected records. Neither changes a workflow state, so running them more often
is safe. Neither sends email by itself; notification depends on the follower
configuration of each record.

---

## 3. Sequences

| Sequence code | Prefix | Padding |
|---|---|---|
| `ls.mp.tool` | `TOOL/` | 5 |
| `ls.mp.tool.maintenance` | `TM/<year>/` | 5 |
| `ls.mp.molding_parameter` | `MPS/` | 5 |
| `ls.mp.injection_molding` | `IM/<year>/` | 6 |

Sequences ship without a company, making them global. To number per plant,
create company-specific sequences with the same codes.

Prefixes may be changed to match site conventions. **Changing a prefix does not
renumber existing records**, which is correct: an issued reference must never be
reused or altered.

---

## 4. Data retention and deletion

The module deliberately blocks deletion of records that constitute production
evidence.

| Record | Deletable? |
|---|---|
| Moulding run in draft or cancelled | Yes |
| Moulding run in any other state | **No** |
| Parameter reading | **Never, by anyone** |
| Completed maintenance event | **No** |
| Approved specification | **No** |
| Specification referenced by any run | **No** |

Uninstalling the module drops its tables and therefore all of the above.
Establish the retention period applicable to the organisation and export before
any uninstallation.

---

## 5. Multi-company operation

Tools, components, grades, specifications and runs each carry a company.
Constraints verify that a run's component and tool belong to the run's company,
and that a specification's component and tool belong to the specification's
company, so cross-company records cannot be linked.

Scrap reasons may be shared by leaving the company empty.

---

## 6. Performance considerations

The following fields are stored computed fields and are recalculated when their
dependencies change:

- `ls.mp.tool.total_shot_count`, `recorded_shot_count`, `maintenance_status`,
  `shots_since_maintenance`, `next_maintenance_date`;
- `ls.mp.injection_molding.qty_good`, `qty_rejected`, `reject_rate`,
  `out_of_tolerance_count`, `has_deviation`.

The shot count of a tool depends on its runs, so a tool accumulating a very
large number of runs will recompute over all of them when a run closes. Index
coverage is provided on the foreign keys involved (`tool_id`, `component_id`,
`run_id`, `company_id`).

**This information could not be verified by measurement:** no performance
testing was carried out, because no Odoo runtime or database was available in
the preparation environment. Performance qualification against realistic data
volumes is one of the outstanding tasks listed in `VALIDATION_REPORT.md`.

---

## 7. Backup

Standard Odoo practice applies: back up the PostgreSQL database and the
filestore together. This module stores no data outside the database and adds no
filestore attachments of its own beyond ordinary chatter attachments.
