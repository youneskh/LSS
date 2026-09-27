# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Adverse event recorded in the context of a complaint.

No reporting deadline is hard-coded by this module. The number of calendar
days available to submit a report to a competent authority is read from
``ls.complaint.category.ae_reporting_deadline_days`` and must be configured by
the Regulatory Affairs function. See ``docs/02_regulatory_analysis.md``.
"""

import logging
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

REPORT_DUE_ACTIVITY_SUMMARY = "Adverse event report due"


class LsComplaintAdverseEvent(models.Model):
    """Adverse event, incident or reaction associated with a complaint."""

    _name = "ls.complaint.adverse_event"
    _description = "Complaint Adverse Event"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "awareness_date desc, id desc"
    _check_company_auto = True

    name = fields.Char(
        string="Reference",
        required=True,
        readonly=True,
        copy=False,
        index=True,
        default=lambda self: _("New"),
    )
    complaint_id = fields.Many2one(comodel_name="ls.complaint", required=True,
                                   ondelete="cascade",
                                   index=True,
                                   check_company=True,)
    company_id = fields.Many2one(comodel_name="res.company", related="complaint_id.company_id",
                                 store=True,
                                 index=True,
                                 readonly=True,)
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("assessed", "Assessed"),
            ("submitted", "Submitted"),
            ("closed", "Closed"),
        ],
        default="draft",
        required=True,
        copy=False,
        index=True,
        tracking=True,
    )

    # ------------------------------------------------------------------
    # Event data
    # ------------------------------------------------------------------
    event_date = fields.Date(help="Date on which the event occurred, when known.",)
    awareness_date = fields.Date(required=True,
                                 default=fields.Date.context_today,
                                 tracking=True,
                                 help="Date on which the organisation became aware of the event. "
                                 "Reporting deadlines are counted from this date.",)
    event_description = fields.Text(required=True)
    seriousness = fields.Selection(
        selection=[
            ("serious", "Serious"),
            ("non_serious", "Non Serious"),
            ("undetermined", "Undetermined"),
        ],
        default="undetermined",
        required=True,
        tracking=True,
    )
    seriousness_criteria = fields.Text(
        help="Criteria applied to qualify the seriousness of the event, "
        "referencing the organisation's procedure.",
    )
    outcome = fields.Selection(
        selection=[
            ("recovered", "Recovered"),
            ("recovering", "Recovering"),
            ("not_recovered", "Not Recovered"),
            ("sequelae", "Recovered With Sequelae"),
            ("fatal", "Fatal"),
            ("unknown", "Unknown"),
        ],
        default="unknown",
        required=True,
        tracking=True,
    )
    causality_assessment = fields.Selection(
        selection=[
            ("certain", "Certain"),
            ("probable", "Probable"),
            ("possible", "Possible"),
            ("unlikely", "Unlikely"),
            ("unrelated", "Unrelated"),
            ("not_assessable", "Not Assessable"),
        ],
        tracking=True,
    )
    causality_rationale = fields.Text()

    # ------------------------------------------------------------------
    # Subject data (pseudonymised)
    # ------------------------------------------------------------------
    patient_reference = fields.Char(
        string="Subject Pseudonym",
        help="Pseudonymised identifier only. Do not record directly "
        "identifying personal data in this field.",
    )
    patient_age_range = fields.Selection(
        selection=[
            ("neonate", "Neonate"),
            ("infant", "Infant"),
            ("child", "Child"),
            ("adolescent", "Adolescent"),
            ("adult", "Adult"),
            ("elderly", "Elderly"),
            ("unknown", "Unknown"),
        ],
        default="unknown",
    )
    patient_sex = fields.Selection(
        selection=[
            ("female", "Female"),
            ("male", "Male"),
            ("other", "Other"),
            ("not_disclosed", "Not Disclosed"),
        ],
        default="not_disclosed",
    )

    # ------------------------------------------------------------------
    # Reportability and submission
    # ------------------------------------------------------------------
    reportable = fields.Boolean(
        string="Reportable to Authority",
        copy=False,
        tracking=True,
    )
    reportability_rationale = fields.Text(
        help="Documented rationale supporting the reportability decision, "
        "including the regulation and the article applied.",
    )
    authority_id = fields.Many2one(
        comodel_name="res.partner",
        string="Competent Authority",
    )
    report_due_date = fields.Date(
        compute="_compute_report_due_date",
        store=True,
        help="Awareness date plus the reporting deadline configured on the "
        "complaint category. Empty when no deadline is configured.",
    )
    report_submitted_date = fields.Date(readonly=True, copy=False)
    report_reference = fields.Char(
        string="Authority Acknowledgement Reference",
        copy=False,
    )
    submitted_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                      copy=False,)
    follow_up_required = fields.Boolean(tracking=True)
    follow_up_notes = fields.Text()
    closure_notes = fields.Text(copy=False)
    is_report_overdue = fields.Boolean(
        compute="_compute_is_report_overdue",
        search="_search_is_report_overdue",
    )

    _name_company_uniq = models.Constraint(
        "UNIQUE(name, company_id)",
        "The adverse event reference must be unique per company.",
    )

    # ------------------------------------------------------------------
    # Compute methods
    # ------------------------------------------------------------------
    @api.depends("name", "complaint_id.name")
    def _compute_display_name(self):
        """Prefix the adverse event reference with the complaint reference."""
        for record in self:
            record.display_name = f"{record.complaint_id.name} / {record.name}"

    @api.depends(
        "awareness_date",
        "reportable",
        "complaint_id.category_id.ae_reporting_deadline_days",
    )
    def _compute_report_due_date(self):
        """Derive the submission deadline from the configured category value."""
        for record in self:
            deadline_days = (
                record.complaint_id.category_id.ae_reporting_deadline_days or 0
            )
            if record.reportable and record.awareness_date and deadline_days:
                record.report_due_date = record.awareness_date + timedelta(
                    days=deadline_days
                )
            else:
                record.report_due_date = False

    def _compute_is_report_overdue(self):
        """Flag reportable events whose configured deadline has passed."""
        today = fields.Date.context_today(self)
        for record in self:
            record.is_report_overdue = bool(
                record.reportable
                and record.state in ("draft", "assessed")
                and record.report_due_date
                and record.report_due_date < today
            )

    @api.model
    def _search_is_report_overdue(self, operator, value):
        """Search implementation for the non-stored overdue flag."""
        if operator not in ("=", "!="):
            raise UserError(
                _("This filter only supports the '=' and '!=' operators.")
            )
        overdue_domain = [
            ("reportable", "=", True),
            ("state", "in", ["draft", "assessed"]),
            ("report_due_date", "!=", False),
            ("report_due_date", "<", fields.Date.context_today(self)),
        ]
        positive = (operator == "=") == bool(value)
        if positive:
            return overdue_domain
        return ["!"] + overdue_domain

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("event_date", "awareness_date")
    def _check_dates(self):
        """Awareness cannot precede the event, nor be in the future."""
        today = fields.Date.context_today(self)
        for record in self:
            if record.awareness_date and record.awareness_date > today:
                raise ValidationError(
                    _(
                        "Adverse event %(name)s: the awareness date cannot be in "
                        "the future.",
                        name=record.name,
                    )
                )
            if (
                record.event_date
                and record.awareness_date
                and record.event_date > record.awareness_date
            ):
                raise ValidationError(
                    _(
                        "Adverse event %(name)s: the event date cannot be later "
                        "than the awareness date.",
                        name=record.name,
                    )
                )

    @api.constrains("reportable", "reportability_rationale", "state")
    def _check_reportability_rationale(self):
        """Any reportability decision must be justified once assessed."""
        for record in self:
            if record.state != "draft" and not record.reportability_rationale:
                raise ValidationError(
                    _(
                        "Adverse event %(name)s: the reportability rationale is "
                        "mandatory once the event is assessed.",
                        name=record.name,
                    )
                )

    # ------------------------------------------------------------------
    # ORM overrides
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Assign the adverse event reference from the company sequence."""
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == _("New"):
                complaint = self.env["ls.complaint"].browse(vals.get("complaint_id"))
                company_id = complaint.company_id.id or self.env.company.id
                sequence = self.env["ir.sequence"].with_company(company_id)
                vals["name"] = (
                    sequence.next_by_code("ls.complaint.adverse_event") or _("New")
                )
        return super().create(vals_list)

    def write(self, vals):
        """Freeze closed adverse events."""
        tracked = {
            "state",
            "message_follower_ids",
            "message_ids",
            "activity_ids",
        }
        if set(vals) - tracked:
            frozen = self.filtered(lambda record: record.state == "closed")
            if frozen:
                raise UserError(
                    _(
                        "Adverse events %(names)s are closed and can no longer be "
                        "modified.",
                        names=", ".join(frozen.mapped("name")),
                    )
                )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_assessed(self):
        """Forbid deletion once an adverse event left the draft state."""
        assessed = self.filtered(lambda record: record.state != "draft")
        if assessed:
            raise UserError(
                _(
                    "Adverse events %(names)s cannot be deleted because they are "
                    "no longer in draft.",
                    names=", ".join(assessed.mapped("name")),
                )
            )

    # ------------------------------------------------------------------
    # State machine
    # ------------------------------------------------------------------
    def _ensure_state(self, allowed_states, action_label):
        """Raise when a record is not in one of ``allowed_states``.

        :param tuple allowed_states: technical state values allowed
        :param str action_label: human readable action used in the message
        :raises UserError: when at least one record is in a wrong state
        """
        wrong = self.filtered(lambda record: record.state not in allowed_states)
        if wrong:
            raise UserError(
                _(
                    "Action '%(action)s' is not allowed for adverse events "
                    "%(names)s in their current status.",
                    action=action_label,
                    names=", ".join(wrong.mapped("name")),
                )
            )

    def action_assess(self):
        """Record the reportability decision and move to Assessed."""
        self._ensure_state(("draft",), _("Assess"))
        for record in self:
            if not record.reportability_rationale:
                raise UserError(
                    _(
                        "Adverse event %(name)s: the reportability rationale is "
                        "mandatory.",
                        name=record.name,
                    )
                )
            if not record.causality_assessment:
                raise UserError(
                    _(
                        "Adverse event %(name)s: the causality assessment is "
                        "mandatory.",
                        name=record.name,
                    )
                )
            if record.reportable and not record.authority_id:
                raise UserError(
                    _(
                        "Adverse event %(name)s: the competent authority must be "
                        "identified for a reportable event.",
                        name=record.name,
                    )
                )
        self.write({"state": "assessed"})
        for record in self:
            record.message_post(
                body=_(
                    "Adverse event assessed. Reportable: %(reportable)s",
                    reportable=_("Yes") if record.reportable else _("No"),
                )
            )
        return True

    def action_submit(self):
        """Record the submission of the report to the competent authority."""
        self._ensure_state(("assessed",), _("Record Submission"))
        for record in self:
            if not record.reportable:
                raise UserError(
                    _(
                        "Adverse event %(name)s is not reportable, no submission "
                        "can be recorded.",
                        name=record.name,
                    )
                )
            if not record.report_reference:
                raise UserError(
                    _(
                        "Adverse event %(name)s: the authority acknowledgement "
                        "reference is mandatory.",
                        name=record.name,
                    )
                )
        self.write(
            {
                "state": "submitted",
                "report_submitted_date": fields.Date.context_today(self),
                "submitted_by_id": self.env.user.id,
            }
        )
        for record in self:
            record.activity_unlink(["mail.mail_activity_data_todo"])
            record.message_post(body=_("Report submitted to the competent authority."))
        return True

    def action_close(self):
        """Close the adverse event once every obligation is discharged."""
        self._ensure_state(("assessed", "submitted"), _("Close"))
        for record in self:
            if record.reportable and record.state != "submitted":
                raise UserError(
                    _(
                        "Adverse event %(name)s is reportable and cannot be closed "
                        "before the submission is recorded.",
                        name=record.name,
                    )
                )
            if record.follow_up_required and not record.follow_up_notes:
                raise UserError(
                    _(
                        "Adverse event %(name)s: follow-up notes are mandatory "
                        "when a follow-up is required.",
                        name=record.name,
                    )
                )
        self.write({"state": "closed"})
        for record in self:
            record.activity_unlink(["mail.mail_activity_data_todo"])
            record.message_post(body=_("Adverse event closed."))
        return True

    # ------------------------------------------------------------------
    # Scheduled actions
    # ------------------------------------------------------------------
    @api.model
    def _cron_notify_due_adverse_event_reports(self, limit=200):
        """Schedule an activity on reportable events whose deadline passed.

        :param int limit: maximum number of events processed per run
        :return: number of activities created
        """
        today = fields.Date.context_today(self)
        events = self.search(
            [
                ("reportable", "=", True),
                ("state", "in", ["draft", "assessed"]),
                ("report_due_date", "!=", False),
                ("report_due_date", "<=", today),
            ],
            limit=limit,
        )
        created = 0
        for event in events:
            existing = event.activity_ids.filtered(
                lambda activity: activity.summary == REPORT_DUE_ACTIVITY_SUMMARY
            )
            if existing:
                continue
            responsible = event.complaint_id.owner_id or event.create_uid
            event.activity_schedule(
                act_type_xmlid="mail.mail_activity_data_todo",
                summary=REPORT_DUE_ACTIVITY_SUMMARY,
                note=_(
                    "The configured reporting deadline (%(due)s) is reached.",
                    due=event.report_due_date,
                ),
                user_id=responsible.id,
            )
            created += 1
        _logger.info(
            "ls_complaint: %s adverse event reporting activities created", created
        )
        return created
