# Life Sciences — Medical Plastics (`ls_medical_plastics`)

Injection moulding execution records, mould/tool register, moulding parameter
specifications and material traceability for medical plastics and
pharmaceutical primary packaging manufacturing.

| Attribute | Value |
|---|---|
| Technical name | `ls_medical_plastics` |
| Version | 19.0.1.0.0 |
| Target platform | Odoo 19.0 **Community** Edition |
| Licence | AGPL-3.0-or-later |
| Author | Life Sciences Suite Architecture Team |
| Depends on | `base`, `mail`, `product`, `stock`, `mrp` |

---

## Scope statement — read this first

This module **supports the implementation** of processes used in regulated
medical plastics manufacturing. It makes no compliance claim.

Specifically, this module:

- does **not** certify compliance with any regulatory framework;
- does **not** implement electronic signatures — the identities it records are
  Odoo user accounts authenticated by the platform;
- does **not** implement deviation management, document control, CAPA, training
  or change control — it provides reference fields as extension points instead;
- has **not** been installed against a live Odoo 19 instance by its authors, and
  its automated tests have **never been executed**.

Validation of the installed system (IQ/OQ/PQ) remains entirely the
responsibility of the operating organisation. See
`doc/VALIDATION_REPORT.md` for the honest delivery status and the list of
qualification tasks that remain outstanding.

---

## What the module does

### Tool and cavity register
Moulds, inserts and fixtures carry a lifecycle state
(draft → qualified → in service → maintenance/quarantine → decommissioned), a
per-cavity register generated automatically from the declared cavity count,
cumulative shot counting, and dual preventive maintenance scheduling on both
shot count and elapsed months. An individual cavity can be blocked with a
recorded reason without withdrawing the whole tool from service.

Shot counting is derived from **closed runs only**, so a run still open for
correction cannot inflate the counter that drives maintenance.

### Moulding parameter specifications
The approved process window for one component on one tool, versioned and
subject to an approval workflow. Only one specification may be approved at a
time for a given component, tool and work centre; approving a new version
supersedes the previous one automatically.

**Segregation of duties is enforced at ORM level:** the author may neither
review nor approve the specification, and the reviewer may not approve it.

### Moulding runs
The production record of one moulding campaign, advancing through
draft → setup → start-up verification → running → completed → reviewed →
closed. The run cannot leave start-up verification while required readings are
missing, material consumption is unrecorded, or a critical parameter is out of
tolerance. Review is blocked for the operator and the setter of the run. A
closed run is frozen against modification and cannot be deleted.

### Append-only parameter readings
Readings cannot be edited or deleted — at the model level *and* in the access
control list, where no role holds write or delete permission on them. A wrong
value is corrected by capturing a new reading that supersedes it and states the
reason; the original entry remains visible in the record and in the printed
report.

Each reading **freezes the acceptance criteria in force at the moment of
capture**, so a later revision of the specification cannot retroactively change
whether a historical reading was in tolerance.

### Material traceability
Resin and masterbatch consumption is recorded per run against qualified grades
and lots. Grades in direct drug contact require a lot reference. The
traceability wizard resolves genealogy in four directions: from a produced lot,
forward from a material lot, or by component or tool over a period.

---

## Installation

See `doc/INSTALLATION.md`. In brief: place the module in the addons path,
update the apps list, and install `ls_medical_plastics`.

## Documentation

| Document | Contents |
|---|---|
| `doc/INSTALLATION.md` | Installation and upgrade procedure |
| `doc/CONFIGURATION.md` | Post-installation configuration sequence |
| `doc/USER_MANUAL.md` | Day-to-day operation by role |
| `doc/ADMINISTRATOR_MANUAL.md` | Roles, access rights, scheduled actions |
| `doc/DEVELOPER_MANUAL.md` | Architecture, extension points, conventions |
| `doc/API_REFERENCE.md` | Models, fields, constraints and methods (generated from source) |
| `doc/REGULATORY_MAPPING.md` | Specific provisions mapped to specific implementation |
| `doc/DEVIATIONS_AND_LIMITATIONS.md` | Every deviation and every known limitation |
| `doc/TEST_REPORT.md` | Test inventory and honest execution status |
| `doc/VALIDATION_REPORT.md` | Delivery gate verdict and outstanding qualification |
| `doc/CHANGELOG.md` | Version history |
| `doc/RELEASE_NOTES.md` | Release summary |

## Security roles

| Group | Capability |
|---|---|
| Viewer | Read-only across the module |
| Operator | Records runs, readings, material consumption and scrap |
| Tool Technician | Tool maintenance and the cavity register |
| Engineer | Components, material grades, tools, draft specifications |
| Manager | Approves specifications, reviews and closes runs, decommissions tools |

Roles form an implication chain, so a manager holds every capability below.

## Support and contribution

Issues and contributions follow the process of the Life Sciences Suite
repository. The module is licensed AGPL-3.0-or-later; see `LICENSE`.
