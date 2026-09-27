# 10 — Developer Manual

## 1. Adding a new controlled document type

```python
class MyDocument(models.Model):
    _name = "ls.qms.my_document"
    _description = "My Controlled Document"
    _inherit = ["ls.qms.document.mixin"]

    _ls_qms_sequence_code = "ls.qms.my_document"

    _reference_version_uniq = models.Constraint(
        "UNIQUE(reference, version, company_id)",
        "The version of a document must be unique per reference and company.",
    )

    body = fields.Html(string="Body")
    previous_revision_id = fields.Many2one(
        comodel_name="ls.qms.my_document", string="Previous Revision"
    )

    @api.model
    def _ls_qms_content_fields(self):
        return super()._ls_qms_content_fields() | {"body"}
```

Four further steps are required:

1. Add the model name to `LS_QMS_DOCUMENT_MODELS` in
   `models/ls_qms_document_mixin.py`, so that the review reminder covers it.
2. Create the sequence in a data file, with the code declared above.
3. Add three rows to `security/ir.model.access.csv`.
4. Add a global record rule following the pattern of the existing rules.

## 2. Extension points

| Method | Purpose | Contract |
|---|---|---|
| `_ls_qms_content_fields` | Fields frozen once published | Returns a set of field names; call `super()` and use the union operator |
| `_ls_qms_revision_defaults` | Values copied onto the next revision | Returns a dictionary; call `super()` and update it |
| `_ls_qms_signature_hook` | Point where an authenticated signature is collected | Receives the meaning of the signature; must return `True` to let the transition proceed, or raise |
| `_ls_qms_check_group` | Privilege check on a transition | Receives a group external identifier and an action label; raises a user error when the group is absent |
| `action_submit_for_review` | Completeness check before review | Override, verify the fields, then call `super()` |

## 3. Implementing the electronic signature module

`_ls_qms_signature_hook` is called by `action_approve` with the meaning
`"approval"`. A module named `ls_electronic_signature` may override it to
request a second authentication, record the signature and link it to the
record. Until such a module exists, approval records the acting user and the
timestamp only, and this module does not claim otherwise.

## 4. Conventions applied

| Convention | Application |
|---|---|
| Naming of models | `ls.qms.` prefix |
| Naming of private methods | `_ls_qms_` prefix for methods added by this module to shared models |
| Naming of files | One file per model, named after the model |
| Docstrings | Every public and private method carries one |
| Line length | 79 characters |
| Import order | Standard library, third party, Odoo, then module local |

## 5. Running a single test

```bash
odoo-bin -d <database> -u ls_qms --test-enable \
  --test-tags /ls_qms:TestDocumentLifecycle.test_05_segregation_of_duties \
  --stop-after-init
```
