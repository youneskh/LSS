# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Time points of a stability study."""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..constants import TIMEPOINT_STATES


class LsPharmaStabilityTimepoint(models.Model):
    """A scheduled pull point of a stability study.

    A time point is the intersection of one storage condition and one month
    of the study.  It is the unit at which samples are pulled and at which
    results are recorded.
    """

    _name = "ls.pharma.stability.timepoint"
    _description = "Stability Study Time Point"
    _order = "study_id, condition_id, month, id"

    _study_condition_month_uniq = models.Constraint(
        "UNIQUE(study_id, condition_id, month)",
        "A stability study can only have one time point per storage "
        "condition and month.",
    )

    study_id = fields.Many2one(comodel_name="ls.pharma.stability_study", required=True,
                               ondelete="cascade",
                               index=True,)
    company_id = fields.Many2one(comodel_name="res.company", related="study_id.company_id",
                                 store=True,
                                 index=True,)
    condition_id = fields.Many2one(
        comodel_name="ls.pharma.stability.condition",
        string="Storage Condition",
        required=True,
        ondelete="restrict",
        index=True,
    )
    month = fields.Integer(required=True)
    date_scheduled = fields.Date(string="Scheduled Date", required=True, index=True)
    date_pulled = fields.Date(string="Pulled On", copy=False)
    date_tested = fields.Date(string="Tested On", copy=False)
    pulled_by_user_id = fields.Many2one(
        comodel_name="res.users", string="Pulled By", copy=False
    )
    sample_ids = fields.One2many(
        comodel_name="ls.pharma.stability.sample",
        inverse_name="timepoint_id",
        string="Samples",
    )
    result_ids = fields.One2many(
        comodel_name="ls.pharma.stability.result",
        inverse_name="timepoint_id",
        string="Results",
    )
    result_count = fields.Integer(
        string="Results", compute="_compute_result_summary", store=True
    )
    nonconforming_count = fields.Integer(
        string="Non-Conforming Results",
        compute="_compute_result_summary",
        store=True,
    )
    is_overdue = fields.Boolean(
        string="Overdue",
        compute="_compute_is_overdue",
        store=True,
        help=(
            "Set when the scheduled date has passed and the time point has "
            "not yet been pulled."
        ),
    )
    state = fields.Selection(
        selection=TIMEPOINT_STATES,
        string="Status",
        default="scheduled",
        required=True,
        copy=False,
        index=True,
    )
    remark = fields.Text()

    @api.depends("result_ids.is_conform")
    def _compute_result_summary(self):
        """Count the results and the non-conforming results."""
        for timepoint in self:
            timepoint.result_count = len(timepoint.result_ids)
            timepoint.nonconforming_count = len(
                timepoint.result_ids.filtered(lambda result: not result.is_conform)
            )

    @api.depends("date_scheduled", "state")
    def _compute_is_overdue(self):
        """Flag a time point whose scheduled date has passed unpulled."""
        today = fields.Date.context_today(self)
        for timepoint in self:
            timepoint.is_overdue = bool(
                timepoint.state == "scheduled"
                and timepoint.date_scheduled
                and timepoint.date_scheduled < today
            )

    @api.depends("study_id", "condition_id", "month")
    def _compute_display_name(self):
        """Show the month and the condition of the time point."""
        for timepoint in self:
            timepoint.display_name = "%s M%s %s" % (
                timepoint.study_id.name or "",
                timepoint.month,
                timepoint.condition_id.name or "",
            )

    @api.constrains("month")
    def _check_month(self):
        """Reject a negative month."""
        for timepoint in self:
            if timepoint.month < 0:
                raise ValidationError(
                    self.env._("The month of a time point cannot be negative.")
                )

    @api.constrains("date_scheduled", "date_pulled", "date_tested")
    def _check_date_order(self):
        """Reject a testing date that precedes the pull date."""
        for timepoint in self:
            if (
                timepoint.date_pulled
                and timepoint.date_tested
                and timepoint.date_tested < timepoint.date_pulled
            ):
                raise ValidationError(
                    self.env._(
                        "A time point cannot be tested before its samples "
                        "have been pulled."
                    )
                )

    def action_pull(self):
        """Record that the samples of the selected time points were pulled."""
        for timepoint in self:
            if timepoint.state != "scheduled":
                raise UserError(
                    self.env._(
                        "Time point %(name)s is not scheduled and cannot be "
                        "pulled.",
                        name=timepoint.display_name,
                    )
                )
            timepoint.write(
                {
                    "state": "pulled",
                    "date_pulled": timepoint.date_pulled
                    or fields.Date.context_today(self),
                    "pulled_by_user_id": self.env.user.id,
                }
            )
            timepoint.sample_ids.filtered(
                lambda sample: sample.state == "stored"
            ).write({"state": "pulled"})
        return True

    def action_record_tested(self):
        """Record that the selected time points have been tested."""
        for timepoint in self:
            if timepoint.state != "pulled":
                raise UserError(
                    self.env._(
                        "Time point %(name)s must be pulled before it can be "
                        "declared tested.",
                        name=timepoint.display_name,
                    )
                )
            if not timepoint.result_ids:
                raise UserError(
                    self.env._(
                        "Time point %(name)s carries no result.",
                        name=timepoint.display_name,
                    )
                )
            timepoint.write(
                {
                    "state": "tested",
                    "date_tested": timepoint.date_tested
                    or fields.Date.context_today(self),
                }
            )
        return True

    def action_complete(self):
        """Close the selected time points on the basis of their results."""
        for timepoint in self:
            if timepoint.state != "tested":
                raise UserError(
                    self.env._(
                        "Time point %(name)s must be tested before it can be "
                        "closed.",
                        name=timepoint.display_name,
                    )
                )
            if timepoint.nonconforming_count:
                timepoint.state = "out_of_specification"
                timepoint.study_id.message_post(
                    body=self.env._(
                        "Time point %(name)s carries %(count)s non-conforming "
                        "result(s) and has been closed as out of "
                        "specification.",
                        name=timepoint.display_name,
                        count=timepoint.nonconforming_count,
                    )
                )
            else:
                timepoint.state = "completed"
        return True

    def action_mark_missed(self):
        """Mark the selected time points as missed."""
        for timepoint in self:
            if not timepoint.remark:
                raise UserError(
                    self.env._(
                        "A remark is required to justify why time point "
                        "%(name)s was missed.",
                        name=timepoint.display_name,
                    )
                )
        self.write({"state": "missed"})
        return True
