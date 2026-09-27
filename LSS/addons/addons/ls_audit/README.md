# Life Sciences — Audit Management (`ls_audit`)

Audit programme, fieldwork, findings and reporting for regulated
manufacturing, on **Odoo 19.0 Community Edition**.

| | |
|---|---|
| **Technical name** | `ls_audit` |
| **Version** | 19.0.1.0.0 |
| **Licence** | AGPL-3.0 |
| **Depends on** | `base`, `mail`, `hr` |
| **Models** | 14 (11 persistent, 3 transient) |
| **Security groups** | 4 |
| **Scheduled actions** | 3 |
| **PDF reports** | 2 |

---

## 1. Read this first

### 1.1 This module is not compliance

It is designed to **support** the implementation of an audit process. It
does not certify compliance with any regulatory framework, and it is not
validated software. Compliance depends on your procedures, your computer
system validation, your staff training and your quality system. See
`doc/02_regulatory_analysis.md` for what each framework actually requires
and what this module does or does not do about it.

### 1.2 The approvals here are not 21 CFR Part 11 electronic signatures

Every approval records the acting user, a timestamp, and a tracked change
history in the chatter. That is an **audit trail**, not a signature.
21 CFR 11.50 and 11.200 additionally require the signature manifestation to
carry the printed name, date, time and meaning of the signing, and require
signature components to be re-authenticated at the moment of signing. This
module implements neither. The generated PDF report states this explicitly
in its signature block so that a printed report cannot be mistaken for a
signed one.

Sites that need Part 11 signatures must add a dedicated electronic
signature component and re-validate.

### 1.3 Known limitations

| # | Limitation | Consequence | Remedy |
|---|---|---|---|
| 1 | **Never executed.** Odoo 19 was not available in the build environment, so the test suite has never run. Verification was static only. | Runtime defects are possible. | Run `--test-enable` on a scratch database before any other use. See §4. |
| 2 | No CAPA module exists to depend on. | `capa_reference` on findings is free text, not a link. | Add a bridge module when `ls_capa` exists. |
| 3 | Configuration records carry a **required** `company_id`. | The shipped finding categories belong to the install company only. | Additional companies need their own configuration records. |
| 4 | No kanban views. | Findings and audits use list, form, calendar, graph and pivot only. | Odoo 19 kanban template syntax could not be verified; deliberately omitted rather than shipped broken. |
| 5 | No ISO clause text is shipped. | Clause references are free text. | ISO standard text is copyrighted and cannot be redistributed. |
| 6 | `.pot` covers Python strings only. | Field and view labels are untranslated until exported. | Run Odoo's own exporter once installed (§5). |

---

## 2. What the module does

### 2.1 Object model

```
ls.audit.program            Annual or periodic audit programme
  └── ls.audit.schedule     One audit engagement
        ├── ls.audit.response   One assessed checklist question
        ├── ls.audit.finding    One departure from the audit criteria
        └── ls.audit.report     The report concluding the audit

ls.audit.checklist          Versioned, approved question template
  └── ls.audit.checklist.line

ls.audit.type               Classification (internal / external)
ls.audit.area               Hierarchical auditable area, with an owner
ls.audit.auditor            Auditor qualification register
ls.audit.finding.category   Severity, deadline, CAPA and root cause policy
```

### 2.2 Controls the module enforces

These are the reason the module exists. Each is a hard constraint, not a
warning, and each has a dedicated test.

**Impartiality**

- An audit cannot be saved when a member of the audit team also appears
  among the auditees.
- An audit cannot be saved when a member of the audit team owns one of the
  audited areas.
- A finding cannot be assigned to the auditor who raised it.
- A finding cannot be verified and closed by the auditee who answered it.

**Competence**

- An audit cannot leave `planned` unless its lead auditor holds a current
  qualification flagged as lead auditor.
- An audit cannot leave `planned` when any team member's qualification has
  expired.
- An audit cannot leave `planned` when a team member's qualified scope
  excludes an audited area. An empty scope means no restriction.

**Segregation of duties on reporting**

- The preparer of a report cannot review it.
- The preparer of a report cannot approve it.
- A report cannot be approved before it has been reviewed.
- A report cannot be issued without at least one recipient.

**Evidence and completeness**

- A question cannot be recorded as non-conform or observation without
  evidence.
- An audit cannot be completed while a mandatory question is unanswered.
  Optional questions do not block.
- A finding cannot be closed without a documented verification method and
  a documented verification result.
