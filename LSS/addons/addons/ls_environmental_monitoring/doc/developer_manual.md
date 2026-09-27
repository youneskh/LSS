# Developer Manual — `ls_environmental_monitoring`

## 1. Layout

```
ls_environmental_monitoring/
├── __manifest__.py            depends on base and mail only
├── models/
│   ├── constants.py           vocabulary; no Odoo imports
│   ├── evaluation.py          pure evaluation and statistics; no Odoo imports
│   ├── ls_env_grade.py        ls_env_area.py       ls_env_parameter.py
│   ├── ls_env_method.py       ls_env_sampling_point.py
│   ├── ls_env_limit.py        ls_env_plan.py       ls_env_plan_line.py
│   ├── ls_env_sample.py       ls_env_result.py     ls_env_excursion.py
│   └── ls_env_trend.py        ls_env_trend_line.py
├── wizards/                   five transient models
├── security/                  groups, global record rules, 46 access rules
├── views/                     eleven view files plus menus
├── data/                      sequences, cron, deliberately empty master data
├── report/                    two QWeb reports
├── tests/                     142 tests
├── doc/                       eleven documents
└── static_check.py            offline checker
```

## 2. The central design decision

**All compliance-critical logic lives in `models/evaluation.py`, which imports
nothing from Odoo.**

Threshold comparison, severity ranking, descriptive statistics and trend
direction are pure functions over plain Python values. They are therefore
testable without a database, and were the only part of the module that could be
executed and measured in an environment with no Odoo runtime: 38 tests, 100%
measured statement coverage.

If you extend the evaluation rules, put the logic there and test it there.

## 3. Data model

```
ls.env.grade ──┐
               ├──> ls.env.area ──> ls.env.sampling_point ──> ls.env.limit
               │                            │                      │
ls.env.parameter ──> ls.env.method          │                      │
       │                    │               │                      │
       └────────────────────┴──> ls.env.plan.line <── ls.env.plan   │
                                      │                            │
                                      v                            │
                                ls.env.sample ──> ls.env.result <───┘ (snapshot)
                                      │                 │
                                      └──> ls.env.excursion <┘
                                
ls.env.trend ──> ls.env.trend.line
```

### Three invariants worth understanding

1. **Limits are versioned, never edited.** Approving a replacement supersedes
   its predecessor. `write` rejects threshold changes on an approved limit;
   `unlink` rejects anything but a draft.

2. **Results snapshot the criteria applied.** `_snapshot_limit` copies the
   thresholds onto the result at evaluation time. A historical evaluation
   therefore never depends on the limit record still holding those values.

3. **State machines are declarative.** `SAMPLE_TRANSITIONS` and
   `EXCURSION_TRANSITIONS` in `constants.py` are the single source of truth.
   `_check_transition` refuses anything not listed. To add a state, add it to
   the selection **and** to the transition map.

## 4. Extension points

### Linking an excursion to a corrective action record

`ls.env.excursion.action_create_external_record` raises by default, reporting
that no such module is installed. Override it:

```python
class LsEnvExcursion(models.Model):
    _inherit = "ls.env.excursion"

    def action_create_external_record(self):
        self.ensure_one()
        capa = self.env["your.capa.model"].create({
            "origin": self.name,
            "description": self.impact_assessment,
        })
        self.external_reference = capa.name
        return {
            "type": "ir.actions.act_window",
            "res_model": "your.capa.model",
            "res_id": capa.id,
            "view_mode": "form",
        }
```

### Changing when an excursion is raised

Override `ls.env.result._requires_excursion`. It returns a boolean per result.

### Adding a parameter type

Add to `PARAMETER_TYPES` in `constants.py`. If the new type represents a count
that cannot be negative, add it to the `counting_types` tuple in
`ls.env.result._check_value_not_negative`.

### Changing the evaluation rules

Override `ls.env.result.action_evaluate`, or replace the pure functions it calls.
Keep the pure functions pure so they remain testable without a database.

## 5. Odoo 19 conventions applied

| Convention | Applied |
|---|---|
| `models.Constraint` replaces `_sql_constraints` | Yes — verified against the official Odoo 19 tutorial |
| `<list>` replaces `<tree>` | Yes |
| Direct attributes replace the `attrs` dictionary | Yes |
| `_compute_display_name` replaces `name_get` | Yes |
| `_read_group` replaces `read_group` | Yes |
| `self.env._()` for translation | Yes — carried forward as a suite convention, not re-verified |
| `<chatter/>` | Yes — carried forward as a suite convention, not re-verified |

Facts that could not be verified were engineered around rather than guessed. The
full record is in `doc/deviations.md` section B. In short: no `res.users` groups
field is referenced, no `ir.rule` group restriction is used, no menu declares a
group, no group implies another, and no group links to a privilege record.

## 6. Testing

```bash
# Offline: static analysis, no Odoo needed
python3 static_check.py

# Offline: prove the checker actually detects faults
python3 ../negative_control.py

# Requires a live Odoo 19 instance
./odoo-bin -d <db> -i ls_environmental_monitoring \
    --test-enable --test-tags /ls_environmental_monitoring
```

The 104 database-backed tests have **never been executed**. Expect failures
arising from the unverified API points above. `doc/test_report.md` states
exactly what was and was not run.

### Extending the static checker

`static_check.py` uses `ast` and `lxml` only. When you add a check, **add a
matching case to `negative_control.py`** and confirm it is caught. Two defects
in the checker itself were found this way during development; without the
negative control both would have produced a falsely clean result.

## 7. Coding standards

- PEP 8, 88-character soft limit
- Docstrings on every public method, stating what it does and what it raises
- No raw SQL; the ORM only, enforced by the static checker
- Type information conveyed through field definitions and docstrings
- No placeholder comments; enforced by the static checker
- AGPL-3.0 header on every Python file; enforced by the static checker
