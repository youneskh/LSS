# Copyright 2026 Life Sciences Suite
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Root cause investigation attached to a deviation."""

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

INVESTIGATION_STATE_SELECTION = [
    ("draft", "Draft"),
    ("in_progress", "In Progress"),
    ("completed", "Completed"),
]


class LsDeviationInvestigation(models.Model):
    """Structured determination of the root cause of a deviation."""

    _name = "ls.deviation.investigation"
    _description = "Deviation Investigation"
    _inherit = ["mail.thread"]
    _order = "date_started desc, id desc"

    deviation_id = fields.Many2one(
        comodel_name="ls.deviation",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(
        related="deviation_id.company_id",
        store=True,
        index=True,
    )
    name = fields.Char(
        string="Subject",
        required=True,
        help="Short subject of this investigation.",
    )
    rca_method_id = fields.Many2one(
        comodel_name="ls.deviation.rca.method",
        string="RCA Method",
        required=True,
        ondelete="restrict",
        tracking=True,
    )
    investigator_id = fields.Many2one(comodel_name="res.users", required=True,
                                      default=lambda self: self.env.user,
                                      ondelete="restrict",
                                      tracking=True,)
    date_started = fields.Datetime(default=fields.Datetime.now, required=True)
    date_completed = fields.Datetime(readonly=True, copy=False)
    findings = fields.Text(
        help="Facts established during the investigation, including the data "
        "reviewed and the personnel interviewed.",
    )
    contributing_factors = fields.Text()
    root_cause = fields.Text(
        tracking=True,
        help="The determined root cause. Where a root cause cannot be "
        "established, record the most probable cause together with the "
        "rationale for that conclusion.",
    )
    root_cause_determined = fields.Boolean(
        default=True,
        help="Clear when no definitive root cause could be established, in "
        "which case the most probable cause and its rationale are recorded.",
    )
    state = fields.Selection(
        selection=INVESTIGATION_STATE_SELECTION,
        required=True,
        default="draft",
        tracking=True,
    )

    @api.constrains("date_started", "date_completed")
    def _check_dates(self):
        """The completion date cannot precede the start date."""
        for record in self:
            if record.date_completed and record.date_completed < record.date_started:
                raise ValidationError(
                    _(
                        "Investigation '%(subject)s': the completion date "
                        "cannot precede the start date.",
                        subject=record.name,
                    )
                )

    def action_start(self):
        """Move the investigation to ``in_progress``."""
        return self.write({"state": "in_progress"})

    def action_complete(self):
        """Complete the investigation once a root cause is recorded."""
        for record in self:
            if not (record.root_cause or "").strip():
                raise ValidationError(
                    _(
                        "Investigation '%(subject)s' cannot be completed "
                        "without a recorded root cause.",
                        subject=record.name,
                    )
                )
            if not (record.findings or "").strip():
                raise ValidationError(
                    _(
                        "Investigation '%(subject)s' cannot be completed "
                        "without recorded findings.",
                        subject=record.name,
                    )
                )
        return self.write(
            {"state": "completed", "date_completed": fields.Datetime.now()}
        )
