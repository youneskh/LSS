# Phase 1 — Business Analysis

## 1.1 Business objectives

| # | Objective |
|---|---|
| BO-1 | Allow a regulated organisation to replace handwritten approval signatures on Odoo records with electronic signatures. |
| BO-2 | Produce evidence of each signature that survives inspection: who signed, when, what it meant, and what exactly was signed. |
| BO-3 | Make undetected alteration of signature evidence infeasible for anyone holding ordinary application or database access. |
| BO-4 | Prevent a record from advancing through its lifecycle until the signatures its procedures require are present and still valid. |
| BO-5 | Detect and report attempted misuse of identification codes and passwords without delay. |
| BO-6 | Keep the technical footprint small enough to be validated economically: no Enterprise code, no external services, no custom JavaScript. |

## 1.2 Business requirements

| # | Requirement | Objective |
|---|---|---|
| BR-1 | A signature shall record the signer's printed name, the instant of signing, and the meaning of the signature. | BO-2 |
| BR-2 | Those three items shall appear in every human readable rendering, including PDF. | BO-2 |
| BR-3 | A signature shall be bound to the content it attests to, such that later modification of that content is visible. | BO-2, BO-3 |
| BR-4 | A signature record shall not be modifiable or deletable by any user, including administrators. | BO-3 |
| BR-5 | Executing a signature shall require the signer to re-present credentials. | BO-1 |
| BR-6 | A signature shall be executable only by the account that is logged in. | BO-1 |
| BR-7 | The set of admissible meanings shall be configurable and access controlled. | BO-1 |
| BR-8 | Configuration shall express where signatures are required, how many, and by whom. | BO-4 |
| BR-9 | A controlled state transition shall be refused when its signatures are absent or stale. | BO-4 |
| BR-10 | Every signature attempt, successful or refused, shall be recorded. | BO-5 |
| BR-11 | A refused attempt indicating possible misuse shall notify a designated security unit immediately. | BO-5 |
| BR-12 | Repeated failures shall block further attempts for a configurable period. | BO-5 |
| BR-13 | The integrity of the whole signature history shall be verifiable on demand and on a schedule. | BO-3 |
| BR-14 | Signatures shall be routable as work items with an expected signer and a deadline. | BO-1 |
| BR-15 | The module shall run on Odoo 19 Community with no Enterprise dependency. | BO-6 |

## 1.3 Stakeholders

| Stakeholder | Interest |
|---|---|
| Quality Assurance | Owns the signature meanings and the policies; releases product on the strength of these signatures. |
| Production and Laboratory personnel | Execute signatures as part of daily work; need the dialog to be fast and unambiguous. |
| Regulatory Affairs | Must be able to show an inspector what was signed, by whom, and that it has not changed. |
| System Security Unit | Named in 21 CFR 11.300(d); receives misuse notifications and investigates. |
| Validation team | Qualifies the module; needs a small, deterministic, testable surface. |
| IT administration | Installs, configures, backs up, and monitors. |
| Internal and external auditors | Read the evidence; must be unable to alter it. |

## 1.4 User roles

| Role | Group | May |
|---|---|---|
| Signer | `group_ls_signature_signer` | Execute signatures; see their own signature history; create and answer requests. |
| Viewer | `group_ls_signature_viewer` | Read all signatures and requests of accessible companies. |
| Auditor | `group_ls_signature_auditor` | Additionally read attempts, sessions and integrity checks. Read only by design. |
| Manager | `group_ls_signature_manager` | Additionally configure meanings, policies and settings. Holds **no** write or delete right over signature evidence. |
| Security Unit | `group_ls_signature_security` | Receives misuse notifications. |

## 1.5 User stories

| # | Story |
|---|---|
| US-1 | As a QA officer, I approve a batch record with my credentials so that release is authorised by a named person. |
| US-2 | As a QA officer, I see immediately that a previously approved record has since been edited, so I do not release on a stale approval. |
| US-3 | As a production supervisor, I request a second signature from a colleague with a deadline. |
| US-4 | As a signer, I refuse a request and record why, so that the refusal is part of the record. |
| US-5 | As an auditor, I open a signature and read the exact content that was signed, without trusting the record's present state. |
| US-6 | As an auditor, I print a signature certificate for an inspection dossier. |
| US-7 | As a security officer, I am notified within seconds when someone attempts to sign under another person's identification code. |
| US-8 | As a validation engineer, I run a chain verification and obtain a dated, stored result I can attach to a report. |
| US-9 | As a QA manager, I configure that release requires two approvals by two different people. |
| US-10 | As an administrator, I confirm from the settings screen that database level immutability is active. |

## 1.6 Use cases

