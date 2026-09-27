# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Measurable quality objectives derived from the quality policy."""

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

#: Objective lifecycle states.
OBJECTIVE_STATES = [
    ("draft", "Draft"),
    ("in_progress", "In Progress"),
    ("achieved", "Achieved"),
    ("not_achieved", "Not Achieved"),
    ("cancelled", "Cancelled"),
]

#: Ratio of the time-proportional expectation below which an objective is
#: reported as "At Risk" rather than "Off Track". Design decision of this
#: module, not a requirement of any standard.
AT_RISK_RATIO = 0.8


def compute_achievement_rate(direction, baseline, target, current, tolerance):
    """Return the achievement rate of an objective, as a percentage.

    The formulas applied are:

    * ``increase``: ``(current - baseline) / (target - baseline) * 100``
    * ``decrease``: ``(baseline - current) / (baseline - target) * 100``
    * ``maintain`` with a tolerance greater than zero:
      ``100 - abs(current - target) / tolerance * 100``
    * ``maintain`` without tolerance: ``100`` when the current value equals
      the target, ``0`` otherwise.

    The result is floored at ``0``. It is not capped, so an over performing
    objective returns a rate above ``100``.

    :param str direction: ``increase``, ``decrease`` or ``maintain``.
    :param float baseline: value measured before the objective started.
    :param float target: value to be reached.
    :param float current: latest measured value.
    :param float tolerance: accepted deviation for ``maintain`` objectives.
    :rtype: float
    """
    if direction == "increase":
        span = target - baseline
        rate = (current - baseline) / span * 100.0 if span > 0 else 0.0
    elif direction == "decrease":
        span = baseline - target
        rate = (baseline - current) / span * 100.0 if span > 0 else 0.0
    elif tolerance > 0:
        rate = 100.0 - abs(current - target) / tolerance * 100.0
    else:
        rate = 100.0 if current == target else 0.0
    return max(0.0, rate)