- A finding category may make a root cause and a CAPA reference mandatory;
  the response wizard enforces whatever the category demands.

**Record integrity**

- Closed and cancelled audits, closed findings and issued reports become
  read-only. Archiving and chatter subscription remain possible so the
  record can still be filed and followed.
- Approved checklists cannot be edited; their questions cannot be added,
  changed or deleted. Changing a checklist means issuing a new version.
- Audits that have left `planned` and findings that have been issued
  cannot be deleted.

### 2.3 Traceability by design

When a checklist is loaded into an audit, the **question text is copied**
into the audit's own records. Publishing a later template version therefore
cannot alter what a past audit actually asked. This is tested explicitly
(`test_template_change_does_not_alter_executed_audit`).

Programmes, audits, findings and reports each receive a reference from a
dedicated sequence: `APG/`, `AUD/`, `FND/`, `ARP/`, each followed by the
year and a four-digit counter.

### 2.4 State machines

| Model | States |
|---|---|
| `ls.audit.program` | draft → approved → in_progress → closed, plus cancelled |
| `ls.audit.schedule` | planned → scheduled → in_progress → completed → follow_up → closed, plus cancelled |
| `ls.audit.finding` | draft → open → responded → in_progress → verification → closed, plus cancelled |
| `ls.audit.report` | draft → under_review → approved → issued, plus cancelled |
| `ls.audit.checklist` | draft → approved → obsolete |

Cancellation of a programme, audit, finding or report always goes through a
wizard that requires a written justification, which is stored on the record
and posted to its chatter.

### 2.5 Scheduled actions

| Action | Frequency | Effect |
|---|---|---|
| Overdue audits | Daily | Schedules one activity for the lead auditor of each audit past its planned date and not yet started. Idempotent: re-running does not duplicate. |
| Overdue findings | Daily | Notifies on findings past their response due date. |
| Auditor qualifications | Weekly | Reports qualifications expiring within 60 days or already expired. Recomputes the stored status before filtering, because it depends on the current date. |

---

## 3. Installation

See `doc/03_installation_guide.md` for the full procedure. In short:

```bash
# 1. Place the module on the addons path
cp -r ls_audit /path/to/addons/

# 2. Install
odoo-bin -d <database> -i ls_audit --stop-after-init
```

Then activate Developer Mode, open **Apps**, and confirm
*Life Sciences - Audit Management* is installed.

## 4. Running the tests — do this before anything else

The suite has **never been executed**. Run it on a scratch database:

```bash
odoo-bin -d test_ls_audit -i ls_audit \
         --test-enable --test-tags /ls_audit \
         --log-level=test --stop-after-init
```

11 test modules cover configuration, programme, audit workflow,
independence, checklist versioning, finding workflow, reporting, security,
scheduled actions and installation structure.

Treat any failure as a defect in this module, not in your database.

## 5. Translations

The shipped `i18n/ls_audit.pot` covers the 103 strings raised by the Python
code. To add field labels, help texts and view strings:

```bash
odoo-bin -d <database> --i18n-export=ls_audit.pot \
         --modules=ls_audit --stop-after-init
```

Then copy the result over `i18n/ls_audit.pot` and create per-language `.po`
files beside it.

## 6. Documentation

| File | Content |
|---|---|
| `doc/01_business_analysis.md` | Objectives, stakeholders, roles, user stories, scope, risks |
| `doc/02_regulatory_analysis.md` | What each framework requires and what this module does about it |
| `doc/03_installation_guide.md` | Installation, upgrade, uninstall, troubleshooting |
| `doc/04_configuration_guide.md` | Setting up types, areas, auditors, categories, checklists |
| `doc/05_user_manual.md` | Running a programme, an audit, findings, reports |
| `doc/06_administrator_manual.md` | Groups, record rules, sequences, crons, backup |
| `doc/07_developer_manual.md` | Architecture, extension points, conventions |
| `doc/08_api_reference.md` | Every public method, its contract and its errors |
| `doc/09_test_report.md` | Test inventory, coverage claim and its limits |
| `doc/10_validation_report.md` | Static verification performed, evidence, residual risk |
| `doc/11_compliance_checklist.md` | Final gate, item by item, with honest verdicts |
| `CHANGELOG.md` | Version history |

## 7. Credits

**Author** — Life Sciences Suite Architecture Team
**Licence** — AGPL-3.0 or later

This module is part of the Life Sciences Suite. It is independent of the
Odoo Enterprise Edition and contains no Enterprise source code.
