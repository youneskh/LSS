# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Audit engagement.

This model carries a single audit from planning through execution, reporting
and follow up to closure.  It is named ``ls.audit.schedule`` to stay aligned
with the Life Sciences Suite Functional Specification, section 7.4, even
though the record represents the whole engagement and not only its date.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

#: Statuses in which an audit is considered finished and becomes read only.
FINAL_STATES = ("closed", "cancelled")


class LsAuditSchedule(models.Model):
    """Single audit engagement, from planning to closure."""

    _name = "ls.audit.schedule"
    _description = "Audit"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_planned desc, reference desc"

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
        translate=True,
        tracking=True,
        help="Short title describing the audit.",
    )
    program_id = fields.Many2one(
        comodel_name="ls.audit.program",
        string="Audit Programme",
        ondelete="restrict",
        tracking=True,
        index=True,
        help="Programme this audit belongs to.",
    )
    audit_type_id = fields.Many2one(comodel_name="ls.audit.type", required=True,
                                    ondelete="restrict",
                                    tracking=True,
                                    help="Classification of the audit engagement.",)
    area_ids = fields.Many2many(
        comodel_name="ls.audit.area",
        relation="ls_audit_schedule_area_rel",
        column1="audit_id",
        column2="area_id",
        string="Audited Areas",
        required=True,
        tracking=True,
        help="Areas, processes or systems in the scope of this audit.",
    )
    audited_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Audited Organisation",
        tracking=True,
        help="External organisation being audited, for a supplier audit, or "
             "the auditing body, for a regulatory inspection.",
    )
    objective = fields.Text(required=True,
                            help="What the audit is intended to determine.",)
    scope = fields.Text(required=True,
                        help="Boundaries of the audit: sites, processes, products, periods "
                        "and shifts covered, and explicit exclusions.",)
    criteria = fields.Text(
        string="Audit Criteria",
        help="Set of requirements used as a reference against which "
             "evidence is compared, for example internal procedures, "
             "customer requirements or a named standard.",
    )
    lead_auditor_id = fields.Many2one(comodel_name="res.users", required=True,
                                      default=lambda self: self.env.user,
                                      tracking=True,
                                      index=True,
                                      help="Auditor leading the audit team and accountable for the audit "
                                      "report. Must hold a valid lead auditor qualification.",)
    auditor_ids = fields.Many2many(
        comodel_name="res.users",
        relation="ls_audit_schedule_auditor_rel",
        column1="audit_id",
        column2="user_id",
        string="Audit Team",
        help="Additional auditors taking part in the audit.",
    )
    auditee_ids = fields.Many2many(
        comodel_name="res.users",
        relation="ls_audit_schedule_auditee_rel",
        column1="audit_id",
        column2="user_id",
        string="Auditees",
        help="Representatives of the audited areas.",
    )
    date_planned = fields.Date(
        string="Planned Date",
        required=True,
        default=fields.Date.context_today,
        tracking=True,
        index=True,
        help="Date on which the audit is planned to take place.",
    )
    date_start = fields.Datetime(
        string="Actual Start",
        readonly=True,
        copy=False,
        tracking=True,
        help="Date and time at which the audit was actually started.",
    )
    date_end = fields.Datetime(
        string="Actual End",
        readonly=True,
        copy=False,
        tracking=True,
        help="Date and time at which the audit fieldwork was completed.",
    )
    duration_hours = fields.Float(
        string="Duration (hours)",
        compute="_compute_duration_hours",
        store=True,
        help="Elapsed time between the actual start and the actual end.",
    )
    state = fields.Selection(
        selection=[
            ("planned", "Planned"),
            ("scheduled", "Scheduled"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("follow_up", "Follow-up"),
            ("closed", "Closed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="planned",
        required=True,
        tracking=True,
        copy=False,
        index=True,
        help="Lifecycle status of the audit.",
    )
    checklist_id = fields.Many2one(
        comodel_name="ls.audit.checklist",
        string="Checklist Used",
        readonly=True,
        copy=False,
        tracking=True,
        help="Approved checklist template loaded into this audit. Recorded "
             "for traceability of the executed question set.",
    )
    response_ids = fields.One2many(
        comodel_name="ls.audit.response",
        inverse_name="audit_id",
        string="Checklist Responses",
        copy=False,
        help="Questions assessed during the audit.",
    )
    finding_ids = fields.One2many(
        comodel_name="ls.audit.finding",
        inverse_name="audit_id",
        string="Findings",
        copy=False,
        help="Findings raised during the audit.",
    )
    report_ids = fields.One2many(
        comodel_name="ls.audit.report",
        inverse_name="audit_id",
        string="Audit Reports",
        copy=False,
        help="Audit reports produced for this audit.",
    )
    response_count = fields.Integer(
        string="Question Count",
        compute="_compute_response_statistics",
        help="Number of questions loaded into the audit.",
    )
    assessed_count = fields.Integer(
        string="Assessed Questions",
        compute="_compute_response_statistics",
        help="Number of questions that received an assessment.",
    )
    conformity_rate = fields.Float(
        string="Conformity Rate (%)",
        compute="_compute_response_statistics",
        store=True,
        help="Share of applicable assessed questions found conform.",
    )
    finding_count = fields.Integer(
        string="Findings",
        compute="_compute_finding_statistics",
        help="Total number of findings raised during the audit.",
    )
    open_finding_count = fields.Integer(
        string="Open Findings",
        compute="_compute_finding_statistics",
        store=True,
        help="Number of findings that are neither closed nor cancelled.",
    )
    critical_finding_count = fields.Integer(
        string="Critical Findings",
        compute="_compute_finding_statistics",
        store=True,
        help="Number of findings classified with a critical severity.",
    )
    major_finding_count = fields.Integer(
        string="Major Findings",
        compute="_compute_finding_statistics",
        store=True,
        help="Number of findings classified with a major severity.",
    )
    report_count = fields.Integer(
        string="Reports",
        compute="_compute_report_count",
        help="Number of audit reports produced for this audit.",
    )
    is_overdue = fields.Boolean(
        string="Overdue",
        compute="_compute_is_overdue",
        search="_search_is_overdue",
        help="An audit is overdue when its planned date has passed while it "
             "has not been started.",
    )
    cancellation_reason = fields.Text(readonly=True,
                                      copy=False,
                                      help="Justification recorded when the audit was cancelled.",)
    closed_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                   copy=False,
                                   tracking=True,
                                   help="User who closed the audit.",)
    closure_date = fields.Datetime(readonly=True,
                                   copy=False,
                                   tracking=True,
                                   help="Date and time at which the audit was closed.",)
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,
                                 index=True,
                                 help="Company owning this audit.",)
    active = fields.Boolean(default=True,
                            help="Archived audits are hidden from selection lists.",)

    _reference_company_uniq = models.Constraint(
        "UNIQUE(reference, company_id)",
        "The audit reference must be unique per company.",
    )

    # ------------------------------------------------------------------
    # Computed fields
    # ------------------------------------------------------------------

    @api.depends("date_start", "date_end")
    def _compute_duration_hours(self):
        """Compute the elapsed fieldwork duration in hours."""
        for audit in self:
            if audit.date_start and audit.date_end:
                delta = audit.date_end - audit.date_start
                audit.duration_hours = delta.total_seconds() / 3600.0
            else:
                audit.duration_hours = 0.0

    @api.depends("response_ids", "response_ids.result")
    def _compute_response_statistics(self):
        """Count assessed questions and derive the conformity rate."""
        for audit in self:
            responses = audit.response_ids
            assessed = responses.filtered(
                lambda response: response.result != "pending"
            )
            applicable = assessed.filtered(
                lambda response: response.result != "not_applicable"
            )
            conform = applicable.filtered(
                lambda response: response.result == "conform"
            )
            audit.response_count = len(responses)
            audit.assessed_count = len(assessed)
            audit.conformity_rate = (
                100.0 * len(conform) / len(applicable) if applicable else 0.0
            )

    @api.depends("finding_ids", "finding_ids.state", "finding_ids.severity")
    def _compute_finding_statistics(self):
        """Count findings by status and by severity."""
        for audit in self:
            findings = audit.finding_ids
            audit.finding_count = len(findings)
            audit.open_finding_count = len(
                findings.filtered(
                    lambda finding: finding.state
                    not in ("closed", "cancelled")
                )
            )
            audit.critical_finding_count = len(
                findings.filtered(
                    lambda finding: finding.severity == "critical"
                )
            )
            audit.major_finding_count = len(
                findings.filtered(lambda finding: finding.severity == "major")
            )

    @api.depends("report_ids")
    def _compute_report_count(self):
        """Count the audit reports produced for the audit."""
        for audit in self:
            audit.report_count = len(audit.report_ids)

    @api.depends("date_planned", "state")
    def _compute_is_overdue(self):
        """Flag audits whose planned date passed before they were started."""
        today = fields.Date.context_today(self)
        for audit in self:
            audit.is_overdue = bool(
                audit.date_planned
                and audit.date_planned < today
                and audit.state in ("planned", "scheduled")
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
        overdue_domain = [
            ("date_planned", "<", today),
            ("state", "in", ("planned", "scheduled")),
        ]
        not_overdue_domain = [
            "|",
            ("date_planned", ">=", today),
            ("state", "not in", ("planned", "scheduled")),
        ]
        looking_for_overdue = bool(value) == (operator == "=")
        return overdue_domain if looking_for_overdue else not_overdue_domain

    @api.depends("reference", "name")
    def _compute_display_name(self):
        """Show the reference together with the audit title."""
        for audit in self:
            audit.display_name = "[%s] %s" % (
                audit.reference or "",
                audit.name or "",
            )

    # ------------------------------------------------------------------
    # ORM overrides
    # ------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        """Allocate the audit reference from the dedicated sequence.

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
                    .next_by_code("ls.audit.schedule")
                    or _("New")
                )
        return super().create(vals_list)

    def write(self, vals):
        """Prevent modification of an audit that reached a final status.

        Only the fields listed in ``allowed_fields`` remain writable, so that
        a closed audit stays an accurate record of what was performed while
        still allowing archiving and message subscription.

        :param vals: values to write.
        :return: ``True``.
        :rtype: bool
        :raise UserError: when a locked audit would be modified.
        """
        allowed_fields = {
            "active",
            "message_follower_ids",
            "message_ids",
            "activity_ids",
        }
        if not set(vals) <= allowed_fields:
            locked = self.filtered(lambda audit: audit.state in FINAL_STATES)
            if locked:
                raise UserError(
                    _(
                        "Audit(s) %(refs)s reached a final status and can no "
                        "longer be modified.",
                        refs=", ".join(locked.mapped("reference")),
                    )
                )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_audit_schedule(self):
        """Forbid deletion of an audit that left the planned status.

        :return: ``True``.
        :rtype: bool
        :raise UserError: when a started audit would be deleted.
        """
        started = self.filtered(lambda audit: audit.state != "planned")
        if started:
            raise UserError(
                _(
                    "Audit(s) %(refs)s cannot be deleted because they left "
                    "the planned status. Cancel them instead so that the "
                    "record and its audit trail are retained.",
                    refs=", ".join(started.mapped("reference")),
                )
            )

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------

    @api.constrains("lead_auditor_id", "auditor_ids", "auditee_ids")
    def _check_auditor_independence(self):
        """Forbid an auditor from auditing their own work.

        The audit team and the auditees must be disjoint sets. This supports
        the objectivity and impartiality expectation applied to internal
        audit programmes.

        :raise ValidationError: when a user is both auditor and auditee.
        """
        for audit in self:
            team = audit.auditor_ids | audit.lead_auditor_id
            conflicting = team & audit.auditee_ids
            if conflicting:
                raise ValidationError(
                    _(
                        "Audit %(ref)s is not impartial: %(names)s appear "
                        "both in the audit team and among the auditees. An "
                        "auditor cannot audit their own work.",
                        ref=audit.reference,
                        names=", ".join(conflicting.mapped("name")),
                    )
                )

    @api.constrains("lead_auditor_id", "auditor_ids", "area_ids")
    def _check_auditor_not_area_owner(self):
        """Forbid an auditor from auditing an area they own.

        :raise ValidationError: when an auditor owns an audited area.
        """
        for audit in self:
            team = audit.auditor_ids | audit.lead_auditor_id
            owners = audit.area_ids.mapped("responsible_id")
            conflicting = team & owners
            if conflicting:
                raise ValidationError(
                    _(
                        "Audit %(ref)s is not impartial: %(names)s own at "
                        "least one of the audited areas and cannot be part "
                        "of the audit team.",
                        ref=audit.reference,
                        names=", ".join(conflicting.mapped("name")),
                    )
                )

    @api.constrains("program_id", "date_planned")
    def _check_planned_date_within_program(self):
        """Forbid a planned date outside the programme period.

        :raise ValidationError: when the planned date falls outside the
            period covered by the programme.
        """
        for audit in self:
            program = audit.program_id
            if not program or not audit.date_planned:
                continue
            in_period = (
                program.date_start
                <= audit.date_planned
                <= program.date_end
            )
            if not in_period:
                raise ValidationError(
                    _(
                        "The planned date of audit %(ref)s falls outside the "
                        "period of programme %(program)s "
                        "(%(start)s to %(end)s).",
                        ref=audit.reference,
                        program=program.display_name,
                        start=program.date_start,
                        end=program.date_end,
                    )
                )

    @api.constrains("company_id", "program_id", "audit_type_id", "area_ids")
    def _check_company_consistency(self):
        """Forbid references to records of another company.

        :raise ValidationError: when a linked record belongs to another
            company.
        """
        for audit in self:
            if (
                audit.program_id
                and audit.program_id.company_id != audit.company_id
            ):
                raise ValidationError(
                    _(
                        "The programme of audit %(ref)s belongs to another "
                        "company.",
                        ref=audit.reference,
                    )
                )
            if audit.audit_type_id.company_id != audit.company_id:
                raise ValidationError(
                    _(
                        "The audit type of audit %(ref)s belongs to another "
                        "company.",
                        ref=audit.reference,
                    )
                )
            other_areas = audit.area_ids.filtered(
                lambda area, audit=audit: area.company_id != audit.company_id
            )
            if other_areas:
                raise ValidationError(
                    _(
                        "Audit %(ref)s covers areas of another company: "
                        "%(areas)s.",
                        ref=audit.reference,
                        areas=", ".join(other_areas.mapped("complete_name")),
                    )
                )

    # ------------------------------------------------------------------
    # Business helpers
    # ------------------------------------------------------------------

    def _get_auditor_qualification(self, user):
        """Return the qualification record of ``user`` for this company.

        :param user: ``res.users`` record to look up.
        :return: the matching ``ls.audit.auditor`` record, possibly empty.
        :rtype: recordset
        """
        self.ensure_one()
        return self.env["ls.audit.auditor"].search(
            [
                ("user_id", "=", user.id),
                ("company_id", "=", self.company_id.id),
            ],
            limit=1,
        )

    def _check_team_qualification(self):
        """Verify that the audit team holds valid qualifications.

        :raise UserError: when the lead auditor is not a qualified lead
            auditor, or when a team member has no valid qualification for the
            audited areas.
        """
        for audit in self:
            lead_qualification = audit._get_auditor_qualification(
                audit.lead_auditor_id
            )
            is_qualified_lead = (
                lead_qualification
                and lead_qualification.is_lead_auditor
            )
            if not is_qualified_lead:
                raise UserError(
                    _(
                        "%(name)s is not registered as a qualified lead "
                        "auditor and cannot lead audit %(ref)s.",
                        name=audit.lead_auditor_id.name,
                        ref=audit.reference,
                    )
                )
            team = audit.auditor_ids | audit.lead_auditor_id
            for member in team:
                qualification = audit._get_auditor_qualification(member)
                if not qualification:
                    raise UserError(
                        _(
                            "%(name)s has no auditor qualification record "
                            "and cannot be assigned to audit %(ref)s.",
                            name=member.name,
                            ref=audit.reference,
                        )
                    )
                if not qualification.is_qualified_for(audit.area_ids):
                    raise UserError(
                        _(
                            "The qualification of %(name)s is expired or "
                            "does not cover every area of audit %(ref)s.",
                            name=member.name,
                            ref=audit.reference,
                        )
                    )

    def _check_state(self, expected, action_label):
        """Verify that every audit is in one of the ``expected`` statuses.

        :param expected: tuple of accepted status codes.
        :param action_label: translated label of the attempted transition.
        :raise UserError: when an audit is in an unexpected status.
        """
        wrong = self.filtered(lambda audit: audit.state not in expected)
        if wrong:
            raise UserError(
                _(
                    "Action '%(action)s' is not allowed for audit(s) "
                    "%(refs)s in their current status.",
                    action=action_label,
                    refs=", ".join(wrong.mapped("reference")),
                )
            )

    # ------------------------------------------------------------------
    # Workflow transitions
    # ------------------------------------------------------------------

    def action_schedule(self):
        """Confirm the audit plan and notify the participants.

        :raise UserError: when the audit is not planned, when the programme
            is not approved, or when the team is not qualified.
        """
        self._check_state(("planned",), _("Schedule"))
        for audit in self:
            if audit.program_id and audit.program_id.state not in (
                "approved",
                "in_progress",
            ):
                raise UserError(
                    _(
                        "Audit %(ref)s cannot be scheduled because its "
                        "programme has not been approved.",
                        ref=audit.reference,
                    )
                )
        self._check_team_qualification()
        self.write({"state": "scheduled"})
        for audit in self:
            audit.message_subscribe(
                partner_ids=(
                    audit.auditor_ids
                    | audit.lead_auditor_id
                    | audit.auditee_ids
                ).partner_id.ids
            )
        return True

    def action_start(self):
        """Start the audit fieldwork.

        :raise UserError: when the audit is not scheduled or has no question
            loaded.
        """
        self._check_state(("scheduled",), _("Start"))
        for audit in self:
            if not audit.response_ids:
                raise UserError(
                    _(
                        "Audit %(ref)s cannot be started because no "
                        "checklist has been loaded.",
                        ref=audit.reference,
                    )
                )
        self.write(
            {"state": "in_progress", "date_start": fields.Datetime.now()}
        )
        return True

    def action_complete(self):
        """Complete the fieldwork once every mandatory question is assessed.

        :raise UserError: when the audit is not in progress or when a
            mandatory question is still pending.
        """
        self._check_state(("in_progress",), _("Complete"))
        for audit in self:
            pending = audit.response_ids.filtered(
                lambda response: response.is_mandatory
                and response.result == "pending"
            )
            if pending:
                raise UserError(
                    _(
                        "Audit %(ref)s still has %(count)s mandatory "
                        "question(s) without assessment.",
                        ref=audit.reference,
                        count=len(pending),
                    )
                )
        self.write({"state": "completed", "date_end": fields.Datetime.now()})
        return True

    def action_follow_up(self):
        """Move a completed audit into the follow-up status.

        :raise UserError: when the audit is not completed or when no audit
            report has been issued.
        """
        self._check_state(("completed",), _("Follow-up"))
        for audit in self:
            issued = audit.report_ids.filtered(
                lambda report: report.state == "issued"
            )
            if not issued:
                raise UserError(
                    _(
                        "Audit %(ref)s cannot move to follow-up because no "
                        "audit report has been issued.",
                        ref=audit.reference,
                    )
                )
        self.write({"state": "follow_up"})
        return True

    def action_close(self):
        """Close the audit once every finding reached a final status.

        :raise UserError: when the audit is not in follow-up, when an issued
            report is missing, or when a finding is still open.
        """
        self._check_state(("follow_up",), _("Close"))
        for audit in self:
            if audit.open_finding_count:
                raise UserError(
                    _(
                        "Audit %(ref)s still has %(count)s open finding(s) "
                        "and cannot be closed.",
                        ref=audit.reference,
                        count=audit.open_finding_count,
                    )
                )
            issued = audit.report_ids.filtered(
                lambda report: report.state == "issued"
            )
            if not issued:
                raise UserError(
                    _(
                        "Audit %(ref)s cannot be closed because no audit "
                        "report has been issued.",
                        ref=audit.reference,
                    )
                )
        self.write(
            {
                "state": "closed",
                "closed_by_id": self.env.user.id,
                "closure_date": fields.Datetime.now(),
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

    def action_load_checklist(self):
        """Open the wizard loading an approved checklist into the audit.

        :return: an act window action opening the checklist load wizard.
        :rtype: dict
        """
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "ls.audit.checklist.load",
            "view_mode": "form",
            "target": "new",
            "context": {"default_audit_id": self.id},
        }

    def action_view_findings(self):
        """Open the findings raised during this audit.

        :return: an act window action listing the audit findings.
        :rtype: dict
        """
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Findings"),
            "res_model": "ls.audit.finding",
            "view_mode": "list,form",
            "domain": [("audit_id", "=", self.id)],
            "context": {
                "default_audit_id": self.id,
                "default_company_id": self.company_id.id,
            },
        }

    def action_view_reports(self):
        """Open the audit reports produced for this audit.

        :return: an act window action listing the audit reports.
        :rtype: dict
        """
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Audit Reports"),
            "res_model": "ls.audit.report",
            "view_mode": "list,form",
            "domain": [("audit_id", "=", self.id)],
            "context": {
                "default_audit_id": self.id,
                "default_company_id": self.company_id.id,
            },
        }

    # ------------------------------------------------------------------
    # Scheduled actions
    # ------------------------------------------------------------------

    @api.model
    def _cron_notify_overdue_audits(self):
        """Notify lead auditors of audits that passed their planned date.

        :return: the number of audits for which a notification was created.
        :rtype: int
        """
        today = fields.Date.context_today(self)
        overdue = self.search(
            [
                ("date_planned", "<", today),
                ("state", "in", ("planned", "scheduled")),
            ]
        )
        activity_type = self.env.ref(
            "mail.mail_activity_data_todo", raise_if_not_found=False
        )
        if not activity_type:
            return 0
        for audit in overdue:
            summary = _("Overdue audit %(ref)s", ref=audit.reference)
            existing = self.env["mail.activity"].search_count(
                [
                    ("res_model", "=", self._name),
                    ("res_id", "=", audit.id),
                    ("summary", "=", summary),
                ]
            )
            if existing:
                continue
            audit.activity_schedule(
                act_type_xmlid="mail.mail_activity_data_todo",
                summary=summary,
                note=_(
                    "The planned date of this audit has passed while the "
                    "audit has not been started."
                ),
                user_id=audit.lead_auditor_id.id,
            )
        return len(overdue)
