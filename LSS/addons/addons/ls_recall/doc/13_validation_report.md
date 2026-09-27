# Validation Report

Module: `ls_recall`
Status: **INCOMPLETE — qualification not performed**

---

## 1. Statement of status

This is not a validation report in the regulatory sense. A validation
report records the outcome of qualification activities that were
performed. Those activities have not been performed.

What this document does is state what a validating organisation would
need to do, what the module already provides towards it, and what is
outstanding. It is an input to your validation, not a substitute for it.

**A supplier cannot validate a system for you.** Validation is against
your intended use, in your environment, with your data and your people.

## 2. What the supplier side has produced

| GAMP-style deliverable | Status | Where |
|------------------------|--------|-------|
| Functional specification | Complete | `03_functional_specification.md` |
| Design specification | Complete | `04_technical_specification.md` |
| Design review | Complete, 8 findings fixed | `05_architecture_review.md` |
| Source code | Complete | the module |
| Unit and integration tests | **Written, never executed** | `tests/`, `12_test_plan_and_report.md` |
| Static analysis | **Executed, passes** | `12_test_plan_and_report.md` §4 |
| Traceability, requirement to test | Complete | `12_test_plan_and_report.md` §2.3 |
| Known limitations | Complete | `14_verification_register.md` |
| Installation instructions | Complete | `06_installation_guide.md` |
| Operating instructions | Complete | `08_user_manual.md`, `09_administrator_manual.md` |

## 3. What the implementing organisation must produce

| Deliverable | Note |
|-------------|------|
| Validation plan | Scope, approach, acceptance criteria, roles |
| User requirements specification | Yours, not this document's. `01_business_analysis.md` is a supplier view and will not match your intended use exactly. |
| Risk assessment | Against patient safety, product quality and data integrity, for your product types |
| Supplier assessment | Note that this module has no commercial supplier behind it; assess accordingly |
| Configuration specification | Roles, plans, sequences, scheduled actions as you set them |
| IQ | Installed version, addons path, database, dependency versions |
| OQ | Execute the automated suite and record the real results; test each closure gate and each write restriction |
| PQ | Walk real recall scenarios with the actual users, including out of hours and including an override |
| Traceability matrix | URS → FS → test, using your URS |
| Validation summary report | Yours |
| Periodic review | Frequency per your procedure |

## 4. Recommended risk-based scope

Highest scrutiny, because failure has regulatory consequence:

1. Distribution tracing — if it misses a consignee, a consignee is not
   contacted. Test against known distribution data, and specifically
   test product distributed outside Odoo.
2. Closure gating and the override path — including that a coordinator
   cannot override.
3. Immutability of sent communications, approved reports and closed
   actions — test over RPC as well as the interface, since that is why
   the restrictions are in `write()`.
4. Effectiveness sampling arithmetic — the rounding-up behaviour at each
   level, with consignee counts that produce fractions.
5. Access rights — each of the three roles against each model.

Lower scrutiny: printed layouts, search filters, scheduled reminders
(they change no state).

## 5. Data integrity assessment

| Aspect | Position |
|--------|----------|
| Attribution | Workflow actions record the acting user and server time |
| Change history | Odoo chatter over `tracking=True` fields, plus explicit chatter entries for reconciliation changes and state transitions |
| Field-level audit trail | **Not provided.** Requires a dedicated module. |
| Electronic signature | **Not provided.** See `02_regulatory_analysis.md` §4. |
| Record alteration | Blocked at application level, not at database level. A direct SQL statement bypasses it. |
| Retention | Outside the module |

Disclose all five of these in your validation file. The last one in
particular: application-level immutability is a real control, but it is
not the same as a tamper-evident store, and an inspector who asks the
question deserves the accurate answer.

## 6. ANPP assessment — reserved

The module asserts no ANPP mapping, because no ANPP-published recall
requirement text could be verified during development
(`02_regulatory_analysis.md` §5).

An implementing organisation in Algeria should:

1. obtain the current ANPP requirements for recall procedures;
2. compare them against §3 of `03_functional_specification.md`;
3. record the comparison, including any gap, in its validation file;
4. where a gap exists, close it by configuration, by procedure, or by
   extending the module through one of the seams in
   `10_developer_manual.md` §2.

This section is deliberately left as a placeholder for that comparison
rather than filled with an unverified mapping.

## 7. Conclusion

| Question | Answer |
|----------|--------|
| Is the module validated? | No. |
| Is it ready to be validated? | Yes, on the evidence in `12_test_plan_and_report.md` §4 — with the open items in `14_verification_register.md` §A resolved first. |
| Can it be used in a regulated environment today? | Not on this evidence. Qualify it first. |
