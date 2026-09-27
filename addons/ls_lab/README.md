# Life Sciences — Laboratory Management (`ls_lab`)

Quality-control laboratory management for **Odoo 19 Community Edition**, built for
regulated Life Sciences environments.

**Version:** 19.0.1.0.0 · **License:** LGPL-3 · **Layer:** 4 (Industry)

---

## What this module does

| Domain | Capability |
|--------|-----------|
| **Controlled masters** | Analytical test methods and product specifications with approval lifecycles, immutability once approved, and explicit version succession. |
| **Sample lifecycle** | Registration against an approved specification, automatic generation of the test list, result capture, second-person review, approval and reporting. |
| **Result integrity** | Conformity is **computed from the approved specification**, never asserted by a user. |
| **Non-conformance** | Automatic OOS on a failing result, two-phase investigation, authorised retest and resample, conclusion and product disposition. |
| **Stability** | Studies with configurable storage conditions and time points that generate pull samples. |
| **Reporting** | Certificates of Analysis and OOS investigation reports as QWeb PDF. |

Ten models, four security groups, three wizards, three notification-only scheduled
actions, two PDF reports, 253 declared fields.

---

## Read this before deploying

### 1. This module has not been installed on a live Odoo 19 server

The build environment had no Odoo runtime and no PostgreSQL server. The module is
**statically verified**, not **live-verified**:

- every Python file compiles;
- every XML file is well-formed;
- every view arch validates against the **real Odoo 19 RNG schemas**, retrieved
  from `github.com/odoo/odoo` branch `19.0` and shipped in `tools/rng/`;
- the static checker reports zero findings, and is itself validated by a
  negative-control harness that seeds 25 known faults and confirms all 25 are
  detected;
- the test suite is **written but not executed**.

The delivery gate is therefore **CONDITIONAL PASS**. See `doc/VALIDATION_REPORT.md`.

### 2. Regulatory compliance is not claimed

This module **supports implementation** of laboratory processes. It does not
certify compliance with any framework. See
`doc/PHASE1-2_BUSINESS_AND_REGULATORY_ANALYSIS.md` for the sourced regulatory
analysis, including which claims are verified and which are not.

### 3. Electronic signatures are NOT 21 CFR Part 11 signatures

The signature wizard records the signing user, a UTC timestamp and the declared
meaning of the signature. It does **not** re-authenticate the user, does not
implement two distinct identification components, and does not cryptographically
bind the signature to the record.

**FDA 21 CFR Part 11 compliance is not claimed.** Organisations requiring Part 11
signatures must implement re-authentication at platform level and validate it.

### 4. No regulatory values are shipped

No storage conditions, time point schedules, shelf-life rules, acceptance limits
or pharmacopoeial content are shipped as data or constants. The consolidated
**ICH Q1 reached Step 2b on 11 April 2025 and had not reached Step 4** at build
time; until it does, the legacy Q1A(R2)–Q1E and Q5C series remain applicable.
Because the governing reference is in transition, all such values are
configuration owned by the implementing organisation.

---

## Installation

```bash
# 1. place the module on the addons path
cp -r ls_lab /mnt/extra-addons/

# 2. verify before installing
python3 /mnt/extra-addons/ls_lab/tools/static_check.py /mnt/extra-addons/ls_lab

# 3. update the apps list and install
odoo -d <database> -i ls_lab --stop-after-init
```

Dependencies: `base`, `mail`, `product`, `stock`, `uom` — all present in Odoo 19
Community. **No Life Sciences Suite module is a hard dependency**, so `ls_lab`
installs standalone.

Full detail: `doc/INSTALLATION_GUIDE.md`.

---

## Security groups

| Group | Can |
|-------|-----|
| Laboratory Viewer | Read everything. |
| Laboratory Analyst | Register samples, record results. Cannot review own results. |
| Laboratory Reviewer | Second-person review, conduct investigations. Cannot approve samples or close investigations. |
| Laboratory Manager | Approve methods, specifications and samples; close investigations; issue certificates; maintain configuration. |

Segregation of duties is enforced at the **ORM layer**, not merely by hiding
buttons: analyst ≠ result reviewer, sample reviewer ≠ approver, OOS investigator ≠
closing approver.

---

## Tooling

| Tool | Purpose |
|------|---------|
| `tools/static_check.py` | Offline checker: compilation, XML, real Odoo 19 RNG validation, field and method resolution, external identifiers, ACL completeness, manifest integrity, forbidden constructs. |
| `tools/negative_control.py` | Seeds 25 known faults and asserts the checker detects each one. A checker that reports nothing is worthless until proven to report something. |
| `tools/retrofit_scan.py` | Scans **other suite modules** for the Odoo 19 construct regressions identified during this build, notably the search-view `<group>` defect. |
| `tools/rng/` | The seven Odoo 19 RNG schemas, retrieved from branch `19.0`. |

---

## Finding of note for the rest of the suite

Odoo 19 ships **no `view.rng`**. It ships one RNG per view type. In that grammar,
`<group>` permits neither `expand` nor `string`.

```xml
<!-- FAILS at install time inside a <search> view -->
<group expand="0" string="Group By"> ... </group>

<!-- CORRECT: Odoo 19 core itself writes it bare -->
<group> ... </group>
```

Form views are **not** RNG-validated, which is why `<group string="...">` is
harmless in a form and fatal in a search view. Run `tools/retrofit_scan.py`
against the other suite modules to find occurrences.

Evidence and citations: `doc/API_VERIFICATION_RECORD.md`.

---

## Documentation

| Document | Contents |
|----------|----------|
| `doc/API_VERIFICATION_RECORD.md` | Every Odoo 19 API fact used, with the source file and line proving it. |
| `doc/PHASE1-2_BUSINESS_AND_REGULATORY_ANALYSIS.md` | Business analysis and sourced regulatory analysis. |
| `doc/PHASE3-5_SPECIFICATION_AND_ARCHITECTURE.md` | Functional spec, technical spec, architecture review. |
| `doc/API_REFERENCE.md` | AST-generated model and field inventory. |
| `doc/INSTALLATION_GUIDE.md` | Installation and upgrade. |
| `doc/CONFIGURATION_GUIDE.md` | Post-installation configuration. |
| `doc/USER_MANUAL.md` | Day-to-day laboratory operation. |
| `doc/ADMINISTRATOR_MANUAL.md` | Roles, parameters, scheduled actions. |
| `doc/DEVELOPER_MANUAL.md` | Extension points and conventions. |
| `doc/TEST_REPORT.md` | Test inventory and execution record **to be completed**. |
| `doc/VALIDATION_REPORT.md` | Delivery gate, what was and was not verified. |
| `doc/SPECIFICATION_DEVIATIONS.md` | Every departure from the suite specification, with rationale. |
| `doc/CHANGELOG.md`, `doc/RELEASE_NOTES.md` | Version history. |
