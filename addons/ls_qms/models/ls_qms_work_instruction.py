# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Work instructions subordinate to a standard operating procedure."""

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class LsQmsWorkInstruction(models.Model):
    """Controlled work instruction detailing one step of a procedure."""

    _name = "ls.qms.work_instruction"
    _description = "Work Instruction"
    _check_company_auto = True
    _inherit = ["ls.qms.document.mixin"]
    _order = "reference, version desc"

    _ls_qms_sequence_code = "ls.qms.work_instruction"

    _reference_version_uniq = models.Constraint(
        "UNIQUE (reference, version, company_id)",
        "The reference and version of a work instruction must be unique per"
        " company.",
    )

    sop_id = fields.Many2one(
        comodel_name="ls.qms.sop",
        string="Parent Procedure",
        required=True,
        index=True,
        check_company=True,
        tracking=True,
        help="Procedure implemented by this work instruction.",
    )
    instruction_body = fields.Html(
        string="Instructions",
        sanitize=True,
        help="Step by step operations to be executed.",
    )
    equipment_reference = fields.Char(help="Identification of the equipment used, when applicable.",)
    safety_precautions = fields.Text()
    estimated_duration_minutes = fields.Integer(
        string="Estimated Duration (Minutes)",
    )
    previous_revision_id = fields.Many2one(comodel_name="ls.qms.work_instruction", readonly=True,
                                           copy=False,
                                           index=True,)
    next_revision_ids = fields.One2many(
        comodel_name="ls.qms.work_instruction",
        inverse_name="previous_revision_id",
        string="Following Revisions",
        readonly=True,
    )

    _duration_positive = models.Constraint(
        "CHECK (estimated_duration_minutes >= 0)",
        "The estimated duration of a work instruction cannot be negative.",
    )

    @api.constrains("sop_id", "company_id")
    def _check_sop_company(self):
        """Keep the work instruction in the company of its procedure."""
        for instruction in self:
            if instruction.sop_id.company_id != instruction.company_id:
                raise ValidationError(
                    _(
                        "Work instruction %(reference)s and its parent "
                        "procedure must belong to the same company.",
                        reference=instruction.reference,
                    )
                )

    def _ls_qms_content_fields(self):
        """Freeze the instruction body once the revision is published."""
        return super()._ls_qms_content_fields() + [
            "sop_id",
            "instruction_body",
            "equipment_reference",
            "safety_precautions",
            "estimated_duration_minutes",
        ]

    def action_submit_for_review(self):
        """Require an instruction body before the review stage."""
        for instruction in self:
            if not instruction.instruction_body:
                raise UserError(
                    _(
                        "The instructions of %(reference)s are empty. "
                        "Complete them before submitting the document for "
                        "review.",
                        reference=instruction.reference,
                    )
                )
        return super().action_submit_for_review()

    def action_publish(self):
        """Forbid publication while the parent procedure is not published."""
        for instruction in self:
            if instruction.sop_id.state != "published":
                raise UserError(
                    _(
                        "Work instruction %(reference)s cannot be published "
                        "because its parent procedure %(sop)s is not "
                        "published.",
                        reference=instruction.reference,
                        sop=instruction.sop_id.reference,
                    )
                )
        return super().action_publish()
