# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Environmental monitoring sample."""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from .constants import (
    EVAL_NOT_EVALUATED,
    EVALUATIONS,
    OCCUPANCY_IN_OPERATION,
    OCCUPANCY_STATES,
    SAMPLE_APPROVED,
    SAMPLE_CANCELLED,
    SAMPLE_COLLECTED,
    SAMPLE_DRAFT,
    SAMPLE_IN_ANALYSIS,
    SAMPLE_LOCKED_STATES,
    SAMPLE_RESULTS_ENTERED,
    SAMPLE_REVIEWED,
    SAMPLE_SCHEDULED,
    SAMPLE_STATES,
    SAMPLE_TRANSITIONS,
)
from .evaluation import worst_evaluation


class LsEnvSample(models.Model):
    """A sample taken at one sampling point at one point in time.

    A sample carries one result per parameter measured on that occasion. The
    state machine records who performed each step and when, and refuses any
    transition that is not declared in
    :data:`~.constants.SAMPLE_TRANSITIONS`.
    """

    _name = "ls.env.sample"
    _description = "Environmental Monitoring Sample"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "scheduled_date desc, name desc"

    name = fields.Char(
        string="Sample Reference",
        required=True,
        readonly=True,
        copy=False,
        default=lambda self: self.env._("New"),
        index=True,
    )
    sampling_point_id = fields.Many2one(comodel_name="ls.env.sampling_point", required=True,
                                        index=True,
                                        tracking=True,
                                        ondelete="restrict",)
    area_id = fields.Many2one(comodel_name="ls.env.area", related="sampling_point_id.area_id",
                              store=True,
                              index=True,)
    grade_id = fields.Many2one(comodel_name="ls.env.grade", related="sampling_point_id.grade_id",
                               store=True,)
    plan_id = fields.Many2one(
        comodel_name="ls.env.plan",
        string="Source Plan",
        readonly=True,
        index=True,
        ondelete="set null",
        help="Plan from which this sample was generated. Empty for a sample "
        "raised outside the routine schedule.",
    )
    is_unscheduled = fields.Boolean(
        string="Unscheduled",
        compute="_compute_is_unscheduled",
        store=True,
        help="Indicates a sample taken outside the approved routine plan, for "
        "example in response to an investigation.",
    )
    occupancy_state = fields.Selection(selection=OCCUPANCY_STATES, required=True,
                                       default=OCCUPANCY_IN_OPERATION,
                                       tracking=True,
                                       help="State the area was in when the sample was taken. This selects "
                                       "the limits applied during evaluation.",)
    scheduled_date = fields.Date(required=True,
                                 index=True,
                                 tracking=True,
                                 default=fields.Date.context_today,)
    collection_datetime = fields.Datetime(
        string="Collected On", readonly=True, copy=False, tracking=True
    )
    collected_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                      copy=False,
                                      tracking=True,)
    analysis_start_datetime = fields.Datetime(
        string="Analysis Started", readonly=True, copy=False
    )
    results_entered_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                            copy=False,
                                            tracking=True,)
    results_entered_datetime = fields.Datetime(
        string="Results Entered On", readonly=True, copy=False
    )
    reviewed_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                     copy=False,
                                     tracking=True,)
    review_datetime = fields.Datetime(
        string="Reviewed On", readonly=True, copy=False
    )
    approved_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                     copy=False,
                                     tracking=True,)
    approval_datetime = fields.Datetime(
        string="Approved On", readonly=True, copy=False
    )
    cancellation_reason = fields.Text(readonly=True, copy=False)
    state = fields.Selection(
        selection=SAMPLE_STATES,
        string="Status",
        default=SAMPLE_DRAFT,
        required=True,
        readonly=True,
        copy=False,
        index=True,
        tracking=True,
    )
    result_ids = fields.One2many(
        comodel_name="ls.env.result",
        inverse_name="sample_id",
        string="Results",
    )
    result_count = fields.Integer(string="Results", compute="_compute_result_count")
    overall_evaluation = fields.Selection(
        selection=EVALUATIONS,
        string="Overall Outcome",
        compute="_compute_overall_evaluation",
        store=True,
        index=True,
        help="Most severe outcome across the results of this sample.",
    )
    excursion_ids = fields.One2many(
        comodel_name="ls.env.excursion",
        inverse_name="sample_id",
        string="Excursions",
    )
    excursion_count = fields.Integer(
        string="Excursions", compute="_compute_excursion_count"
    )
    batch_reference = fields.Char(
        string="Batch / Campaign Reference",
        tracking=True,
        help="Identifier of the production batch or campaign in progress, "
        "recorded as free text so that the module does not depend on a "
        "manufacturing module being installed.",
    )
    is_overdue = fields.Boolean(
        string="Overdue",
        compute="_compute_is_overdue",
        search="_search_is_overdue",
        help="A sample still awaiting collection after its scheduled date.",
    )
    notes = fields.Text()
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,
                                 index=True,)

    _name_company_unique = models.Constraint(
        "UNIQUE(name, company_id)",
        "The sample reference must be unique per company.",
    )

    # ------------------------------------------------------------------
    # Computes
    # ------------------------------------------------------------------
    @api.depends("plan_id")
    def _compute_is_unscheduled(self):
        """Flag samples that did not originate from an approved plan."""
        for record in self:
            record.is_unscheduled = not record.plan_id

    @api.depends("result_ids")
    def _compute_result_count(self):
        """Count the results attached to each sample."""
        for record in self:
            record.result_count = len(record.result_ids)

    @api.depends("excursion_ids")
    def _compute_excursion_count(self):
        """Count the excursions raised from each sample."""
        for record in self:
            record.excursion_count = len(record.excursion_ids)

    @api.depends("result_ids.evaluation")
    def _compute_overall_evaluation(self):
        """Roll the result outcomes up to the sample."""
        for record in self:
            if not record.result_ids:
                record.overall_evaluation = EVAL_NOT_EVALUATED
            else:
                record.overall_evaluation = worst_evaluation(
                    record.result_ids.mapped("evaluation")
                )

    def _compute_is_overdue(self):
        """Flag samples past their scheduled date and not yet collected."""
        today = fields.Date.context_today(self)
        for record in self:
            record.is_overdue = bool(
                record.state in (SAMPLE_DRAFT, SAMPLE_SCHEDULED)
                and record.scheduled_date
                and record.scheduled_date < today
            )

    def _search_is_overdue(self, operator, value):
        """Translate a search on ``is_overdue`` into a stored-field domain.

        ``is_overdue`` depends on the current date and cannot be stored, so a
        search method is provided to keep the field usable in filters.
        """
        if operator not in ("=", "!="):
            raise UserError(
                self.env._("The overdue filter supports only equality operators.")
            )
        today = fields.Date.context_today(self)
        overdue_domain = [
            ("state", "in", [SAMPLE_DRAFT, SAMPLE_SCHEDULED]),
            ("scheduled_date", "<", today),
        ]
        looking_for_overdue = (operator == "=") == bool(value)
        if looking_for_overdue:
            return overdue_domain
        return ["!"] + overdue_domain

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("sampling_point_id", "company_id")
    def _check_company_consistency(self):
        """Reject a sampling point belonging to a different company."""
        for record in self:
            if record.sampling_point_id.company_id != record.company_id:
                raise ValidationError(
                    self.env._(
                        "The sampling point must belong to the same company as the "
                        "sample."
                    )
                )

    @api.constrains("collection_datetime", "scheduled_date")
    def _check_collection_not_in_future(self):
        """Reject a collection timestamp in the future.

        A record of a sample taken at a future moment cannot be contemporaneous
        with the activity it documents.
        """
        now = fields.Datetime.now()
        for record in self:
            if record.collection_datetime and record.collection_datetime > now:
                raise ValidationError(
                    self.env._(
                        "The collection date and time of sample '%(sample)s' cannot "
                        "be in the future.",
                        sample=record.name,
                    )
                )

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Assign the sample reference from the configured sequence."""
        for vals in vals_list:
            if vals.get("name", self.env._("New")) == self.env._("New"):
                company_id = vals.get("company_id") or self.env.company.id
                sequence = self.env["ir.sequence"].with_company(company_id)
                vals["name"] = (
                    sequence.next_by_code("ls.env.sample") or self.env._("New")
                )
        return super().create(vals_list)

    def write(self, vals):
        """Prevent changes to a sample once it is approved or cancelled.

        Only the notes and the message-tracking fields remain writable, so
        that a later observation can be attached without altering the record
        of what was measured.
        """
        editable_when_locked = {
            "message_follower_ids",
            "message_ids",
            "activity_ids",
            "notes",
        }
        if not editable_when_locked.issuperset(vals):
            for record in self:
                if record.state in SAMPLE_LOCKED_STATES:
                    raise UserError(
                        self.env._(
                            "Sample '%(sample)s' is %(state)s and can no longer be "
                            "modified.",
                            sample=record.name,
                            state=dict(SAMPLE_STATES).get(record.state, record.state),
                        )
                    )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_env_sample(self):
        """Restrict deletion to samples that were never collected."""
        for record in self:
            if record.state != SAMPLE_DRAFT:
                raise UserError(
                    self.env._(
                        "Only a draft sample can be deleted. Cancel the sample "
                        "instead so that the record is retained."
                    )
                )

    # ------------------------------------------------------------------
    # State machine
    # ------------------------------------------------------------------
    def _check_manager_role(self):
        """Raise unless the current user holds the manager role.

        Review and approval are restricted to the manager role. The check is
        made here rather than through an access control list because access
        control lists apply to a whole model and cannot restrict an individual
        state transition.
        """
        if not self.env.user.has_group(
            "ls_environmental_monitoring.group_ls_env_manager"
        ):
            raise UserError(
                self.env._(
                    "Only a user holding the Environmental Monitoring Manager role "
                    "may review or approve a sample."
                )
            )

    def _check_transition(self, target_state):
        """Raise unless every record may move to ``target_state``."""
        state_labels = dict(SAMPLE_STATES)
        for record in self:
            allowed = SAMPLE_TRANSITIONS.get(record.state, ())
            if target_state not in allowed:
                raise UserError(
                    self.env._(
                        "Sample '%(sample)s' cannot move from '%(current)s' to "
                        "'%(target)s'.",
                        sample=record.name,
                        current=state_labels.get(record.state, record.state),
                        target=state_labels.get(target_state, target_state),
                    )
                )

    def action_schedule(self):
        """Move a draft sample into the scheduled state."""
        self._check_transition(SAMPLE_SCHEDULED)
        self.write({"state": SAMPLE_SCHEDULED})
        return True

    def action_collect(self):
        """Record collection of the sample by the current user."""
        self._check_transition(SAMPLE_COLLECTED)
        for record in self:
            if not record.result_ids:
                raise UserError(
                    self.env._(
                        "Sample '%(sample)s' has no parameter to measure. Add at "
                        "least one result line before recording collection.",
                        sample=record.name,
                    )
                )
        self.write(
            {
                "state": SAMPLE_COLLECTED,
                "collection_datetime": fields.Datetime.now(),
                "collected_by_id": self.env.user.id,
            }
        )
        return True

    def action_start_analysis(self):
        """Record the start of analysis or incubation."""
        self._check_transition(SAMPLE_IN_ANALYSIS)
        self.write(
            {
                "state": SAMPLE_IN_ANALYSIS,
                "analysis_start_datetime": fields.Datetime.now(),
            }
        )
        return True

    def action_enter_results(self):
        """Evaluate the recorded values and mark the results as entered."""
        self._check_transition(SAMPLE_RESULTS_ENTERED)
        for record in self:
            missing = record.result_ids.filtered(lambda r: not r.has_value())
            if missing:
                raise UserError(
                    self.env._(
                        "Every result of sample '%(sample)s' must have a recorded "
                        "value before the results can be submitted.",
                        sample=record.name,
                    )
                )
        self.result_ids.action_evaluate()
        self.write(
            {
                "state": SAMPLE_RESULTS_ENTERED,
                "results_entered_by_id": self.env.user.id,
                "results_entered_datetime": fields.Datetime.now(),
            }
        )
        return True

    def action_review(self):
        """Record technical review of the results.

        The reviewer must not be the user who entered the results.
        """
        self._check_transition(SAMPLE_REVIEWED)
        self._check_manager_role()
        for record in self:
            if record.results_entered_by_id == self.env.user:
                raise UserError(
                    self.env._(
                        "Sample '%(sample)s' must be reviewed by a user other than "
                        "the one who entered the results.",
                        sample=record.name,
                    )
                )
        self.write(
            {
                "state": SAMPLE_REVIEWED,
                "reviewed_by_id": self.env.user.id,
                "review_datetime": fields.Datetime.now(),
            }
        )
        return True

    def action_approve(self):
        """Approve the sample and raise excursions for any breach.

        The approver must not be the user who entered the results.
        """
        self._check_transition(SAMPLE_APPROVED)
        self._check_manager_role()
        for record in self:
            if record.results_entered_by_id == self.env.user:
                raise UserError(
                    self.env._(
                        "Sample '%(sample)s' must be approved by a user other than "
                        "the one who entered the results.",
                        sample=record.name,
                    )
                )
        self.write(
            {
                "state": SAMPLE_APPROVED,
                "approved_by_id": self.env.user.id,
                "approval_datetime": fields.Datetime.now(),
            }
        )
        for record in self:
            record.result_ids._raise_excursions_if_required()
        return True

    def action_cancel(self):
        """Cancel the sample, recording the reason supplied in the context."""
        self._check_transition(SAMPLE_CANCELLED)
        reason = self.env.context.get("cancellation_reason")
        if not reason:
            raise UserError(
                self.env._("A reason must be supplied to cancel a sample.")
            )
        # ``state`` is written last so the locked-state guard in ``write`` does
        # not reject the reason being stored in the same call.
        self.write({"cancellation_reason": reason})
        self.write({"state": SAMPLE_CANCELLED})
        return True

    def action_reopen_analysis(self):
        """Return a reviewed or submitted sample to analysis for correction."""
        self._check_transition(SAMPLE_IN_ANALYSIS)
        self.write(
            {
                "state": SAMPLE_IN_ANALYSIS,
                "reviewed_by_id": False,
                "review_datetime": False,
            }
        )
        return True

    # ------------------------------------------------------------------
    # Scheduling
    # ------------------------------------------------------------------
    @api.model
    def generate_from_plans(self, plans, date_to, limit):
        """Create the samples due under ``plans`` up to ``date_to``.

        Generation is idempotent. A sample is created only when no sample
        already exists for the same plan, sampling point, parameter set and
        scheduled date, so repeated runs do not duplicate the schedule.

        :param plans: ``ls.env.plan`` recordset, expected to be approved
        :param date_to: last due date to generate, inclusive
        :param int limit: maximum number of samples to create in this run
        :returns: the created ``ls.env.sample`` records
        """
        created = self.browse()
        remaining = limit
        for plan in plans:
            for line in plan.line_ids:
                if remaining <= 0:
                    return created
                due_dates = line._due_dates_until(date_to, remaining)
                latest_generated = None
                for due_date in due_dates:
                    sample = self._get_or_create_scheduled_sample(line, due_date)
                    if sample:
                        created |= sample
                        remaining -= 1
                    latest_generated = due_date
                    if remaining <= 0:
                        break
                if latest_generated is not None:
                    line.next_due_date = line._next_occurrence_on_or_after(
                        latest_generated, strictly=True
                    )
        return created

    @api.model
    def _get_or_create_scheduled_sample(self, line, due_date):
        """Return a new sample for ``line`` on ``due_date``, or nothing.

        When a sample already covers the same point, occupancy state and date,
        the parameter of the line is added to it rather than a second sample
        being created, so that all parameters measured at one point on one
        occasion stay on a single record.
        """
        existing = self.search(
            [
                ("sampling_point_id", "=", line.sampling_point_id.id),
                ("scheduled_date", "=", due_date),
                ("occupancy_state", "=", line.occupancy_state),
                ("state", "not in", [SAMPLE_CANCELLED]),
            ],
            limit=1,
        )
        if existing:
            already_measured = line.parameter_id in existing.result_ids.mapped(
                "parameter_id"
            )
            if not already_measured and existing.state in (
                SAMPLE_DRAFT,
                SAMPLE_SCHEDULED,
            ):
                self.env["ls.env.result"].create(
                    {
                        "sample_id": existing.id,
                        "parameter_id": line.parameter_id.id,
                        "method_id": line.method_id.id or False,
                    }
                )
            return self.browse()
        sample = self.create(
            {
                "sampling_point_id": line.sampling_point_id.id,
                "plan_id": line.plan_id.id,
                "occupancy_state": line.occupancy_state,
                "scheduled_date": due_date,
                "company_id": line.company_id.id,
                "state": SAMPLE_SCHEDULED,
                "result_ids": [
                    (
                        0,
                        0,
                        {
                            "parameter_id": line.parameter_id.id,
                            "method_id": line.method_id.id or False,
                        },
                    )
                ],
            }
        )
        return sample

    @api.model
    def cron_notify_overdue_samples(self):
        """Notify the responsible users of samples that are past due.

        A message is posted on each overdue sample once per run. The message
        is the notification channel because it is retained with the record and
        is visible to anyone later reviewing the sample.

        :returns: the number of samples notified
        :rtype: int
        """
        today = fields.Date.context_today(self)
        overdue = self.search(
            [
                ("state", "in", [SAMPLE_DRAFT, SAMPLE_SCHEDULED]),
                ("scheduled_date", "<", today),
            ]
        )
        for sample in overdue:
            sample.message_post(
                body=self.env._(
                    "This sample was scheduled for %(date)s and has not yet been "
                    "collected.",
                    date=sample.scheduled_date,
                )
            )
        return len(overdue)

    def action_open_cancel_wizard(self):
        """Open the wizard that records the cancellation reason."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Cancel Sample"),
            "res_model": "ls.env.sample.cancel.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_sample_id": self.id},
        }

    def action_view_excursions(self):
        """Open the excursions raised from this sample."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Excursions"),
            "res_model": "ls.env.excursion",
            "view_mode": "list,form",
            "domain": [("sample_id", "=", self.id)],
        }
