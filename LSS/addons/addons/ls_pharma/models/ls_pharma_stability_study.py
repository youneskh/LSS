# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Stability studies."""

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..constants import (
    ICH_ACCELERATED_TIMEPOINTS,
    ICH_INTERMEDIATE_TIMEPOINTS,
    ICH_LONG_TERM_QUARTERLY_UNTIL_MONTH,
    ICH_LONG_TERM_SEMESTRIAL_UNTIL_MONTH,
    STABILITY_STUDY_STATES,
    STABILITY_STUDY_TYPES,
)


class LsPharmaStabilityStudy(models.Model):
    """A stability study conducted on a batch of a product.

    21 CFR 211.166 requires a written testing programme designed to assess
    the stability characteristics of drug products, and requires that the
    results of that testing be used in assigning appropriate storage
    conditions and expiration dates.

    The time points proposed by this model follow the testing frequencies
    published in ICH Q1A(R2):

    * at the long-term storage condition, testing every three months over the
      first year, every six months over the second year and annually
      thereafter through the proposed shelf life;
    * at the accelerated storage condition, a minimum of three time points
      including the initial and final time points, for example 0, 3 and 6
      months, from a six-month study;
    * at the intermediate storage condition, when it is called for as a
      result of a significant change at the accelerated storage condition, a
      minimum of four time points including the initial and final time
      points, for example 0, 6, 9 and 12 months, from a twelve-month study.

    Source: ICH Q1A(R2), reproduced by the United States Food and Drug
    Administration as Guidance for Industry Q1A(R2) Stability Testing of New
    Drug Substances and Products, https://www.fda.gov/media/71707/download

    The generated schedule is a proposal.  The study owner may add, remove or
    move any time point, because the guideline states recommendations rather
    than a fixed schedule and because a national guideline may require a
    different frequency.
    """

    _name = "ls.pharma.stability_study"
    _description = "Stability Study"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_start desc, name desc"

    _name_company_uniq = models.Constraint(
        "UNIQUE(name, company_id)",
        "The stability study reference must be unique per company.",
    )

    name = fields.Char(
        string="Study Reference",
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: self.env._("New"),
    )
    title = fields.Char(required=True, tracking=True)
    study_type = fields.Selection(selection=STABILITY_STUDY_TYPES, required=True,
                                  default="registration",
                                  tracking=True,)
    product_id = fields.Many2one(comodel_name="product.product", required=True,
                                 index=True,
                                 tracking=True,)
    batch_id = fields.Many2one(comodel_name="ls.pharma.batch", index=True,
                               tracking=True,
                               help=(
                                   "Batch placed on stability. A study may be created before the "
                                   "batch exists, in which case the field is completed later."),
                               )
    protocol_reference = fields.Char(required=True,
                                     help="Reference of the approved stability protocol.",)
    packaging_description = fields.Char(
        string="Packaging Configuration",
        help=(
            "Container closure system in which the samples are stored. "
            "ICH Q1A(R2) requires that stability studies be conducted in the "
            "container closure system proposed for marketing."
        ),
    )
    date_start = fields.Date(
        string="Study Start", required=True, default=fields.Date.context_today
    )
    duration_months = fields.Integer(
        string="Planned Duration (Months)",
        required=True,
        default=24,
    )
    date_planned_end = fields.Date(
        string="Planned End",
        compute="_compute_date_planned_end",
        store=True,
    )
    condition_ids = fields.Many2many(
        comodel_name="ls.pharma.stability.condition",
        relation="ls_stability_study_condition_rel",
        column1="study_id",
        column2="condition_id",
        string="Storage Conditions",
        help="Conditions under which samples of this study are stored.",
    )
    timepoint_ids = fields.One2many(
        comodel_name="ls.pharma.stability.timepoint",
        inverse_name="study_id",
        string="Time Points",
    )
    sample_ids = fields.One2many(
        comodel_name="ls.pharma.stability.sample",
        inverse_name="study_id",
        string="Stability Samples",
    )
    timepoint_count = fields.Integer(
        string="Time Points", compute="_compute_counts", store=True
    )
    timepoint_overdue_count = fields.Integer(
        string="Overdue Time Points", compute="_compute_counts", store=True
    )
    sample_count = fields.Integer(
        string="Samples", compute="_compute_counts", store=True
    )
    has_significant_change = fields.Boolean(
        string="Significant Change Observed",
        compute="_compute_counts",
        store=True,
        help=(
            "Set when at least one result of this study has been marked as a "
            "significant change. ICH Q1A(R2) requires testing at the "
            "intermediate storage condition when a significant change occurs "
            "at the accelerated storage condition."
        ),
    )
    proposed_shelf_life_months = fields.Integer(
        string="Proposed Shelf Life (Months)",
        tracking=True,
        help="Shelf life proposed on the basis of the data generated by this study.",
    )
    conclusion = fields.Text()
    state = fields.Selection(
        selection=STABILITY_STUDY_STATES,
        string="Status",
        default="draft",
        required=True,
        copy=False,
        tracking=True,
        index=True,
    )
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,
                                 index=True,)
    active = fields.Boolean(default=True)

    # ------------------------------------------------------------------
    # Computed fields
    # ------------------------------------------------------------------
    @api.depends("date_start", "duration_months")
    def _compute_date_planned_end(self):
        """Compute the planned end from the start date and the duration."""
        for study in self:
            if study.date_start and study.duration_months > 0:
                study.date_planned_end = study.date_start + relativedelta(
                    months=study.duration_months
                )
            else:
                study.date_planned_end = False

    @api.depends(
        "timepoint_ids.state",
        "timepoint_ids.is_overdue",
        "timepoint_ids.result_ids.is_significant_change",
        "sample_ids",
    )
    def _compute_counts(self):
        """Compute the aggregates displayed on the study."""
        for study in self:
            study.timepoint_count = len(study.timepoint_ids)
            study.timepoint_overdue_count = len(
                study.timepoint_ids.filtered(lambda point: point.is_overdue)
            )
            study.sample_count = len(study.sample_ids)
            study.has_significant_change = any(
                result.is_significant_change
                for point in study.timepoint_ids
                for result in point.result_ids
            )

    @api.depends("name", "title")
    def _compute_display_name(self):
        """Show the study reference together with its title."""
        for study in self:
            if study.title:
                study.display_name = "%s - %s" % (study.name, study.title)
            else:
                study.display_name = study.name or ""

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("duration_months")
    def _check_duration(self):
        """Reject a non-positive planned duration."""
        for study in self:
            if study.duration_months <= 0:
                raise ValidationError(
                    self.env._(
                        "The planned duration of study %(name)s must be "
                        "strictly positive.",
                        name=study.name,
                    )
                )

    @api.constrains("proposed_shelf_life_months")
    def _check_proposed_shelf_life(self):
        """Reject a negative proposed shelf life."""
        for study in self:
            if study.proposed_shelf_life_months < 0:
                raise ValidationError(
                    self.env._("The proposed shelf life cannot be negative.")
                )

    @api.constrains("batch_id", "product_id")
    def _check_batch_product(self):
        """Reject a batch that does not carry the product of the study."""
        for study in self:
            if (
                study.batch_id
                and study.product_id
                and study.batch_id.product_id.id != study.product_id.id
            ):
                raise ValidationError(
                    self.env._(
                        "Batch %(batch)s does not carry product %(product)s.",
                        batch=study.batch_id.name,
                        product=study.product_id.display_name,
                    )
                )

    # ------------------------------------------------------------------
    # Overrides
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Assign the study reference from the dedicated sequence."""
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == self.env._("New"):
                sequence = self.env["ir.sequence"].next_by_code(
                    "ls.pharma.stability_study"
                )
                vals["name"] = sequence or self.env._("New")
        return super().create(vals_list)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_pharma_stability_study(self):
        """Forbid the deletion of a study that has left the draft state."""
        for study in self:
            if study.state != "draft":
                raise UserError(
                    self.env._(
                        "Study %(name)s has left the draft state and can no "
                        "longer be deleted.",
                        name=study.name,
                    )
                )

    # ------------------------------------------------------------------
    # Schedule generation
    # ------------------------------------------------------------------
    @api.model
    def _ich_timepoint_months(self, condition_type, duration_months):
        """Return the time points recommended by ICH Q1A(R2).

        :param str condition_type: technical value of the condition type.
        :param int duration_months: duration of the study in months.
        :returns: the ordered months at which testing is recommended.
        :rtype: list of int
        """
        if condition_type == "accelerated":
            return [
                month
                for month in ICH_ACCELERATED_TIMEPOINTS
                if month <= duration_months
            ]
        if condition_type == "intermediate":
            return [
                month
                for month in ICH_INTERMEDIATE_TIMEPOINTS
                if month <= duration_months
            ]
        if condition_type == "long_term":
            months = []
            month = 0
            while month <= duration_months:
                months.append(month)
                if month < ICH_LONG_TERM_QUARTERLY_UNTIL_MONTH:
                    month += 3
                elif month < ICH_LONG_TERM_SEMESTRIAL_UNTIL_MONTH:
                    month += 6
                else:
                    month += 12
            return months
        # For any other condition type no frequency is published by
        # ICH Q1A(R2), so only the initial and final time points are proposed.
        return sorted({0, duration_months})

    def action_generate_schedule(self):
        """Generate the recommended time points for the selected studies.

        Existing time points are preserved.  Only the combinations of
        condition and month that are not already present are created.

        :returns: the created time points.
        :rtype: recordset of ``ls.pharma.stability.timepoint``
        """
        timepoint_model = self.env["ls.pharma.stability.timepoint"]
        created = timepoint_model
        for study in self:
            if study.state not in ("draft", "scheduled"):
                raise UserError(
                    self.env._(
                        "Time points can only be generated while study "
                        "%(name)s is in the draft or scheduled state.",
                        name=study.name,
                    )
                )
            if not study.condition_ids:
                raise UserError(
                    self.env._(
                        "Study %(name)s has no storage condition. At least "
                        "one condition is required to generate a schedule.",
                        name=study.name,
                    )
                )
            existing = {
                (point.condition_id.id, point.month)
                for point in study.timepoint_ids
            }
            values_list = []
            for condition in study.condition_ids:
                # A long-term condition runs for the whole planned duration of
                # the study. An accelerated or intermediate condition runs for
                # its own shorter duration, so the smaller of the two applies.
                if condition.condition_type == "long_term":
                    duration = study.duration_months
                else:
                    duration = min(
                        study.duration_months, condition.default_duration_months
                    )
                for month in study._ich_timepoint_months(
                    condition.condition_type, duration
                ):
                    if (condition.id, month) in existing:
                        continue
                    values_list.append(
                        {
                            "study_id": study.id,
                            "condition_id": condition.id,
                            "month": month,
                            "date_scheduled": study.date_start
                            + relativedelta(months=month),
                        }
                    )
            if values_list:
                created |= timepoint_model.create(values_list)
            if study.state == "draft" and study.timepoint_ids:
                study.state = "scheduled"
        return created

    def action_open_schedule_wizard(self):
        """Open the wizard that generates a stability schedule.

        :rtype: dict
        """
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Generate Stability Schedule"),
            "res_model": "ls.pharma.stability.schedule.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_study_id": self.id},
        }

    # ------------------------------------------------------------------
    # State machine
    # ------------------------------------------------------------------
    def action_start(self):
        """Move the selected studies to the ongoing state."""
        for study in self:
            if study.state not in ("draft", "scheduled"):
                raise UserError(
                    self.env._(
                        "Study %(name)s cannot be started from state "
                        "%(state)s.",
                        name=study.name,
                        state=study.state,
                    )
                )
            if not study.timepoint_ids:
                raise UserError(
                    self.env._(
                        "Study %(name)s has no time point and cannot be "
                        "started.",
                        name=study.name,
                    )
                )
        self.write({"state": "ongoing"})
        return True

    def action_complete(self):
        """Complete the selected studies."""
        for study in self:
            if study.state != "ongoing":
                raise UserError(
                    self.env._(
                        "Study %(name)s is not ongoing and cannot be "
                        "completed.",
                        name=study.name,
                    )
                )
            pending = study.timepoint_ids.filtered(
                lambda point: point.state
                not in ("completed", "out_of_specification", "missed")
            )
            if pending:
                raise UserError(
                    self.env._(
                        "Study %(name)s still has %(count)s time point(s) "
                        "that have not reached a final state.",
                        name=study.name,
                        count=len(pending),
                    )
                )
            if not study.conclusion:
                raise UserError(
                    self.env._(
                        "A conclusion is required before study %(name)s can "
                        "be completed, because 21 CFR 211.166 requires that "
                        "the results of stability testing be used in "
                        "assigning storage conditions and expiration dates.",
                        name=study.name,
                    )
                )
        self.write({"state": "completed"})
        return True

    def action_terminate(self):
        """Terminate the selected studies before their planned end."""
        for study in self:
            if not study.conclusion:
                raise UserError(
                    self.env._(
                        "A written justification is required in the "
                        "conclusion before study %(name)s can be terminated.",
                        name=study.name,
                    )
                )
        self.write({"state": "terminated"})
        return True

    # ------------------------------------------------------------------
    # Scheduled action
    # ------------------------------------------------------------------
    @api.model
    def cron_flag_overdue_timepoints(self):
        """Post a message on studies that carry an overdue time point.

        :returns: the number of studies that were notified.
        :rtype: int
        """
        studies = self.search([("state", "=", "ongoing")])
        notified = 0
        for study in studies:
            overdue = study.timepoint_ids.filtered(lambda point: point.is_overdue)
            if not overdue:
                continue
            study.message_post(
                body=self.env._(
                    "Study %(name)s carries %(count)s overdue time point(s). "
                    "The earliest was scheduled for %(date)s.",
                    name=study.name,
                    count=len(overdue),
                    date=min(overdue.mapped("date_scheduled")),
                )
            )
            notified += 1
        return notified
