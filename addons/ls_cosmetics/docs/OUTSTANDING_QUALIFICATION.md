# Outstanding Qualification Tasks

The module is delivered as **CONDITIONAL PASS**. This is what the receiving
team must complete before production use. Nothing on this list has been done
in the build environment, and no result from it is claimed anywhere in this
deliverable.

---

## 1. Execute the test suite

Roughly 100 test methods exist across 9 files. **None has ever been run** —
the build environment has no Odoo runtime and no PostgreSQL.

```bash
odoo-bin -d <test_db> -i ls_cosmetics --test-enable --stop-after-init \
         --log-level=test
```

| File | Covers |
|---|---|
| `tests/test_ingredient.py` | INCI uniqueness, CMR and exclusion flags, label tokens, annex linkage |
| `tests/test_formulation.py` | 100 % total, duplicate lines, segregation of duties, freezing, annex evaluation, list generation |
| `tests/test_safety_assessment.py` | Part A gating, named-assessor approval, specific assessments, review cron |
| `tests/test_claim.py` | Six criteria, evidence rules, Art. 20(3) declarations |
| `tests/test_label.py` | Article 19(1) particulars, 30-month rule, freezing |
| `tests/test_pif.py` | Article 11(2) items, ten-year clock, archiving gates |
| `tests/test_dz_authorization.py` | Sixteen dossier items, 45-day and 1-month deadlines |
| `tests/test_security.py` | Per-group access rights, multi-company scoping |
| `tests/test_wizards.py` | Versioning, supersession, list preview |

Expect to fix failures. Tests written without execution routinely contain
fixture-ordering and constraint-interaction errors that only a run reveals.

## 2. Measure coverage

```bash
coverage run --source=addons/ls_cosmetics $(which odoo-bin) \
        -d <test_db> -i ls_cosmetics --test-enable --stop-after-init
coverage report -m
```

**No coverage percentage is claimed in this deliverable.** The suite
specification sets a 95 % target; whether this module meets it is unknown
until measured.

## 3. Run the real linters

```bash
pip install flake8 pylint pylint-odoo
flake8 --max-line-length=99 addons/ls_cosmetics
pylint --load-plugins=pylint_odoo -d all -e odoolint addons/ls_cosmetics
```

Not run here — no network access to install them. The custom checker in
`tools/static_check.py` covers a subset: syntax, XML well-formedness, view
field cross-references, button targets, `ref=` resolution, ACL coverage,
manifest reconciliation, placeholder tokens, raw SQL, a PEP 8 subset, licence
headers and docstrings.

## 4. Installation and upgrade test

- Install on a clean Odoo 19 Community database.
- Confirm `post_init_hook` behaves on your server (see ADMIN_GUIDE §2).
- Confirm the inherited product view resolves (see ADMIN_GUIDE §4.3) — this is
  the single most likely installation failure.
- Re-install over itself (`-u ls_cosmetics`) to test the upgrade path.
- Confirm the four groups appear and menu visibility matches intent.

## 5. Load and verify annex data

Populate `ls.cosmetic.restriction` from the current consolidated text, with
provenance on every entry. Verify with a deliberately over-limit formulation
that the blocking finding fires and refuses approval.

## 6. Computer system validation

| Stage | Content |
|---|---|
| URS | Your requirements, traced to the module's fields |
| IQ | Installed version, dependencies, database, addons path |
| OQ | Each workflow and each gate exercised against acceptance criteria |
| PQ | Real dossiers processed by trained users in the production configuration |

The regulatory traceability matrix in `README.md` §2 is the starting point for
the URS trace: it maps specific published provisions to specific fields and
constraints.

## 7. Confirm the ISO 22716 harmonised-standard position

The PIF defaults `gmp_standard` to ISO 22716:2007. Whether that standard is a
harmonised standard conferring the Article 8(2) presumption of conformity at
your date must be confirmed against the current list of harmonised standards.
The module does not assert it.
