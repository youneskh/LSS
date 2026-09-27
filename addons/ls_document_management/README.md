# Life Sciences - Document Management (`ls_document_management`)

Controlled document management for regulated Life Sciences environments, built
for **Odoo 19 Community Edition**.

Odoo Community Edition does not ship the Enterprise **Documents** application.
This module provides an independent, controlled document management system
suitable for GxP environments, with folder hierarchy, immutable versioning,
a formal review-and-approval lifecycle, retention policies, document control
records and links to any other Odoo record.

---

## Regulatory notice

This module is designed to **support** the implementation of document control
processes. **It does not by itself make an organisation compliant with any
regulatory framework.** Compliance depends on organisational procedures,
computer system validation, staff training and quality management, none of
which are provided by software alone.

No statement in this module or its documentation should be read as a
certification of compliance with ISO 13485:2016, FDA 21 CFR Part 11, EU GMP
Annex 11, or any other framework. See `docs/regulatory_analysis.md` for the
scope and, importantly, the **limits** of what this module supports.

---

## Features

- **Hierarchical folders** with unlimited nesting and a computed full path.
- **Folder-level access control.** Each folder can restrict which security
  groups may read or modify the documents it contains. Enforced by record
  rules, not only by the user interface.
- **Immutable versioning.** Every version stores one file, a mandatory summary
  of change, the author, and a **SHA-256 checksum** of the content computed at
  creation. The controlled fields of a version cannot be modified after
  creation; a change of content requires a new version.
- **Document lifecycle.** Draft -> Under Review -> Approved -> Published ->
  Archived, with a revision loop that keeps the effective version in force
  while a new one is prepared.
- **Parallel approval routing.** One approval record per approver; the document
  is approved only once every approval is granted. Approval and authoring roles
  are segregated.
- **Retention policies.** Configurable retention period and trigger, with a
  daily scheduled action that flags documents as due soon or elapsed and either
  notifies Document Managers or archives the document. **No retention action
  ever deletes a record.** A legal-hold flag exempts a document from automatic
  archiving.
- **Document Control Record** QWeb PDF report listing the version and approval
  history including checksums.
- **Links to any Odoo record**, so a document can be attached to records of
  other modules (for example the other Life Sciences Suite modules) without
  creating a hard module dependency.
- **Multi-company** isolation through global record rules.
- **Chatter** (messages and activities) on the document.

## Roles

The module defines four roles under the *Document Management* privilege:

| Role | Capabilities |
|------|--------------|
| Viewer | Read documents and version history. |
| Editor | Create documents, upload versions, submit for review. Implies Viewer. |
| Approver | Record approval decisions. Implies Viewer, **not** Editor, to keep authoring and approval segregated. |
| Manager | Configure folders, tags and retention policies; publish and archive. Implies Editor and Approver. |

## Data model

| Model | Purpose |
|-------|---------|
| `ls.document.folder` | Hierarchical storage and access-control unit. |
| `ls.document.document` | Controlled document master record and lifecycle. |
| `ls.document.version` | Immutable file revision with SHA-256 checksum. |
| `ls.document.approval` | One approver's decision on one version. |
| `ls.document.retention_policy` | Retention duration, trigger and end-of-life action. |
| `ls.document.tag` | Free-form categorisation. |
| `ls.document.link` | Link from a document to any Odoo record. |

## Dependencies

`base`, `mail`. The `mail` dependency is required for the chatter (message and
activity history) on documents; it is not requested by the parent
specification but is necessary to deliver the specified Activity History
feature.

## Installation

1. Copy the `ls_document_management` directory into your Odoo add-ons path.
2. Update the app list and install **Life Sciences - Document Management**.
3. Assign the *Document Management* roles to users under
   *Settings > Users & Companies > Users*.

See `docs/installation_guide.md` for details.

## Verification status

The module ships with a test suite of **101 test methods** across seven test
modules. **These tests have not been executed in the environment where this
module was produced**, because that environment had neither an Odoo runtime nor
network access. The tests are provided so that they can be run in a proper Odoo
19 instance:

```
odoo -d <db> -i ls_document_management --test-enable --stop-after-init
```

A static self-check (`selfcheck.py`, kept outside the module) validates Python
compilation, XML well-formedness, manifest/file consistency, access-rights
integrity, XML-id cross-references and the absence of constructs removed in
Odoo 17-19. Its output is recorded in `docs/static_check_output.txt`. **This
static check is not a substitute for running the module in Odoo, for
`pylint-odoo`, or for computer system validation.** See
`docs/validation_report.md` for the honest, itemised status of every claim.

## Licence

AGPL-3.0-or-later. See the OCA licence conventions.