| # | Use case | Primary actor | Outcome |
|---|---|---|---|
| UC-1 | Execute a signature | Signer | Append-only signature row created; attempt logged as success. |
| UC-2 | Refuse a signature (wrong password) | Signer | No signature; attempt logged; security unit notified. |
| UC-3 | Attempt under another identity | Any user | No signature; attempt logged as identity mismatch; security unit notified. |
| UC-4 | Lock out after repeated failure | System | Further attempts refused for the configured window. |
| UC-5 | Block a controlled transition | System | `UserError` naming the missing meaning and count. |
| UC-6 | Detect a stale signature | System | `is_current` false; signature stops counting toward policies. |
| UC-7 | Route a request | Signer | Request pending; expected signers notified. |
| UC-8 | Expire a request | Scheduler | Overdue pending request moved to expired. |
| UC-9 | Verify the chain | Auditor or scheduler | Stored, dated pass or fail result. |
| UC-10 | Print a certificate | Auditor | PDF carrying the manifestation and the integrity evidence. |

## 1.7 Functional scope

In scope: signature meanings; signature policies; signature execution with
credential re-verification; append-only signature log with hash chain; session
continuity tracking; attempt logging, alerting and lockout; signature requests
with deadline and expiry; chain verification, manual and scheduled; QWeb
manifestation block and certificate report; the mixin that makes any model
signable; settings; access rights and record rules; multi-company isolation.

## 1.8 Out of scope

Explicitly **not** provided, each with its reason:

| Excluded | Reason |
|---|---|
| Handwritten signature capture on a tablet | 21 CFR 11.200(b) covers biometrics; a drawn image is neither biometric nor a second identification component, so it would add validation burden without adding control. |
| Biometric authentication | Requires hardware and a vendor-specific driver; out of the module's boundary. |
| PKI or X.509 digital signatures | Not required by Part 11; would introduce key lifecycle management, itself a validated process. |
| A general audit trail of all field changes | Belongs to `ls_audit_trail` (specification §7.15). This module records signatures, not every change. |
| Document management and versioning | Belongs to `ls_document_management` (specification §7.7). |
| Identity proofing of the signer before account issuance | 21 CFR 11.100(b) places this obligation on the organisation, not on software. |
| The certification letter to the FDA | 21 CFR 11.100(c) requires a written certification from the organisation to the agency. Software cannot issue it. |
| Custom JavaScript or OWL components | See §5.4 of the architecture review: every line of custom front-end code must be re-qualified at each upgrade, and none is needed here. |

## 1.9 Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R-1 | The private `res.users` password API differs on the target 19.0 build. | Medium | High | Isolated adapter with run-time detection, an explicit override parameter, and a loud failure that is never reported to the signer as a wrong password. Qualification test OQ-CRED-001. |
| R-2 | A database role lacks trigger privileges, so DB-level immutability is absent. | Low | Medium | Installation records the outcome in a system parameter, surfaces it in settings, and the test suite skips rather than falsely passing. Python and ACL protections remain. |
| R-3 | A model uses the derived payload default, then gains a field, invalidating every existing signature. | Medium | High | The mixin documents the whitelist as the correct practice; the fixture model demonstrates it; the developer manual states it as a rule. |
| R-4 | A signature is executed on a shared account. | Medium | High | Outside software control. The administrator manual states named accounts as a precondition; 21 CFR 11.100(a) places the obligation on the organisation. |
| R-5 | Backup or replication tooling restores an older signature table, silently truncating the chain. | Low | High | Chain verification detects sequence gaps; the daily scheduled action bounds detection latency to 24 hours. |
| R-6 | Notification e-mail is not delivered, so a misuse alert is missed. | Medium | Medium | The attempt row is written regardless, on an independent cursor, and a warning is logged when no recipient or template resolves. |
| R-7 | A view element used here is renamed in a later Odoo release. | Medium | Low | Qualification test OQ-VIEW-001; views are the only version-sensitive surface. |

## 1.10 Success criteria

| # | Criterion | How verified |
|---|---|---|
| SC-1 | Module installs and upgrades on a clean Odoo 19 Community database. | `test_install.py` |
| SC-2 | No access right anywhere grants write or delete on the signature log or the attempt log. | `test_install.py` |
| SC-3 | Modification is refused via ORM, via `sudo()`, and via direct SQL. | `test_log_immutability.py` |
| SC-4 | A tampered payload and a deleted entry are both detected. | `test_log_chain.py`, `test_integrity_check.py` |
| SC-5 | A signature cannot be attributed to another person. | `test_security.py` |
| SC-6 | A controlled transition is blocked when unsigned and after the record changes. | `test_mixin.py` |
| SC-7 | Lockout engages at the configured threshold and clears on success. | `test_attempt.py`, `test_wizard.py` |
| SC-8 | Static analysis reports no blocking finding. | Phase 8 |

## Gate

**PASS.** Objectives, requirements, roles, stories, use cases, scope,
exclusions with reasons, risks with mitigations, and measurable success
criteria are defined. No item is deferred.
