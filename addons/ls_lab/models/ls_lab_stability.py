# Part of the Life Sciences Suite. See LICENSE file for full copyright and licensing details.
"""Stability studies and their time points.

No storage condition, time point schedule, shelf-life rule or acceptance limit
is shipped with this module. The consolidated ICH Q1 guideline reached Step 2b
on 11 April 2025 and had not reached Step 4 at the time of this build; until it
does, the legacy Q1A(R2)-Q1E and Q5C series remain applicable. Because the
governing reference is in transition, every schedule value here is
configuration owned by the implementing organisation.
"""

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class LsLabStabilityStudy(models.Model):
    """A stability study on one batch of one product."""

    _name = "ls.lab.stability_study"
    _description = "Laboratory Stability Study"
    _check_company_auto = True
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "start_date desc, name desc"

    name = fields.Char(
        string="Study Reference",
        required=True,
        readonly=True,
        copy=False,
        default="New",
        tracking=True,
    )
    description = fields.Char(tracking=True)
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("approved", "Approved"),
            ("ongoing", "Ongoing"),
            ("completed", "Completed"),
            ("terminated", "Terminated"),
        ],
        string="Status",
        default="draft",
        required=True,
        copy=False,
        tracking=True,
    )
    product_id = fields.Many2one(comodel_name="product.product", required=True,
                                 index=True,
                                 tracking=True,)
    lot_id = fields.Many2one(
        comodel_name="stock.lot",
        string="Lot / Serial Number",
        index=True,
        check_company=True,
    )
    batch_reference = fields.Char()
    batch_size = fields.Float(digits=(16, 4))
    batch_size_uom_id = fields.Many2one(
        comodel_name="uom.uom", string="Batch Size Unit"
    )
    manufacture_date = fields.Date(string="Manufacturing Date")
    study_type = fields.Selection(
        selection=[
            ("long_term", "Long Term"),
            ("intermediate", "Intermediate"),
            ("accelerated", "Accelerated"),
            ("in_use", "In Use"),
            ("photostability", "Photostability"),
            ("ongoing_annual", "Ongoing / Annual"),
        ],
        default="long_term",
        required=True,
        tracking=True,
    )
    storage_condition_id = fields.Many2one(comodel_name="ls.lab.storage_condition", required=True,
                                           tracking=True,)
    container_closure = fields.Char(string="Container Closure System")
    specification_id = fields.Many2one(comodel_name="ls.lab.specification", domain="[('state', '=', 'approved')]",
                                       help="Specification used for the samples pulled at each time point.",
                                       )
    protocol_reference = fields.Char(help="Free-text reference to the approved stability protocol document.",)
    start_date = fields.Date(tracking=True)
    planned_end_date = fields.Date()
    timepoint_ids = fields.One2many(
        comodel_name="ls.lab.stability_timepoint",
        inverse_name="study_id",
        string="Time Points",
    )
    timepoint_count = fields.Integer(
        string="Time Points", compute="_compute_timepoint_statistics"
    )
    completed_timepoint_count = fields.Integer(
        string="Completed Time Points", compute="_compute_timepoint_statistics"
    )
    approved_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                     copy=False,
                                     tracking=True,)
    approval_date = fields.Datetime(readonly=True, copy=False)
    termination_reason = fields.Text(copy=False)
    company_id = fields.Many2one(comodel_name="res.company", default=lambda self: self.env.company,
                                 index=True,)

    _name_uniq = models.Constraint(
        "UNIQUE (name)",
        "The stability study reference must be unique.",
    )

    @api.depends("timepoint_ids.state")
    def _compute_timepoint_statistics(self):
        """Count time points in total and those completed."""
        for study in self:
            study.timepoint_count = len(study.timepoint_ids)
            study.completed_timepoint_count = len(
                study.timepoint_ids.filtered(lambda tp: tp.state == "completed")
            )

    @api.depends("name", "product_id")
    def _compute_display_name(self):
        """Show the study reference with its product."""
        for study in self:
            product = study.product_id.display_name or ""
            study.display_name = f"{study.name} - {product}".strip(" -")

    @api.model_create_multi
    def create(self, vals_list):
        """Assign the study reference from the sequence."""
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "ls.lab.stability_study"
                ) or "New"
        return super().create(vals_list)

    def _assert_state(self, expected, action_label):
        """Raise unless every study is in one of the expected states."""
        expected = expected if isinstance(expected, (list, tuple, set)) else (expected,)
        wrong = self.filtered(lambda rec: rec.state not in expected)
        if wrong:
            raise UserError(
                self.env._(
                    "Action '%(action)s' is not available for stability "
                    "study/studies %(records)s in their current state.",
                    action=action_label,
                    records=", ".join(wrong.mapped("name")),
                )
            )

    def action_approve(self):
        """Approve the study protocol."""
        self._assert_state("draft", "Approve")
        for study in self:
            if not study.timepoint_ids:
                raise UserError(
                    self.env._(
                        "Stability study '%(study)s' cannot be approved because "
                        "no time points have been defined.",
                        study=study.name,
                    )
                )
        return self.write({
            "state": "approved",
            "approved_by_id": self.env.user.id,
            "approval_date": fields.Datetime.now(),
        })

    def action_start(self):
        """Start the study, requiring a start date."""
        self._assert_state("approved", "Start")
        for study in self:
            if not study.start_date:
                raise UserError(
                    self.env._(
                        "A start date is required before stability study "
                        "'%(study)s' can begin, because time point due dates are "
                        "derived from it.",
                        study=study.name,
                    )
                )
        return self.write({"state": "ongoing"})

    def action_complete(self):
        """Complete the study once no time point remains planned."""
        self._assert_state("ongoing", "Complete")
        for study in self:
            outstanding = study.timepoint_ids.filtered(
                lambda tp: tp.state in ("planned", "sampled", "tested")
            )
            if outstanding:
                raise UserError(
                    self.env._(
                        "Stability study '%(study)s' still has %(count)s time "
                        "point(s) that are neither completed, missed nor "
                        "cancelled.",
                        study=study.name,
                        count=len(outstanding),
                    )
                )
        return self.write({"state": "completed"})

    def action_terminate(self):
        """Terminate the study early, requiring a reason."""
        self._assert_state(("approved", "ongoing"), "Terminate")
        for study in self:
            if not study.termination_reason:
                raise UserError(
                    self.env._(
                        "A termination reason must be recorded before stability "
                        "study '%(study)s' can be terminated.",
                        study=study.name,
                    )
                )
        return self.write({"state": "terminated"})

    def action_view_timepoints(self):
        """Open the time points of this study."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Time Points"),
            "res_model": "ls.lab.stability_timepoint",
            "view_mode": "list,form",
            "domain": [("study_id", "=", self.id)],
            "context": {"default_study_id": self.id},
        }

    @api.model
    def _cron_notify_due_timepoints(self):
        """Post a notice listing time points due or overdue.

        Notification-only: no time point state and no study state is changed
        (BRU-29).
        """
        horizon_days = int(
            self.env["ir.config_parameter"].sudo().get_param(
                "ls_lab.timepoint_notice_days", default="14"
            )
        )
        today = fields.Date.context_today(self)
        limit_date = today + relativedelta(days=horizon_days)
        studies = self.search([("state", "=", "ongoing")])
        notified = 0
        for study in studies:
            due = study.timepoint_ids.filtered(
                lambda tp: tp.state == "planned"
                and tp.scheduled_date
                and tp.scheduled_date <= limit_date
            )
            if not due:
                continue
            listing = "\n".join(
                f"- {tp.name} ({tp.scheduled_date})" for tp in due
            )
            study.message_post(
                body=self.env._(
                    "The following stability time points are due or overdue:\n"
                    "%(listing)s\nThis notice does not change any time point "
                    "status.",
                    listing=listing,
                )
            )
            notified += 1
        return notified

    @api.constrains("lot_id", "product_id")
    def _check_lot_id_matches_product(self):
        """The lot must belong to the product of the record.

        :raise ValidationError: when the lot was created for another product.
        """
        for record in self:
            product = record.product_id
            if record.lot_id and product and record.lot_id.product_id != product:
                raise ValidationError(
                    self.env._(
                        "Lot %(lot)s belongs to product %(lot_product)s, not to "
                        "%(product)s.",
                        lot=record.lot_id.display_name,
                        lot_product=record.lot_id.product_id.display_name,
                        product=product.display_name,
                    )
                )


class LsLabStabilityTimepoint(models.Model):
    """One scheduled pull point of a stability study."""

    _name = "ls.lab.stability_timepoint"
    _description = "Laboratory Stability Time Point"
    _order = "study_id, sequence, interval_months, id"

    study_id = fields.Many2one(
        comodel_name="ls.lab.stability_study",
        string="Stability Study",
        required=True,
        ondelete="cascade",
        index=True,
    )
    name = fields.Char(
        string="Time Point",
        required=True,
        help="Label of the time point, for example 'Initial' or '6 months'.",
    )
    sequence = fields.Integer(default=10)
    interval_months = fields.Integer(
        string="Interval (months)",
        default=0,
        required=True,
        help="Months after the study start date at which this point is due.",
    )
    window_days = fields.Integer(
        string="Window (days)",
        default=0,
        help="Permitted deviation in days around the scheduled date, as "
             "defined by the organisation's stability protocol.",
    )
    scheduled_date = fields.Date(compute="_compute_scheduled_date",
                                 store=True,
                                 help="Derived from the study start date plus the interval in months.",)
    state = fields.Selection(
        selection=[
            ("planned", "Planned"),
            ("sampled", "Sampled"),
            ("tested", "Tested"),
            ("completed", "Completed"),
            ("missed", "Missed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="planned",
        required=True,
        copy=False,
    )
    sample_id = fields.Many2one(
        comodel_name="ls.lab.sample",
        string="Pull Sample",
        readonly=True,
        copy=False,
    )
    actual_pull_date = fields.Date(readonly=True, copy=False)
    notes = fields.Text()
    company_id = fields.Many2one(related="study_id.company_id", store=True,
                                 index=True,)

    _interval_positive = models.Constraint(
        "CHECK (interval_months >= 0)",
        "The stability time point interval must be zero or positive.",
    )

    @api.depends("study_id.start_date", "interval_months")
    def _compute_scheduled_date(self):
        """Derive the due date from the study start date (BRU-25)."""
        for timepoint in self:
            start = timepoint.study_id.start_date
            if start:
                timepoint.scheduled_date = start + relativedelta(
                    months=timepoint.interval_months
                )
            else:
                timepoint.scheduled_date = False

    @api.depends("study_id", "name")
    def _compute_display_name(self):
        """Show the study reference with the time point label."""
        for timepoint in self:
            study = timepoint.study_id.name or ""
            timepoint.display_name = f"{study} / {timepoint.name}".strip(" /")

    def action_open_pull_wizard(self):
        """Open the wizard that creates the pull sample (BRU-24)."""
        self.ensure_one()
        if self.state != "planned":
            raise UserError(
                self.env._(
                    "Time point '%(timepoint)s' is in status '%(state)s' and no "
                    "sample can be generated from it.",
                    timepoint=self.display_name,
                    state=self.state,
                )
            )
        if self.study_id.state != "ongoing":
            raise UserError(
                self.env._(
                    "Stability study '%(study)s' is not ongoing, so no pull "
                    "sample can be generated.",
                    study=self.study_id.name,
                )
            )
        return {
            "type": "ir.actions.act_window",
            "res_model": "ls.lab.stability_pull_wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_timepoint_id": self.id},
        }

    def action_mark_tested(self):
        """Record that the pull sample has completed testing."""
        for timepoint in self:
            if timepoint.state != "sampled":
                raise UserError(
                    self.env._(
                        "Only sampled time points can be marked tested. "
                        "'%(timepoint)s' is in status '%(state)s'.",
                        timepoint=timepoint.display_name,
                        state=timepoint.state,
                    )
                )
        return self.write({"state": "tested"})

    def action_mark_completed(self):
        """Close the time point."""
        for timepoint in self:
            if timepoint.state != "tested":
                raise UserError(
                    self.env._(
                        "Only tested time points can be completed. "
                        "'%(timepoint)s' is in status '%(state)s'.",
                        timepoint=timepoint.display_name,
                        state=timepoint.state,
                    )
                )
        return self.write({"state": "completed"})

    def action_mark_missed(self):
        """Record a missed time point, requiring notes (BRU-27)."""
        for timepoint in self:
            if timepoint.state != "planned":
                raise UserError(
                    self.env._(
                        "Only planned time points can be recorded as missed. "
                        "'%(timepoint)s' is in status '%(state)s'.",
                        timepoint=timepoint.display_name,
                        state=timepoint.state,
                    )
                )
            if not timepoint.notes:
                raise UserError(
                    self.env._(
                        "Notes explaining why time point '%(timepoint)s' was "
                        "missed are required before it can be recorded as "
                        "missed.",
                        timepoint=timepoint.display_name,
                    )
                )
        return self.write({"state": "missed"})
