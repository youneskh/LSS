# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Quality records: evidence retained by the quality management system."""

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

#: Quality record lifecycle states.
RECORD_STATES = [
    ("draft", "Draft"),
    ("confirmed", "Confirmed"),
    ("archived", "Archived"),
    ("disposed", "Disposed"),
]

#: States in which a record is evidence and is protected from modification.
LOCKED_RECORD_STATES = ("confirmed", "archived", "disposed")

#: Default retention period applied when no system parameter is configured.
DEFAULT_RETENTION_PERIOD_MONTHS = 60


class LsQmsQualityRecord(models.Model):
    """Retained evidence produced by a quality management system activity."""

    _name = "ls.qms.quality_record"
    _description = "Quality Record"
    _check_company_auto = True
    _inherit = ["mail.thread", "mail.activity.mixin", "ls.qms.parameter.mixin"]
    _order = "date_record desc, reference"

    _reference_uniq = models.Constraint(
        "UNIQUE (reference, company_id)",
        "The reference of a quality record must be unique per company.",
    )
    _retention_positive = models.Constraint(
        "CHECK (retention_period_months >= 0)",
        "The retention period of a quality record cannot be negative.",
    )

    name = fields.Char(string="Subject", required=True, tracking=True)
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
    record_type = fields.Selection(
        selection=[
            ("management_review", "Management Review"),
            ("quality_meeting", "Quality Meeting Minutes"),
            ("process_verification", "Process Verification Record"),
            ("document_review", "Document Review Record"),
            ("objective_review", "Quality Objective Review"),
            ("customer_feedback", "Customer Feedback Record"),
            ("internal_communication", "Internal Quality Communication"),
            ("qms_change_evaluation", "QMS Change Evaluation"),
        ],
        required=True,
        index=True,
        tracking=True,
        help="Nature of the evidence. Extending modules add their own types"
        " with the selection_add attribute.",
    )
    state = fields.Selection(
        selection=RECORD_STATES,
        required=True,
        readonly=True,
        copy=False,
        default="draft",
        index=True,
        tracking=True,
    )
    date_record = fields.Date(
        string="Record Date",
        required=True,
        default=fields.Date.context_today,
        tracking=True,
        help="Date on which the recorded activity took place.",
    )
    author_id = fields.Many2one(
        comodel_name="res.users",
        string="Recorded By",
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
    )
    department_id = fields.Many2one(comodel_name="hr.department")
    description = fields.Text(help="Facts observed and data collected.",)
    conclusion = fields.Text(help="Outcome, decisions taken and actions requested.",)
    policy_id = fields.Many2one(
        comodel_name="ls.qms.policy",
        string="Related Policy",
        check_company=True,
    )
    sop_id = fields.Many2one(
        comodel_name="ls.qms.sop",
        string="Related Procedure",
        check_company=True,
    )
    quality_plan_id = fields.Many2one(
        comodel_name="ls.qms.quality_plan",
        string="Related Quality Plan",
        check_company=True,
    )
    objective_id = fields.Many2one(
        comodel_name="ls.qms.objective",
        string="Related Objective",
        check_company=True,
    )
    retention_period_months = fields.Integer(
        string="Retention Period (Months)",
        required=True,
        default=lambda self: self._default_retention_period_months(),
    )
    date_retention_until = fields.Date(
        string="Retain Until",
        compute="_compute_date_retention_until",
        store=True,
        readonly=False,
        help="Computed as Record Date + Retention Period. It can be "
        "overridden when a specific retention requirement applies.",
    )
    retention_expired = fields.Boolean(compute="_compute_retention_expired",)
    attachment_count = fields.Integer(compute="_compute_attachment_count")

    @api.model
    def _default_retention_period_months(self):
        """Return the configured default retention period, in months."""
        return self._get_int_parameter(
            "ls_qms.default_retention_period_months",
            DEFAULT_RETENTION_PERIOD_MONTHS,
        )

    @api.depends("date_record", "retention_period_months")
    def _compute_date_retention_until(self):
        """Derive the retention limit from the record date."""
        for record in self:
            if record.date_record and record.retention_period_months > 0:
                record.date_retention_until = (
                    record.date_record
                    + relativedelta(months=record.retention_period_months)
                )
            else:
                record.date_retention_until = False

    @api.depends("date_retention_until", "state")
    def _compute_retention_expired(self):
        """Flag records whose retention period has elapsed."""
        today = fields.Date.context_today(self)
        for record in self:
            record.retention_expired = bool(
                record.date_retention_until
                and record.state in ("confirmed", "archived")
                and record.date_retention_until < today
            )

    def _compute_attachment_count(self):
        """Count the ``ir.attachment`` records linked to each record."""
        if not self.ids:
            for record in self:
                record.attachment_count = 0
            return
        grouped = self.env["ir.attachment"]._read_group(
            domain=[("res_model", "=", self._name), ("res_id", "in", self.ids)],
            groupby=["res_id"],
            aggregates=["__count"],
        )
        counts = dict(grouped)
        for record in self:
            record.attachment_count = counts.get(record.id, 0)

    @api.depends("reference", "name")
    def _compute_display_name(self):
        """Render quality records as ``[REFERENCE] Subject``."""
        for record in self:
            record.display_name = "[%s] %s" % (
                record.reference or "/",
                record.name or "",
            )

    def _ls_qms_content_fields(self):
        """Return the fields protected once the record is confirmed.

        :rtype: list
        """
        return [
            "name",
            "record_type",
            "date_record",
            "author_id",
            "department_id",
            "description",
            "conclusion",
            "policy_id",
            "sop_id",
            "quality_plan_id",
            "objective_id",
            "retention_period_months",
        ]

    @api.model_create_multi
    def create(self, vals_list):
        """Allocate the record reference from the numbering sequence."""
        for vals in vals_list:
            if not vals.get("reference") or vals["reference"] == "/":
                reference = self.env["ir.sequence"].next_by_code(
                    "ls.qms.quality_record"
                )
                if not reference:
                    raise UserError(
                        _(
                            "The numbering sequence ls.qms.quality_record is "
                            "missing. Update the Life Sciences QMS module to "
                            "restore it."
                        )
                    )
                vals["reference"] = reference
        return super().create(vals_list)

    def write(self, vals):
        """Restrict correction of confirmed records to QMS managers.

        Confirmed records are evidence. They remain correctable by a QMS
        manager so that documented corrections stay possible, and every
        correction is written to the message log by the tracking mechanism.
        """
        protected_fields = set(self._ls_qms_content_fields())
        if protected_fields.intersection(vals):
            locked = self.filtered(
                lambda rec: rec.state in LOCKED_RECORD_STATES
            )
            if locked and not self.env.user.has_group(
                "ls_qms.group_ls_qms_manager"
            ):
                raise UserError(
                    _(
                        "Quality records %(references)s are confirmed. Only "
                        "a QMS manager may correct them, and the correction "
                        "is logged.",
                        references=", ".join(locked.mapped("reference")),
                    )
                )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_qms_quality_record(self):
        """Allow deletion of draft records only."""
        undeletable = self.filtered(lambda rec: rec.state != "draft")
        if undeletable:
            raise UserError(
                _(
                    "Only draft quality records may be deleted. Records "
                    "%(references)s must be retained until the end of their "
                    "retention period.",
                    references=", ".join(undeletable.mapped("reference")),
                )
            )

    def action_confirm(self):
        """Confirm draft records so that they become retained evidence."""
        for record in self:
            if record.state != "draft":
                raise UserError(
                    _(
                        "Quality record %(reference)s is already confirmed.",
                        reference=record.reference,
                    )
                )
        self.write({"state": "confirmed"})
        for record in self:
            record.message_post(
                body=_(
                    "Quality record confirmed by %(user)s.",
                    user=self.env.user.display_name,
                )
            )
        return True

    def action_archive_record(self):
        """Move confirmed records to the archive."""
        for record in self:
            if record.state != "confirmed":
                raise UserError(
                    _(
                        "Only confirmed quality records may be archived. "
                        "Record %(reference)s is not confirmed.",
                        reference=record.reference,
                    )
                )
        self.write({"state": "archived"})
        return True

    def action_dispose(self):
        """Record the disposal of an archived record past its retention."""
        self.env["ls.qms.quality_record"]._check_disposal_allowed(self)
        self.write({"state": "disposed", "active": False})
        for record in self:
            record.message_post(
                body=_(
                    "Quality record disposed by %(user)s after the retention "
                    "period.",
                    user=self.env.user.display_name,
                )
            )
        return True

    @api.model
    def _check_disposal_allowed(self, records):
        """Validate that ``records`` may be disposed of.

        :param records: quality records to be disposed of.
        :raises UserError: when a record is not archived, is still within its
            retention period, or the user is not a QMS manager.
        """
        if not self.env.user.has_group("ls_qms.group_ls_qms_manager"):
            raise UserError(
                _("Only a QMS manager may dispose of quality records.")
            )
        today = fields.Date.context_today(self)
        for record in records:
            if record.state != "archived":
                raise UserError(
                    _(
                        "Quality record %(reference)s must be archived before "
                        "disposal.",
                        reference=record.reference,
                    )
                )
            if (
                record.date_retention_until
                and record.date_retention_until >= today
            ):
                raise UserError(
                    _(
                        "Quality record %(reference)s must be retained until "
                        "%(date)s.",
                        reference=record.reference,
                        date=record.date_retention_until,
                    )
                )

    def action_open_attachments(self):
        """Open the attachments linked to the quality record."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Attachments"),
            "res_model": "ir.attachment",
            "view_mode": "list,form",
            "domain": [("res_model", "=", self._name), ("res_id", "=", self.id)],
            "context": {
                "default_res_model": self._name,
                "default_res_id": self.id,
            },
        }

    @api.model
    def _cron_retention_review(self):
        """Schedule a disposal review on records past their retention date.

        :return: the number of activities created.
        :rtype: int
        """
        activity_type = self.env.ref(
            "ls_qms.mail_activity_type_ls_qms_retention",
            raise_if_not_found=False,
        )
        if not activity_type:
            return 0
        today = fields.Date.context_today(self)
        records = self.search(
            [
                ("state", "in", ("confirmed", "archived")),
                ("date_retention_until", "!=", False),
                ("date_retention_until", "<", today),
            ]
        )
        created = 0
        for record in records:
            existing = self.env["mail.activity"].search_count(
                [
                    ("res_model", "=", self._name),
                    ("res_id", "=", record.id),
                    ("activity_type_id", "=", activity_type.id),
                ]
            )
            if existing:
                continue
            record.activity_schedule(
                act_type_xmlid="ls_qms.mail_activity_type_ls_qms_retention",
                date_deadline=record.date_retention_until,
                summary=_(
                    "Retention period elapsed for %(reference)s",
                    reference=record.reference,
                ),
                user_id=record.author_id.id,
            )
            created += 1
        return created
