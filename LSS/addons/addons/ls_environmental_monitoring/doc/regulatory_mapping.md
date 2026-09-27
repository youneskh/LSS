# Regulatory Mapping — `ls_environmental_monitoring`

## Statement of scope

This module **supports** the implementation of environmental monitoring
processes. It does not certify compliance with any regulatory framework, and no
statement in this document should be read as a claim of compliance.

Compliance depends on organisational procedures, system validation, staff
training, the quality management system and ongoing monitoring — none of which
software can supply.

**This module ships no numeric acceptance criteria.** Alert, action and
specification limits are entered and approved by the implementing organisation,
which owns the scientific and regulatory justification for the values it sets.
This is a deliberate design decision, recorded in `doc/deviations.md`.

---

## 1. Verification status of the cited provisions

Each provision below is marked with how it was verified for this delivery.

| Marker | Meaning |
|---|---|
| **V** | Text of the provision was verified against an official or authoritative source during this work |
| **U** | Could not be verified from official documentation during this work |

| Provision | Status | Basis of verification |
|---|---|---|
| 21 CFR 211.42(c)(10)(iv) — a system for monitoring environmental conditions in aseptic processing | **V** | Text confirmed via eCFR (ecfr.gov, 21 CFR Part 211 Subpart C) |
| 21 CFR 211.46(b) — equipment for control of air pressure, micro-organisms, dust, humidity and temperature | **V** | Text confirmed via the FDA aseptic processing guidance document, which quotes the provision |
| 21 CFR 211.113(b) — written procedures to prevent microbiological contamination of sterile products | **V** | Text confirmed via the FDA aseptic processing guidance document |
| EU GMP Annex 1 (2022 revision) — published August 2022 | **V** | Confirmed by multiple independent secondary sources including NSF |
| EU GMP Annex 1 — effective 25 August 2023, except section 8.123 effective 25 August 2024 | **V** | Confirmed by multiple independent secondary sources including NSF |
| EU GMP Annex 1 — requires a documented Contamination Control Strategy, and a risk-based, trended environmental monitoring programme | **V** | Consistently reported across the industry sources reviewed |
| EU GMP Annex 1 — **specific numeric limits** for grades A to D | **U** | The clause-level numeric tables were not verified against the official published text. **No numeric limit from Annex 1 is embedded in this module.** |
| ISO 14644-1 — cleanroom classification by airborne particle concentration | **U** | The standard is referenced by the sources reviewed, but its clause text is not publicly available and was not verified |
| ISO 14644-2 — monitoring plan requirements | **U** | Not verified from the published standard |
| ISO 22716 — GMP guidelines for cosmetics, premises and hygiene provisions | **U** | Clause text not verified |
| ISO 13485:2016 — clause 6.4 work environment and contamination control | **U** | Clause text not verified |
| WHO GMP environmental monitoring guidance | **U** | Specific document and clause not verified |
| ANPP (Algeria) / Algerian BPF requirements | **U** | Official ANPP publications were not available. **No ANPP-specific requirement is claimed by this module.** |

---

## 2. Mapping of verified provisions to implemented features

Only provisions marked **V** above are mapped here. A mapping states how the
module supports a process; it does not assert that the process is compliant.

### 21 CFR 211.42(c)(10)(iv) — a system for monitoring environmental conditions

| Element of the provision | Supporting feature | Where implemented |
|---|---|---|
| A defined system exists | Monitoring plan with approval and versioning | `ls.env.plan`, `ls.env.plan.line` |
| Locations are defined | Sampling points with a recorded selection rationale | `ls.env.sampling_point.selection_rationale` |
| Conditions are monitored | Samples generated on schedule, with recorded collection | `ls.env.sample`, `generate_from_plans` |
| Results are captured | One result per parameter, with the recorded value | `ls.env.result` |
| Results are assessed | Automatic evaluation against approved limits | `ls.env.result.action_evaluate` |
| Out-of-limit conditions are handled | Excursion record with assessment, investigation and closure | `ls.env.excursion` |

### 21 CFR 211.46(b) — control of pressure, micro-organisms, dust, humidity and temperature

| Element of the provision | Supporting feature | Where implemented |
|---|---|---|
| Micro-organisms | Viable air, surface and personnel parameter types | `constants.PARAMETER_TYPES` |
| Dust | Non-viable particle parameter type | `constants.PARAMETER_TYPES` |
| Humidity | Relative humidity parameter type | `constants.PARAMETER_TYPES` |
| Temperature | Temperature parameter type, with lower-bound limits supported | `constants.PARAMETER_TYPES`, `ls.env.limit.direction` |
| Air pressure | Differential pressure parameter type | `constants.PARAMETER_TYPES` |

### 21 CFR 211.113(b) — written procedures

