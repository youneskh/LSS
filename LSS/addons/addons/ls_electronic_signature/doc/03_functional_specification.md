# Phase 3 — Functional Specification

## 3.1 Menu structure

The suite specification (§7.14) places the menus under a "Security" root. Odoo
reserves the Settings application for that purpose and offers no "Security"
application menu, so the module supplies its own root. The submenu names follow
the specification.

```
Electronic Signatures                      (root, Signer)
├── Signatures
│   ├── Signature Requests                 action_ls_signature_request
│   ├── My Signatures                      action_ls_signature_log_mine
│   └── Signature Log                      action_ls_signature_log        (Viewer)
├── Monitoring                             (Auditor)
│   ├── Signature Attempts                 action_ls_signature_attempt
│   ├── Signing Sessions                   action_ls_signature_session
│   ├── Integrity Checks                   action_ls_signature_integrity_check
│   └── Verify Chain Now                   action_ls_signature_integrity_run (Manager)
└── Configuration                          (Manager)
    ├── Signature Meanings                 action_ls_signature_meaning
    ├── Signature Policies                 action_ls_signature_policy
    └── Settings                           action_ls_signature_settings
```

Signable models additionally gain, on their own form: a **Sign** button, a
**Request Signature** button, and a signature smart button.

## 3.2 Workflows and state machines

### 3.2.1 Signature execution (no state machine — atomic)

A signature has no lifecycle. It either exists or it does not. This is
deliberate: a record with states could be moved between them, and a signature
that can change is not evidence.

Ordered control sequence, executed by `ls.signature.wizard.action_sign`:

| Step | Check | Failure result |
|---|---|---|
| 1 | Binding statement acknowledged | `policy_violation` |
| 2 | Identification code not locked out | `locked_out`, notified |
| 3 | Submitted code equals session login | `identity_mismatch`, notified |
| 4 | Password required? (session continuity + policy) | — |
| 5 | Password correct | `invalid_password`, notified |
| 5a | Credential API fault | `system_error` — never reported as a wrong password |
| 6 | Meaning is available to this signer | `not_authorised`, notified |
| 7 | Signer is in the policy's authorised groups | `not_authorised`, notified |
| 8 | Reason supplied if the meaning demands one | `reason_missing` |
| 9 | Session registered, signature appended | — |
| 10 | Attempt logged as `success` | — |
| 11 | Originating request closed, if any | — |

### 3.2.2 Signature request

```
draft ──action_send──▶ pending ──(signature executed)──▶ signed
                          │
                          ├──action_decline (reason required)──▶ declined
                          ├──_cron_expire_requests (deadline past)──▶ expired
                          └──action_cancel──▶ cancelled
draft ──action_cancel──▶ cancelled
```

`signed` and `cancelled` are terminal; `action_cancel` refuses them.

### 3.2.3 Signing session

```
(first signature) ──▶ open ──(further signatures)──▶ open
                        ├──idle timeout, scheduled action──▶ closed (idle)
                        └──action_close, Manager──▶ closed (manual)
```

### 3.2.4 Controlled field transition

```
write(vals) ──▶ any transition policy triggered by vals?
                 │ no  ──▶ proceed
                 └ yes ──▶ count signatures that carry the meaning,
                           were executed by an authorised signer,
                           and are still current
                           │ enough ──▶ proceed
                           └ short  ──▶ UserError naming meaning,
                                        required count and present count
```

## 3.3 Approval workflow

Multi-signature approval is expressed by `required_signature_count` together
with `distinct_signers` on a policy. With `distinct_signers = True` (default),
two signatures by the same person count as one. There is no sequential
ordering: Part 11 does not require it, and imposing an order would prevent
legitimate parallel approval.

## 3.4 Business rules

