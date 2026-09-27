# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Investigation record attached to a complaint."""

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

METHODOLOGY_SELECTION = [
    ("five_whys", "5 Whys"),
    ("ishikawa", "Ishikawa / Fishbone"),
    ("fmea", "FMEA"),
    ("fault_tree", "Fault Tree Analysis"),
    ("is_is_not", "Is / Is-Not Analysis"),
    ("laboratory_analysis", "Laboratory Analysis"),
    ("batch_record_review", "Batch Record Review"),
    ("other", "Other Methodology"),
]

ROOT_CAUSE_CATEGORY_SELECTION = [
    ("man", "Personnel"),
    ("machine", "Equipment"),
    ("material", "Material"),
    ("method", "Method or Procedure"),
    ("measurement", "Measurement"),
    ("environment", "Environment"),
    ("supplier", "Supplier"),
    ("transport_storage", "Transport or Storage"),
    ("not_determined", "Not Determined"),
]


class LsComplaintInvestigation(models.Model):
    """Root cause investigation of a complaint."""

    _name = "ls.complaint.investigation"
    _description = "Complaint Investigation"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "complaint_id, sequence, id"
    _check_company_auto = True

    name = fields.Char(
        string="Reference",
        required=True,
        readonly=True,
        copy=False,
        index=True,
        default=lambda self: _("New"),
    )
    sequence = fields.Integer(default=10)
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
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        default="draft",
        required=True,
        copy=False,
        index=True,
        tracking=True,
    )
    investigator_id = fields.Many2one(comodel_name="res.users", required=True,
                                      default=lambda self: self.env.user,
                                      tracking=True,)
    date_started = fields.Datetime(copy=False, readonly=True)
    date_completed = fields.Datetime(copy=False, readonly=True)
    methodology = fields.Selection(
        selection=METHODOLOGY_SELECTION,
        tracking=True,
    )
    methodology_other_description = fields.Char(
        string="Other Methodology Description",
        help="Mandatory when the methodology is 'Other Methodology'.",
    )
    investigation_plan = fields.Text()
    investigation_summary = fields.Text(
        help="Facts collected, samples examined and evidence reviewed.",
    )
    root_cause_category = fields.Selection(
        selection=ROOT_CAUSE_CATEGORY_SELECTION,
        tracking=True,
    )
    root_cause_description = fields.Text()
    conclusion = fields.Selection(
        selection=[
            ("confirmed", "Complaint Confirmed"),
            ("not_confirmed", "Complaint Not Confirmed"),
            ("inconclusive", "Inconclusive"),
        ],
        tracking=True,
    )
    batch_impact_assessment = fields.Text(
        help="Assessment of the impact on other batches or units in the market.",
    )
    other_batches_impacted = fields.Boolean(tracking=True)
    approved_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                     copy=False,
                                     tracking=True,)
    approval_date = fields.Datetime(readonly=True, copy=False)
    rejection_reason = fields.Text(
        copy=False,
        help="Justification of the rejection. Must be filled in before "
        "the Reject action is used.",
    )

    _name_company_uniq = models.Constraint(
        "UNIQUE(name, company_id)",
        "The investigation reference must be unique per company.",
    )

    @api.depends("name", "complaint_id.name")
    def _compute_display_name(self):
        """Prefix the investigation reference with the complaint reference."""
        for record in self:
            record.display_name = f"{record.complaint_id.name} / {record.name}"

    @api.constrains("date_started", "date_completed")
    def _check_dates(self):
        """Completion cannot precede the start."""
        for record in self:
            if (
                record.date_started
                and record.date_completed
                and record.date_completed < record.date_started
            ):
                raise ValidationError(
                    _(
                        "Investigation %(name)s: the completion date cannot "
                        "precede the start date.",
                        name=record.name,
                    )
                )

    @api.constrains("methodology", "methodology_other_description")
    def _check_methodology_other(self):
        """'Other Methodology' requires an explicit description."""
        for record in self:
            if (
                record.methodology == "other"
                and not record.methodology_other_description
            ):
                raise ValidationError(
                    _(
                        "Investigation %(name)s: a description is mandatory when "
                        "the methodology is 'Other Methodology'.",
                        name=record.name,
                    )
                )

    @api.constrains("investigator_id", "approved_by_id")
    def _check_segregation_of_duties(self):
        """The approver of an investigation cannot be its investigator."""
        for record in self:
            if (
                record.approved_by_id
                and record.investigator_id
                and record.approved_by_id == record.investigator_id
            ):
                raise ValidationError(
                    _(
                        "Investigation %(name)s: the approver must be different "
                        "from the investigator (segregation of duties).",
                        name=record.name,
                    )
                )

    @api.model_create_multi
    def create(self, vals_list):
        """Assign the investigation reference from the company sequence."""
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == _("New"):
                complaint = self.env["ls.complaint"].browse(vals.get("complaint_id"))
                company_id = complaint.company_id.id or self.env.company.id
                sequence = self.env["ir.sequence"].with_company(company_id)
                vals["name"] = (
                    sequence.next_by_code("ls.complaint.investigation") or _("New")
                )
        return super().create(vals_list)

    def write(self, vals):
        """Freeze approved and rejected investigations."""
        tracked = {
            "state",
            "message_follower_ids",
            "message_ids",
            "activity_ids",
        }
        if set(vals) - tracked:
            frozen = self.filtered(
                lambda record: record.state in ("approved", "rejected")
            )
            if frozen:
                raise UserError(
                    _(
                        "Investigations %(names)s are finalised and can no longer "
                        "be modified.",
                        names=", ".join(frozen.mapped("name")),
                    )
                )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_started(self):
        """Forbid deletion once an investigation started."""
        started = self.filtered(lambda record: record.state != "draft")
        if started:
            raise UserError(
                _(
                    "Investigations %(names)s cannot be deleted because they are "
                    "no longer in draft.",
                    names=", ".join(started.mapped("name")),
                )
            )

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
                    "Action '%(action)s' is not allowed for investigations "
                    "%(names)s in their current status.",
                    action=action_label,
                    names=", ".join(wrong.mapped("name")),
                )
            )

    def action_start(self):
        """Move the investigation from Draft to In Progress."""
        self._ensure_state(("draft",), _("Start"))
        self.write({"state": "in_progress", "date_started": fields.Datetime.now()})
        return True

    def action_complete(self):
        """Move the investigation from In Progress to Completed."""
        self._ensure_state(("in_progress",), _("Complete"))
        for record in self:
            missing = [
                label
                for field_name, label in (
                    ("methodology", _("Methodology")),
                    ("investigation_summary", _("Investigation Summary")),
                    ("root_cause_category", _("Root Cause Category")),
                    ("conclusion", _("Conclusion")),
                )
                if not record[field_name]
            ]
            if missing:
                raise UserError(
                    _(
                        "Investigation %(name)s cannot be completed, the "
                        "following information is missing: %(fields)s.",
                        name=record.name,
                        fields=", ".join(missing),
                    )
                )
            if (
                record.root_cause_category != "not_determined"
                and not record.root_cause_description
            ):
                raise UserError(
                    _(
                        "Investigation %(name)s: a root cause description is "
                        "mandatory unless the root cause is 'Not Determined'.",
                        name=record.name,
                    )
                )
        self.write({"state": "completed", "date_completed": fields.Datetime.now()})
        return True

    def action_approve(self):
        """Approve a completed investigation."""
        self._ensure_state(("completed",), _("Approve"))
        for record in self:
            if record.investigator_id == self.env.user:
                raise UserError(
                    _(
                        "Investigation %(name)s cannot be approved by its own "
                        "investigator (segregation of duties).",
                        name=record.name,
                    )
                )
        self.write(
            {
                "state": "approved",
                "approved_by_id": self.env.user.id,
                "approval_date": fields.Datetime.now(),
            }
        )
        for record in self:
            record.message_post(body=_("Investigation approved."))
        return True

    def action_reject(self, reason=None):
        """Reject a completed investigation with a documented reason.

        :param str reason: rejection justification, taken from the context
            key ``rejection_reason`` when not supplied
        :return: ``True``
        """
        self._ensure_state(("completed",), _("Reject"))
        for record in self:
            record_reason = (
                reason
                or self.env.context.get("rejection_reason")
                or record.rejection_reason
            )
            if not record_reason:
                raise UserError(
                    _(
                        "Investigation %(name)s: a rejection reason is mandatory.",
                        name=record.name,
                    )
                )
            super(LsComplaintInvestigation, record).write(
                {"state": "rejected", "rejection_reason": record_reason}
            )
            record.message_post(
                body=_(
                    "Investigation rejected. Reason: %(reason)s",
                    reason=record_reason,
                )
            )
        return True
