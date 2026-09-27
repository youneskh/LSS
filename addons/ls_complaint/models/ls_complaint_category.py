# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Master data used to classify complaints and to drive configurable targets."""

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

SEVERITY_SELECTION = [
    ("critical", "Critical"),
    ("major", "Major"),
    ("minor", "Minor"),
]


class LsComplaintCategory(models.Model):
    """Configurable complaint category.

    All time targets default to ``0`` which means *not configured*. No
    regulatory timeline is hard-coded by this module: the deploying
    organisation must configure every target according to the requirements
    that apply to it. See ``docs/02_regulatory_analysis.md``.
    """

    _name = "ls.complaint.category"
    _description = "Complaint Category"
    _order = "sequence, name, id"

    name = fields.Char(required=True, translate=True, index=True)
    code = fields.Char(
        required=True,
        help="Short unique code used in reports and imports.",
    )
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,
                                 index=True,)
    description = fields.Text(translate=True)
    default_severity = fields.Selection(selection=SEVERITY_SELECTION, help="Severity proposed when this category is selected. "
                                        "The value can always be overridden by the assessor.",)
    requires_investigation = fields.Boolean(
        default=True,
        help="When enabled, a complaint of this category cannot reach the "
        "Resolution state without at least one approved investigation.",
    )
    acknowledgement_target_days = fields.Integer(
        string="Acknowledgement Target (days)",
        default=0,
        help="Calendar days after receipt by which the complainant should be "
        "acknowledged. 0 means no target is configured.",
    )
    investigation_target_days = fields.Integer(
        string="Investigation Target (days)",
        default=0,
        help="Calendar days after receipt by which the investigation should be "
        "completed. 0 means no target is configured.",
    )
    closure_target_days = fields.Integer(
        string="Closure Target (days)",
        default=0,
        help="Calendar days after receipt by which the complaint should be "
        "closed. 0 means no target is configured.",
    )
    ae_reporting_deadline_days = fields.Integer(
        string="Adverse Event Reporting Deadline (days)",
        default=0,
        help="Calendar days after the awareness date by which a reportable "
        "adverse event must be submitted to the competent authority. "
        "0 means no deadline is configured. This value is NOT pre-filled by "
        "the module: it must be set by Regulatory Affairs on the basis of the "
        "regulations applicable to the product and market.",
    )
    complaint_ids = fields.One2many(
        comodel_name="ls.complaint",
        inverse_name="category_id",
        string="Complaints",
    )
    complaint_count = fields.Integer(compute="_compute_complaint_count",)

    _code_company_uniq = models.Constraint(
        "UNIQUE(code, company_id)",
        "The complaint category code must be unique per company.",
    )

    @api.depends("complaint_ids")
    def _compute_complaint_count(self):
        """Count the complaints attached to each category."""
        data = self.env["ls.complaint"]._read_group(
            domain=[("category_id", "in", self.ids)],
            groupby=["category_id"],
            aggregates=["__count"],
        )
        mapped = {category.id: count for category, count in data}
        for record in self:
            record.complaint_count = mapped.get(record.id, 0)

    @api.constrains(
        "acknowledgement_target_days",
        "investigation_target_days",
        "closure_target_days",
        "ae_reporting_deadline_days",
    )
    def _check_targets_positive(self):
        """Forbid negative day targets."""
        for record in self:
            negatives = [
                value
                for value in (
                    record.acknowledgement_target_days,
                    record.investigation_target_days,
                    record.closure_target_days,
                    record.ae_reporting_deadline_days,
                )
                if value < 0
            ]
            if negatives:
                raise ValidationError(
                    _(
                        "Category '%(name)s': day targets cannot be negative.",
                        name=record.name,
                    )
                )

    @api.constrains("acknowledgement_target_days", "closure_target_days")
    def _check_target_consistency(self):
        """Acknowledgement cannot be due after closure."""
        for record in self:
            if (
                record.acknowledgement_target_days
                and record.closure_target_days
                and record.acknowledgement_target_days > record.closure_target_days
            ):
                raise ValidationError(
                    _(
                        "Category '%(name)s': the acknowledgement target "
                        "(%(ack)s days) cannot be later than the closure "
                        "target (%(closure)s days).",
                        name=record.name,
                        ack=record.acknowledgement_target_days,
                        closure=record.closure_target_days,
                    )
                )

    def action_view_complaints(self):
        """Open the complaints of the current category."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Complaints"),
            "res_model": "ls.complaint",
            "view_mode": "list,form",
            "domain": [("category_id", "=", self.id)],
            "context": {"default_category_id": self.id},
        }
