# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Supplier audit management, from planning to closure of findings."""
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

AUDIT_TYPE_SELECTION = [
    ("on_site", "On-Site Audit"),
    ("remote", "Remote Audit"),
    ("desktop", "Desktop Audit"),
    ("document_review", "Documentation Review"),
    ("surveillance", "Surveillance Audit"),
    ("for_cause", "For-Cause Audit"),
]

AUDIT_STATE_SELECTION = [
    ("draft", "Draft"),
    ("planned", "Planned"),
    ("in_progress", "In Progress"),
    ("report_draft", "Report Drafted"),
    ("report_issued", "Report Issued"),
    ("response_received", "Response Received"),
    ("closed", "Closed"),
    ("cancelled", "Cancelled"),
]

AUDIT_OUTCOME_SELECTION = [
    ("acceptable", "Acceptable"),
    ("acceptable_with_actions", "Acceptable with Actions"),
    ("not_acceptable", "Not Acceptable"),
]

FINDING_SEVERITY_SELECTION = [
    ("critical", "Critical"),
    ("major", "Major"),
    ("minor", "Minor"),
    ("observation", "Observation"),
]

FINDING_STATE_SELECTION = [
    ("open", "Open"),
    ("response_received", "Response Received"),
    ("action_agreed", "Action Agreed"),
    ("implemented", "Implemented"),
    ("verified", "Verified"),
    ("closed", "Closed"),
    ("cancelled", "Cancelled"),
]


