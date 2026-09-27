# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Quality plans applicable to a product, a process or a project."""

from odoo import _, fields, models
from odoo.exceptions import UserError


class LsQmsQualityPlan(models.Model):
    """Controlled quality plan built from control lines."""

    _name = "ls.qms.quality_plan"
    _description = "Quality Plan"
    _inherit = ["ls.qms.document.mixin"]
    _order = "reference, version desc"

    _ls_qms_sequence_code = "ls.qms.quality_plan"

    _reference_version_uniq = models.Constraint(
        "UNIQUE (reference, version, company_id)",
        "The reference and version of a quality plan must be unique per"
        " company.",
    )

    subject = fields.Char(help="Product, process or project covered by the plan.",)
    scope = fields.Text()
    objective_summary = fields.Text(
        string="Quality Objectives of the Plan",
    )
    line_ids = fields.One2many(
        comodel_name="ls.qms.quality_plan.line",
        inverse_name="quality_plan_id",
        string="Control Lines",
        copy=True,
    )
    line_count = fields.Integer(
        string="Control Lines",
        compute="_compute_line_count",
    )
    sop_ids = fields.Many2many(
        comodel_name="ls.qms.sop",
        string="Applicable Procedures",
    )
    previous_revision_id = fields.Many2one(
        comodel_name="ls.qms.quality_plan",
        readonly=True,
        copy=False,
        index=True,
    )
    next_revision_ids = fields.One2many(
        comodel_name="ls.qms.quality_plan",
        inverse_name="previous_revision_id",
        string="Following Revisions",
        readonly=True,
    )

    def _compute_line_count(self):
        """Count the control lines of each quality plan."""
        for plan in self:
            plan.line_count = len(plan.line_ids)

    def _ls_qms_content_fields(self):
        """Freeze the plan content once the revision is published."""
        return super()._ls_qms_content_fields() + [
            "subject",
            "scope",
            "objective_summary",
            "line_ids",
            "sop_ids",
        ]

    def action_submit_for_review(self):
        """Require at least one control line before the review stage."""
        for plan in self:
            if not plan.line_ids:
                raise UserError(
                    _(
                        "Quality plan %(reference)s has no control line. Add "
                        "at least one control before submitting it for "
                        "review.",
                        reference=plan.reference,
                    )
                )
        return super().action_submit_for_review()
