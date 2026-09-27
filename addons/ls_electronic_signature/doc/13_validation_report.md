# Validation Report

## 1 Status

**This is not a completed validation report. It is the validation input
package.** Computer system validation is performed by the regulated
organisation, in its own environment, against its own intended use. A software
supplier cannot validate a system it has never installed.

This document states what the supplier has done, what remains, and what the
organisation must do.

## 2 What the supplier has completed

| Deliverable | Status | Evidence |
|---|---|---|
| Business analysis | Complete | `01_business_analysis.md` |
| Regulatory analysis against verified primary sources | Complete | `02_regulatory_analysis.md` |
| Functional specification | Complete | `03_functional_specification.md` |
| Technical specification | Complete | `04_technical_specification.md` |
| Architecture review, 12 findings, 10 closed in code | Complete | `05_architecture_review.md` |
| Source code, no placeholders or dead code | Complete | Module source; verified by `static_check.py` |
| Automated test suite, 140 tests, fully traced | **Written, not executed** | `07_test_report.md` |
| Static analysis | **Partial** — stdlib checks pass with 0 findings; flake8/pylint-odoo not installable offline | `08_static_analysis.md` |
| User, administrator, developer manuals and API reference | Complete | `09`–`12` |

## 3 What the organisation must complete

### 3.1 Outstanding qualification tests

| # | Test | Why it cannot be discharged by the supplier |
|---|---|---|
| **OQ-CRED-001** | Password accepted when correct, refused when incorrect, and refused as `invalid_password` rather than `system_error` | The `res.users` password verification API is private and its 19.0 signature could not be verified from official documentation. Must be exercised against the real build. |
| **OQ-VIEW-001** | Every view renders without a parse error | `<chatter/>` and the settings `<app>`/`<block>`/`<setting>` elements could not be verified against 19.0 documentation. |
| **MT-1** | §11.50(b) manifestation legible on printed output | Requires `wkhtmltopdf` and a printer. |
| **MT-2** | §11.300(d) alert delivered end to end | Requires a configured mail server. |
| **MT-3** | Concurrent signing keeps the chain contiguous | Requires two live sessions. |
| **PT-1/PT-2** | Verification time at volume; signing latency | Hardware dependent. |

### 3.2 Documents the organisation owns

A User Requirements Specification stating **its** intended use; a risk
assessment against **its** processes and products; an Installation
Qualification (see `06_installation_configuration.md` §3); Operational and
Performance Qualification; SOPs for signing, for responding to misuse alerts,
for responding to a failed integrity check, and for periodic review; a training
record for every signer; and the 21 CFR 11.100(c) certification letter to the
agency.

## 4 Risk-based validation input

| Function | Patient safety / product quality impact | Suggested rigour |
|---|---|---|
| Signature creation and immutability | **High** — the record of who authorised what | Full OQ with negative testing |
| Hash chain and verification | **High** — detection of falsification | Full OQ including tamper simulation |
| Identity and credential verification | **High** — attribution | Full OQ; OQ-CRED-001 is mandatory |
| Transition policy enforcement | **High** — prevents unauthorised release | Full OQ, including the stale-signature case |
| Attempt logging, alerting, lockout | Medium | OQ including MT-2 |
| Session continuity | Medium | OQ; consider leaving `require_full_credentials` enabled everywhere and reducing this to a configuration check |
| Requests and expiry | Low | Functional testing |
| Reports | Medium (§11.50(b)) | MT-1 |

## 5 Residual risks accepted or transferred

| Risk | Treatment |
|---|---|
| Private credential API changes at a future Odoo release | Isolated in one module; fails loudly, never silently. Re-run OQ-CRED-001 at every upgrade. **Transferred to the upgrade procedure.** |
| Database role cannot create the immutability trigger | Recorded as a fact in a system parameter and surfaced in settings. Three protection layers remain. **Accept only after recording the reduced protection.** |
| Shared or unnamed accounts | Not detectable by software. **Transferred to the organisation.** |
| Partial database restore truncates the chain | Detected within 24 hours by the scheduled verification. **Transferred to the backup procedure.** |
| Notification not delivered | Attempt row is written regardless, on an independent cursor; failure to notify is logged. **Transferred to mail server monitoring.** |
| Model gains a field and invalidates signatures | Prevented by declaring the payload whitelist. **Transferred to the development procedure**, documented in `11_developer_manual.md` §2. |

## 6 Periodic review

| Activity | Frequency |
|---|---|
| Review failed integrity checks | Daily, or on alert |
| Review refused attempts | Per security procedure |
| Confirm ACL invariant and trigger presence | After every upgrade, and at least annually |
| Confirm `attempt_isolated_cursor = 1` | After every restore or upgrade |
| Re-run the automated suite | After every upgrade |
| Review meanings and policies against current SOPs | Annually |

## 7 Supplier statement

The supplier states, without qualification:

1. No claim of compliance with, or certification against, any regulatory
   framework is made.
2. Where information could not be verified from official documentation, the
   document says so explicitly rather than asserting it.
3. The test suite was **written but not executed**; no test result is reported
   as passing.
4. flake8 and pylint-odoo were **not run**, because they could not be installed
   in an offline environment; the substitute checks that were run are listed
   individually.
5. Two architecture review findings (AR-11, AR-12) remain open and mitigated,
   and are carried into the qualification tests above.
