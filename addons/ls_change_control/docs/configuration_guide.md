# Configuration Guide

Module: `ls_change_control`

All configuration is performed by a user holding the **Change Control
Manager** group, from the Configuration menu.

The configuration of this module is a quality record. It determines who
approves what, and which areas are assessed. It should be reviewed and
approved by the quality unit before use, and any subsequent modification
should itself be managed under the change control procedure of the
organisation.

## 1. Assign the security groups

Settings, Users and Companies, Users, then for each user select one value in
the `Change Control` field.

| Group | Give it to |
|-------|-----------|
| Viewer | Anyone who must read change records without acting: auditors, management, support functions |
| Requester | Anyone who raises change requests, **and every subject matter expert who performs impact assessments**, **and every person responsible for an implementation action or a verification** |
| Approver | Anyone who signs approvals |
| Change Control Manager | The quality unit personnel who drive the process |

**Important.** The specification of the suite defines exactly four groups, and
this module implements exactly those four. There is no dedicated assessor
group. A subject matter expert must therefore hold at least the Requester
group in order to write their assessment. Restriction to their own assessment
is enforced by the application logic, not by the group: `action_complete`
refuses any user who is neither the assigned assessor nor a manager.

The groups are cumulative: a Manager automatically holds Approver, Requester
and Viewer rights.

## 2. Impact areas

Configuration, Impact Areas.

Fourteen areas are delivered: Facilities and Premises, Utilities, Equipment,
Manufacturing Process, Product and Formulation, Materials and Suppliers,
Analytical Methods, Cleaning and Sanitisation, Packaging and Labelling,
Documentation, Computerised Systems, Personnel and Training, Regulatory
Dossier, Environmental Monitoring.

| Field | Meaning |
|-------|---------|
| Impact Area | Name shown to the assessor |
| Code | Short unique code used in exports |
| Sequence | Display order |
| Description | Guidance shown to the assessor on the scope of the area |
| Assessment Mandatory | When enabled, the assessment of this area must be completed before the change can be approved |
| Active | An archived area stays on existing requests but cannot be selected on new ones |

Adapt the list to the scope of the site. A site that performs no sterile
manufacturing may archive Environmental Monitoring. Never delete an area that
has been used: archive it, so that historical records remain readable.

## 3. Change categories

Configuration, Change Categories.

Ten categories are delivered: Facility, Equipment, Manufacturing Process,
Product and Formulation, Analytical Method, Material or Supplier, Packaging and
Labelling, Documentation, Computerised System, Organisational.

| Field | Meaning |
|-------|---------|
| Category, Code, Sequence, Description | Identification |
| Implementation Deadline (days) | Added to the approval date to propose a planned implementation date. Set to 0 to propose no date |
| Effectiveness Verification Required | When disabled, a change of this category may be closed without a verification |
| Verification Delay (days) | Added to the actual implementation date to compute the planned verification date. When 0, the company default applies |
| Default Impact Areas | Proposed on a request of this category |
| Approval Template | The roles that must approve |

### 3.1 Approval template

Each line carries a role, an optional default approver and a mandatory flag.

Eleven roles are available: Quality Assurance, Quality Control, Production,
Engineering and Maintenance, Validation, Regulatory Affairs, Research and
Development, Supply Chain, Information Technology, Site Management, Qualified
Person.

| Situation | What to do |
|-----------|-----------|
| The role is always held by the same person | Set the Default Approver. The approval is generated ready to sign |
| The role is held by several people depending on the change | Leave Default Approver empty. The change control manager assigns it during the review. The impact assessment cannot start while an approval has no approver |
| The approval is desirable but must not block | Clear the Mandatory flag |

The `Sequence` orders the display only. Approvals may be granted in any order:
the process is not blocked by one absent approver.

The list of roles is deliberately closed, so that the approval matrix of a site
is deterministic. Adding a role requires a small extension module; see
`docs/developer_manual.md`.

## 4. Company parameters

Configuration, Settings. The parameters apply to **one company**, that is to
one manufacturing site. In a multi-site organisation, set them for each
company.

| Parameter | Default | Effect |
|-----------|---------|--------|
| Approval Reminder Delay (days) | 3 | An approval pending longer than this triggers a daily reminder to the approver. Set to 0 to disable reminders for this company |
| Effectiveness Verification Mandatory | Enabled | When disabled, no change of this company requires a verification, whatever the category says |
| Default Verification Delay (days) | 30 | Used when the category defines no delay of its own |
| Block Closure on Open Actions | Enabled | When enabled, the change cannot leave Implementation while an action is Pending or In Progress |

A category that requires a verification while neither the category nor the
company defines a delay is rejected at save time: the module refuses a
configuration that would make the planned verification date impossible to
compute.

## 5. Sequence

Settings, Technical, Sequences, `Change Control Request`.

One global sequence is delivered, prefix `CC/%(year)s/`, padding 5, producing
references such as `CC/2026/00001`.

To use a distinct series per site, create an additional sequence with the same
code `ls.change_control.request` and set its Company. The module resolves the
sequence of the company of the request first, and falls back to the global one.

Never modify the sequence of a company that already holds records: the
references of existing records are not changed, and a discontinuity in the
series must be justifiable to an inspector.

## 6. Scheduled actions

Settings, Technical, Scheduled Actions. Three daily actions are delivered and
active. They may be deactivated, but deactivating them removes the automatic
detection of late items.

## 7. Mail templates

Settings, Technical, Email Templates. Three templates are delivered. They may
be edited to match the wording of the organisation. Edits are preserved by a
module upgrade.

Notifications are queued rather than sent immediately; they leave with the
standard Odoo mail queue.

## 8. Configuration checklist before going live

1. The four groups are assigned, and the assignment has been approved by the quality unit.
2. The impact areas match the scope of the site.
3. Every category in use carries an approval matrix that reflects the approved procedure.
4. Every approval template line either carries a default approver, or the procedure states who assigns approvers.
5. The company parameters are set for every company.
6. The sequence produces the reference format required by the procedure.
7. The three scheduled actions are active.
8. A test change has been run end to end on a validation database and the printed record has been reviewed.
