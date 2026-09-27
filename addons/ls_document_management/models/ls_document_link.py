# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Links between a controlled document and any other Odoo record.

The link stores the target model name and the target record id, which allows
a document to be attached to records of modules that are not dependencies of
this module, such as the other Life Sciences Suite modules.
"""

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError


class LsDocumentLink(models.Model):
    """Association between a controlled document and a business record."""

    _name = "ls.document.link"
    _description = "Life Sciences Document Link"
    _order = "document_id, res_model, res_id"

    document_id = fields.Many2one(comodel_name="ls.document.document", required=True,
                                  index=True,
                                  ondelete="cascade",)
    company_id = fields.Many2one(comodel_name="res.company", related="document_id.company_id",
                                 store=True,
                                 index=True,)
    res_model = fields.Char(
        string="Linked Model",
        required=True,
        index=True,
        help="Technical name of the model of the linked record.",
    )
    res_id = fields.Many2oneReference(
        string="Linked Record Id",
        model_field="res_model",
        required=True,
        index=True,
    )
    res_name = fields.Char(
        string="Linked Record",
        compute="_compute_res_name",
        store=True,
    )
    relation_type = fields.Selection(
        selection=[
            ("applies_to", "Applies To"),
            ("evidence_for", "Is Evidence For"),
            ("supersedes", "Supersedes"),
            ("references", "References"),
        ],
        string="Relation",
        required=True,
        default="applies_to",
    )
    note = fields.Char()

    _document_target_uniq = models.Constraint(
        "UNIQUE(document_id, res_model, res_id, relation_type)",
        "This record is already linked to the document with the same relation.",
    )

    @api.depends("res_model", "res_id")
    def _compute_res_name(self):
        """Resolve the display name of the linked record.

        Records the user cannot read, and records of models that no longer
        exist, are reported explicitly rather than raising an error, so that
        the document form stays usable.
        """
        for link in self:
            link.res_name = link._resolve_res_name()

    def _resolve_res_name(self):
        """Return the display name of the target record.

        :return: the display name, or an explicit placeholder when the target
            cannot be resolved.
        """
        self.ensure_one()
        if not self.res_model or not self.res_id:
            return ""
        if self.res_model not in self.env:
            return _("Unknown model: %(model)s", model=self.res_model)
        record = self.env[self.res_model].browse(self.res_id)
        if not record.exists():
            return _("Deleted record (id %(res_id)s)", res_id=self.res_id)
        try:
            return record.display_name
        except AccessError:
            return _("Restricted record (id %(res_id)s)", res_id=self.res_id)

    @api.constrains("res_model")
    def _check_res_model(self):
        """Reject links pointing at a model that is not installed."""
        for link in self:
            if link.res_model not in self.env:
                raise ValidationError(
                    _(
                        "Model '%(model)s' does not exist in this database.",
                        model=link.res_model,
                    )
                )

    def action_open_linked_record(self):
        """Open the form view of the linked record."""
        self.ensure_one()
        if self.res_model not in self.env:
            raise ValidationError(
                _(
                    "Model '%(model)s' does not exist in this database.",
                    model=self.res_model,
                )
            )
        return {
            "type": "ir.actions.act_window",
            "res_model": self.res_model,
            "res_id": self.res_id,
            "view_mode": "form",
            "target": "current",
        }
