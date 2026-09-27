# Developer Manual

Module: `ls_supplier_qualification` · Odoo 19 Community Edition

---

## 1. Layout

```
models/     18 model classes across 14 files, one file per model
wizards/    2 transient models plus their form views
security/   groups, ir.model.access.csv, record rules
data/       sequences, standards, categories, criteria, templates,
            mail templates, scheduled actions   (all noupdate="1")
demo/       fictitious data, .invalid addresses
views/      one file per model, plus the menu file
report/     report actions and three QWeb template files
tests/      common.py fixtures plus 13 test modules
tools/      static_check.py, extract_pot.py   (not loaded by Odoo)
i18n/       translation template
doc/        phase documents and manuals
```

## 2. Conventions this module follows

* Line length at most 88 characters.
* Every module, class and method carries a docstring.
* Every model declares `_description`.
* User-facing strings pass through `_()`.
* No `print`, no debugger, no commented-out code, no TODO/FIXME markers.
* Selection lists live at module level as named constants so that other modules
  can import them (`STATE_SELECTION`, `APPROVED_STATES`,
  `CRITICALITY_SELECTION`, and so on).

`python3 tools/static_check.py .` enforces all of the above, plus XML
well-formedness, ACL coverage against declared models, manifest file existence,
module-local external-identifier resolution, and the absence of the deprecated
`<tree>` tag. Run it before every commit.

## 3. Model map

```
ls.supplier.qualification ──┬── ls.supplier.material
                            ├── ls.supplier.assessment ── ls.supplier.assessment.line
                            ├── ls.supplier.audit ── ls.supplier.audit.finding
                            ├── ls.supplier.performance
                            ├── ls.supplier.review
                            └── ls.supplier.signature

configuration:
ls.supplier.standard
ls.supplier.category ──── drives the prerequisites of a dossier
ls.supplier.criterion ─── ls.supplier.assessment.template.line
                                    └── ls.supplier.assessment.template

extended:
res.company, res.config.settings, res.partner, purchase.order
```

Children point up with `qualification_id`. `partner_id` and `company_id` are
stored related fields on the children, so a search by supplier does not need a
join through the dossier.

## 4. The four design decisions worth knowing

**Scoring rules are frozen.** `ls.supplier.assessment` copies
`max_score_per_criterion`, `mandatory_min_score`, `pass_threshold` and
`conditional_threshold` from the template in `create`. `_compute_scores` reads
the copies, never the template. Editing a template cannot change a past result.
`ls.supplier.performance` does the same with the company weights and
thresholds, via `default_get`.

**Prerequisites live in one method.** `_get_blocking_reasons` returns a list of
translated strings. The computed fields `blocking_reasons` and
`is_ready_for_approval`, the `action_submit_for_approval` guard and the approval
wizard all call it. To add a prerequisite, extend that method and nothing else.

**The signature log is append-only in the ORM.** `write` and `unlink` raise
unconditionally. Creation happens through `sign()`, which runs `sudo()` because
no group holds create rights. `verify_chain()` recomputes the SHA-256 chain and
returns the entries whose stored digest no longer matches.

**Partner status fields are not stored.** Their value depends on
`self.env.company`; a stored field would hold one value shared by all
companies. `_search_ls_is_approved_supplier` keeps searching working. Do not
"optimise" these by adding `store=True`. See `doc/05_architecture_review.md`,
finding F-01.

## 5. Extending the module

### 5.1 Add a prerequisite for approval

```python
class LsSupplierQualification(models.Model):
    _inherit = "ls.supplier.qualification"

    def _get_blocking_reasons(self):
        """Add a quality-agreement prerequisite to the standard list."""
        reasons = super()._get_blocking_reasons()
        if not self.quality_agreement_id:
            reasons.append(_("No signed quality agreement is attached."))
        return reasons
```

The banner, the submission guard and the wizard pick it up with no further
change.

### 5.2 Change the purchase policy

