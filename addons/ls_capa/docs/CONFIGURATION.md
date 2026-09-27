# ls_capa — Configuration Guide

Configuration is performed by a user in the **CAPA Manager** group.

---

## 1. CAPA categories

*Quality > Configuration > CAPA Categories*

Categories classify CAPA records by process area and supply the default
resolution lead time used to propose a due date.

| Field | Purpose |
|---|---|
| Category | Display name, translatable |
| Code | Short unique code, unique per company |
| Sequence | Presentation order |
| Default Resolution Lead Time (days) | Added to the identification date to propose the due date. Must be greater than zero. |
| Description | Scope and guidance on when to use the category |
| Company | Owning company |

Five categories are preloaded: Production (30 days), Laboratory (30),
Quality System (60), Supplier (60), Facility and Equipment (45).

Adjust the lead times to match the resolution targets stated in your own
CAPA procedure. The proposed due date is always editable on the CAPA
record, so a category lead time is a default rather than a constraint.

Archive rather than delete a category that is no longer used; historical
CAPA records keep referencing it.

## 2. Security group assignment

*Settings > Users & Companies > Users > (user) > Access Rights*

Under the **CAPA Management** privilege, assign exactly one group. The
groups form an implication chain, so a higher group already carries the
permissions of those below it.

| Assign | To |
|---|---|
| CAPA Viewer | Auditors, inspectors, read-only stakeholders |
| CAPA Investigator | Staff who raise CAPA records and investigate root cause |
| CAPA Coordinator | Staff who plan actions and run effectiveness checks |
| CAPA Manager | Quality Assurance staff who verify, close and configure |

**Segregation of duties.** Verification and closure are restricted to
CAPA Manager. To keep verification independent of execution, avoid
granting CAPA Manager to the same person who owns the actions.

## 3. Sequences

*Settings > Technical > Sequences* (developer mode)

| Code | Default prefix |
|---|---|
| `ls.capa.issue` | `CAPA/%(year)s/` |
| `ls.capa.root_cause` | `RCA/%(year)s/` |
| `ls.capa.action` | `CAPA-ACT/%(year)s/` |
| `ls.capa.effectiveness` | `CAPA-EFF/%(year)s/` |

Change the prefix or padding to match your document numbering procedure.
Do **not** reduce the next number, and do not change the prefix in a way
that could produce a reference already in use: CAPA references are
unique per company and a collision raises a database error.

## 4. Optional project integration

Actions can be mirrored as `project.task` records.

1. Create or identify the project that should receive CAPA tasks.
2. Note its numeric database id (visible in the URL as `id=<n>`).
3. Go to *Settings > Technical > System Parameters* and create:
   - Key: `ls_capa.default_project_id`
   - Value: the numeric id, for example `7`

When the parameter is absent or non-numeric, generated tasks are created
without a project and must be filed manually. The parameter is read at
task creation time, so changing it affects only future tasks.

## 5. Overdue notification

*Settings > Technical > Scheduled Actions > CAPA: Notify Overdue Records*

Shipped **inactive** so that no site starts sending notifications without
a deliberate decision. Activate it to post a chatter reminder, addressed
to the CAPA owner, on every open CAPA past its due date.

The action posts on every run and does not deduplicate. The interval
therefore controls notification frequency; the default is daily.

## 6. Email and activity behaviour

All four main models inherit `mail.thread`. Followers receive
notifications according to standard Odoo subscription rules. No custom
email template is shipped; configure notification behaviour through the
standard Odoo mail settings.

## 7. Multi-company

Every CAPA model carries a `company_id` and a global record rule
restricting visibility to the user's allowed companies. Child records
inherit the company of their parent CAPA through a stored related field.

Categories are company-specific: create one set per company, or share a
category by leaving the company empty at database level if your policy
allows it.
