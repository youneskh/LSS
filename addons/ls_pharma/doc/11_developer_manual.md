# Developer Manual

## 11.1 Conventions in this module

- One model per file, the file named after the model.
- A copyright and licence header on every source file.
- Docstrings in the imperative mood on every module, class and method.
- Line length 88, with URLs exempt.
- Odoo 19 idioms: `models.Constraint`, `<list>`, `<chatter/>`,
  `_compute_display_name`, `self.env._()`, `res.groups.privilege`.
- No raw SQL, no JavaScript, no controller.

## 11.2 Where the logic lives

| Concern | Location |
|---|---|
| Selections, regulatory citations, ICH and GS1 constants | `constants.py` |
| GS1 arithmetic and element strings | `gs1.py`, importable without Odoo |
| State machines and their guards | The `action_*` methods on each model |
| Business rules | `@api.constrains` methods |
| Presentation | `views/` only |

A rule of thumb the module follows: if a rule expresses a separation of duty
or a regulatory precondition, it belongs in a constraint or a guard, never in
a view attribute alone. A view attribute is a convenience for the user; a
constraint is a control.

## 11.3 Extension points

### 11.3.1 Adding data rather than code

Storage conditions and CTD template sections are data records. A new climatic
zone or a regional dossier structure needs no Python.

### 11.3.2 Linking to other suite modules

`ls.pharma.batch_record.discrepancy` carries `external_reference`, a free-text
field intended to hold the reference of a deviation or CAPA record held by
another module. A site that installs `ls_deviation` can replace it with a
many-to-one in a small bridging module:

```python
class LsPharmaBatchRecordDiscrepancy(models.Model):
    _inherit = "ls.pharma.batch_record.discrepancy"

    deviation_id = fields.Many2one(comodel_name="ls.deviation")
```

Do not add such a dependency to this module. It is deliberately standalone.

### 11.3.3 Extending the standard product and company views

This module does not inherit any view it does not own, because the XML
identifiers of the standard product and company views could not be verified
against the Odoo 19 source and an unresolved reference aborts installation.

If you have verified those identifiers for your own build, add a local module:

```python
# in your own module, having confirmed the identifier exists in your build
<record id="product_template_form_pharma" model="ir.ui.view">
    <field name="model">product.template</field>
    <field name="inherit_id" ref="product.product_template_form_view"/>
    <field name="arch" type="xml">
        <xpath expr="//sheet" position="inside">
            <group string="Pharmaceutical">
                <field name="is_pharmaceutical"/>
                <field name="pharma_dosage_form"/>
            </group>
        </xpath>
    </field>
</record>
```

The fields are ordinary fields on `product.template`; nothing in this module
needs to change.

### 11.3.4 Reusing the GS1 module

```python
from odoo.addons.ls_pharma import gs1

gs1.compute_check_digit("629104150021")      # 3
gs1.is_valid_gtin14("03612345000019")        # True
gs1.build_sscc("0361234", "3", "12345")
```

It imports nothing from Odoo, so it can also be unit tested outside a server.

## 11.4 Things not to change

| Item | Why |
|---|---|
| The order of values in `_integrity_payload` | Reordering invalidates every stored digest |
| `perm_unlink` on `ls.pharma.batch.release` | The access file and the model must keep agreeing |
| The `RELEASE_CHECKLIST` structure | The model, the wizard and the certificate all derive from it |
| The Quality Assurance group's implications | The independence of the quality unit is expressed there |

## 11.5 Adding a model

1. Create `models/ls_pharma_<name>.py` with the header and a docstring that
   cites the provision the model supports, if any.
2. Import it in `models/__init__.py`.
3. Add its access rules to `security/ir.model.access.csv`.
4. Add a multi-company record rule unless the model is shared reference data
   or transient, and document the exclusion in the rules file if so.
5. Add views and an action, and a menu if the model is reached directly.
6. Add tests.
7. Run `python3 ls_pharma/static_check.py ls_pharma`. It will tell you if you
   forgot step 3 or 5.

## 11.6 The static checker

`static_check.py` ships inside the module. It reads the sources with `ast`
and `lxml` and uses nothing outside the standard library beyond `lxml`, so it
runs anywhere. Section 8.2 of the static analysis report lists what it
checks; section 8.5 lists what it cannot.

If you extend it, extend the negative controls too. The report records
fifteen injected faults; a check that has never been shown to fail is not
evidence.

## 11.7 Regenerating the derived artefacts

The delivered archive carries a `tools/` directory beside the module:

```bash
python3 tools/generate_api_reference.py ls_pharma   # doc/12_api_reference.md
python3 tools/generate_pot.py ls_pharma             # i18n/ls_pharma.pot
python3 tools/generate_acl.py                       # the access file
python3 tools/generate_ctd_template.py ls_pharma    # the CTD template data
```

The API reference and the access file are generated, not hand written. Edit
the generator, not its output.

For the translation template, prefer the canonical export once you have a
running server:

```bash
odoo-bin -d <database> --i18n-export=ls_pharma.pot --modules=ls_pharma
```
