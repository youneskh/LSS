# Part of the Life Sciences Suite. See LICENSE file for full copyright
# and licensing details.
"""Risk control measures.

Each record is one risk control measure applied to a risk. The model carries
the control option category of ISO 14971:2019 clause 7.1, separate evidence
for implementation verification (clause 7.2) and effectiveness verification,
and the declaration of any new risk introduced by the measure itself
(clause 7.5).
"""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from . import constants


class LsRiskMitigation(models.Model):
    """One risk control measure with implementation and effectiveness evidence."""

    _name = "ls.risk.mitigation"
    _description = "Risk Control Measure"
    _inherit = ["mail.thread", "mail.activity.mixin", "ls.risk.role.mixin"]
    _order = "risk_id, option_priority, sequence, id"

    name = fields.Char(
        string="Reference",
        required=True,
        readonly=True,
        copy=False,
        default=constants.SEQUENCE_PLACEHOLDER,
        index=True,
    )
    risk_id = fields.Many2one(comodel_name="ls.risk.register", required=True,
                              ondelete="cascade",
                              index=True,
                              tracking=True,)
    company_id = fields.Many2one(comodel_name="res.company", related="risk_id.company_id",
                                 store=True,
                                 readonly=True,
                                 index=True,)
    sequence = fields.Integer(default=10)
    title = fields.Char(required=True, tracking=True)
    description = fields.Text(required=True)
    control_option = fields.Selection(
        selection=constants.CONTROL_OPTIONS,
        string="Risk Control Option",
        required=True,
        tracking=True,
        help="Category of risk control option, recorded to support the risk "
        "control option analysis of ISO 14971:2019 clause 7.1. The options "
        "are applied in the order in which they are listed.",
    )
    option_priority = fields.Integer(compute="_compute_option_priority",
                                     store=True,
                                     help="Numeric priority of the selected control option, used to order "
                                     "measures so that the most preferred option appears first.",)
    option_analysis = fields.Text(help="Rationale for selecting this control option in preference to a "
                                  "more preferred option, where applicable.",)
    responsible_id = fields.Many2one(comodel_name="res.users", required=True,
                                     default=lambda self: self.env.user,
                                     tracking=True,)
    due_date = fields.Date(tracking=True)
    state = fields.Selection(
        selection=constants.MITIGATION_STATES,
        string="Status",
        default="draft",
        required=True,
        tracking=True,
        copy=False,
        index=True,
    )
    is_overdue = fields.Boolean(string="Overdue", compute="_compute_is_overdue")

    # ------------------------------------------------------------------
    # Approval
    # ------------------------------------------------------------------
    approved_by_id = fields.Many2one(comodel_name="res.users", readonly=True, copy=False)
    approval_date = fields.Datetime(readonly=True, copy=False)

    # ------------------------------------------------------------------
    # Implementation verification (clause 7.2)
    # ------------------------------------------------------------------
    implementation_date = fields.Date(readonly=True, copy=False)
    implementation_evidence = fields.Text(help="Reference to the objective evidence that the measure was "
                                          "implemented, supporting ISO 14971:2019 clause 7.2.",)
    implementation_verified_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                                    copy=False,
                                                    tracking=True,)
    implementation_verification_date = fields.Datetime(readonly=True, copy=False)

    # ------------------------------------------------------------------
    # Effectiveness verification
    # ------------------------------------------------------------------
    effectiveness_evidence = fields.Text(help="Reference to the objective evidence that the measure is "
                                         "effective in reducing the risk.",)
    effectiveness_verified_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                                   copy=False,
                                                   tracking=True,)
    effectiveness_verification_date = fields.Datetime(readonly=True, copy=False)

    # ------------------------------------------------------------------
    # Risks arising from the measure itself (clause 7.5)
    # ------------------------------------------------------------------
    introduces_new_risk = fields.Boolean(tracking=True,
                                         help="Set when this measure itself introduces a new hazard or "
                                         "increases an existing risk, as required to be considered by "
                                         "ISO 14971:2019 clause 7.5.",)
    new_risk_description = fields.Text()
    new_risk_id = fields.Many2one(
        comodel_name="ls.risk.register",
        string="New Risk Record",
        copy=False,
        help="Risk register entry created for the risk introduced by this "
        "control measure.",
    )
    cancel_reason = fields.Text(string="Cancellation Reason", readonly=True, copy=False)

    _name_company_uniq = models.Constraint(
        "UNIQUE(name, company_id)",
        "The risk control measure reference must be unique per company.",
    )

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------
    @api.depends("control_option")
    def _compute_option_priority(self):
        """Map the control option onto its numeric priority."""
        for measure in self:
            measure.option_priority = constants.CONTROL_OPTION_PRIORITY.get(
                measure.control_option, 99
            )

    @api.depends("due_date", "state")
    def _compute_is_overdue(self):
        """Flag measures past their due date that are not yet verified."""
        today = fields.Date.context_today(self)
        for measure in self:
            measure.is_overdue = bool(
                measure.due_date
                and measure.due_date < today
                and measure.state in constants.MITIGATION_PENDING_STATES
            )

    @api.depends("name", "title")
    def _compute_display_name(self):
        """Show the reference followed by the title."""
        for measure in self:
            measure.display_name = (
                f"{measure.name} - {measure.title}" if measure.title else measure.name
            )

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("introduces_new_risk", "new_risk_description")
    def _check_new_risk_described(self):
        """Require a description whenever a new risk is declared."""
        for measure in self:
            if measure.introduces_new_risk and not (
                measure.new_risk_description or ""
            ).strip():
                raise ValidationError(
                    self.env._(
                        "Describe the new risk introduced by measure %(name)s.",
                        name=measure.display_name,
                    )
                )

    @api.constrains("new_risk_id", "risk_id")
    def _check_new_risk_not_self(self):
        """Forbid pointing the introduced risk at the risk being controlled."""
        for measure in self:
            if measure.new_risk_id and measure.new_risk_id == measure.risk_id:
                raise ValidationError(
                    self.env._(
                        "The new risk introduced by measure %(name)s cannot be "
                        "the risk that the measure controls.",
                        name=measure.display_name,
                    )
                )

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Assign the measure reference from the configured sequence.

        :param list vals_list: list of field value dictionaries.
        :return: the created records.
        :rtype: :class:`odoo.models.Model`
        """
        risk_model = self.env["ls.risk.register"]
        for vals in vals_list:
            if vals.get("name", constants.SEQUENCE_PLACEHOLDER) == constants.SEQUENCE_PLACEHOLDER:
                company_id = (
                    risk_model.browse(vals["risk_id"]).company_id.id
                    if vals.get("risk_id")
                    else self.env.company.id
                )
                sequence = self.env["ir.sequence"].with_company(company_id)
                vals["name"] = (
                    sequence.next_by_code(constants.SEQUENCE_MITIGATION)
                    or constants.SEQUENCE_PLACEHOLDER
                )
        return super().create(vals_list)

    def write(self, vals):
        """Protect verification evidence once a measure is verified.

        :param dict vals: field values to write.
        :raise UserError: when verified evidence fields are edited.
        :return: ``True`` when the write succeeded.
        :rtype: bool
        """
        protected = {
            "description",
            "control_option",
            "implementation_evidence",
            "effectiveness_evidence",
        }
        if protected.intersection(vals):
            locked = self.filtered(lambda m: m.state == "verified")
            if locked:
                raise UserError(
                    self.env._(
                        "A verified risk control measure cannot be modified. "
                        "Blocked references: %(refs)s",
                        refs=", ".join(locked.mapped("name")),
                    )
                )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_risk_mitigation(self):
        """Restrict deletion to draft measures.

        :raise UserError: when any record has left the draft state.
        :return: ``True`` when deletion succeeded.
        :rtype: bool
        """
        blocked = self.filtered(lambda m: m.state != "draft")
        if blocked:
            raise UserError(
                self.env._(
                    "Only draft risk control measures can be deleted. Cancel "
                    "the others instead. Blocked references: %(refs)s",
                    refs=", ".join(blocked.mapped("name")),
                )
            )

    # ------------------------------------------------------------------
    # Workflow actions
    # ------------------------------------------------------------------
    def action_approve(self):
        """Approve a draft measure for implementation.

        :raise UserError: when the measure is not in draft.
        :return: ``True`` when all records were approved.
        :rtype: bool
        """
        self._ensure_risk_manager(self.env._("approve a risk control measure"))
        for measure in self:
            if measure.state != "draft":
                raise UserError(
                    self.env._("Only a draft risk control measure can be approved.")
                )
            measure.write(
                {
                    "state": "approved",
                    "approved_by_id": self.env.user.id,
                    "approval_date": fields.Datetime.now(),
                }
            )
        return True

    def action_start(self):
        """Mark an approved measure as being implemented.

        :raise UserError: when the measure is not approved.
        :return: ``True`` when all records advanced.
        :rtype: bool
        """
        for measure in self:
            if measure.state != "approved":
                raise UserError(
                    self.env._(
                        "Only an approved risk control measure can be started."
                    )
                )
            measure.state = "in_progress"
        return True

    def action_mark_implemented(self):
        """Record that the measure has been implemented.

        :raise UserError: when the measure is not in progress or has no
            implementation evidence.
        :return: ``True`` when all records advanced.
        :rtype: bool
        """
        for measure in self:
            if measure.state != "in_progress":
                raise UserError(
                    self.env._(
                        "Only a risk control measure in progress can be marked "
                        "as implemented."
                    )
                )
            if not (measure.implementation_evidence or "").strip():
                raise UserError(
                    self.env._(
                        "Record the implementation evidence for %(name)s before "
                        "marking it implemented.",
                        name=measure.display_name,
                    )
                )
            measure.write(
                {
                    "state": "implemented",
                    "implementation_date": fields.Date.context_today(measure),
                    "implementation_verified_by_id": self.env.user.id,
                    "implementation_verification_date": fields.Datetime.now(),
                }
            )
        return True

    def action_verify_effectiveness(self):
        """Verify the effectiveness of an implemented measure.

        Segregation of duties is enforced at ORM level: the person who
        verified implementation may not also verify effectiveness.

        :raise UserError: when the measure is not implemented, has no
            effectiveness evidence, or when the same user verified
            implementation.
        :return: ``True`` when all records were verified.
        :rtype: bool
        """
        for measure in self:
            if measure.state != "implemented":
                raise UserError(
                    self.env._(
                        "Only an implemented risk control measure can have its "
                        "effectiveness verified."
                    )
                )
            if not (measure.effectiveness_evidence or "").strip():
                raise UserError(
                    self.env._(
                        "Record the effectiveness evidence for %(name)s before "
                        "verifying it.",
                        name=measure.display_name,
                    )
                )
            if measure.implementation_verified_by_id == self.env.user:
                raise UserError(
                    self.env._(
                        "Segregation of duties: %(user)s verified the "
                        "implementation of %(name)s and therefore cannot verify "
                        "its effectiveness.",
                        user=self.env.user.display_name,
                        name=measure.display_name,
                    )
                )
            measure.write(
                {
                    "state": "verified",
                    "effectiveness_verified_by_id": self.env.user.id,
                    "effectiveness_verification_date": fields.Datetime.now(),
                }
            )
        return True

    def action_create_new_risk(self):
        """Create a risk register entry for the risk this measure introduces.

        :raise UserError: when no new risk is declared or one already exists.
        :return: an action opening the newly created risk.
        :rtype: dict
        """
        self.ensure_one()
        if not self.introduces_new_risk:
            raise UserError(
                self.env._(
                    "Declare that this measure introduces a new risk before "
                    "creating a risk record for it."
                )
            )
        if self.new_risk_id:
            raise UserError(
                self.env._(
                    "A risk record already exists for the risk introduced by "
                    "%(name)s.",
                    name=self.display_name,
                )
            )
        new_risk = self.env["ls.risk.register"].create(
            {
                "title": self.env._(
                    "Risk introduced by control measure %s", self.name
                ),
                "description": self.new_risk_description,
                "company_id": self.company_id.id,
                "risk_type": self.risk_id.risk_type,
                "category_id": self.risk_id.category_id.id or False,
                "matrix_id": self.risk_id.matrix_id.id,
                "owner_id": self.risk_id.owner_id.id,
            }
        )
        self.new_risk_id = new_risk
        return {
            "type": "ir.actions.act_window",
            "res_model": "ls.risk.register",
            "res_id": new_risk.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_open_cancel_wizard(self):
        """Open the risk control measure cancellation wizard.

        :return: an action opening the cancellation wizard.
        :rtype: dict
        """
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Cancel Risk Control Measures"),
            "res_model": "ls.risk.mitigation.cancel.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_mitigation_ids": self.ids},
        }