| # | Rule |
|---|---|
| BRU-1 | A signature is executed only by the account that is logged in. |
| BRU-2 | A signature record is never modified or deleted, by anyone, by any route. |
| BRU-3 | A signature stops satisfying a policy as soon as the signed content changes. |
| BRU-4 | A meaning code is unique within a company and matches `^[A-Z][A-Z0-9_]{1,31}$`. |
| BRU-5 | A policy may target only a model that inherits the signature mixin. |
| BRU-6 | A transition policy names an existing field and a target value. |
| BRU-7 | A policy requires at least one signature (database CHECK). |
| BRU-8 | A meaning marked `require_reason` refuses a blank or whitespace-only reason. |
| BRU-9 | Declining a request requires a non-blank reason. |
| BRU-10 | A user who has signed cannot be deleted; archiving is the supported route. |
| BRU-11 | Every attempt is recorded even when the transaction is rolled back. |
| BRU-12 | Chain sequence numbers are contiguous per company, starting at 1. |
| BRU-13 | Without a web session all signature components are required. |
| BRU-14 | A credential API fault is never presented to the signer as a wrong password. |

## 3.5 Notifications

| Event | Recipients | Template | Send mode |
|---|---|---|---|
| Request sent | Expected signers | `mail_template_signature_request` | Queued |
| Attempt refused as possible misuse | `group_ls_signature_security` | `mail_template_signature_alert` | **Forced immediate** — §11.300(d) |
| Chain verification failed | `group_ls_signature_security` | `mail_template_integrity_failure` | **Forced immediate** |

When no recipient or template resolves, a warning is written to the server log
so that the failure to notify is itself evidenced.

## 3.6 Scheduled actions

| Action | Interval | Method |
|---|---|---|
| Verify hash chain | 1 day | `ls.signature.integrity.check._cron_verify_all_companies` |
| Close idle signing sessions | 15 minutes | `ls.signature.session._cron_close_idle_sessions` |
| Expire overdue requests | 1 hour | `ls.signature.request._cron_expire_requests` |

## 3.7 Reports

| Report | Model | Purpose |
|---|---|---|
| `signature_manifestation` (template) | any | Reusable block satisfying §11.50(b); embedded via `t-call` in any report of a signable model. |
| Signature Certificate (PDF) | `ls.signature.log` | Standalone evidence: manifestation, signed record, integrity evidence, and the full signed payload. |

## 3.8 Dashboards and KPIs

Attempts carry a graph view (bar, by day and outcome). The measurable
indicators the module makes available are:

| KPI | Source |
|---|---|
| Signatures executed per period, per meaning, per signer | Signature log group-by |
| Proportion of refused attempts | Attempt log grouped by outcome |
| Lockout events | Attempts with result `locked_out` |
| Stale signatures | Signature log filtered on `is_current = False` |
| Overdue requests | Requests pending past deadline |
| Chain verification pass rate | Integrity check grouped by state |

No dashboard client action is supplied: Odoo 19 Community renders graph and
pivot views natively, and a custom dashboard would be JavaScript requiring
re-qualification at every upgrade.

## 3.9 Search, filters and group-by

| Model | Searchable | Filters | Group by |
|---|---|---|---|
| Signature log | reference, signer name, login, record, meaning, chain hash | My Signatures; Today; All Components Presented | Signer; Meaning; Model; Signature Date |
| Attempt | login, IP, user | Failures Only; Possible Unauthorised Use; Today | Outcome; Identification Code; Date |
| Request | reference, record, signers, meaning | To Sign by Me; Awaiting Signature; Overdue | Status; Meaning; Model |
| Policy | name, model, meaning | Field Transition; Manual; Archived | Model; Meaning; Trigger |
| Meaning | code, name | Reason Mandatory; Archived | Company |
| Session | user | Open; Closed | User; Close Reason |

## 3.10 Actions and wizards

| Wizard | Purpose |
|---|---|
| `ls.signature.wizard` | Executes a signature. The only supported creation path. |
| `ls.signature.decline.wizard` | Records refusal of a request with a mandatory reason. |

| Object action | Model | Purpose |
|---|---|---|
| `action_verify` | log | Verify selected signatures; raises on divergence. |
| `action_open_signed_record` | log | Open the signed record. |
| `action_run_now` | integrity check | Verify the active company's chain immediately. |
| `action_close` | session | Force a signing session closed. |
| `action_ls_sign` | mixin | Open the signature dialog. |
| `action_ls_request_signature` | mixin | Open a draft request. |
| `action_ls_view_signatures` | mixin | List signatures of the record. |

## Gate

**PASS.** Menus, navigation, workflows, state machines, approval mechanics,
business rules, notifications, scheduled actions, reports, KPIs, search
facilities, actions and wizards are specified. Two design exclusions
(no signature lifecycle, no custom dashboard) are stated with reasons.