```python
class ResPartner(models.Model):
    _inherit = "res.partner"

    def ls_get_qualification_blocking_message(self, products=None):
        """Allow orders below a threshold from unapproved suppliers."""
        if self.env.context.get("ls_skip_qualification_check"):
            return ""
        return super().ls_get_qualification_blocking_message(products=products)
```

### 5.3 Add a state to the dossier

Extend `STATE_SELECTION` by inheriting the field with
`selection_add=[("your_state", "Your State")]` and `ondelete`, add the
transition method, and extend `statusbar_visible` in the form view. Review
`_compute_days_to_expiry` and `_compute_next_dates`, which test membership in
`APPROVED_STATES`.

### 5.4 Add a signature meaning

```python
from odoo.addons.ls_supplier_qualification.models import ls_supplier_signature

class LsSupplierSignature(models.Model):
    _inherit = "ls.supplier.signature"

    meaning = fields.Selection(
        selection_add=[("escalated", "Escalated")],
        ondelete={"escalated": "cascade"},
    )
```

Then call `self.env["ls.supplier.signature"].sign(record=..., meaning="escalated", ...)`.

### 5.5 Bridge to a future suite module

Bridge modules, not edits to this one. Suggested names and content:

| Bridge | Depends on | Adds |
|--------|-----------|------|
| `ls_supplier_qualification_capa` | this, `ls_capa` | A `capa_id` on `ls.supplier.audit.finding` and a button that opens a CAPA from a critical finding. |
| `ls_supplier_qualification_qms` | this, `ls_qms` | A `sop_id` on the dossier and on the category. |
| `ls_supplier_qualification_signature` | this, `ls_electronic_signature` | Overrides `sign()` to delegate to the suite signature service with real re-authentication. |

## 6. Public API surface

Methods intended to be called by other modules or by RPC are listed in
`doc/11_api_documentation.md`. Anything prefixed with a single underscore is
internal; override it if you must, but expect it to change between versions.

Stable, safe to depend on:

* the state transition methods on every model;
* `_get_blocking_reasons`, `_apply_approval`,
  `_check_segregation_of_duties` on the dossier;
* `sign`, `verify_chain`, `action_verify_chain` on the signature log;
* `ls_get_qualification_blocking_message` on `res.partner`;
* `_ls_check_supplier_qualification` on `purchase.order`;
* the module-level selection constants.

## 7. Tests

```bash
odoo-bin -d <db> -i ls_supplier_qualification --test-enable \
    --test-tags /ls_supplier_qualification --stop-after-init
```

`tests/common.py` builds the shared fixture: four users covering the three
groups, two suppliers, two products, two criteria, one template, two categories
and one dossier. Four helpers do the repetitive work: `_create_material`,
`_create_assessment`, `_create_closed_audit`, `_approve`.

Users are created with `new_test_user` from `odoo.tests.common`, which takes
group external identifiers as a string. That is deliberate: it avoids naming
the user-groups field directly, which insulates the suite from a rename in the
platform.

Every test module is tagged `post_install, -at_install`, because the module
extends `purchase` and needs the full registry.

When adding a test, add it to `tests/__init__.py`; the offline checker does not
detect an orphaned test file.

## 8. Translations

```bash
odoo-bin -d <db> --i18n-export=i18n/ls_supplier_qualification.pot \
    --modules=ls_supplier_qualification --stop-after-init
```

`tools/extract_pot.py` produces an offline approximation when no Odoo instance
is available. Regenerate with the official exporter before a release: it
resolves selection labels, model descriptions and inherited views that a static
reader cannot see.

## 9. Release checklist

- [ ] `python3 tools/static_check.py .` reports PASS
- [ ] `flake8` and `pylint --load-plugins=pylint_odoo` clean
- [ ] Test suite green on a clean Odoo 19 Community database
- [ ] Coverage measured and recorded in `doc/12_test_report.md`
- [ ] `.pot` regenerated with the official exporter
- [ ] Version bumped in `__manifest__.py`
- [ ] `doc/CHANGELOG.md` and `doc/RELEASE_NOTES.md` updated
- [ ] The three verification points in `doc/05_architecture_review.md` §5.8
      confirmed against the target build
