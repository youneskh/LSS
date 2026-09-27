# Phase 6 — Development Report

## 6.1 What was built

| Category | Count | Notes |
|---|---|---|
| Python model files | 26 | One model per file, named after the model |
| Abstract models | 1 | The material mixin |
| Transient models | 3 | The three wizards |
| Pure-function modules | 1 | `gs1.py`, no ORM import |
| View files | 11 | Ten view files and the menu file |
| Report files | 3 | Two templates and the actions |
| Data files | 4 | Sequences, ICH conditions, CTD template, crons |
| Demo files | 1 | Master data only |
| Security files | 3 | Groups, 143 access rules, 22 record rules |
| Test modules | 11 | Including shared fixtures |
| Documentation files | 20 | Nineteen documents in `doc/` plus the README |

## 6.2 Coding rules applied

- Odoo 19 idioms only: `models.Constraint`, `<list>`, `<chatter/>`,
  `_compute_display_name`, `self.env._()`, `res.groups.privilege`.
- A copyright and licence header on every source file.
- A docstring on every module, class and method, in the imperative mood, with
  parameter and return documentation where a method takes or returns
  something non-obvious.
- Line length capped at 88 characters, with one documented exemption: a line
  that carries a URL, because breaking a citation URL makes it unusable.
- No duplicated logic, no dead code, no commented-out code, no `TODO` and no
  `FIXME`. The static checker enforces the last point mechanically.
- No raw SQL. The static checker enforces this too.

## 6.3 Decisions taken during development, and why

| Decision | Reason |
|---|---|
| An abstract mixin shared by the two material models | Satisfies both the model name required by the suite specification and the separate excipient menu without duplicating twelve fields |
| Explicit ancestor-walk loops instead of the private recursion helper | The private helper's name and signature in Odoo 19 could not be verified |
| Global record rules with no group field | The name of the group field on `ir.rule` in Odoo 19 could not be verified |
| `user.has_group()` in guards and `new_test_user` in tests | Avoids naming the groups field on `res.users`, whose Odoo 19 name could not be verified |
| Serial numbers drawn from `secrets`, never from a sequence | Article 4 of Regulation (EU) 2016/161 requires that the value not be possible to deduce |
| The release payload order fixed by one documented method | Reordering it would invalidate every previously stored digest |
| The checklist declared once in the constants | Keeps the model, the wizard and the printed certificate from drifting apart |
| No kanban view and no JavaScript | The Odoo 19 kanban template API could not be verified |

## 6.4 Verification performed during development

| Check | Tool | Result |
|---|---|---|
| Python syntax | `python3 -m py_compile` on every file | Clean |
| XML well-formedness | `lxml.etree.parse` on every file | Clean |
| Field and reference consistency | `static_check.py` | 0 findings |
| Defects found and fixed during the phase | — | A double hyphen inside an XML comment that made the record rules file unparseable; three lines over the length limit; a checker false positive on the legitimate `placeholder` attribute; a checker false positive on citation URLs |

## 6.5 What was not done

`flake8`, `pylint`, `pylint-odoo` and `black` were not run. The build
environment has no network access, so they could not be installed. The line
length and whitespace subset that the static checker enforces is a partial
substitute and is not represented as more than that.

## Gate verdict

**PASS.** The code is complete against the functional and technical
specifications, and every departure is recorded. The absence of the standard
linters is carried into the delivery gate rather than hidden.
