# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Audit finding.

A finding records a departure from the audit criteria, together with the
objective evidence supporting it, the auditee response, the actions taken and
the verification that those actions were effective.  The finding cannot be
closed until the effectiveness verification has been documented.
"""

from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class LsAuditFinding(models.Model):
    """Departure from the audit criteria raised during an audit."""

    _name = "ls.audit.finding"
    _description = "Audit Finding"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    # Ordering on category_id sorts through the comodel _order, which is
    # "sequence, name": the most severe categories carry the lowest
    # sequence. Ordering on the severity selection itself would sort the
    # stored strings alphabetically, which is not the severity order.
    _order = "category_id, response_due_date, reference"

    reference = fields.Char(required=True,
                            readonly=True,
                            copy=False,
                            default=lambda self: _("New"),
                            index=True,
                            help="Unique reference allocated automatically on creation.",
                            )
    name = fields.Char(
        string="Title",
        required=True,
        tracking=True,
        help="Short statement of the finding.",
    )
    audit_id = fields.Many2one(comodel_name="ls.audit.schedule", required=True,
                               ondelete="restrict",
                               index=True,
                               tracking=True,
                               help="Audit during which the finding was raised.",)
    response_id = fields.Many2one(
        comodel_name="ls.audit.response",
        string="Source Question",
        ondelete="set null",
        help="Checklist question the finding was raised from.",
    )
    category_id = fields.Many2one(comodel_name="ls.audit.finding.category", required=True,
                                  ondelete="restrict",
                                  tracking=True,
                                  help="Classification driving the severity, the response deadline "
                                  "and whether a corrective action is mandatory.",)
    severity = fields.Selection(related="category_id.severity", store=True,
                                readonly=True,
                                index=True,
                                help="Severity inherited from the finding category.",)
    requires_capa = fields.Boolean(related="category_id.requires_capa", readonly=True,
                                   help="Whether a corrective and preventive action is mandatory.",)
    requires_root_cause = fields.Boolean(related="category_id.requires_root_cause", readonly=True,
                                         help="Whether a documented root cause is mandatory.",)
    area_id = fields.Many2one(comodel_name="ls.audit.area", required=True,
                              ondelete="restrict",
                              help="Area the finding relates to.",)
    description = fields.Text(
        string="Statement of Non-conformity",
        required=True,
        help="Clear statement of the requirement that was not met.",
    )
    evidence = fields.Text(
        string="Objective Evidence",
        required=True,
        help="Verifiable records or statements of fact supporting the "
             "finding.",
    )
    reference_clause = fields.Char(
        string="Requirement Reference",
        help="Reference of the requirement that was not met, for example a "
             "clause number or an internal procedure section.",
    )
    raised_by_id = fields.Many2one(comodel_name="res.users", required=True,
                                   default=lambda self: self.env.user,
                                   readonly=True,
                                   help="Auditor who raised the finding.",)
    raised_date = fields.Date(
        string="Raised On",
        required=True,
        default=fields.Date.context_today,
        readonly=True,
        help="Date on which the finding was raised.",
    )
    auditee_id = fields.Many2one(
        comodel_name="res.users",
        string="Responsible Auditee",
        required=True,
        tracking=True,
        index=True,
        help="User accountable for investigating the finding and providing "
             "the response.",
    )
    issue_date = fields.Date(
        string="Issued On",
        readonly=True,
        copy=False,
        tracking=True,
        help="Date on which the finding was formally issued to the auditee.",
    )
    response_due_date = fields.Date(
        string="Response Due",
        compute="_compute_response_due_date",
        store=True,
        readonly=False,
        tracking=True,
        help="Date by which the auditee response is expected. Proposed from "
             "the category deadline and adjustable by the lead auditor.",
    )
    root_cause = fields.Text(help="Result of the root cause investigation.",)
    correction = fields.Text(
        string="Immediate Correction",
        help="Action taken to eliminate the detected non-conformity itself.",
    )
    corrective_action = fields.Text(help="Action taken to eliminate the cause of the non-conformity so "
                                    "that it does not recur.",)
    capa_reference = fields.Char(tracking=True,
                                 help="Reference of the corrective and preventive action record held "
                                 "in the CAPA system. Recorded as a reference because the CAPA "
                                 "module is not a dependency of this module.",)
    action_due_date = fields.Date(
        string="Action Due",
        tracking=True,
        help="Date by which the corrective action is expected to be "
             "completed.",
    )
    responded_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                      copy=False,
                                      help="User who submitted the auditee response.",)
    response_date = fields.Date(
        string="Responded On",
        readonly=True,
        copy=False,
        tracking=True,
        help="Date on which the auditee response was submitted.",
    )
    verification_method = fields.Text(help="How the effectiveness of the action was verified.",)
    verification_result = fields.Text(help="Outcome of the effectiveness verification.",)
    verified_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                     copy=False,
                                     tracking=True,
                                     help="User who verified the effectiveness of the action.",)
    verification_date = fields.Date(
        string="Verified On",
        readonly=True,
        copy=False,
        tracking=True,
        help="Date on which the effectiveness verification was performed.",
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("open", "Issued"),
            ("responded", "Response Received"),
            ("in_progress", "Action In Progress"),
            ("verification", "Pending Verification"),
            ("closed", "Closed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
        copy=False,
        index=True,
        help="Lifecycle status of the finding.",
    )
    is_overdue = fields.Boolean(
        string="Overdue",
        compute="_compute_is_overdue",
        search="_search_is_overdue",
        help="A finding is overdue when the response due date has passed "
             "while no response has been submitted.",
    )
    days_open = fields.Integer(compute="_compute_days_open",
                               help="Number of days between the issue date and either the closure "
                               "date or today.",)
    cancellation_reason = fields.Text(readonly=True,
                                      copy=False,
                                      help="Justification recorded when the finding was cancelled.",)
    closure_date = fields.Date(
        string="Closed On",
        readonly=True,
        copy=False,
        tracking=True,
        help="Date on which the finding was closed.",
    )
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,
                                 index=True,
                                 help="Company owning this finding.",)
    active = fields.Boolean(default=True,
                            help="Archived findings are hidden from selection lists.",)

    _reference_company_uniq = models.Constraint(
        "UNIQUE(reference, company_id)",
        "The finding reference must be unique per company.",
    )

    # ------------------------------------------------------------------
    # Computed fields
    # ------------------------------------------------------------------

    @api.depends(
        "issue_date",
        "raised_date",
        "category_id.response_deadline_days",
    )
    def _compute_response_due_date(self):
        """Propose the response due date from the category deadline."""
        for finding in self:
            start_date = finding.issue_date or finding.raised_date
            deadline_days = finding.category_id.response_deadline_days
            if start_date and deadline_days:
                finding.response_due_date = start_date + timedelta(
                    days=deadline_days
                )
            elif start_date:
                finding.response_due_date = start_date
            else:
                finding.response_due_date = False

    @api.depends("response_due_date", "state")
    def _compute_is_overdue(self):
        """Flag findings whose response deadline passed without a response."""
        today = fields.Date.context_today(self)
        for finding in self:
            finding.is_overdue = bool(
                finding.response_due_date
                and finding.response_due_date < today
                and finding.state in ("open", "responded", "in_progress")
            )

    def _search_is_overdue(self, operator, value):
        """Translate a search on ``is_overdue`` into a stored-field domain.

        :param operator: comparison operator provided by the search engine.
        :param value: value provided by the search engine.
        :return: a domain expressed on stored fields only.
        :rtype: list
        :raise UserError: when an unsupported operator is used.
        """
        if operator not in ("=", "!="):
            raise UserError(
                _("The overdue filter only supports equality operators.")
            )
        today = fields.Date.context_today(self)
        open_states = ("open", "responded", "in_progress")
        overdue_domain = [
            ("response_due_date", "<", today),
            ("state", "in", open_states),
        ]
        not_overdue_domain = [
            "|",
            ("response_due_date", ">=", today),
            ("state", "not in", open_states),
        ]
        looking_for_overdue = bool(value) == (operator == "=")
        return overdue_domain if looking_for_overdue else not_overdue_domain

    @api.depends("issue_date", "closure_date")
    def _compute_days_open(self):
        """Compute how long the finding stayed open."""
        today = fields.Date.context_today(self)
        for finding in self:
            if not finding.issue_date:
                finding.days_open = 0
                continue
            end_date = finding.closure_date or today
            finding.days_open = (end_date - finding.issue_date).days

    @api.depends("reference", "name")
    def _compute_display_name(self):
        """Show the reference together with the finding title."""
        for finding in self:
            finding.display_name = "[%s] %s" % (
                finding.reference or "",
                finding.name or "",
            )

    # ------------------------------------------------------------------
    # Onchange
    # ------------------------------------------------------------------

    @api.onchange("audit_id")
    def _onchange_audit_id(self):
        """Propose the area and the auditee from the selected audit."""
        if not self.audit_id:
            return
        self.company_id = self.audit_id.company_id
        if len(self.audit_id.area_ids) == 1:
            self.area_id = self.audit_id.area_ids
        if self.area_id and self.area_id.responsible_id:
            self.auditee_id = self.area_id.responsible_id

    @api.onchange("area_id")
    def _onchange_area_id(self):
        """Propose the area owner as responsible auditee."""
        if self.area_id and self.area_id.responsible_id:
            self.auditee_id = self.area_id.responsible_id

    # ------------------------------------------------------------------
    # ORM overrides
    # ------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        """Allocate the reference and link the source question.

        :param vals_list: list of value dictionaries.
        :return: the created recordset.
        :rtype: recordset
        """
        for vals in vals_list:
            if vals.get("reference", _("New")) == _("New"):
                company_id = vals.get("company_id") or self.env.company.id
                vals["reference"] = (
                    self.env["ir.sequence"]
                    .with_company(company_id)
                    .next_by_code("ls.audit.finding")
                    or _("New")
                )
        findings = super().create(vals_list)
        for finding in findings:
            if finding.response_id and not finding.response_id.finding_id:
                finding.response_id.finding_id = finding.id
        return findings

    def write(self, vals):
        """Prevent modification of a finding that reached a final status.

        :param vals: values to write.
        :return: ``True``.
        :rtype: bool
        :raise UserError: when a locked finding would be modified.
        """
        allowed_fields = {
            "active",
            "message_follower_ids",
            "message_ids",
            "activity_ids",
        }
        if not set(vals) <= allowed_fields:
            locked = self.filtered(
                lambda finding: finding.state in ("closed", "cancelled")
            )
            if locked:
                raise UserError(
                    _(
                        "Finding(s) %(refs)s reached a final status and can "
                        "no longer be modified.",
                        refs=", ".join(locked.mapped("reference")),
                    )
                )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_audit_finding(self):
        """Forbid deletion of a finding that was issued.

        :return: ``True``.
        :rtype: bool
        :raise UserError: when an issued finding would be deleted.
        """
        issued = self.filtered(lambda finding: finding.state != "draft")
        if issued:
            raise UserError(
                _(
                    "Finding(s) %(refs)s were issued and cannot be deleted. "
                    "Cancel them instead so that the record and its audit "
                    "trail are retained.",
                    refs=", ".join(issued.mapped("reference")),
                )
            )

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------

    @api.constrains("auditee_id", "raised_by_id")
    def _check_auditee_is_not_auditor(self):
        """Forbid the auditor who raised a finding from also answering it.

        :raise ValidationError: when the auditee equals the raising auditor.
        """
        for finding in self:
            if finding.auditee_id == finding.raised_by_id:
                raise ValidationError(
                    _(
                        "Finding %(ref)s cannot be assigned to %(name)s, who "
                        "raised it. The response must come from the audited "
                        "area.",
                        ref=finding.reference,
                        name=finding.auditee_id.name,
                    )
                )

    @api.constrains("audit_id", "area_id")
    def _check_area_in_audit_scope(self):
        """Forbid a finding on an area outside the audit scope.

        :raise ValidationError: when the area is not part of the audit.
        """
        for finding in self:
            if finding.area_id not in finding.audit_id.area_ids:
                raise ValidationError(
                    _(
                        "Area '%(area)s' is not in the scope of audit "
                        "%(ref)s.",
                        area=finding.area_id.complete_name,
                        ref=finding.audit_id.reference,
                    )
                )

    @api.constrains("company_id", "audit_id", "category_id", "area_id")
    def _check_company_consistency(self):
        """Forbid references to records of another company.

        :raise ValidationError: when a linked record belongs to another
            company.
        """
        for finding in self:
            mismatched = []
            if finding.audit_id.company_id != finding.company_id:
                mismatched.append(_("audit"))
            if finding.category_id.company_id != finding.company_id:
                mismatched.append(_("category"))
            if finding.area_id.company_id != finding.company_id:
                mismatched.append(_("area"))
            if mismatched:
                raise ValidationError(
                    _(
                        "Finding %(ref)s references records of another "
                        "company: %(items)s.",
                        ref=finding.reference,
                        items=", ".join(mismatched),
                    )
                )

    # ------------------------------------------------------------------
    # Workflow transitions
    # ------------------------------------------------------------------

    def _check_state(self, expected, action_label):
        """Verify that every finding is in one of the ``expected`` statuses.

        :param expected: tuple of accepted status codes.
        :param action_label: translated label of the attempted transition.
        :raise UserError: when a finding is in an unexpected status.
        """
        wrong = self.filtered(lambda finding: finding.state not in expected)
        if wrong:
            raise UserError(
                _(
                    "Action '%(action)s' is not allowed for finding(s) "
                    "%(refs)s in their current status.",
                    action=action_label,
                    refs=", ".join(wrong.mapped("reference")),
                )
            )

    def action_issue(self):
        """Issue the finding to the auditee and notify them.

        :raise UserError: when the finding is not in draft status or when the
            parent audit is not at least in progress.
        """
        self._check_state(("draft",), _("Issue"))
        for finding in self:
            if finding.audit_id.state not in (
                "in_progress",
                "completed",
                "follow_up",
            ):
                raise UserError(
                    _(
                        "Finding %(ref)s cannot be issued because audit "
                        "%(audit)s is not in progress.",
                        ref=finding.reference,
                        audit=finding.audit_id.reference,
                    )
                )
        self.write(
            {"state": "open", "issue_date": fields.Date.context_today(self)}
        )
        template = self.env.ref(
            "ls_audit.mail_template_finding_issued", raise_if_not_found=False
        )
        for finding in self:
            finding.message_subscribe(
                partner_ids=finding.auditee_id.partner_id.ids
            )
            if template:
                template.send_mail(finding.id, force_send=False)
        return True

    def action_submit_response(self):
        """Open the wizard collecting the auditee response.

        :return: an act window action opening the response wizard.
        :rtype: dict
        """
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "ls.audit.finding.response",
            "view_mode": "form",
            "target": "new",
            "context": {"default_finding_id": self.id},
        }

    def action_accept_response(self):
        """Accept the auditee response and start the action phase.

        :raise UserError: when the finding has no response, when a mandatory
            root cause is missing, or when a mandatory CAPA reference is
            missing.
        """
        self._check_state(("responded",), _("Accept Response"))
        for finding in self:
            if finding.requires_root_cause and not (
                finding.root_cause and finding.root_cause.strip()
            ):
                raise UserError(
                    _(
                        "Finding %(ref)s requires a documented root cause "
                        "before the response can be accepted.",
                        ref=finding.reference,
                    )
                )
            if finding.requires_capa and not (
                finding.capa_reference and finding.capa_reference.strip()
            ):
                raise UserError(
                    _(
                        "Finding %(ref)s requires a CAPA reference before "
                        "the response can be accepted.",
                        ref=finding.reference,
                    )
                )
        self.write({"state": "in_progress"})
        return True

    def action_reject_response(self):
        """Reject the auditee response and request a new one.

        :raise UserError: when the finding has no pending response.
        """
        self._check_state(("responded",), _("Reject Response"))
        self.write({"state": "open"})
        for finding in self:
            finding.message_post(
                body=_(
                    "The response was rejected by %(user)s. A revised "
                    "response is required.",
                    user=self.env.user.name,
                )
            )
        return True

    def action_request_verification(self):
        """Declare the action complete and request effectiveness checking.

        :raise UserError: when the finding is not in the action phase.
        """
        self._check_state(("in_progress",), _("Request Verification"))
        self.write({"state": "verification"})
        return True

    def action_verify_and_close(self):
        """Verify effectiveness and close the finding.

        :raise UserError: when the finding is not pending verification, when
            the verification is not documented, or when the verifier is the
            auditee.
        """
        self._check_state(("verification",), _("Verify and Close"))
        for finding in self:
            if not (
                finding.verification_method
                and finding.verification_method.strip()
            ):
                raise UserError(
                    _(
                        "Finding %(ref)s cannot be closed because the "
                        "verification method has not been documented.",
                        ref=finding.reference,
                    )
                )
            if not (
                finding.verification_result
                and finding.verification_result.strip()
            ):
                raise UserError(
                    _(
                        "Finding %(ref)s cannot be closed because the "
                        "verification result has not been documented.",
                        ref=finding.reference,
                    )
                )
            if self.env.user == finding.auditee_id:
                raise UserError(
                    _(
                        "Finding %(ref)s cannot be verified by the "
                        "responsible auditee. Verification must be performed "
                        "independently.",
                        ref=finding.reference,
                    )
                )
        self.write(
            {
                "state": "closed",
                "verified_by_id": self.env.user.id,
                "verification_date": fields.Date.context_today(self),
                "closure_date": fields.Date.context_today(self),
            }
        )
        return True

    def action_cancel(self):
        """Open the cancellation wizard requesting a justification.

        :return: an act window action opening the cancellation wizard.
        :rtype: dict
        """
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "ls.audit.cancel",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_res_model": self._name,
                "default_res_id": self.id,
            },
        }

    # ------------------------------------------------------------------
    # Scheduled actions
    # ------------------------------------------------------------------

    @api.model
    def _cron_notify_overdue_findings(self):
        """Notify auditees and lead auditors of overdue findings.

        :return: the number of findings for which a notification was created.
        :rtype: int
        """
        today = fields.Date.context_today(self)
        overdue = self.search(
            [
                ("response_due_date", "<", today),
                ("state", "in", ("open", "responded", "in_progress")),
            ]
        )
        template = self.env.ref(
            "ls_audit.mail_template_finding_overdue", raise_if_not_found=False
        )
        if not template:
            return 0
        for finding in overdue:
            template.send_mail(finding.id, force_send=False)
        return len(overdue)
