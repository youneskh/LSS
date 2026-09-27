# Phase 5 — Architecture Review

## 5.1 Method

The review asks, for each principle, what the module actually does and where
it falls short. Findings are recorded whether or not they were fixed.

## 5.2 Odoo architecture

| Question | Finding |
|---|---|
| Is the core modified? | No. Two models are extended by inheritance; nothing is patched. |
| Is Enterprise code used or imitated? | No. Nothing is copied, and no Enterprise-only model or view is referenced. |
| Is the MVC separation respected? | Yes. Business rules live in the models; the views hold presentation and no logic beyond visibility expressions. |
| Are ORM idioms used? | Yes. `search`, `filtered`, `mapped` and `create` with a list of values; no raw SQL anywhere, which the static checker verifies. |
| Are Odoo 19 idioms used? | Yes: `models.Constraint`, `<list>`, `<chatter/>`, `_compute_display_name`, `self.env._()`, `res.groups.privilege`. |

## 5.3 OCA conventions

One model per file, files named after the model, alphabetical imports, a
copyright and licence header on every file, AGPL-3 throughout, and a manifest
that names the author and the licence. The module deviates from the OCA
convention of shipping a `readme/` fragment directory; it ships a single
`README.md` and a `doc/` set instead, which suits a validated environment
better because each phase gate is a separate controlled document.

## 5.4 SOLID

| Principle | Assessment |
|---|---|
| Single responsibility | Held. Each model records one thing. The batch record does not compute yields; the batch does. GS1 arithmetic lives in one module that knows nothing about the ORM. |
| Open / closed | Held for the parts likely to change: storage conditions and the dossier structure are data, not code, so a manufacturer adds a climatic zone or a regional section without touching Python. |
| Liskov substitution | Held. The material mixin is abstract and both concrete materials honour its contract; no method is overridden to raise. |
| Interface segregation | Held. The mixin carries only what both materials need; ingredient-specific and excipient-specific fields stay on their own model. |
| Dependency inversion | Partially held. The models depend on the ORM directly, as any Odoo module must. The one piece of domain logic worth isolating, the GS1 arithmetic, is isolated behind pure functions. |

## 5.5 DRY

The release checklist is declared once, in `constants.py`, as a list binding
each entry to its regulatory citation. The persistent model, the wizard and
the printed certificate all derive from that one declaration, and a test
asserts that the derivation still holds. The ICH frequencies are constants,
not literals scattered through the schedule generator. The access file is
generated from a matrix rather than typed.

One residual duplication is accepted: the eight checklist field names appear
both in the constants and as field definitions on two models, because Odoo
fields must be declared statically. The test
`test_release_checklist_and_model_agree` exists precisely to detect drift.

## 5.6 KISS

The module ships no JavaScript, no custom widget and no controller. Every
behaviour is a model method, a constraint, a view or a data record. Where a
simple mechanism sufficed, it was used: the schedule generator is a loop over
months, not a rule engine.

## 5.7 Separation of concerns

| Concern | Where it lives |
|---|---|
| Regulatory citations | `constants.py` and model docstrings |
| GS1 arithmetic | `gs1.py`, no ORM |
| Business rules | Model constraints and action guards |
| Presentation | Views only |
| Configuration | Data records and company settings |
| Verification | `static_check.py` and `tests/` |

## 5.8 Upgradeability

Every data file is `noupdate="1"`, so manufacturer edits survive an upgrade.
No view of another module is inherited, so an upstream layout change cannot
break installation. No private Odoo API is called. The integrity payload
order is fixed by a documented method and must never be reordered for an
existing installation, because doing so would invalidate every stored digest;
that warning is in the method docstring where a future maintainer will see it.

## 5.9 Extensibility

The intended extension points are: adding storage conditions or dossier
template sections as data; pointing `external_reference` on a discrepancy at
a deviation or CAPA record held by another module; inheriting any model of
this module from a site-specific module; and reusing `gs1.py` directly.

## 5.10 Findings

| # | Finding | Disposition |
|---|---|---|
| AR-1 | The batch model is large, carrying the state machine, the yield rules and the navigation helpers | Accepted. Splitting it would scatter one aggregate across files and complicate the guards. |
| AR-2 | Standard product and company views are not extended, so the new fields are not visible on the standard forms | Accepted with a declared deviation; the alternative risked installation failure on an unverified identifier. |
| AR-3 | The checklist field names are duplicated between constants and field declarations | Accepted; a test detects drift. |
| AR-4 | Reports depend on `web.external_layout`, which is resolved at render time | Accepted and recorded as a residual risk. |
| AR-5 | No kanban view is shipped | Accepted; the Odoo 19 kanban template API could not be verified, and a broken kanban is worse than none. |

## Gate verdict

**PASS with five accepted findings.** None of the five is a defect in the
implementation; each is a trade-off taken deliberately and recorded here and,
where it affects a user, in the deviation register.
