# Part of the Life Sciences Suite. See LICENSE file for full copyright details.
"""A minimal signable record used to exercise the signature module.

This model exists so that the electronic signature module can be tested and
demonstrated against a real signable model without the production module
carrying a model that has no business purpose. It mirrors the shape of a
typical regulated record: a name, a lifecycle state, a controlled numeric
value and free text.
"""

from odoo import fields, models


class LsSignatureTestRecord(models.Model):
    """A controlled document-like record that can carry signatures."""

    _name = "ls.signature.test.record"
    _description = "Signable Test Record"
    _inherit = ["ls.signature.mixin"]
    _order = "name"

    #: The payload is declared explicitly. An explicit whitelist is stable
    #: across upgrades, whereas a derived list changes whenever a field is
    #: added and would invalidate existing signatures without notice.
    _ls_signature_field_whitelist = ("name", "state", "quantity", "description")

    name = fields.Char(required=True)
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("review", "Under Review"),
            ("released", "Released"),
        ],
        default="draft",
        required=True,
    )
    quantity = fields.Float(default=0.0)
    description = fields.Text()
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.company,
        ondelete="restrict",
    )
