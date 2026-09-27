# Validation Report — `ls_medical_device`

**Verdict: CONDITIONAL PASS.**

The module is structurally complete and passes every check that could be
performed offline. It has **never been installed against a running Odoo 19
instance**, and its test suite has **never been executed**. It is not
qualified for use in a regulated environment until the activities in section 5
are completed by the receiving organisation.

## 1. Phase gates

| Phase | Gate | Basis |
|---|---|---|
| 1 Business analysis | PASS | Scope, roles and out-of-scope items defined; see README section "What this module does not do" |
| 2 Regulatory analysis | PASS | Provisions identified and mapped; unverifiable items declared, not asserted |
| 3 Functional specification | PASS | Menus, workflows, state machines, reports and wizards realised |
| 4 Technical specification | PASS | 17 models, 350 fields, 26 SQL constraints, 30 Python constraints, 45 ACL lines, 11 record rules |
| 5 Architecture review | PASS | Section 2 below |
| 6 Development | PASS | 7,819 Python lines, 3,719 XML lines; no placeholders, no raw SQL, no dead code |
| 7 Testing | **FAIL** | 137 tests written; **none executed**; no coverage measured |
| 8 Static analysis | **CONDITIONAL PASS** | Custom offline checker passes and is validated by 16 negative controls; `flake8`, `pylint`, `pylint-odoo` not run |
| 9 Documentation | PASS | Ten documents; API reference generated from source |
| 10 Final validation | **CONDITIONAL PASS** | Contingent on phases 7 and 8 |

Phase 7 is recorded as **FAIL**, not as a conditional pass. A suite that has
never run is not evidence. The master framework states that a phase cannot be
passed until its issues are resolved; resolving this one requires an Odoo
runtime, which the build environment does not provide.

## 2. Architecture review

| Criterion | Assessment |
|---|---|
| Odoo architecture | Standard module layout; models, views, security, data, reports, wizards separated |
| OCA conventions | AGPL-3, per-model files, sequenced data, docstrings, no core modification |
| SOLID | Each model owns one regulatory artefact; the controlled-record pattern is applied uniformly rather than duplicated ad hoc |
| DRY | Shared selections and regulatory values centralised in `constants.py`; the approval workflow follows one shape across six models |
| KISS | No custom JavaScript, no OWL components, no controllers. Nothing was added that could not be verified against Odoo 19 |
| Separation of concerns | Regulatory values in `constants.py` with sources; configuration in `data/`; behaviour in models |
| Upgradeability | No core inheritance beyond mixins; no unverified field names in data files; crons created through a registry-aware hook |
| Extensibility | No dependency on other suite modules; integration by inheritance, documented in the developer manual |
| Security | Two enforcement layers: ACL plus Python authority checks that survive programmatic access |

### Accepted architectural limitations

- **Record rules are global only.** Access-level differentiation is carried by
  ACL and Python checks. Cause: the `ir.rule` groups field name in Odoo 19.0
  could not be verified.
- **No kanban views and no custom JavaScript.** The Odoo 19 template API could
  not be verified; shipping an unverifiable template risks a broken view.
- **Scheduled actions created in Python.** The `ir.cron` field set could not be
  verified.

Each limitation trades a feature for installability. That is the correct trade
in a regulated context, but it is a trade, and it is recorded here rather than
presented as a design preference.

## 3. Regulatory support — what is and is not claimed

This module **supports** the implementation of processes aligned with the
provisions below. It **does not certify compliance** with any of them.

Verified provisions applied: MDR Articles 10(8), 27, 56(2), 61(11), 83, 84,
85, 86(1), 86(2), 88; Annexes I, II, III, XIII Section 2; ISO 14971:2019
process structure.

Explicitly not implemented: vigilance case management (Article 87), EUDAMED
submission, electronic signatures (21 CFR Part 11), Annex VIII classification
rules, UDI carrier generation.

### Items that could not be verified

| Item | Treatment |
|---|---|
| MDR Annex II section titles | Shipped as editable template data; section 6 title flagged as unconfirmed |
| ISO 14971 severity and probability categories | Shipped as configuration defaults; the standard requires the manufacturer to define its own |
| Risk matrix boundaries | Configuration defaults, informative only; the recorded decision governs |
| Notified body designations | None shipped; the register is populated by the organisation |
| EUDAMED legacy-device registration deadline | Sources differ (27 vs 28 November 2026); neither asserted |
| ANPP / Algerian BPF requirements | **Not claimed.** No official ANPP publication was available to verify any requirement |

## 4. Evidence actually held

| Evidence | Held |
|---|---|
| Python syntax verified, 33 files | Yes |
| XML well-formed, 25 files | Yes |
| Static checker passes | Yes |
| Static checker validated by 16 injected faults | Yes |
| Regulatory values traced to a cited source | Yes |
| Module installs | **No** |
| Module upgrades | **No** |
| Tests pass | **No — never executed** |
| Coverage ≥ 95% | **No — never measured** |
| `flake8` / `pylint-odoo` clean | **No — not run** |
| Views render | **No** |
| PDF reports render | **No** |

## 5. Outstanding qualification activities

The receiving organisation must complete the following before regulated use.

**Installation qualification (IQ)**
1. Install on a validated Odoo 19.0 Community instance and record the outcome.
2. Confirm the artefacts listed in `installation_guide.md` section 4.
3. Record the Odoo version, PostgreSQL version and Python version used.

**Operational qualification (OQ)**
4. Execute the 137-test suite; record passes, failures and the remedy for each
   failure.
5. Measure coverage and record the figure against the 95% target.
6. Run `flake8`, `pylint` and `pylint-odoo`; record and resolve findings.
7. Open every view and confirm it renders. The static checker validates view
   structure, not rendering.
8. Render all three PDF reports.
9. Exercise each workflow interactively at each of the four access levels.
10. Confirm both scheduled actions execute.

**Performance qualification (PQ)**
11. Verify the module against the organisation's own user requirements
    specification.
12. Confirm the Annex II section titles against the Official Journal text and
    correct the templates where they differ.
13. Define the ISO 14971 severity and probability scales in the risk
    management plan and reconcile them with `constants.py`.
14. Confirm the notified body scope notes on classes Is, Im and Ir.
15. Populate the notified body register from the current published
    designations and record the verification date.
16. Confirm the current EUDAMED obligations applicable to the organisation.
17. Perform user acceptance testing with the intended user population.

**Ongoing**
18. Establish periodic review of the regulatory values in `constants.py`
    against the current text of the Regulation.
19. Establish a change control process for the configuration data.

## 6. Statement

Software alone does not establish regulatory compliance. Compliance depends on
the organisation's procedures, its system validation, the competence of its
staff, its quality management system and its ongoing monitoring. This module is
one input to that system. Nothing in this report should be read as a
certification, and no statement in it should be relied upon without the
organisation performing its own verification.
