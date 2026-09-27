# Part of the Life Sciences Suite. See LICENSE file for full copyright
# and licensing details.
"""Failure Mode and Effects Analysis.

FMEA is kept structurally separate from :mod:`ls_risk_assessment` because the
two use different constructs. An ISO 14971:2019 risk estimation uses severity
of harm and probability of occurrence of harm, evaluated against defined
acceptability criteria. FMEA additionally uses a detection rating and
combines the three ratings into a Risk Priority Number.

Verification note: the 1-10 rating scales and the Risk Priority Number are a
widely used industry convention. They could not be verified as a normative
requirement of ISO 14971:2019 or of any other standard referenced by this
suite, and the threshold above which action is required is therefore
configuration data set by the organisation on each worksheet.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from . import constants


class LsRiskFmea(models.Model):
    """An FMEA worksheet covering a defined scope."""

    _name = "ls.risk.fmea"
    _description = "FMEA Worksheet"
    _inherit = ["mail.thread", "mail.activity.mixin", "ls.risk.role.mixin"]
    _order = "id desc"

    name = fields.Char(
        string="Reference",
        required=True,
        readonly=True,
        copy=False,
        default=constants.SEQUENCE_PLACEHOLDER,
        index=True,
    )
    title = fields.Char(required=True, tracking=True)
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,
                                 index=True,)
    fmea_type = fields.Selection(selection=constants.FMEA_TYPES, required=True,
                                 default="process",
                                 tracking=True,)
    scope = fields.Text(required=True)
    assumptions = fields.Text(string="Assumptions and Boundaries")
    revision = fields.Integer(default=1, required=True, tracking=True)
    revision_reason = fields.Text()
    facilitator_id = fields.Many2one(comodel_name="res.users", required=True,
                                     default=lambda self: self.env.user,
                                     tracking=True,)
    team_member_ids = fields.Many2many(
        comodel_name="res.users",
        relation="ls_risk_fmea_team_rel",
        column1="fmea_id",
        column2="user_id",
        string="Team Members",
    )
    start_date = fields.Date(required=True, default=fields.Date.context_today)
    rpn_threshold = fields.Integer(
        string="RPN Action Threshold",
        default=100,
        required=True,
        tracking=True,
        help="Risk Priority Number at or above which a recommended action is "
        "required. This threshold is defined by the organisation; it is not "
        "prescribed by any standard referenced by this module.",
    )
    severity_action_threshold = fields.Integer(default=9,
                                               required=True,
                                               tracking=True,
                                               help="Severity rating at or above which a recommended action is "
                                               "required regardless of the Risk Priority Number. Defined by the "
                                               "organisation.",)
    state = fields.Selection(
        selection=constants.FMEA_STATES,
        string="Status",
        default="draft",
        required=True,
        tracking=True,
        copy=False,
        index=True,
    )
    active = fields.Boolean(default=True)
    line_ids = fields.One2many(
        comodel_name="ls.risk.fmea.line",
        inverse_name="fmea_id",
        string="Failure Modes",
        copy=True,
    )
    line_count = fields.Integer(
        string="Failure Mode Count", compute="_compute_line_statistics", store=True
    )
    max_rpn = fields.Integer(
        string="Highest RPN", compute="_compute_line_statistics", store=True
    )
    action_required_count = fields.Integer(
        string="Lines Requiring Action",
        compute="_compute_line_statistics",
        store=True,
    )
    open_action_count = fields.Integer(
        string="Open Actions", compute="_compute_line_statistics", store=True
    )
    reviewed_by_id = fields.Many2one(comodel_name="res.users", readonly=True, copy=False)
    review_date = fields.Datetime(readonly=True, copy=False)
    approved_by_id = fields.Many2one(comodel_name="res.users", readonly=True, copy=False)
    approval_date = fields.Datetime(readonly=True, copy=False)
    cancel_reason = fields.Text(string="Cancellation Reason", readonly=True, copy=False)

    _name_company_uniq = models.Constraint(
        "UNIQUE(name, company_id)",
        "The FMEA reference must be unique per company.",
    )
    _revision_positive = models.Constraint(
        "CHECK(revision > 0)",
        "The FMEA revision number must be strictly positive.",
    )
    _rpn_threshold_range = models.Constraint(
        "CHECK(rpn_threshold >= 1 AND rpn_threshold <= 1000)",
        "The RPN action threshold must be between 1 and 1000.",
    )
    _severity_threshold_range = models.Constraint(
        "CHECK(severity_action_threshold >= 1 AND severity_action_threshold <= 10)",
        "The severity action threshold must be between 1 and 10.",
    )

    @api.depends(
        "line_ids.rpn",
        "line_ids.action_required",
        "line_ids.action_state",
    )
    def _compute_line_statistics(self):
        """Derive worksheet level statistics from its lines."""
        for fmea in self:
            lines = fmea.line_ids
            fmea.line_count = len(lines)
            fmea.max_rpn = max(lines.mapped("rpn"), default=0)
            action_lines = lines.filtered("action_required")
            fmea.action_required_count = len(action_lines)
            fmea.open_action_count = len(
                action_lines.filtered(lambda line: line.action_state != "completed")
            )

    @api.depends("name", "title", "revision")
    def _compute_display_name(self):
        """Show the reference, title and revision."""
        for fmea in self:
            fmea.display_name = f"{fmea.name} - {fmea.title} (rev. {fmea.revision})"

    @api.model_create_multi
    def create(self, vals_list):
        """Assign the worksheet reference from the configured sequence.

        :param list vals_list: list of field value dictionaries.
        :return: the created records.
        :rtype: :class:`odoo.models.Model`
        """
        for vals in vals_list:
            if vals.get("name", constants.SEQUENCE_PLACEHOLDER) == constants.SEQUENCE_PLACEHOLDER:
                company_id = vals.get("company_id") or self.env.company.id
                sequence = self.env["ir.sequence"].with_company(company_id)
                vals["name"] = (
                    sequence.next_by_code(constants.SEQUENCE_FMEA)
                    or constants.SEQUENCE_PLACEHOLDER
                )
        return super().create(vals_list)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_risk_fmea(self):
        """Restrict deletion to draft and cancelled worksheets.

        :raise UserError: when any record is beyond the draft or cancelled state.
        :return: ``True`` when deletion succeeded.
        :rtype: bool
        """
        blocked = self.filtered(lambda fmea: fmea.state not in ("draft", "cancelled"))
        if blocked:
            raise UserError(
                self.env._(
                    "Only draft or cancelled FMEA worksheets can be deleted. "
                    "Blocked references: %(refs)s",
                    refs=", ".join(blocked.mapped("name")),
                )
            )

    def action_start(self):
        """Move a draft worksheet into the in-progress state.

        :raise UserError: when the worksheet is not in draft.
        :return: ``True`` when all records advanced.
        :rtype: bool
        """
        for fmea in self:
            if fmea.state != "draft":
                raise UserError(
                    self.env._("Only a draft FMEA worksheet can be started.")
                )
            fmea.state = "in_progress"
        return True

    def action_submit_review(self):
        """Submit an in-progress worksheet for review.

        :raise UserError: when the worksheet is not in progress or has no lines.
        :return: ``True`` when all records advanced.
        :rtype: bool
        """
        for fmea in self:
            if fmea.state != "in_progress":
                raise UserError(
                    self.env._(
                        "Only an FMEA worksheet in progress can be submitted for "
                        "review."
                    )
                )
            if not fmea.line_ids:
                raise UserError(
                    self.env._(
                        "FMEA %(name)s has no failure modes recorded.",
                        name=fmea.display_name,
                    )
                )
            fmea.state = "review"
        return True

    def action_review(self):
        """Record the review of a worksheet.

        :raise UserError: when the worksheet is not under review or when the
            reviewer facilitated the analysis.
        :return: ``True`` when all records were reviewed.
        :rtype: bool
        """
        self._ensure_risk_manager(self.env._("record the review of an FMEA worksheet"))
        for fmea in self:
            if fmea.state != "review":
                raise UserError(
                    self.env._("Only an FMEA worksheet under review can be reviewed.")
                )
            if fmea.facilitator_id == self.env.user:
                raise UserError(
                    self.env._(
                        "Segregation of duties: %(user)s facilitated FMEA "
                        "%(name)s and therefore cannot review it.",
                        user=self.env.user.display_name,
                        name=fmea.display_name,
                    )
                )
            fmea.write(
                {
                    "reviewed_by_id": self.env.user.id,
                    "review_date": fields.Datetime.now(),
                }
            )
        return True

    def action_approve(self):
        """Approve a reviewed worksheet.

        :raise UserError: when the worksheet was not reviewed, when lines
            requiring action have none recorded, or when the approver
            facilitated the analysis.
        :return: ``True`` when all records were approved.
        :rtype: bool
        """
        self._ensure_risk_manager(self.env._("approve an FMEA worksheet"))
        for fmea in self:
            if fmea.state != "review":
                raise UserError(
                    self.env._("Only an FMEA worksheet under review can be approved.")
                )
            if not fmea.reviewed_by_id:
                raise UserError(
                    self.env._(
                        "FMEA %(name)s must be reviewed before it is approved.",
                        name=fmea.display_name,
                    )
                )
            if fmea.facilitator_id == self.env.user:
                raise UserError(
                    self.env._(
                        "Segregation of duties: %(user)s facilitated FMEA "
                        "%(name)s and therefore cannot approve it.",
                        user=self.env.user.display_name,
                        name=fmea.display_name,
                    )
                )
            missing = fmea.line_ids.filtered(
                lambda line: line.action_required
                and not (line.recommended_action or "").strip()
            )
            if missing:
                raise UserError(
                    self.env._(
                        "The following failure modes of %(name)s require a "
                        "recommended action: %(lines)s",
                        name=fmea.display_name,
                        lines=", ".join(missing.mapped("failure_mode")),
                    )
                )
            fmea.write(
                {
                    "state": "approved",
                    "approved_by_id": self.env.user.id,
                    "approval_date": fields.Datetime.now(),
                }
            )
        return True

    def action_close(self):
        """Close an approved worksheet.

        :raise UserError: when the worksheet is not approved or still has open
            actions.
        :return: ``True`` when all records were closed.
        :rtype: bool
        """
        self._ensure_risk_manager(self.env._("close an FMEA worksheet"))
        for fmea in self:
            if fmea.state != "approved":
                raise UserError(
                    self.env._("Only an approved FMEA worksheet can be closed.")
                )
            if fmea.open_action_count:
                raise UserError(
                    self.env._(
                        "FMEA %(name)s still has %(count)s open action(s).",
                        name=fmea.display_name,
                        count=fmea.open_action_count,
                    )
                )
            fmea.state = "closed"
        return True

    def action_open_cancel_wizard(self):
        """Open the FMEA cancellation wizard.

        :return: an action opening the cancellation wizard.
        :rtype: dict
        """
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Cancel FMEA Worksheets"),
            "res_model": "ls.risk.fmea.cancel.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_fmea_ids": self.ids},
        }

    def action_create_revision(self):
        """Create the next revision of an approved or closed worksheet.

        The current worksheet is closed where necessary and a copy is created
        with an incremented revision number, so that the superseded analysis
        remains available as a record.

        :raise UserError: when the worksheet is not approved or closed.
        :return: an action opening the new revision.
        :rtype: dict
        """
        self.ensure_one()
        if self.state not in ("approved", "closed"):
            raise UserError(
                self.env._(
                    "Only an approved or closed FMEA worksheet can be revised."
                )
            )
        new_revision = self.copy(
            {
                "revision": self.revision + 1,
                "state": "draft",
                "reviewed_by_id": False,
                "review_date": False,
                "approved_by_id": False,
                "approval_date": False,
            }
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": "ls.risk.fmea",
            "res_id": new_revision.id,
            "view_mode": "form",
            "target": "current",
        }


class LsRiskFmeaLine(models.Model):
    """One failure mode row of an FMEA worksheet."""

    _name = "ls.risk.fmea.line"
    _description = "FMEA Failure Mode"
    _order = "fmea_id, sequence, id"

    fmea_id = fields.Many2one(
        comodel_name="ls.risk.fmea",
        string="FMEA",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(comodel_name="res.company", related="fmea_id.company_id",
                                 store=True,
                                 readonly=True,
                                 index=True,)
    sequence = fields.Integer(default=10)
    item = fields.Char(required=True)
    item_function = fields.Char(string="Function", required=True)
    failure_mode = fields.Char(required=True)
    failure_effect = fields.Text(string="Effect of Failure", required=True)
    severity = fields.Integer(string="Severity (S)", required=True, default=1)
    failure_cause = fields.Text(string="Potential Cause", required=True)
    occurrence = fields.Integer(string="Occurrence (O)", required=True, default=1)
    current_controls = fields.Text()
    detection = fields.Integer(string="Detection (D)", required=True, default=1)
    rpn = fields.Integer(compute="_compute_rpn",
                         store=True,
                         help="Risk Priority Number, the product of severity, occurrence and "
                         "detection.",)
    action_required = fields.Boolean(compute="_compute_action_required",
                                     store=True,
                                     help="Set when the Risk Priority Number reaches the worksheet "
                                     "threshold, or when the severity reaches the worksheet severity "
                                     "threshold.",)
    recommended_action = fields.Text()
    responsible_id = fields.Many2one(comodel_name="res.users")
    target_date = fields.Date()
    actions_taken = fields.Text()
    action_state = fields.Selection(
        selection=[
            ("not_required", "Not Required"),
            ("open", "Open"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
        ],
        string="Action Status",
        default="not_required",
        required=True,
    )
    revised_severity = fields.Integer()
    revised_occurrence = fields.Integer()
    revised_detection = fields.Integer()
    revised_rpn = fields.Integer(compute="_compute_revised_rpn", store=True)
    rpn_reduction = fields.Integer(compute="_compute_revised_rpn", store=True)
    risk_id = fields.Many2one(
        comodel_name="ls.risk.register",
        string="Risk Register Entry",
        help="Risk register entry raised from this failure mode.",
    )

    _severity_range = models.Constraint(
        "CHECK(severity >= 1 AND severity <= 10)",
        "Severity must be between 1 and 10.",
    )
    _occurrence_range = models.Constraint(
        "CHECK(occurrence >= 1 AND occurrence <= 10)",
        "Occurrence must be between 1 and 10.",
    )
    _detection_range = models.Constraint(
        "CHECK(detection >= 1 AND detection <= 10)",
        "Detection must be between 1 and 10.",
    )
    _revised_severity_range = models.Constraint(
        "CHECK(revised_severity >= 0 AND revised_severity <= 10)",
        "Revised severity must be between 1 and 10, or left empty.",
    )
    _revised_occurrence_range = models.Constraint(
        "CHECK(revised_occurrence >= 0 AND revised_occurrence <= 10)",
        "Revised occurrence must be between 1 and 10, or left empty.",
    )
    _revised_detection_range = models.Constraint(
        "CHECK(revised_detection >= 0 AND revised_detection <= 10)",
        "Revised detection must be between 1 and 10, or left empty.",
    )

    @api.depends("severity", "occurrence", "detection")
    def _compute_rpn(self):
        """Compute the Risk Priority Number as S x O x D."""
        for line in self:
            line.rpn = line.severity * line.occurrence * line.detection

    @api.depends(
        "rpn",
        "severity",
        "fmea_id.rpn_threshold",
        "fmea_id.severity_action_threshold",
    )
    def _compute_action_required(self):
        """Flag lines that meet either worksheet action threshold."""
        for line in self:
            line.action_required = bool(
                line.rpn >= line.fmea_id.rpn_threshold
                or line.severity >= line.fmea_id.severity_action_threshold
            )

    @api.depends(
        "revised_severity", "revised_occurrence", "revised_detection", "rpn"
    )
    def _compute_revised_rpn(self):
        """Compute the revised RPN and the reduction achieved."""
        for line in self:
            if line.revised_severity and line.revised_occurrence and line.revised_detection:
                line.revised_rpn = (
                    line.revised_severity
                    * line.revised_occurrence
                    * line.revised_detection
                )
                line.rpn_reduction = line.rpn - line.revised_rpn
            else:
                line.revised_rpn = 0
                line.rpn_reduction = 0

    @api.depends("item", "failure_mode")
    def _compute_display_name(self):
        """Show the item and its failure mode."""
        for line in self:
            line.display_name = f"{line.item} - {line.failure_mode}"

    @api.constrains(
        "revised_severity", "revised_occurrence", "revised_detection"
    )
    def _check_revised_ratings_complete(self):
        """Require all three revised ratings together, or none of them."""
        for line in self:
            provided = [
                bool(line.revised_severity),
                bool(line.revised_occurrence),
                bool(line.revised_detection),
            ]
            if any(provided) and not all(provided):
                raise ValidationError(
                    self.env._(
                        "Revised severity, occurrence and detection must all be "
                        "provided together on failure mode %(name)s.",
                        name=line.display_name,
                    )
                )

    @api.onchange("severity", "occurrence", "detection")
    def _onchange_ratings(self):
        """Open the action when a rating change makes action required."""
        for line in self:
            required = bool(
                line.severity * line.occurrence * line.detection
                >= line.fmea_id.rpn_threshold
                or line.severity >= line.fmea_id.severity_action_threshold
            )
            if required and line.action_state == "not_required":
                line.action_state = "open"

    def action_create_risk(self):
        """Raise a risk register entry from this failure mode.

        :raise UserError: when a risk record already exists, or when the
            company has no approved default matrix.
        :return: an action opening the created risk.
        :rtype: dict
        """
        self.ensure_one()
        if self.risk_id:
            raise UserError(
                self.env._(
                    "A risk register entry already exists for failure mode "
                    "%(name)s.",
                    name=self.display_name,
                )
            )
        matrix = self.env["ls.risk.matrix"].search(
            [
                ("company_id", "=", self.company_id.id),
                ("is_default", "=", True),
                ("state", "=", "approved"),
            ],
            limit=1,
        )
        if not matrix:
            raise UserError(
                self.env._(
                    "Company %(company)s has no approved default risk matrix. "
                    "Configure one before raising risks from an FMEA.",
                    company=self.company_id.display_name,
                )
            )
        risk = self.env["ls.risk.register"].create(
            {
                "title": self.env._(
                    "%(item)s - %(mode)s",
                    item=self.item,
                    mode=self.failure_mode,
                ),
                "description": self.failure_cause,
                "harm": self.failure_effect,
                "hazard": self.failure_mode,
                "company_id": self.company_id.id,
                "risk_type": "process"
                if self.fmea_id.fmea_type == "process"
                else "product",
                "matrix_id": matrix.id,
                "owner_id": (self.responsible_id or self.fmea_id.facilitator_id).id,
            }
        )
        self.risk_id = risk
        return {
            "type": "ir.actions.act_window",
            "res_model": "ls.risk.register",
            "res_id": risk.id,
            "view_mode": "form",
            "target": "current",
        }
