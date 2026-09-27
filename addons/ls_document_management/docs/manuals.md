# Manuals

Module: `ls_document_management` — Odoo 19 Community.

Contents: Installation Guide, Configuration Guide, User Manual, Administrator
Manual, Developer Manual, API notes.

---

## 1. Installation Guide

### 1.1 Prerequisites

- A running **Odoo 19 Community** instance (on-premise or Odoo.sh).
- PostgreSQL as configured by Odoo.
- Filesystem access to the add-ons path, or a way to deploy custom modules.
- The `base` and `mail` modules (both ship with Odoo).

### 1.2 Steps

1. Place the `ls_document_management` directory in a directory that is on the
   Odoo `addons_path`.
2. Restart the Odoo service so it discovers the new module.
3. Enable developer mode, then *Apps > Update Apps List*.
4. Search for **Life Sciences - Document Management** and click *Install*.

### 1.3 Post-installation

- The install creates the four security groups, the document sequence
  (`DOC-00001` ...) and the daily retention scheduled action (active).
- Assign roles to users (see Administrator Manual).
- If demo data was loaded, a sample folder tree and one document are present;
  do not use demo data in production.

---

## 2. Configuration Guide

All configuration is under **Documents > Configuration** and requires the
Manager role.

### 2.1 Retention policies

*Configuration > Retention Policies*. For each policy set:

- **Code** and **Name** (code is unique per company).
- **Retention Duration** and unit (months or years).
- **Retention Trigger**: *Publication Date* or *Archiving Date*.
- **Advance Notice (Days)**: how many days before the due date a document is
  flagged *Due Soon*.
- **End of Retention Action**: *Notify Document Managers*, or *Archive Document
  and Notify*. Neither deletes records.

Determining which retention period applies to a given record type is an
organisational responsibility; the demo policy is illustrative only.

### 2.2 Folders

*Configuration > Folders*. For each folder set:

- **Name** and optional **Parent Folder** (unlimited nesting; cycles are
  rejected).
- **Default Retention Policy** proposed to documents created in the folder.
- **Read Groups** / **Write Groups**: leave empty for open access to all
  document-role holders, or list groups to restrict. Managers always retain
  access for administration.
- **Default Approvers** proposed on new documents in the folder.

### 2.3 Tags

*Configuration > Tags*. Free-form labels with a colour, unique per company.

---

## 3. User Manual

### 3.1 Creating a document (Editor)

1. *Documents > Documents > New*.
2. Enter the title, choose a folder (retention policy and approvers may be
   proposed automatically), add tags and a description.
3. Click **New Version**, upload the file, and enter a **Summary of Change**
   (mandatory) and an optional reason.
4. Confirm the approver list.
5. Click **Submit for Review**. One approval request is created per approver.

### 3.2 Approving or rejecting (Approver)

1. *Documents > My Approvals* lists items awaiting your decision.
2. Open the document, review the file in the **Version History** tab.
3. On your approval line, click **Approve**, or use **Reject** on the document
   to record a mandatory reason. Rejection returns the document to Draft and
   cancels the other pending approvals.
4. When every approver has approved, the document becomes **Approved**.

### 3.3 Publishing and archiving (Manager)

- **Publish** an approved document to make its latest version the *effective
  version*, with today's date as the effective date. A previously effective
  version is marked superseded.
- **Start Revision** on a published document to return it to Draft while
  keeping the current version in force; upload a new version and resubmit.
- **Archive** a published document to withdraw it from use.
- **Reset to Draft** an approved document before publication if needed.

### 3.4 Retention status

The document shows its **Retention Status**: Not Applicable, Within Retention,
Due Soon, or Retention Elapsed. It is maintained by the daily scheduled action
and by publication/archiving. Set **Legal Hold** to exempt a document from
automatic archiving.

### 3.5 Linking records

In the **Linked Records** tab, add a link by choosing the target model, the
record id and the relation type. Use **Open** to navigate to the record.

### 3.6 Verifying integrity and printing

- **Version History** shows each version's SHA-256 checksum.
- Use the **Document Control Record** print action to produce a PDF of the
  version and approval history.

---

## 4. Administrator Manual

### 4.1 Assigning roles

*Settings > Users & Companies > Users*, open a user, and under the *Document
Management* privilege pick Viewer, Editor, Approver or Manager. Manager implies
Editor and Approver; Editor and Approver each imply Viewer. To keep authoring
and approval segregated for a given person, do not grant both Editor and
Approver unless that separation is not required.

### 4.2 The retention scheduled action

*Settings > Technical > Scheduled Actions >* "Life Sciences Documents:
evaluate retention". It runs daily as OdooBot. It refreshes retention statuses
and, for elapsed documents, notifies managers or archives (per policy). It
never deletes records and never archives a document under legal hold. Adjust
the interval if required; keep it active for retention monitoring to function.

### 4.3 Multi-company

Records are isolated per company by global record rules. Retention policies,
folders and documents each belong to a company. A sub-folder must belong to the
same company as its parent.

### 4.4 Sequence

*Settings > Technical > Sequences >* "Life Sciences Controlled Document"
controls the `DOC-` numbering. It is company-independent by default.

### 4.5 Backups and integrity

Files are stored as Odoo attachments. Follow your standard Odoo backup policy
(database plus filestore). The stored SHA-256 checksums allow post-hoc
detection of file alteration via `verify_integrity()` but are not a substitute
for database access controls and backups.

---

## 5. Developer Manual

### 5.1 Models and key methods

- `ls.document.document`
  - `action_submit_review`, `action_publish`, `action_reject`,
    `action_start_revision`, `action_archive_document`, `action_reset_to_draft`
  - `_evaluate_approvals`, `_create_approvals`, `_pending_approvals`
  - `update_retention_state`, `_cron_evaluate_retention`, `_archive_document`
  - `_check_manager_role` (server-side role guard for publish/archive)
- `ls.document.version`
  - immutable: `write` rejects changes to controlled fields
  - `_build_file_metadata` (size + SHA-256), `verify_integrity`
- `ls.document.approval`
  - `action_approve`, `action_reject`, `_check_decision_allowed`
  - `write` re-checks approver identity for approved/rejected transitions
- `ls.document.folder`
  - `_check_folder_hierarchy` (parent-walk cycle detection)
- `ls.document.link`
  - `Many2oneReference` target; `_resolve_res_name` degrades gracefully

### 5.2 Extension points

- Add document types or metadata by inheriting `ls.document.document`.
- To attach documents to a new model, no change is needed: create
  `ls.document.link` records pointing at it.
- To add an end-of-life behaviour, extend the `end_of_life_action` selection
  and handle it in `_cron_evaluate_retention`. Do not add a deletion path.

### 5.3 Running the tests

```bash
odoo -d <db> -i ls_document_management --test-enable --stop-after-init
```

Tests live in `tests/` and share fixtures in `tests/common.py`.

### 5.4 Odoo 19 specifics relied upon

`models.Constraint` / `models.UniqueIndex`; `Many2oneReference`;
`check_company`; `<list>` and `<chatter/>` view elements;
`res.groups.privilege` with `privilege_id`; `group_ids` / `user.group_ids`;
`ir.cron` without `numbercall`/`doall`. Code written for earlier Odoo versions
will not run unchanged, and vice versa.

---

## 6. API notes

The module adds no custom HTTP controller or JSON endpoint. All models are
accessible through Odoo's standard external API (XML-RPC / JSON-RPC) subject to
the access rights and record rules described above. The immutability of
versions, the approver-identity check and the publish/archive role checks are
enforced server-side and therefore apply to external API calls as well as to
the user interface.
