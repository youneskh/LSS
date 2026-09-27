# Part of the Life Sciences Suite. See LICENSE file for full copyright
# and licensing details.
"""Risk register entry.

One record of :class:`LsRiskRegister` represents one identified risk. The
"risk register" of the functional specification is the list view over this
model; this interpretation is declared in the module documentation.

The record holds the descriptive risk analysis inputs, references its
assessments and risk control measures, and carries the residual risk
acceptance and overall residual risk decisions.
"""

import logging

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from . import constants

_logger = logging.getLogger(__name__)


class LsRiskRegister(models.Model):
    """An identified risk under active management."""

    _name = "ls.risk.register"
    _description = "Risk Register Entry"
    _inherit = ["mail.thread", "mail.activity.mixin", "ls.risk.role.mixin"]
    _order = "identified_date desc, id desc"

    # ------------------------------------------------------------------
    # Identification
    # ------------------------------------------------------------------
    name = fields.Char(
        string="Reference",
        required=True,
        readonly=True,
        copy=False,
        default=constants.SEQUENCE_PLACEHOLDER,
        index=True,
    )
    title = fields.Char(required=True, tracking=True)
    description = fields.Text()
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,
                                 index=True,)
    category_id = fields.Many2one(comodel_name="ls.risk.category", tracking=True,
                                  domain="[('company_id', '=', company_id)]",
                                  )
    risk_type = fields.Selection(selection=constants.RISK_TYPES, required=True,
                                 tracking=True,)
    owner_id = fields.Many2one(
        comodel_name="res.users",
        string="Risk Owner",
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
    )
    identified_by_id = fields.Many2one(comodel_name="res.users", required=True,
                                       default=lambda self: self.env.user,)
    identified_date = fields.Date(
        string="Identification Date",
        required=True,
        default=fields.Date.context_today,
    )
    active = fields.Boolean(default=True)
    state = fields.Selection(
        selection=constants.RISK_STATES,
        string="Status",
        default="draft",
        required=True,
        tracking=True,
        copy=False,
        index=True,
    )

    # ------------------------------------------------------------------
    # Risk analysis inputs (ISO 14971:2019 clauses 5.2 to 5.4)
    # ------------------------------------------------------------------
    intended_use = fields.Text(
        string="Intended Use and Reasonably Foreseeable Misuse",
        help="Supports the risk analysis input required by ISO 14971:2019 "
        "clause 5.2.",
    )
    safety_characteristics = fields.Text(
        string="Characteristics Related to Safety",
        help="Supports the risk analysis input required by ISO 14971:2019 "
        "clause 5.3.",
    )
    hazard = fields.Text(help="Potential source of harm. Supports ISO 14971:2019 clause 5.4.",)
    hazardous_situation = fields.Text(help="Circumstance in which people, property or the environment is "
                                      "exposed to one or more hazards. Supports ISO 14971:2019 clause 5.4.",)
    sequence_of_events = fields.Text(help="Foreseeable sequence of events leading from the hazard to the "
                                     "hazardous situation. Supports ISO 14971:2019 clause 5.4.",)
    harm = fields.Text(help="Injury or damage to the health of people, or damage to property "
                       "or the environment. Supports ISO 14971:2019 clause 5.4.",)

    # ------------------------------------------------------------------
    # Assessments
    # ------------------------------------------------------------------
    matrix_id = fields.Many2one(
        comodel_name="ls.risk.matrix",
        string="Risk Matrix",
        required=True,
        tracking=True,
        default=lambda self: self._default_matrix_id(),
        domain="[('company_id', '=', company_id), ('state', '=', 'approved')]",
        help="Set of acceptability criteria against which this risk is evaluated.",
    )
    assessment_ids = fields.One2many(
        comodel_name="ls.risk.assessment",
        inverse_name="risk_id",
        string="Assessments",
    )
    assessment_count = fields.Integer(compute="_compute_assessment_data", store=True)
    initial_assessment_id = fields.Many2one(comodel_name="ls.risk.assessment", compute="_compute_assessment_data",
                                            store=True,)
    current_assessment_id = fields.Many2one(comodel_name="ls.risk.assessment", compute="_compute_assessment_data",
                                            store=True,
                                            help="Most recent approved assessment of this risk.",)
    initial_risk_level = fields.Selection(selection=constants.RISK_LEVELS, compute="_compute_assessment_data",
                                          store=True,)
    current_risk_level = fields.Selection(selection=constants.RISK_LEVELS, compute="_compute_assessment_data",
                                          store=True,
                                          index=True,)
    current_acceptability = fields.Selection(selection=constants.ACCEPTABILITY, compute="_compute_assessment_data",
                                             store=True,
                                             index=True,)

    # ------------------------------------------------------------------
    # Risk control (ISO 14971:2019 clause 7)
    # ------------------------------------------------------------------
    mitigation_ids = fields.One2many(
        comodel_name="ls.risk.mitigation",
        inverse_name="risk_id",
        string="Risk Control Measures",
    )
    mitigation_count = fields.Integer(
        string="Control Measure Count", compute="_compute_mitigation_data", store=True
    )
    mitigation_open_count = fields.Integer(
        string="Open Control Measures", compute="_compute_mitigation_data", store=True
    )
    all_mitigations_verified = fields.Boolean(
        string="All Control Measures Verified",
        compute="_compute_mitigation_data",
        store=True,
    )
    benefit_risk_analysis = fields.Text(
        string="Benefit-Risk Analysis",
        help="Supports the benefit-risk analysis of ISO 14971:2019 clause 7.4, "
        "performed when a risk is not judged acceptable after risk control.",
    )
    control_completeness_confirmed = fields.Boolean(
        string="Risk Control Completeness Confirmed",
        readonly=True,
        copy=False,
        tracking=True,
        help="Supports ISO 14971:2019 clause 7.6.",
    )
    control_completeness_by_id = fields.Many2one(
        comodel_name="res.users",
        string="Completeness Confirmed By",
        readonly=True,
        copy=False,
    )
    control_completeness_date = fields.Datetime(
        string="Completeness Confirmation Date", readonly=True, copy=False
    )

    # ------------------------------------------------------------------
    # Residual and overall residual risk (clauses 7.3 and 8)
    # ------------------------------------------------------------------
    residual_risk_accepted = fields.Boolean(readonly=True,
                                            copy=False,
                                            tracking=True,
                                            help="Supports the residual risk evaluation of ISO 14971:2019 clause 7.3.",)
    residual_risk_accepted_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                                   copy=False,)
    residual_risk_acceptance_date = fields.Datetime(readonly=True, copy=False)
    residual_risk_justification = fields.Text(
        string="Residual Risk Acceptance Justification", readonly=True, copy=False
    )
    overall_residual_risk_assessment = fields.Text(help="Supports the evaluation of overall residual risk of "
                                                   "ISO 14971:2019 clause 8.",)

    # ------------------------------------------------------------------
    # Monitoring (clause 10.3)
    # ------------------------------------------------------------------
    review_interval_months = fields.Integer(
        string="Review Interval (Months)",
        default=constants.DEFAULT_REVIEW_INTERVAL_MONTHS,
        required=True,
    )
    next_review_date = fields.Date(tracking=True, copy=False, index=True)
    last_review_date = fields.Date(readonly=True, copy=False)
    review_overdue = fields.Boolean(compute="_compute_review_overdue")

    # ------------------------------------------------------------------
    # Closure and cancellation
    # ------------------------------------------------------------------
    closure_reason = fields.Text(readonly=True, copy=False)
    closed_by_id = fields.Many2one(comodel_name="res.users", readonly=True, copy=False)
    closed_date = fields.Datetime(string="Closure Date", readonly=True, copy=False)
    cancel_reason = fields.Text(string="Cancellation Reason", readonly=True, copy=False)

    # ------------------------------------------------------------------
    # Extension point
    # ------------------------------------------------------------------
    linked_model_id = fields.Many2one(comodel_name="ir.model", ondelete="cascade",
                                      help="Optional technical link to a record in another model. Provided "
                                      "as an extension point so that this module carries no dependency on "
                                      "product, stock, mrp or hr.",)
    linked_res_id = fields.Integer(string="Linked Record ID")
    fmea_line_ids = fields.One2many(
        comodel_name="ls.risk.fmea.line",
        inverse_name="risk_id",
        string="Originating FMEA Lines",
    )
    fmea_line_count = fields.Integer(compute="_compute_fmea_line_count")

    _name_company_uniq = models.Constraint(
        "UNIQUE(name, company_id)",
        "The risk reference must be unique per company.",
    )
    _review_interval_positive = models.Constraint(
        "CHECK(review_interval_months > 0)",
        "The review interval must be strictly positive.",
    )
    _linked_res_id_non_negative = models.Constraint(
        "CHECK(linked_res_id >= 0)",
        "The linked record identifier cannot be negative.",
    )

    # ------------------------------------------------------------------
    # Defaults
    # ------------------------------------------------------------------
    @api.model
    def _default_matrix_id(self):
        """Return the active default approved matrix of the current company.

        :return: the default matrix, or an empty recordset when none exists.
        :rtype: :class:`odoo.models.Model`
        """
        return self.env["ls.risk.matrix"].search(
            [
                ("company_id", "=", self.env.company.id),
                ("is_default", "=", True),
                ("state", "=", "approved"),
            ],
            limit=1,
        )

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------
    @api.depends(
        "assessment_ids.state",
        "assessment_ids.assessment_type",
        "assessment_ids.risk_level",
        "assessment_ids.acceptability",
        "assessment_ids.approval_date",
    )
    def _compute_assessment_data(self):
        """Derive assessment counts and the initial and current assessments."""
        for risk in self:
            approved = risk.assessment_ids.filtered(lambda a: a.state == "approved")
            initial = approved.filtered(lambda a: a.assessment_type == "initial")[:1]
            current = approved.sorted(
                key=lambda a: (a.approval_date or fields.Datetime.now(), a.id),
                reverse=True,
            )[:1]
            risk.assessment_count = len(risk.assessment_ids)
            risk.initial_assessment_id = initial
            risk.current_assessment_id = current
            risk.initial_risk_level = initial.risk_level if initial else False
            risk.current_risk_level = current.risk_level if current else False
            risk.current_acceptability = current.acceptability if current else False

    @api.depends("mitigation_ids.state")
    def _compute_mitigation_data(self):
        """Derive risk control measure counts and verification completeness."""
        for risk in self:
            measures = risk.mitigation_ids.filtered(lambda m: m.state != "cancelled")
            pending = measures.filtered(
                lambda m: m.state in constants.MITIGATION_PENDING_STATES
            )
            risk.mitigation_count = len(measures)
            risk.mitigation_open_count = len(pending)
            risk.all_mitigations_verified = bool(measures) and not pending

    def _compute_fmea_line_count(self):
        """Count the FMEA lines that gave rise to each risk."""
        grouped = self.env["ls.risk.fmea.line"]._read_group(
            domain=[("risk_id", "in", self.ids)],
            groupby=["risk_id"],
            aggregates=["__count"],
        )
        counts = {risk.id: count for risk, count in grouped}
        for risk in self:
            risk.fmea_line_count = counts.get(risk.id, 0)

    @api.depends("next_review_date", "state")
    def _compute_review_overdue(self):
        """Flag open risks whose review date has passed."""
        today = fields.Date.context_today(self)
        for risk in self:
            risk.review_overdue = bool(
                risk.state in constants.RISK_OPEN_STATES
                and risk.next_review_date
                and risk.next_review_date < today
            )

    @api.depends("name", "title")
    def _compute_display_name(self):
        """Show the reference followed by the title."""
        for risk in self:
            if risk.name and risk.name != constants.SEQUENCE_PLACEHOLDER:
                risk.display_name = f"{risk.name} - {risk.title}"
            else:
                risk.display_name = risk.title or constants.SEQUENCE_PLACEHOLDER

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("matrix_id", "company_id")
    def _check_matrix_company(self):
        """Keep the matrix and the risk within the same company."""
        for risk in self:
            if risk.matrix_id.company_id != risk.company_id:
                raise ValidationError(
                    self.env._(
                        "Risk %(name)s and its risk matrix must belong to the "
                        "same company.",
                        name=risk.display_name,
                    )
                )

    @api.constrains("category_id", "company_id")
    def _check_category_company(self):
        """Keep the category and the risk within the same company."""
        for risk in self:
            if risk.category_id and risk.category_id.company_id != risk.company_id:
                raise ValidationError(
                    self.env._(
                        "Risk %(name)s and its category must belong to the "
                        "same company.",
                        name=risk.display_name,
                    )
                )

    @api.constrains("linked_model_id", "linked_res_id")
    def _check_linked_record(self):
        """Require both parts of the optional technical link, or neither."""
        for risk in self:
            if bool(risk.linked_model_id) != bool(risk.linked_res_id):
                raise ValidationError(
                    self.env._(
                        "The linked model and the linked record identifier must "
                        "be set together on risk %(name)s.",
                        name=risk.display_name,
                    )
                )

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Assign the register reference from the configured sequence.

        :param list vals_list: list of field value dictionaries.
        :return: the created records.
        :rtype: :class:`odoo.models.Model`
        """
        for vals in vals_list:
            if vals.get("name", constants.SEQUENCE_PLACEHOLDER) == constants.SEQUENCE_PLACEHOLDER:
                company_id = vals.get("company_id") or self.env.company.id
                sequence = self.env["ir.sequence"].with_company(company_id)
                vals["name"] = (
                    sequence.next_by_code(constants.SEQUENCE_RISK)
                    or constants.SEQUENCE_PLACEHOLDER
                )
        return super().create(vals_list)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_risk_register(self):
        """Restrict deletion to draft and cancelled risks.

        Risks that have entered assessment form part of the risk management
        file and are archived rather than deleted.

        :raise UserError: when any record is beyond the draft or cancelled state.
        :return: ``True`` when deletion succeeded.
        :rtype: bool
        """
        blocked = self.filtered(lambda risk: risk.state not in ("draft", "cancelled"))
        if blocked:
            raise UserError(
                self.env._(
                    "Risks that have been assessed cannot be deleted because "
                    "they form part of the risk management file. Archive them "
                    "instead. Blocked references: %(refs)s",
                    refs=", ".join(blocked.mapped("name")),
                )
            )

    def copy_data(self, default=None):
        """Reset workflow evidence when a risk is duplicated.

        :param dict default: overriding values supplied by the caller.
        :return: list of value dictionaries for the copies.
        :rtype: list
        """
        default = dict(default or {})
        default.setdefault("name", constants.SEQUENCE_PLACEHOLDER)
        default.setdefault("state", "draft")
        default.setdefault("title", self.env._("%s (copy)", self.title or ""))
        return super().copy_data(default=default)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _compute_next_review_date(self, from_date=None):
        """Return the next review date derived from the review interval.

        :param from_date: base date; defaults to today in the user's timezone.
        :type from_date: datetime.date or None
        :return: the computed next review date.
        :rtype: datetime.date
        """
        self.ensure_one()
        base = from_date or fields.Date.context_today(self)
        return base + relativedelta(months=self.review_interval_months)

    def _requires_residual_decision(self):
        """Return whether an explicit residual risk decision is required.

        :return: ``True`` when the current acceptability is not plainly
            acceptable, or when no approved assessment exists.
        :rtype: bool
        """
        self.ensure_one()
        if not self.current_assessment_id:
            return True
        return self.current_acceptability in constants.ACCEPTABILITY_REQUIRING_DECISION

    # ------------------------------------------------------------------
    # Workflow actions
    # ------------------------------------------------------------------
    def action_start_assessment(self):
        """Move a draft risk to the assessed state.

        :raise UserError: when the risk is not in draft or lacks an approved
            initial assessment.
        :return: ``True`` when all records advanced.
        :rtype: bool
        """
        for risk in self:
            if risk.state != "draft":
                raise UserError(
                    self.env._("Only a draft risk can be moved to Assessed.")
                )
            if not risk.initial_assessment_id:
                raise UserError(
                    self.env._(
                        "Risk %(name)s needs an approved initial assessment "
                        "before it can leave Draft.",
                        name=risk.display_name,
                    )
                )
            risk.write(
                {
                    "state": "assessed",
                    "next_review_date": risk.next_review_date
                    or risk._compute_next_review_date(),
                }
            )
        return True

    def action_start_risk_control(self):
        """Move an assessed risk into the risk control state.

        :raise UserError: when the risk is not in the assessed state.
        :return: ``True`` when all records advanced.
        :rtype: bool
        """
        for risk in self:
            if risk.state != "assessed":
                raise UserError(
                    self.env._("Only an assessed risk can enter Risk Control.")
                )
            risk.state = "control"
        return True

    def action_confirm_control_completeness(self):
        """Record the risk control completeness confirmation (clause 7.6).

        :raise UserError: when the risk is not in the risk control state or
            has unverified risk control measures.
        :return: ``True`` when all records were confirmed.
        :rtype: bool
        """
        self._ensure_risk_manager(self.env._("confirm risk control completeness"))
        for risk in self:
            if risk.state != "control":
                raise UserError(
                    self.env._(
                        "Risk control completeness can only be confirmed while "
                        "the risk is in Risk Control."
                    )
                )
            # Only measures still pending block the confirmation. A risk
            # without any measure can be confirmed: whether its residual risk
            # is acceptable is decided when monitoring starts.
            if risk.mitigation_open_count:
                raise UserError(
                    self.env._(
                        "Risk %(name)s still has risk control measures that are "
                        "not verified. Verify or cancel them before confirming "
                        "completeness.",
                        name=risk.display_name,
                    )
                )
            risk.write(
                {
                    "control_completeness_confirmed": True,
                    "control_completeness_by_id": self.env.user.id,
                    "control_completeness_date": fields.Datetime.now(),
                }
            )
        return True

    def action_accept_residual_risk(self):
        """Open the residual risk acceptance wizard.

        :return: an action opening the acceptance wizard.
        :rtype: dict
        """
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Accept Residual Risk"),
            "res_model": "ls.risk.residual.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_risk_id": self.id},
        }

    def action_start_monitoring(self):
        """Move a risk under risk control into the monitoring state.

        :raise UserError: when completeness is not confirmed or, where
            required, residual risk has not been accepted.
        :return: ``True`` when all records advanced.
        :rtype: bool
        """
        self._ensure_risk_manager(self.env._("move a risk to Monitoring"))
        for risk in self:
            if risk.state != "control":
                raise UserError(
                    self.env._("Only a risk in Risk Control can move to Monitoring.")
                )
            if not risk.control_completeness_confirmed:
                raise UserError(
                    self.env._(
                        "Confirm risk control completeness for %(name)s before "
                        "moving to Monitoring.",
                        name=risk.display_name,
                    )
                )
            if risk._requires_residual_decision() and not risk.residual_risk_accepted:
                raise UserError(
                    self.env._(
                        "The current acceptability of %(name)s requires a "
                        "recorded residual risk acceptance decision before "
                        "moving to Monitoring.",
                        name=risk.display_name,
                    )
                )
            risk.write(
                {
                    "state": "monitoring",
                    "next_review_date": risk._compute_next_review_date(),
                    "last_review_date": fields.Date.context_today(risk),
                }
            )
        return True

    def action_open_close_wizard(self):
        """Open the closure wizard for the selected risks.

        :return: an action opening the closure wizard.
        :rtype: dict
        """
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Close Risks"),
            "res_model": "ls.risk.close.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_risk_ids": self.ids},
        }

    def action_cancel(self):
        """Open the cancellation wizard for the selected risks.

        :return: an action opening the cancellation wizard.
        :rtype: dict
        """
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Cancel Risks"),
            "res_model": "ls.risk.cancel.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_risk_ids": self.ids},
        }

    def action_reset_to_draft(self):
        """Return a cancelled risk to the draft state.

        :raise UserError: when the risk is not cancelled.
        :return: ``True`` when all records were reset.
        :rtype: bool
        """
        for risk in self:
            if risk.state != "cancelled":
                raise UserError(
                    self.env._("Only a cancelled risk can be reset to Draft.")
                )
            risk.write({"state": "draft", "cancel_reason": False})
        return True

    def action_open_assess_wizard(self):
        """Open the assessment wizard for the selected risks.

        :return: an action opening the assessment wizard.
        :rtype: dict
        """
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Assess Risks"),
            "res_model": "ls.risk.assess.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_risk_ids": self.ids},
        }

    def action_view_assessments(self):
        """Open the assessments of this risk.

        :return: an action listing the related assessments.
        :rtype: dict
        """
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Assessments"),
            "res_model": "ls.risk.assessment",
            "view_mode": "list,form",
            "domain": [("risk_id", "=", self.id)],
            "context": {"default_risk_id": self.id},
        }

    def action_view_mitigations(self):
        """Open the risk control measures of this risk.

        :return: an action listing the related risk control measures.
        :rtype: dict
        """
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Risk Control Measures"),
            "res_model": "ls.risk.mitigation",
            "view_mode": "list,form",
            "domain": [("risk_id", "=", self.id)],
            "context": {"default_risk_id": self.id},
        }

    def action_open_linked_record(self):
        """Open the record referenced by the technical extension point.

        The display name of the target is deliberately not computed anywhere
        in this module, so that no access rule of the target model is
        bypassed. Opening the record applies the target model's own access
        rules.

        :raise UserError: when no link is set.
        :return: an action opening the linked record.
        :rtype: dict
        """
        self.ensure_one()
        if not (self.linked_model_id and self.linked_res_id):
            raise UserError(
                self.env._("No linked record is set on this risk.")
            )
        return {
            "type": "ir.actions.act_window",
            "res_model": self.linked_model_id.model,
            "res_id": self.linked_res_id,
            "view_mode": "form",
            "target": "current",
        }

    # ------------------------------------------------------------------
    # Scheduled action
    # ------------------------------------------------------------------
    @api.model
    def _cron_notify_review_due(self):
        """Notify risk owners of open risks whose review date has passed.

        Schedules an activity for the risk owner when the ``To Do`` activity
        type is available, and otherwise posts a chatter message. Intended to
        be called by the ``ir.cron`` record shipped with this module.

        :return: the number of risks notified.
        :rtype: int
        """
        today = fields.Date.context_today(self)
        overdue = self.search(
            [
                ("state", "in", list(constants.RISK_OPEN_STATES)),
                ("next_review_date", "!=", False),
                ("next_review_date", "<", today),
            ]
        )
        if not overdue:
            return 0
        activity_type = self.env.ref(
            constants.ACTIVITY_TYPE_TODO_XMLID, raise_if_not_found=False
        )
        for risk in overdue:
            body = self.env._(
                "Periodic risk review is overdue. The review was due on %(date)s.",
                date=risk.next_review_date,
            )
            if activity_type:
                risk.activity_schedule(
                    act_type_xmlid=constants.ACTIVITY_TYPE_TODO_XMLID,
                    summary=self.env._("Risk review overdue"),
                    note=body,
                    user_id=risk.owner_id.id,
                )
            else:
                risk.message_post(body=body)
        _logger.info(
            "ls_risk_management: notified %d overdue risk review(s).", len(overdue)
        )
        return len(overdue)
