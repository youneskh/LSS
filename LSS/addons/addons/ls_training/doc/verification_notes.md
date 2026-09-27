# VERIFICATION NOTES

This document records, item by item, what was verified against official
documentation and what was not. It exists because the module was produced
without access to a running Odoo 19 instance.

**Read this before installing.**

---

## 1. Verification status summary

| # | Item | Status | Source |
|---|------|--------|--------|
| 1 | List views use `<list>`, not `<tree>` | **Verified** | Odoo 19.0 developer docs, "View architectures": the root element of list views is `list` (previously `tree`) |
| 2 | `res.groups` uses `privilege_id`, and `res.groups.privilege` carries `category_id` | **Verified** | Odoo 19.0 tutorial "Restrict access to data" instructs creating a group privilege record referencing a `base.module_category_*`, then groups referencing that privilege |
| 3 | `groups_id` renamed to `group_ids` on `ir.ui.menu`, `ir.actions.*`, `ir.ui.view`, `res.users` | **Verified** (secondary sources, consistent) | Two independent Odoo 19 migration write-ups; the Odoo 19 forum answer showing a working `res.groups`/`res.groups.privilege` pair |
| 4 | `ir.rule` group many2many is named `group_ids` | **NOT VERIFIED — see section 2** | Could not be confirmed |
| 5 | `_sql_constraints` list-of-tuples still supported in Odoo 19 | **NOT VERIFIED** | See section 3 |
| 6 | `<chatter/>` element in form views | **NOT VERIFIED** | See section 4 |
| 7 | `ir.cron` field set used here | **NOT VERIFIED** | See section 5 |
| 8 | `hr.employee` still stores `job_id` and `department_id` | **NOT VERIFIED** | See section 6 |

Items 1–3 were confirmed from official Odoo 19.0 documentation or from
sources quoting working Odoo 19 code. Items 4–8 could not be verified from
official documentation and are stated here rather than presented as fact.

---

## 2. `ir.rule` group field — the one item that can block installation

**This information could not be verified from official documentation.**

Up to and including Odoo 18, the many2many from `ir.rule` to `res.groups`
is named `groups`. Odoo 19 pluralised group fields elsewhere
(`groups_id` → `group_ids`). Whether `ir.rule.groups` was renamed to
`ir.rule.group_ids` in the same change could not be confirmed.

**Mitigation shipped with the module.** Two functionally identical files
are provided:

| File | Field name used |
|------|-----------------|
| `security/ls_training_record_rules.xml` (referenced in the manifest) | `group_ids` |
| `security/ls_training_record_rules_alt_groups.xml` (not referenced) | `groups` |

If installation fails with an error such as
`Invalid field 'group_ids' on model 'ir.rule'`, edit `__manifest__.py` and
change the one line:

```python
"security/ls_training_record_rules.xml",
```

to:

```python
"security/ls_training_record_rules_alt_groups.xml",
```

Exactly one of the two files may appear in the manifest at any time.

**Blast radius was deliberately minimised.** All seven multi-company rules
are *global* rules and carry no group field at all, so they are unaffected
either way. Only the six group-scoped rules use the field in question.

`tests/test_security.py::test_record_rules_are_installed` asserts that the
rules loaded, so a wrong assumption surfaces on the first test run rather
than silently.

---

## 3. `_sql_constraints`

**This information could not be verified from official documentation.**

The module declares SQL constraints using the long-standing
`_sql_constraints = [(name, definition, message), ...]` form. Odoo 19 may
offer a newer declarative `models.Constraint` form. Whether the classic
form is deprecated, still supported, or removed in 19 could not be
confirmed.

Risk assessment: low. The classic form has been supported across every
Odoo release the module could be verified against. If it has been removed,
the failure is a clear import- or registry-time error naming the model, and
the eight constraints are listed in `technical_specification.md` for
translation to the newer syntax.

---

## 4. `<chatter/>` form element

**This information could not be verified from official documentation.**

Form views for `ls.training.course`, `ls.training.session`,
`ls.training.certification` and `ls.training.competency.assessment` use the
`<chatter/>` element introduced in Odoo 18, rather than the older
`<div class="oe_chatter">` block containing `message_follower_ids`,
`activity_ids` and `message_ids`.

If the views fail to load, replace each `<chatter/>` with the legacy block.
This affects presentation only; no model logic depends on it.

---

## 5. `ir.cron` fields

**This information could not be verified from official documentation.**

The two scheduled actions in `data/ir_cron_data.xml` set only
`name`, `model_id`, `state`, `code`, `interval_number`, `interval_type`
and `active`. The fields `numbercall`, `doall` and `nextcall` are
deliberately **not** set, because their presence in Odoo 19 could not be
confirmed and omitting them is safe whether they exist or not — Odoo
applies its own defaults.

---

## 6. `hr.employee` field locations

**This information could not be verified from official documentation.**

Odoo 19 restructured the HR application substantially (for example
`hr.contract` was renamed to `hr.version`). This module reads
`hr.employee.job_id`, `hr.employee.department_id`, `hr.employee.company_id`,
`hr.employee.user_id` and `hr.employee.work_email`. Whether all of these
remain stored directly on `hr.employee` in Odoo 19 could not be confirmed.

**This risk directly shaped the architecture.** An earlier design resolved
the training matrix through a PostgreSQL view joining `hr_employee`
columns. That design was rejected in the Phase 5 architecture review
precisely because it would hard-code the physical HR table layout. The
shipped design resolves employees exclusively through the ORM
(`ls.training.requirement._get_target_employees`), so a field that has
moved to a related model still resolves correctly provided it remains
readable from `hr.employee`.

---

## 7. What was NOT executed

The following could not be run in the build environment and **no claim is
made about their outcome**:

| Activity | Status | Reason |
|----------|--------|--------|
| Module installation on Odoo 19 | **Not performed** | No Odoo 19 runtime or PostgreSQL instance available |
| Module upgrade test | **Not performed** | Same |
| Unit / integration / functional test execution | **Not performed** | Same |
| Test coverage measurement | **Not performed** | Requires executing the suite; the 95% target is a *target*, not a measurement |
| `flake8` | **Not performed** | Not installed; network egress disabled, so it could not be installed |
| `pylint` / `pylint-odoo` | **Not performed** | Same |
| Performance testing | **Not performed** | Requires a populated running instance |

### What WAS executed

| Check | Tool | Result |
|-------|------|--------|
| Python syntax, all 24 files | `ast.parse` | PASS |
| XML well-formedness, all 22 files | `lxml.etree.parse` | PASS |
| Manifest completeness (every listed file exists) | custom script | PASS |
| Every XML file referenced by the manifest (except the documented alternate) | custom script | PASS |
| Every internal `ref=""` resolves to a defined XML ID or generated model ID | custom script | PASS — 0 unresolved |
| Every `ir.model.access.csv` model and group reference resolves | custom script | PASS |
| Line length ≤ 79, no trailing whitespace, no tabs | custom script | PASS — 0 issues |
| Docstring on every module, class and function | `ast` | PASS — 264 definitions, 0 missing |
| No `TODO` / `FIXME` / `XXX` / `HACK` tokens | regex | PASS — 0 found |

These custom checks cover a subset of what `flake8` and `pylint-odoo`
would report. They are not a substitute for those tools.

---

## 8. Regulatory statements

No statement in this module or its documentation asserts compliance with,
or certification against, any regulatory framework. All regulatory text
describes how the module **supports** implementation of processes that an
organisation may use as part of its own compliance activities. See
`regulatory_analysis.md`, which states this explicitly and identifies which
requirements the software cannot address at all.