class LsSupplierAudit(models.Model):
    """An audit of a supplier, with its findings and their follow-up."""

    _name = "ls.supplier.audit"
    _description = "Life Sciences Supplier Audit"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "planned_date desc, id desc"
    _check_company_auto = True

    name = fields.Char(
        required=True,
        readonly=True,
        copy=False,
        default="/",
        index=True,
    )
    qualification_id = fields.Many2one(
        comodel_name="ls.supplier.qualification",
        required=True,
        ondelete="cascade",
        index=True,
        tracking=True,
    )
    partner_id = fields.Many2one(
        related="qualification_id.partner_id",
        store=True,
        index=True,
    )
    company_id = fields.Many2one(
        related="qualification_id.company_id",
        store=True,
        index=True,
    )
    audit_type = fields.Selection(
        selection=AUDIT_TYPE_SELECTION,
        required=True,
        default="on_site",
        tracking=True,
    )
    audit_scope = fields.Text(
        required=True,
        help="Processes, sites, products and periods covered by the audit.",
    )
    standard_ids = fields.Many2many(
        comodel_name="ls.supplier.standard",
        relation="ls_supplier_audit_standard_rel",
        column1="audit_id",
        column2="standard_id",
        string="Audit Basis",
        help="Frameworks used as the basis of the audit. The module records "
             "the designation only.",
    )
    planned_date = fields.Date(required=True, tracking=True, index=True)
    date_start = fields.Date(tracking=True)
    date_stop = fields.Date(tracking=True)
    lead_auditor_id = fields.Many2one(
        comodel_name="res.users",
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
        domain=[("share", "=", False)],
    )
    auditor_ids = fields.Many2many(
        comodel_name="res.users",
        relation="ls_supplier_audit_auditor_rel",
        column1="audit_id",
        column2="user_id",
        string="Audit Team",
        domain=[("share", "=", False)],
    )
    auditee_contact_id = fields.Many2one(
        comodel_name="res.partner",
        string="Supplier Contact",
        help="Person of the supplier who receives the audit report.",
    )
    finding_ids = fields.One2many(
        comodel_name="ls.supplier.audit.finding",
        inverse_name="audit_id",
        string="Findings",
        copy=False,
    )
    state = fields.Selection(
        selection=AUDIT_STATE_SELECTION,
        required=True,
        default="draft",
        tracking=True,
        index=True,
        copy=False,
    )
    outcome = fields.Selection(
        selection=AUDIT_OUTCOME_SELECTION,
        tracking=True,
        copy=False,
    )
    conclusion = fields.Text(tracking=True)
    report_date = fields.Date(readonly=True, copy=False, tracking=True)
    response_due_date = fields.Date(copy=False, tracking=True)
    response_received_date = fields.Date(readonly=True, copy=False)

    critical_count = fields.Integer(compute="_compute_finding_counts", store=True)
    major_count = fields.Integer(compute="_compute_finding_counts", store=True)
    minor_count = fields.Integer(compute="_compute_finding_counts", store=True)
    observation_count = fields.Integer(
        compute="_compute_finding_counts", store=True
    )
    open_finding_count = fields.Integer(
        compute="_compute_finding_counts", store=True
    )
    finding_count = fields.Integer(compute="_compute_finding_counts", store=True)

    _name_company_uniq = models.Constraint(
        "UNIQUE(name, company_id)",
        "The audit reference must be unique per company.",
    )

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------
    @api.depends("finding_ids.severity", "finding_ids.state")
    def _compute_finding_counts(self):
        """Count findings by severity and count the ones still open."""
        for record in self:
            findings = record.finding_ids.filtered(
                lambda finding: finding.state != "cancelled"
            )
            record.finding_count = len(findings)
            record.critical_count = len(
                findings.filtered(lambda f: f.severity == "critical")
            )
            record.major_count = len(
                findings.filtered(lambda f: f.severity == "major")
            )
            record.minor_count = len(
                findings.filtered(lambda f: f.severity == "minor")
            )
            record.observation_count = len(
                findings.filtered(lambda f: f.severity == "observation")
            )
            record.open_finding_count = len(
                findings.filtered(lambda f: f.state != "closed")
            )

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("date_start", "date_stop", "planned_date")
    def _check_dates(self):
        """Validate the chronology of the audit dates."""
        for record in self:
            if (
                record.date_start
                and record.date_stop
                and record.date_stop < record.date_start
            ):
                raise ValidationError(
                    _("Audit %s: the end date cannot precede the start date.",
                      record.name)
                )

    @api.constrains("report_date", "response_due_date", "response_received_date")
    def _check_report_dates(self):
        """Validate the chronology of the reporting dates."""
        for record in self:
            if (
                record.report_date
                and record.response_due_date
                and record.response_due_date < record.report_date
            ):
                raise ValidationError(
                    _("Audit %s: the response due date cannot precede the "
                      "report date.", record.name)
                )
            if (
                record.report_date
                and record.response_received_date
                and record.response_received_date < record.report_date
            ):
                raise ValidationError(
                    _("Audit %s: the response cannot be received before the "
                      "report is issued.", record.name)
                )

    @api.constrains("outcome", "critical_count", "state")
    def _check_outcome_consistency(self):
        """An audit with open critical findings cannot be 'Acceptable'."""
        for record in self:
            if (
                record.outcome == "acceptable"
                and record.critical_count
            ):
                raise ValidationError(
                    _("Audit %s reports %s critical finding(s) and therefore "
                      "cannot conclude 'Acceptable'.",
                      record.name, record.critical_count)
                )

    # ------------------------------------------------------------------
    # ORM overrides
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Assign the audit reference from the company sequence."""
        for vals in vals_list:
            if vals.get("name", "/") == "/":
                qualification = self.env["ls.supplier.qualification"].browse(
                    vals.get("qualification_id")
                )
                company_id = qualification.company_id.id or self.env.company.id
                vals["name"] = self.env["ir.sequence"].with_company(
                    company_id
                ).next_by_code("ls.supplier.audit") or "/"
        return super().create(vals_list)

    def copy(self, default=None):
        """Duplicate an audit as a draft without report or findings."""
        self.ensure_one()
        default = dict(default or {})
        default.update({
            "name": "/",
            "state": "draft",
            "outcome": False,
            "report_date": False,
            "response_due_date": False,
            "response_received_date": False,
        })
        return super().copy(default)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_supplier_audit(self):
        """Only draft or cancelled audits may be deleted."""
        for record in self:
            if record.state not in ("draft", "cancelled"):
                raise UserError(
                    _("Audit %s cannot be deleted once it has been planned. "
                      "Cancel it instead.", record.name)
                )

    # ------------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------------
    def action_plan(self):
        """Confirm the audit planning."""
        for record in self:
            if record.state != "draft":
                raise UserError(
                    _("Only a draft audit can be planned (audit %s).",
                      record.name)
                )
            record.state = "planned"
            record.message_post(body=_(
                "Audit planned on %s.", record.planned_date
            ))
            record.activity_schedule(
                "mail.mail_activity_data_todo",
                date_deadline=record.planned_date,
                summary=_("Conduct supplier audit %s", record.name),
                user_id=record.lead_auditor_id.id,
            )
        return True

    def action_start(self):
        """Start the audit execution."""
        for record in self:
            if record.state != "planned":
                raise UserError(
                    _("Only a planned audit can be started (audit %s).",
                      record.name)
                )
            record.write({
                "state": "in_progress",
                "date_start": (
                    record.date_start or fields.Date.context_today(record)
                ),
            })
            record.message_post(body=_("Audit started."))
        return True

    def action_draft_report(self):
        """Move the audit to the report drafting stage."""
        for record in self:
            if record.state != "in_progress":
                raise UserError(
                    _("Only an audit in progress can move to report drafting "
                      "(audit %s).", record.name)
                )
            record.write({
                "state": "report_draft",
                "date_stop": (
                    record.date_stop or fields.Date.context_today(record)
                ),
            })
            record.message_post(body=_("Audit report drafting started."))
        return True

    def action_issue_report(self):
        """Issue the audit report and start the response clock."""
        for record in self:
            if record.state != "report_draft":
                raise UserError(
                    _("Only a drafted report can be issued (audit %s).",
                      record.name)
                )
            if not record.outcome:
                raise UserError(
                    _("Audit %s: the outcome must be set before issuing the "
                      "report.", record.name)
                )
            if not (record.conclusion or "").strip():
                raise UserError(
                    _("Audit %s: a written conclusion is required before "
                      "issuing the report.", record.name)
                )
            report_date = fields.Date.context_today(record)
            record.write({
                "state": "report_issued",
                "report_date": report_date,
                "response_due_date": (
                    record.response_due_date
                    or report_date + relativedelta(
                        days=record.company_id.ls_audit_response_days
                    )
                ),
            })
            record.message_post(body=_(
                "Audit report issued. Outcome: %s.",
                dict(AUDIT_OUTCOME_SELECTION).get(record.outcome, ""),
            ))
            self.env["ls.supplier.signature"].sign(
                record=record,
                meaning="authored",
                reason=_("Audit report issued by the lead auditor."),
                payload={
                    "outcome": record.outcome,
                    "critical_count": record.critical_count,
                    "major_count": record.major_count,
                    "minor_count": record.minor_count,
                },
            )
            template = self.env.ref(
                "ls_supplier_qualification.mail_template_audit_report_issued",
                raise_if_not_found=False,
            )
            if template and record.auditee_contact_id.email:
                template.send_mail(record.id, force_send=False)
        return True

    def action_register_response(self):
        """Record that the supplier response has been received."""
        for record in self:
            if record.state != "report_issued":
                raise UserError(
                    _("Only an issued report can receive a response "
                      "(audit %s).", record.name)
                )
            record.write({
                "state": "response_received",
                "response_received_date": fields.Date.context_today(record),
            })
            record.message_post(body=_("Supplier response received."))
        return True

    def action_close(self):
        """Close the audit once every finding is closed."""
        for record in self:
            if record.state not in ("report_issued", "response_received"):
                raise UserError(
                    _("Only an issued or answered audit can be closed "
                      "(audit %s).", record.name)
                )
            if record.open_finding_count:
                raise UserError(
                    _("Audit %s still has %s open finding(s) and cannot be "
                      "closed.", record.name, record.open_finding_count)
                )
            record.state = "closed"
            record.message_post(body=_("Audit closed."))
            self.env["ls.supplier.signature"].sign(
                record=record,
                meaning="verified",
                reason=_("Audit closed after verification of all findings."),
                payload={
                    "outcome": record.outcome,
                    "finding_count": record.finding_count,
                },
            )
        return True

    def action_cancel(self):
        """Cancel an audit that will not be conducted."""
        for record in self:
            if record.state == "closed":
                raise UserError(
                    _("A closed audit cannot be cancelled (audit %s).",
                      record.name)
                )
            record.state = "cancelled"
            record.message_post(body=_("Audit cancelled."))
        return True

    def action_reset_to_draft(self):
        """Return a cancelled audit to draft."""
        for record in self:
            if record.state != "cancelled":
                raise UserError(
                    _("Only a cancelled audit can be reset to draft "
                      "(audit %s).", record.name)
                )
            record.state = "draft"
            record.message_post(body=_("Audit reset to draft."))
        return True

    def action_view_findings(self):
        """Open the findings of this audit."""
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "ls_supplier_qualification.action_ls_supplier_audit_finding"
        )
        action["domain"] = [("audit_id", "=", self.id)]
        action["context"] = {"default_audit_id": self.id}
        return action

    def _get_report_base_filename(self):
        """Return the file name proposed when printing the audit report."""
        self.ensure_one()
        return "%s - %s" % (self.name, self.partner_id.display_name)


class LsSupplierAuditFinding(models.Model):
    """One finding raised during a supplier audit."""

    _name = "ls.supplier.audit.finding"
    _description = "Life Sciences Supplier Audit Finding"
    _inherit = ["mail.thread"]
    _order = "audit_id, severity, sequence, id"
    _check_company_auto = True

    name = fields.Char(
        string="Reference",
        required=True,
        help="Reference of the finding inside the audit report.",
    )
    sequence = fields.Integer(default=10)
    audit_id = fields.Many2one(
        comodel_name="ls.supplier.audit",
        required=True,
        ondelete="cascade",
        index=True,
    )
    qualification_id = fields.Many2one(
        related="audit_id.qualification_id",
        store=True,
        index=True,
    )
    partner_id = fields.Many2one(
        related="audit_id.partner_id",
        store=True,
        index=True,
    )
    company_id = fields.Many2one(
        related="audit_id.company_id",
        store=True,
        index=True,
    )
    severity = fields.Selection(
        selection=FINDING_SEVERITY_SELECTION,
        required=True,
        default="minor",
        tracking=True,
        index=True,
    )
    description = fields.Text(required=True)
    requirement_reference = fields.Char(
        help="Reference of the requirement the finding relates to, as written "
             "by the auditor.",
    )
    supplier_response = fields.Text()
    root_cause = fields.Text()
    corrective_action = fields.Text()
    action_due_date = fields.Date(tracking=True)
    implementation_date = fields.Date()
    verification_method = fields.Text()
    verified_by_id = fields.Many2one(
        comodel_name="res.users",
        readonly=True,
        copy=False,
        domain=[("share", "=", False)],
    )
    closure_date = fields.Date(readonly=True, copy=False, tracking=True)
    closure_comment = fields.Text()
    state = fields.Selection(
        selection=FINDING_STATE_SELECTION,
        required=True,
        default="open",
        tracking=True,
        index=True,
        copy=False,
    )

    _name_audit_uniq = models.Constraint(
        "UNIQUE(audit_id, name)",
        "The finding reference must be unique inside an audit.",
    )

    @api.constrains("action_due_date", "implementation_date", "closure_date")
    def _check_dates(self):
        """Validate the chronology of the follow-up dates."""
        for record in self:
            report_date = record.audit_id.report_date
            if (
                report_date
                and record.closure_date
                and record.closure_date < report_date
            ):
                raise ValidationError(
                    _("Finding %s cannot be closed before the audit report is "
                      "issued.", record.name)
                )
            if (
                record.implementation_date
                and record.closure_date
                and record.closure_date < record.implementation_date
            ):
                raise ValidationError(
                    _("Finding %s: the closure date cannot precede the "
                      "implementation date.", record.name)
                )

    @api.constrains("state", "severity", "corrective_action")
    def _check_corrective_action(self):
        """Critical and major findings require a documented action."""
        for record in self:
            if record.state in ("open", "response_received", "cancelled"):
                continue
            if record.severity in ("critical", "major") and not (
                record.corrective_action or ""
            ).strip():
                raise ValidationError(
                    _("Finding %s is %s: a corrective action must be "
                      "documented.",
                      record.name,
                      dict(FINDING_SEVERITY_SELECTION).get(record.severity))
                )

    def action_register_response(self):
        """Record the supplier response to the finding."""
        for record in self:
            if record.state != "open":
                raise UserError(
                    _("Only an open finding can register a response "
                      "(finding %s).", record.name)
                )
            if not (record.supplier_response or "").strip():
                raise UserError(
                    _("Finding %s: enter the supplier response first.",
                      record.name)
                )
            record.state = "response_received"
            record.message_post(body=_("Supplier response registered."))
        return True

    def action_agree_action(self):
        """Accept the corrective action proposed by the supplier."""
        for record in self:
            if record.state != "response_received":
                raise UserError(
                    _("Only a finding with a response can have its action "
                      "agreed (finding %s).", record.name)
                )
            if not (record.corrective_action or "").strip():
                raise UserError(
                    _("Finding %s: document the agreed corrective action.",
                      record.name)
                )
            if not record.action_due_date:
                raise UserError(
                    _("Finding %s: set the due date of the corrective action.",
                      record.name)
                )
            record.state = "action_agreed"
            record.message_post(body=_("Corrective action agreed."))
        return True

    def action_mark_implemented(self):
        """Record that the supplier implemented the corrective action."""
        for record in self:
            if record.state != "action_agreed":
                raise UserError(
                    _("Only a finding with an agreed action can be marked "
                      "implemented (finding %s).", record.name)
                )
            record.write({
                "state": "implemented",
                "implementation_date": (
                    record.implementation_date
                    or fields.Date.context_today(record)
                ),
            })
            record.message_post(body=_("Corrective action implemented."))
        return True

    def action_verify(self):
        """Record the effectiveness verification of the corrective action."""
        for record in self:
            if record.state != "implemented":
                raise UserError(
                    _("Only an implemented action can be verified "
                      "(finding %s).", record.name)
                )
            if not (record.verification_method or "").strip():
                raise UserError(
                    _("Finding %s: describe how the action was verified.",
                      record.name)
                )
            record.write({
                "state": "verified",
                "verified_by_id": self.env.user.id,
            })
            record.message_post(body=_("Corrective action verified."))
        return True

    def action_close(self):
        """Close a verified finding."""
        for record in self:
            if record.state != "verified":
                raise UserError(
                    _("Only a verified finding can be closed (finding %s).",
                      record.name)
                )
            record.write({
                "state": "closed",
                "closure_date": fields.Date.context_today(record),
            })
            record.message_post(body=_("Finding closed."))
            self.env["ls.supplier.signature"].sign(
                record=record,
                meaning="verified",
                reason=_("Audit finding closed."),
                payload={
                    "severity": record.severity,
                    "closure_date": record.closure_date,
                },
            )
        return True

    def action_cancel(self):
        """Cancel a finding raised in error."""
        for record in self:
            if record.state == "closed":
                raise UserError(
                    _("A closed finding cannot be cancelled (finding %s).",
                      record.name)
                )
            record.state = "cancelled"
            record.message_post(body=_("Finding cancelled."))
        return True
