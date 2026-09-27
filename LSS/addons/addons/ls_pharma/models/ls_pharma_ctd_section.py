# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Sections of a Common Technical Document dossier."""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..constants import CTD_MODULES, CTD_SECTION_STATES


class LsPharmaCtdSection(models.Model):
    """One section of a Common Technical Document dossier.

    A record with ``is_template`` set belongs to the reusable structure
    shipped with the module and is not attached to a dossier.  A record
    without that flag belongs to one dossier and tracks the preparation of
    that section.
    """

    _name = "ls.pharma.ctd.section"
    _description = "CTD Dossier Section"
    _order = "module, sequence, code, id"

    sequence = fields.Integer(default=10)
    dossier_id = fields.Many2one(comodel_name="ls.pharma.ctd_dossier", ondelete="cascade",
                                 index=True,)
    company_id = fields.Many2one(comodel_name="res.company", related="dossier_id.company_id",
                                 store=True,
                                 index=True,)
    is_template = fields.Boolean(
        string="Template Section",
        default=False,
        help=(
            "A template section belongs to the reusable structure of "
            "ICH M4(R4) and is copied into a dossier when the template is "
            "loaded."
        ),
    )
    module = fields.Selection(
        selection=CTD_MODULES,
        string="CTD Module",
        required=True,
        index=True,
    )
    code = fields.Char(
        string="Section Number",
        required=True,
        help="Section number as it appears in the Common Technical Document.",
    )
    name = fields.Char(string="Section Title", required=True, translate=True)
    responsible_user_id = fields.Many2one(
        comodel_name="res.users", string="Responsible"
    )
    date_due = fields.Date(string="Due Date")
    document_reference = fields.Char(help="Reference of the document that satisfies this section.",)
    state = fields.Selection(
        selection=CTD_SECTION_STATES,
        string="Status",
        default="not_started",
        required=True,
        index=True,
        copy=False,
    )
    deficiency_note = fields.Text(string="Deficiency")
    note = fields.Text(string="Notes")

    @api.depends("code", "name")
    def _compute_display_name(self):
        """Show the section number together with its title."""
        for section in self:
            section.display_name = "%s %s" % (section.code or "", section.name or "")

    @api.constrains("is_template", "dossier_id")
    def _check_template_has_no_dossier(self):
        """Reject a template section that is attached to a dossier."""
        for section in self:
            if section.is_template and section.dossier_id:
                raise ValidationError(
                    self.env._(
                        "A template section cannot belong to a dossier."
                    )
                )
            if not section.is_template and not section.dossier_id:
                raise ValidationError(
                    self.env._(
                        "Section %(code)s must belong to a dossier or be "
                        "marked as a template section.",
                        code=section.code,
                    )
                )

    @api.constrains("state", "deficiency_note")
    def _check_deficiency_note(self):
        """Require the deficiency to be described when it is recorded."""
        for section in self:
            if section.state == "deficiency" and not section.deficiency_note:
                raise ValidationError(
                    self.env._(
                        "Section %(code)s is in deficiency and the deficiency "
                        "must be described.",
                        code=section.code,
                    )
                )

    def action_start(self):
        """Move the selected sections to the preparation state."""
        self.write({"state": "in_preparation"})
        return True

    def action_mark_ready(self):
        """Declare the selected sections ready."""
        for section in self:
            if not section.document_reference:
                raise UserError(
                    self.env._(
                        "Section %(code)s cannot be declared ready without a "
                        "document reference.",
                        code=section.code,
                    )
                )
        self.write({"state": "ready"})
        return True

    def action_mark_complete(self):
        """Mark the selected sections as complete."""
        self.write({"state": "complete"})
        return True