| Element of the provision | Supporting feature | Where implemented |
|---|---|---|
| Procedures are identified | Controlling procedure recorded against each method | `ls.env.method.reference_document` |
| Procedures govern the criteria | Controlling document recorded against each limit | `ls.env.limit.source_reference` |
| Procedures are followed | Method recorded on every result | `ls.env.result.method_id` |

### EU GMP Annex 1 (2022) — risk-based, trended monitoring

| Element | Supporting feature | Where implemented |
|---|---|---|
| Programme is risk-based and justified | Mandatory rationale on plans; selection rationale on points; mandatory justification before a limit is approved | `ls.env.plan.rationale`, `ls.env.sampling_point.selection_rationale`, `ls.env.limit.justification` |
| Programme is linked to a wider strategy | Free-text controlling document reference on grades, methods and limits | `reference_document`, `source_reference` |
| Data are trended | Trend analysis with counts, exceedance rates and summary statistics | `ls.env.trend`, `ls.env.trend.line` |
| Trends are reviewed | Mandatory conclusion before an analysis is marked reviewed | `ls.env.trend.action_review` |
| Programme is periodically reviewed | Review due date on the plan, with a filter for plans due | `ls.env.plan.review_date` |
| Critical locations identified | Critical location flag on sampling points | `ls.env.sampling_point.is_critical` |
| Occupancy state distinguished | At rest and in operation recorded on the sample and used to select limits | `ls.env.sample.occupancy_state` |

---

## 3. Data integrity characteristics (ALCOA+)

The module was designed with the following characteristics. They are described
as design features, not as an assertion that data integrity requirements are
met, which depends on the whole computerised system and its validation.

| Principle | How the module supports it |
|---|---|
| Attributable | Collection, results entry, review and approval each record the acting user and timestamp on the sample |
| Legible | Values are stored in typed fields with the unit recorded against the parameter |
| Contemporaneous | Collection timestamps are set by the system at the moment of the action, and a future collection timestamp is rejected |
| Original | Approved samples and their results are frozen; amendment preserves the original value alongside the correction |
| Accurate | Values are evaluated against approved limits, and the thresholds applied are copied onto the result |
| Complete | A sample cannot be submitted with a missing value; excursions cannot be deleted, only cancelled |
| Consistent | State machines refuse any transition not explicitly declared |
| Enduring | Limits and plans are superseded rather than overwritten; results retain their own copy of the criteria applied |
| Available | All records remain queryable through search views, filters and reports |

---

## 4. What this module deliberately does **not** do

Stating these plainly is more useful than implying wider coverage.

1. **No electronic signatures.** This module does not implement 21 CFR Part 11
   electronic signatures. Approval steps record the acting user and timestamp,
   which is a record of who approved, not a compliant electronic signature. A
   signature capability is the scope of a separate module.
2. **No field-level audit trail.** Change history relies on Odoo's message and
   tracking mechanism on selected fields. A tamper-evident, field-level audit
   trail is the scope of a separate module.
3. **No corrective and preventive action management.** Excursions record the
   assessment and the actions taken, and carry a free-text external reference
   plus an overridable hook (`action_create_external_record`) for a module that
   does manage corrective action.
4. **No deviation management.** Excursions are self-contained; they do not
   create deviation records.
5. **No instrument interface.** Results are entered by a person. There is no
   integration with particle counters or environmental monitoring systems.
6. **No continuous monitoring.** The module records discrete samples. Annex 1
   discusses continuous monitoring in Grade A environments; supporting that
   would require an instrument interface, which is out of scope.
7. **No numeric acceptance criteria.** Repeated here because it is the single
   most important limitation: every threshold must be configured and approved
   by the implementing organisation.
8. **No product disposition decision.** The excursion records a product impact
   assessment. It does not release, reject or quarantine any batch.
9. **No statistical significance testing.** Trend direction is a descriptive
   comparison of two halves of a series and is explicitly labelled as such in
   the user interface.

---

## 5. Qualification activities remaining for the receiving organisation

This module has **not** been installed against a live Odoo 19 instance during
this work. The following remain outstanding and are the responsibility of the
receiving organisation.

1. Installation Qualification: install into the target Odoo 19 Community
   instance and record the outcome.
2. Operational Qualification: execute the supplied test suite against a live
   database and record actual pass and fail results.
3. Performance Qualification: exercise the workflows with production-like data
   volumes and real users.
4. Configuration of all grades, areas, parameters, methods, sampling points,
   limits and plans, each with documented justification.
5. Procedural controls covering who may approve limits and plans, review and
   approve samples, and close excursions.
6. A documented decision on whether the absence of electronic signatures and of
   a field-level audit trail is acceptable for the intended use, or whether the
   companion modules are required.
7. Verification of the unresolved Odoo 19 technical questions recorded in
   `doc/deviations.md`.