class LsQmsObjective(models.Model):
    """Quality objective with periodic measurements and achievement rate."""

    _name = "ls.qms.objective"
    _description = "Quality Objective"
    _check_company_auto = True
    _inherit = ["mail.thread", "mail.activity.mixin", "ls.qms.parameter.mixin"]
    _order = "date_target, reference"

    _reference_uniq = models.Constraint(
        "UNIQUE (reference, company_id)",
        "The reference of a quality objective must be unique per company.",
    )
    _dates_consistent = models.Constraint(
        "CHECK (date_target >= date_start)",
        "The target date of an objective cannot precede its start date.",
    )
    _tolerance_positive = models.Constraint(
        "CHECK (tolerance >= 0)",
        "The tolerance of an objective cannot be negative.",
    )

    name = fields.Char(string="Objective", required=True, tracking=True)
    reference = fields.Char(
        required=True,
        readonly=True,
        copy=False,
        index=True,
        default="/",
    )
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    policy_id = fields.Many2one(
        comodel_name="ls.qms.policy",
        string="Quality Policy",
        check_company=True,
        tracking=True,
        help="Policy from which the objective is derived.",
    )
    department_id = fields.Many2one(comodel_name="hr.department", tracking=True,)
    responsible_id = fields.Many2one(comodel_name="res.users", required=True,
                                     default=lambda self: self.env.user,
                                     tracking=True,)
    description = fields.Text()
    state = fields.Selection(
        selection=OBJECTIVE_STATES,
        required=True,
        readonly=True,
        copy=False,
        default="draft",
        index=True,
        tracking=True,
    )
    date_start = fields.Date(
        string="Start Date",
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )
    date_target = fields.Date(
        string="Target Date",
        required=True,
        tracking=True,
    )
    direction = fields.Selection(
        selection=[
            ("increase", "Increase"),
            ("decrease", "Decrease"),
            ("maintain", "Maintain"),
        ],
        required=True,
        default="increase",
        tracking=True,
        help="Direction of the improvement expected for the indicator.",
    )
    uom_name = fields.Char(
        string="Unit",
        help="Free text unit of the indicator, for example percent or days.",
    )
    baseline_value = fields.Float(
        string="Baseline",
        tracking=True,
        help="Value measured before the objective was set.",
    )
    target_value = fields.Float(
        string="Target",
        required=True,
        tracking=True,
    )
    tolerance = fields.Float(help="Accepted deviation from the target, used by objectives whose"
                             " direction is Maintain.",)
    measurement_ids = fields.One2many(
        comodel_name="ls.qms.objective.measurement",
        inverse_name="objective_id",
        string="Measurements",
    )
    measurement_count = fields.Integer(
        compute="_compute_current_value",
        store=True,
    )
    current_value = fields.Float(compute="_compute_current_value",
                                 store=True,
                                 tracking=True,)
    last_measurement_date = fields.Date(
        compute="_compute_current_value",
        store=True,
    )
    achievement_rate = fields.Float(
        string="Achievement (%)",
        compute="_compute_achievement_rate",
        store=True,
        digits=(16, 2),
        tracking=True,
    )
    performance_status = fields.Selection(
        selection=[
            ("no_data", "No Measurement"),
            ("on_track", "On Track"),
            ("at_risk", "At Risk"),
            ("off_track", "Off Track"),
            ("target_reached", "Target Reached"),
        ],
        compute="_compute_performance_status",
        help="Compares the achievement rate with the share of the objective"
        " period already elapsed. Computed at display time.",
    )

    @api.depends("measurement_ids.value", "measurement_ids.date")
    def _compute_current_value(self):
        """Take the most recent measurement as the current value."""
        for objective in self:
            measurements = objective.measurement_ids.sorted(
                key=lambda m: (m.date, m.id), reverse=True
            )
            objective.measurement_count = len(measurements)
            if measurements:
                objective.current_value = measurements[0].value
                objective.last_measurement_date = measurements[0].date
            else:
                objective.current_value = objective.baseline_value
                objective.last_measurement_date = False

    @api.depends(
        "current_value",
        "baseline_value",
        "target_value",
        "direction",
        "tolerance",
    )
    def _compute_achievement_rate(self):
        """Apply :func:`compute_achievement_rate` to every objective."""
        for objective in self:
            objective.achievement_rate = compute_achievement_rate(
                objective.direction,
                objective.baseline_value,
                objective.target_value,
                objective.current_value,
                objective.tolerance,
            )

    @api.depends(
        "achievement_rate",
        "last_measurement_date",
        "date_start",
        "date_target",
        "state",
    )
    def _compute_performance_status(self):
        """Classify progress against the elapsed share of the period."""
        today = fields.Date.context_today(self)
        for objective in self:
            if objective.achievement_rate >= 100.0:
                objective.performance_status = "target_reached"
            elif not objective.last_measurement_date:
                objective.performance_status = "no_data"
            else:
                expected = objective._expected_progress(today)
                if objective.achievement_rate >= expected:
                    objective.performance_status = "on_track"
                elif objective.achievement_rate >= expected * AT_RISK_RATIO:
                    objective.performance_status = "at_risk"
                else:
                    objective.performance_status = "off_track"

    def _expected_progress(self, today):
        """Return the share of the objective period already elapsed, in %.

        :param today: reference date.
        :rtype: float
        """
        self.ensure_one()
        total_days = (self.date_target - self.date_start).days
        if total_days <= 0:
            return 100.0
        elapsed_days = (today - self.date_start).days
        if elapsed_days <= 0:
            return 0.0
        return min(100.0, elapsed_days / total_days * 100.0)

    @api.constrains("direction", "baseline_value", "target_value")
    def _check_target_direction(self):
        """Reject targets that contradict the declared direction."""
        for objective in self:
            if objective.direction == "increase":
                if objective.target_value <= objective.baseline_value:
                    raise ValidationError(
                        _(
                            "Objective %(name)s aims to increase the "
                            "indicator, so its target must be greater than "
                            "its baseline.",
                            name=objective.name,
                        )
                    )
            elif objective.direction == "decrease":
                if objective.target_value >= objective.baseline_value:
                    raise ValidationError(
                        _(
                            "Objective %(name)s aims to decrease the "
                            "indicator, so its target must be lower than its "
                            "baseline.",
                            name=objective.name,
                        )
                    )

    @api.depends("reference", "name")
    def _compute_display_name(self):
        """Render objectives as ``[REFERENCE] Objective``."""
        for objective in self:
            objective.display_name = "[%s] %s" % (
                objective.reference or "/",
                objective.name or "",
            )

    @api.model_create_multi
    def create(self, vals_list):
        """Allocate the objective reference from the numbering sequence."""
        for vals in vals_list:
            if not vals.get("reference") or vals["reference"] == "/":
                reference = self.env["ir.sequence"].next_by_code(
                    "ls.qms.objective"
                )
                if not reference:
                    raise UserError(
                        _(
                            "The numbering sequence ls.qms.objective is "
                            "missing. Update the Life Sciences QMS module to "
                            "restore it."
                        )
                    )
                vals["reference"] = reference
        return super().create(vals_list)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_qms_objective(self):
        """Allow deletion of draft objectives only."""
        undeletable = self.filtered(lambda obj: obj.state != "draft")
        if undeletable:
            raise UserError(
                _(
                    "Only draft objectives may be deleted. Cancel "
                    "%(references)s instead.",
                    references=", ".join(undeletable.mapped("reference")),
                )
            )

    def action_start(self):
        """Activate a draft objective."""
        for objective in self:
            if objective.state != "draft":
                raise UserError(
                    _(
                        "Objective %(reference)s is not in draft and cannot "
                        "be started.",
                        reference=objective.reference,
                    )
                )
        self.write({"state": "in_progress"})
        return True

    def action_close_achieved(self):
        """Close an objective as achieved."""
        return self._close_objective("achieved")

    def action_close_not_achieved(self):
        """Close an objective as not achieved."""
        return self._close_objective("not_achieved")

    def _close_objective(self, target_state):
        """Close running objectives with ``target_state``.

        :param str target_state: ``achieved`` or ``not_achieved``.
        """
        for objective in self:
            if objective.state != "in_progress":
                raise UserError(
                    _(
                        "Objective %(reference)s must be in progress before "
                        "it can be closed.",
                        reference=objective.reference,
                    )
                )
        self.write({"state": target_state})
        for objective in self:
            objective.message_post(
                body=_(
                    "Objective closed with an achievement rate of "
                    "%(rate).2f%%.",
                    rate=objective.achievement_rate,
                )
            )
        return True

    def action_cancel(self):
        """Cancel an objective that is no longer relevant."""
        self.write({"state": "cancelled"})
        return True

    def action_reset_to_draft(self):
        """Return a cancelled or closed objective to draft."""
        self.write({"state": "draft"})
        return True

    def action_view_measurements(self):
        """Open the measurements recorded for the objective."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Measurements"),
            "res_model": "ls.qms.objective.measurement",
            "view_mode": "list,form,graph",
            "domain": [("objective_id", "=", self.id)],
            "context": {"default_objective_id": self.id},
        }

    @api.model
    def _cron_objective_monitoring(self):
        """Schedule a follow-up activity on objectives at risk.

        An activity is created for every running objective whose target date
        falls within the configured lead time and whose achievement rate is
        below 100%.

        :return: the number of activities created.
        :rtype: int
        """
        activity_type = self.env.ref(
            "ls_qms.mail_activity_type_ls_qms_objective",
            raise_if_not_found=False,
        )
        if not activity_type:
            return 0
        lead_days = self._get_int_parameter(
            "ls_qms.review_reminder_lead_days", 30
        )
        horizon = fields.Date.context_today(self) + relativedelta(
            days=lead_days
        )
        objectives = self.search(
            [
                ("state", "=", "in_progress"),
                ("date_target", "<=", horizon),
                ("achievement_rate", "<", 100.0),
            ]
        )
        created = 0
        for objective in objectives:
            existing = self.env["mail.activity"].search_count(
                [
                    ("res_model", "=", self._name),
                    ("res_id", "=", objective.id),
                    ("activity_type_id", "=", activity_type.id),
                ]
            )
            if existing:
                continue
            objective.activity_schedule(
                act_type_xmlid="ls_qms.mail_activity_type_ls_qms_objective",
                date_deadline=objective.date_target,
                summary=_(
                    "Quality objective %(reference)s below target",
                    reference=objective.reference,
                ),
                user_id=objective.responsible_id.id,
            )
            created += 1
        return created
