# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Product quality complaint master record and its state machine."""

import logging
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from .ls_complaint_category import SEVERITY_SELECTION

_logger = logging.getLogger(__name__)

STATE_SELECTION = [
    ("received", "Received"),
    ("assessment", "Assessment"),
    ("investigation", "Investigation"),
    ("capa_required", "CAPA Required"),
    ("resolution", "Resolution"),
    ("closed", "Closed"),
    ("cancelled", "Cancelled"),
]

OPEN_STATES = ("received", "assessment", "investigation", "capa_required", "resolution")
FINAL_STATES = ("closed", "cancelled")

OVERDUE_ACTIVITY_SUMMARY = "Complaint overdue"

# Fields that stay writable once the complaint reached a final state.
POST_CLOSURE_WRITABLE_FIELDS = frozenset(
    {
        "active",
        "message_follower_ids",
        "message_ids",
        "message_partner_ids",
        "message_main_attachment_id",
        "activity_ids",
        "activity_state",
        "activity_user_id",
        "activity_type_id",
        "activity_type_icon",
        "activity_date_deadline",
        "activity_summary",
        "activity_exception_decoration",
        "activity_exception_icon",
        "my_activity_date_deadline",
        "capa_reference",
    }
)


class LsComplaint(models.Model):
    """Complaint received about a marketed product or a delivered service."""

    _name = "ls.complaint"
    _description = "Product Quality Complaint"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "receipt_date desc, id desc"
    _check_company_auto = True

    # ------------------------------------------------------------------
    # Identification
    # ------------------------------------------------------------------
    name = fields.Char(
        string="Reference",
        required=True,
        readonly=True,
        copy=False,
        index=True,
        default=lambda self: _("New"),
        tracking=True,
    )
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 index=True,
                                 default=lambda self: self.env.company,)
    priority = fields.Selection(
        selection=[("0", "Normal"), ("1", "High"), ("2", "Urgent")],
        default="0",
        tracking=True,
    )
    state = fields.Selection(
        selection=STATE_SELECTION,
        string="Status",
        default="received",
        required=True,
        copy=False,
        index=True,
        tracking=True,
    )

    # ------------------------------------------------------------------
    # Reception
    # ------------------------------------------------------------------
    receipt_date = fields.Datetime(required=True,
                                   copy=False,
                                   default=fields.Datetime.now,
                                   tracking=True,
                                   help="Date and time at which the organisation became aware of the complaint.",)
    occurrence_date = fields.Date(help="Date on which the complainant observed the issue, when known.",)
    channel = fields.Selection(
        selection=[
            ("phone", "Phone"),
            ("email", "Email"),
            ("letter", "Letter"),
            ("portal", "Web Portal"),
            ("sales_representative", "Sales Representative"),
            ("distributor", "Distributor"),
            ("regulatory_authority", "Regulatory Authority"),
            ("internal", "Internal Report"),
            ("other", "Other Channel"),
        ],
        required=True,
        default="email",
        tracking=True,
    )
    channel_other_description = fields.Char(
        string="Other Channel Description",
        help="Mandatory when the reception channel is 'Other Channel'.",
    )
    received_by_id = fields.Many2one(comodel_name="res.users", required=True,
                                     default=lambda self: self.env.user,
                                     tracking=True,)
    owner_id = fields.Many2one(
        comodel_name="res.users",
        string="Responsible",
        tracking=True,
        help="User accountable for progressing the complaint to closure.",
    )
    reviewer_id = fields.Many2one(comodel_name="res.users", copy=False,
                                  tracking=True,
                                  help="User who reviewed the complaint at closure. Set by the closure wizard.",)

    # ------------------------------------------------------------------
    # Complainant
    # ------------------------------------------------------------------
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Complainant",
        tracking=True,
    )
    complainant_type = fields.Selection(
        selection=[
            ("patient", "Patient or Consumer"),
            ("healthcare_professional", "Healthcare Professional"),
            ("customer", "Customer"),
            ("distributor", "Distributor"),
            ("pharmacy", "Pharmacy"),
            ("hospital", "Hospital"),
            ("regulatory_authority", "Regulatory Authority"),
            ("internal", "Internal"),
            ("anonymous", "Anonymous"),
        ],
        tracking=True,
    )
    contact_name = fields.Char()
    contact_email = fields.Char()
    contact_phone = fields.Char()

    # ------------------------------------------------------------------
    # Product data
    # ------------------------------------------------------------------
    product_related = fields.Boolean(default=True,
                                     tracking=True,
                                     help="Uncheck for service, delivery or documentation complaints that do "
                                     "not concern the quality of a manufactured product.",)
    product_id = fields.Many2one(comodel_name="product.product", check_company=True,
                                 tracking=True,)
    lot_id = fields.Many2one(
        comodel_name="stock.lot",
        string="Lot / Serial Number",
        check_company=True,
        domain="[('product_id', '=', product_id)]",
        tracking=True,
    )
    lot_name = fields.Char(
        string="Lot Number (free text)",
        help="Lot number as declared by the complainant when the lot is not "
        "registered in the system.",
    )
    quantity_complained = fields.Float(
        string="Quantity Concerned",
        digits="Product Unit of Measure",
    )
    product_uom_id = fields.Many2one(
        comodel_name="uom.uom",
        string="Unit of Measure",
    )
    manufacturing_date = fields.Date()
    expiry_date = fields.Date()
    market_country_id = fields.Many2one(
        comodel_name="res.country",
        string="Market",
        help="Country in which the complained product was placed on the market.",
    )
    sample_available = fields.Boolean(help="A physical sample of the complained unit is available for examination.",)
    sample_reference = fields.Char()
    sample_received_date = fields.Date()

    # ------------------------------------------------------------------
    # Description and classification
    # ------------------------------------------------------------------
    summary = fields.Char(
        string="Subject",
        required=True,
        tracking=True,
    )
    description = fields.Text(
        string="Complaint Description",
        required=True,
        help="Verbatim description as reported by the complainant.",
    )
    category_id = fields.Many2one(comodel_name="ls.complaint.category", check_company=True,
                                  tracking=True,)
    complaint_type = fields.Selection(
        selection=[
            ("quality_defect", "Product Quality Defect"),
            ("packaging", "Packaging Defect"),
            ("labelling", "Labelling or Artwork"),
            ("efficacy", "Lack of Efficacy"),
            ("safety", "Safety or Adverse Event"),
            ("documentation", "Documentation"),
            ("delivery", "Delivery or Logistics"),
            ("counterfeit_suspicion", "Suspected Falsified Product"),
            ("other", "Other Type"),
        ],
        tracking=True,
    )
    complaint_type_other_description = fields.Char(
        string="Other Type Description",
        help="Mandatory when the complaint type is 'Other Type'.",
    )
    severity = fields.Selection(
        selection=SEVERITY_SELECTION,
        tracking=True,
    )

    # ------------------------------------------------------------------
    # Assessment
    # ------------------------------------------------------------------
    assessment_date = fields.Datetime(copy=False, readonly=True)
    assessed_by_id = fields.Many2one(comodel_name="res.users", copy=False,
                                     readonly=True,)
    assessment_summary = fields.Text(
        help="Initial impact assessment: product, patient and regulatory impact.",
    )
    potential_safety_impact = fields.Boolean(tracking=True)
    potential_regulatory_impact = fields.Boolean(tracking=True)
    investigation_waiver_reason = fields.Text(
        string="Investigation Waiver Justification",
        copy=False,
        help="Documented justification for moving to Resolution without an "
        "investigation. Only allowed when the category does not require one.",
    )

    # ------------------------------------------------------------------
    # Related records
    # ------------------------------------------------------------------
    investigation_ids = fields.One2many(
        comodel_name="ls.complaint.investigation",
        inverse_name="complaint_id",
        string="Investigations",
        copy=False,
    )
    resolution_ids = fields.One2many(
        comodel_name="ls.complaint.resolution",
        inverse_name="complaint_id",
        string="Resolutions",
        copy=False,
    )
    adverse_event_ids = fields.One2many(
        comodel_name="ls.complaint.adverse_event",
        inverse_name="complaint_id",
        string="Adverse Events",
        copy=False,
    )
    investigation_count = fields.Integer(compute="_compute_related_counts")
    resolution_count = fields.Integer(compute="_compute_related_counts")
    adverse_event_count = fields.Integer(compute="_compute_related_counts")
    has_adverse_event = fields.Boolean(
        compute="_compute_regulatory_flags",
        store=True,
    )
    regulatory_reportable = fields.Boolean(
        string="Regulatory Reporting Required",
        compute="_compute_regulatory_flags",
        store=True,
        tracking=True,
    )
    root_cause_summary = fields.Text(
        compute="_compute_root_cause_summary",
    )

    # ------------------------------------------------------------------
    # CAPA linkage (extension point, see docs/developer_manual.md)
    # ------------------------------------------------------------------
    capa_required = fields.Boolean(copy=False, tracking=True)
    capa_justification = fields.Text(copy=False)
    capa_reference = fields.Char(copy=False,
                                 tracking=True,
                                 help="External reference of the CAPA record raised for this complaint.",)

    # ------------------------------------------------------------------
    # Targets, closure and KPI
    # ------------------------------------------------------------------
    acknowledgement_due_date = fields.Date(
        compute="_compute_due_dates",
        store=True,
    )
    investigation_due_date = fields.Date(
        compute="_compute_due_dates",
        store=True,
    )
    closure_due_date = fields.Date(
        compute="_compute_due_dates",
        store=True,
    )
    customer_notified = fields.Boolean(copy=False, tracking=True)
    customer_notification_date = fields.Date(copy=False)
    date_closed = fields.Datetime(readonly=True, copy=False, tracking=True)
    closed_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                   copy=False,)
    closure_summary = fields.Text(copy=False)
    cancellation_reason = fields.Text(copy=False)
    closure_duration_days = fields.Float(
        string="Closure Duration (days)",
        compute="_compute_closure_duration_days",
        store=True,
        help="Calendar days between receipt and closure.",
    )
    is_overdue = fields.Boolean(
        compute="_compute_is_overdue",
        search="_search_is_overdue",
    )

    _name_company_uniq = models.Constraint(
        "UNIQUE(name, company_id)",
        "The complaint reference must be unique per company.",
    )
    _quantity_complained_positive = models.Constraint(
        "CHECK(quantity_complained >= 0)",
        "The quantity concerned cannot be negative.",
    )

    # ------------------------------------------------------------------
    # Compute methods
    # ------------------------------------------------------------------
    @api.depends("name", "summary")
    def _compute_display_name(self):
        """Display the reference followed by the subject."""
        for record in self:
            if record.summary:
                record.display_name = f"{record.name} - {record.summary}"
            else:
                record.display_name = record.name

    @api.depends("investigation_ids", "resolution_ids", "adverse_event_ids")
    def _compute_related_counts(self):
        """Count child investigation, resolution and adverse event records."""
        for record in self:
            record.investigation_count = len(record.investigation_ids)
            record.resolution_count = len(record.resolution_ids)
            record.adverse_event_count = len(record.adverse_event_ids)

    @api.depends("adverse_event_ids", "adverse_event_ids.reportable")
    def _compute_regulatory_flags(self):
        """Derive the adverse event flags from the child adverse events."""
        for record in self:
            record.has_adverse_event = bool(record.adverse_event_ids)
            record.regulatory_reportable = any(
                event.reportable for event in record.adverse_event_ids
            )

    @api.depends(
        "investigation_ids.state",
        "investigation_ids.root_cause_description",
    )
    def _compute_root_cause_summary(self):
        """Concatenate the root causes of every approved investigation."""
        for record in self:
            approved = record.investigation_ids.filtered(
                lambda investigation: investigation.state == "approved"
            )
            record.root_cause_summary = "\n".join(
                f"{investigation.name}: {investigation.root_cause_description or ''}"
                for investigation in approved
            )

    @api.depends(
        "receipt_date",
        "category_id",
        "category_id.acknowledgement_target_days",
        "category_id.investigation_target_days",
        "category_id.closure_target_days",
    )
    def _compute_due_dates(self):
        """Derive target dates from the category configuration.

        A target of ``0`` means the organisation has not configured a target,
        in which case no due date is produced.
        """
        for record in self:
            base_date = (
                fields.Datetime.context_timestamp(record, record.receipt_date).date()
                if record.receipt_date
                else False
            )
            category = record.category_id
            record.acknowledgement_due_date = record._offset_date(
                base_date, category.acknowledgement_target_days
            )
            record.investigation_due_date = record._offset_date(
                base_date, category.investigation_target_days
            )
            record.closure_due_date = record._offset_date(
                base_date, category.closure_target_days
            )

    @staticmethod
    def _offset_date(base_date, days):
        """Return ``base_date`` shifted by ``days`` or ``False``.

        :param base_date: reference date or ``False``
        :param int days: number of calendar days, ``0`` meaning not configured
        :return: a :class:`datetime.date` or ``False``
        """
        if not base_date or not days:
            return False
        return base_date + timedelta(days=days)

    @api.depends("receipt_date", "date_closed")
    def _compute_closure_duration_days(self):
        """Compute the calendar duration between receipt and closure."""
        for record in self:
            if record.receipt_date and record.date_closed:
                delta = record.date_closed - record.receipt_date
                record.closure_duration_days = delta.total_seconds() / 86400.0
            else:
                record.closure_duration_days = 0.0

    def _compute_is_overdue(self):
        """Flag open complaints whose configured closure target has passed."""
        today = fields.Date.context_today(self)
        for record in self:
            record.is_overdue = bool(
                record.state in OPEN_STATES
                and record.closure_due_date
                and record.closure_due_date < today
            )

    @api.model
    def _search_is_overdue(self, operator, value):
        """Search implementation for the non-stored ``is_overdue`` field."""
        if operator not in ("=", "!="):
            raise UserError(
                _("The 'Overdue' filter only supports the '=' and '!=' operators.")
            )
        overdue_domain = [
            ("state", "in", list(OPEN_STATES)),
            ("closure_due_date", "!=", False),
            ("closure_due_date", "<", fields.Date.context_today(self)),
        ]
        positive = (operator == "=") == bool(value)
        if positive:
            return overdue_domain
        return ["!"] + overdue_domain

    # ------------------------------------------------------------------
    # Onchange methods
    # ------------------------------------------------------------------
    @api.onchange("product_id")
    def _onchange_product_id(self):
        """Align the unit of measure and reset an inconsistent lot."""
        for record in self:
            if record.product_id:
                record.product_uom_id = record.product_id.uom_id
            if record.lot_id and record.lot_id.product_id != record.product_id:
                record.lot_id = False

    @api.onchange("category_id")
    def _onchange_category_id(self):
        """Propose the default severity configured on the category."""
        for record in self:
            if record.category_id.default_severity and not record.severity:
                record.severity = record.category_id.default_severity

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        """Pre-fill the contact details from the selected partner."""
        for record in self:
            if record.partner_id:
                record.contact_name = record.partner_id.name
                record.contact_email = record.partner_id.email
                record.contact_phone = record.partner_id.phone

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("receipt_date", "occurrence_date")
    def _check_dates(self):
        """Receipt cannot be in the future and cannot precede the occurrence."""
        now = fields.Datetime.now()
        for record in self:
            if record.receipt_date and record.receipt_date > now:
                raise ValidationError(
                    _(
                        "Complaint %(name)s: the receipt date cannot be in the future.",
                        name=record.name,
                    )
                )
            if (
                record.receipt_date
                and record.occurrence_date
                and record.occurrence_date > record.receipt_date.date()
            ):
                raise ValidationError(
                    _(
                        "Complaint %(name)s: the occurrence date cannot be later "
                        "than the receipt date.",
                        name=record.name,
                    )
                )

    @api.constrains("manufacturing_date", "expiry_date")
    def _check_product_dates(self):
        """Expiry date must follow the manufacturing date."""
        for record in self:
            if (
                record.manufacturing_date
                and record.expiry_date
                and record.expiry_date < record.manufacturing_date
            ):
                raise ValidationError(
                    _(
                        "Complaint %(name)s: the expiry date cannot precede the "
                        "manufacturing date.",
                        name=record.name,
                    )
                )

    @api.constrains("channel", "channel_other_description")
    def _check_channel_other(self):
        """'Other Channel' requires an explicit description."""
        for record in self:
            if record.channel == "other" and not record.channel_other_description:
                raise ValidationError(
                    _(
                        "Complaint %(name)s: a description is mandatory when the "
                        "reception channel is 'Other Channel'.",
                        name=record.name,
                    )
                )

    @api.constrains("complaint_type", "complaint_type_other_description")
    def _check_complaint_type_other(self):
        """'Other Type' requires an explicit description."""
        for record in self:
            if (
                record.complaint_type == "other"
                and not record.complaint_type_other_description
            ):
                raise ValidationError(
                    _(
                        "Complaint %(name)s: a description is mandatory when the "
                        "complaint type is 'Other Type'.",
                        name=record.name,
                    )
                )

    @api.constrains("product_related", "product_id", "state")
    def _check_product_required(self):
        """A product related complaint must identify a product.

        ``state`` is a trigger: the rule applies when the complaint leaves
        the Received state, which is a change of state only.
        """
        for record in self:
            if (
                record.product_related
                and record.state != "received"
                and not record.product_id
            ):
                raise ValidationError(
                    _(
                        "Complaint %(name)s: a product must be identified before "
                        "leaving the Received state.",
                        name=record.name,
                    )
                )

    @api.constrains("lot_id", "product_id")
    def _check_lot_product(self):
        """The selected lot must belong to the selected product."""
        for record in self:
            if record.lot_id and record.lot_id.product_id != record.product_id:
                raise ValidationError(
                    _(
                        "Complaint %(name)s: lot %(lot)s does not belong to the "
                        "selected product.",
                        name=record.name,
                        lot=record.lot_id.display_name,
                    )
                )

    @api.constrains("owner_id", "reviewer_id")
    def _check_segregation_of_duties(self):
        """The reviewer of a complaint cannot be its responsible user."""
        for record in self:
            if (
                record.owner_id
                and record.reviewer_id
                and record.owner_id == record.reviewer_id
            ):
                raise ValidationError(
                    _(
                        "Complaint %(name)s: the reviewer must be different from "
                        "the responsible user (segregation of duties).",
                        name=record.name,
                    )
                )

    # ------------------------------------------------------------------
    # ORM overrides
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Assign the complaint reference from the company sequence."""
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == _("New"):
                company_id = vals.get("company_id") or self.env.company.id
                sequence = self.env["ir.sequence"].with_company(company_id)
                vals["name"] = sequence.next_by_code("ls.complaint") or _("New")
        return super().create(vals_list)

    def write(self, vals):
        """Protect the content of complaints that reached a final state."""
        protected_fields = set(vals) - POST_CLOSURE_WRITABLE_FIELDS
        if protected_fields and "state" not in vals:
            frozen = self.filtered(lambda record: record.state in FINAL_STATES)
            if frozen:
                raise UserError(
                    _(
                        "Complaints %(names)s are closed or cancelled and can no "
                        "longer be modified. Raise a new complaint instead.",
                        names=", ".join(frozen.mapped("name")),
                    )
                )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_progressed(self):
        """Forbid deletion once a complaint left the Received state."""
        progressed = self.filtered(lambda record: record.state != "received")
        if progressed:
            raise UserError(
                _(
                    "Complaints %(names)s cannot be deleted because they left the "
                    "Received state. Cancel them instead.",
                    names=", ".join(progressed.mapped("name")),
                )
            )

    def copy_data(self, default=None):
        """Reset regulated data when duplicating a complaint."""
        default = dict(default or {})
        default.setdefault("name", _("New"))
        default.setdefault("state", "received")
        return super().copy_data(default=default)

    # ------------------------------------------------------------------
    # State machine helpers
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
                    "Action '%(action)s' is not allowed for complaints %(names)s "
                    "in their current status.",
                    action=action_label,
                    names=", ".join(wrong.mapped("name")),
                )
            )

    def _require_fields(self, field_names, action_label):
        """Raise when one of ``field_names`` is empty.

        :param list field_names: technical field names to verify
        :param str action_label: human readable action used in the message
        :raises UserError: when a mandatory value is missing
        """
        descriptions = self.fields_get(field_names, ["string"])
        for record in self:
            missing = [
                descriptions[field_name]["string"]
                for field_name in field_names
                if not record[field_name]
            ]
            if missing:
                raise UserError(
                    _(
                        "Complaint %(name)s: action '%(action)s' requires the "
                        "following information: %(fields)s.",
                        name=record.name,
                        action=action_label,
                        fields=", ".join(missing),
                    )
                )

    # ------------------------------------------------------------------
    # State machine actions
    # ------------------------------------------------------------------
    def action_start_assessment(self):
        """Move the complaint from Received to Assessment."""
        self._ensure_state(("received",), _("Start Assessment"))
        self._require_fields(["owner_id", "category_id"], _("Start Assessment"))
        self.write(
            {
                "state": "assessment",
                "assessment_date": fields.Datetime.now(),
                "assessed_by_id": self.env.user.id,
            }
        )
        for record in self:
            record.message_post(body=_("Assessment started."))
        return True

    def action_start_investigation(self):
        """Move the complaint from Assessment to Investigation."""
        self._ensure_state(("assessment",), _("Start Investigation"))
        self._require_fields(
            ["severity", "complaint_type", "assessment_summary"],
            _("Start Investigation"),
        )
        self.write({"state": "investigation"})
        for record in self:
            if not record.investigation_ids:
                self.env["ls.complaint.investigation"].create(
                    {
                        "complaint_id": record.id,
                        "investigator_id": record.owner_id.id,
                    }
                )
            record.message_post(body=_("Investigation started."))
        return True

    def action_skip_investigation(self):
        """Move to Resolution without investigation, with justification."""
        self._ensure_state(("assessment",), _("Skip Investigation"))
        self._require_fields(
            ["severity", "complaint_type", "investigation_waiver_reason"],
            _("Skip Investigation"),
        )
        for record in self:
            if record.category_id.requires_investigation:
                raise UserError(
                    _(
                        "Complaint %(name)s: category '%(category)s' requires an "
                        "investigation, it cannot be skipped.",
                        name=record.name,
                        category=record.category_id.name,
                    )
                )
            if record.adverse_event_ids:
                raise UserError(
                    _(
                        "Complaint %(name)s: an investigation is mandatory because "
                        "adverse events are recorded.",
                        name=record.name,
                    )
                )
        self.write({"state": "resolution"})
        for record in self:
            record.message_post(
                body=_(
                    "Investigation waived. Justification: %(reason)s",
                    reason=record.investigation_waiver_reason,
                )
            )
        return True

    def action_mark_capa_required(self):
        """Declare that a CAPA record must be raised for this complaint."""
        self._ensure_state(("investigation",), _("CAPA Required"))
        self._require_fields(["capa_justification"], _("CAPA Required"))
        self._check_investigations_approved()
        self.write({"state": "capa_required", "capa_required": True})
        for record in self:
            record.message_post(body=_("A CAPA record is required."))
        return True

    def action_start_resolution(self):
        """Move the complaint to the Resolution state."""
        self._ensure_state(("investigation", "capa_required"), _("Start Resolution"))
        self._check_investigations_approved()
        for record in self:
            if record.state == "capa_required" and not record.capa_reference:
                raise UserError(
                    _(
                        "Complaint %(name)s: the CAPA reference must be recorded "
                        "before starting the resolution.",
                        name=record.name,
                    )
                )
        self.write({"state": "resolution"})
        for record in self:
            record.message_post(body=_("Resolution started."))
        return True

    def _check_investigations_approved(self):
        """Raise unless every required investigation is approved.

        :raises UserError: when the category requires an investigation and no
            approved investigation exists, or when an investigation is still
            in progress.
        """
        for record in self:
            approved = record.investigation_ids.filtered(
                lambda investigation: investigation.state == "approved"
            )
            pending = record.investigation_ids.filtered(
                lambda investigation: investigation.state
                in ("draft", "in_progress", "completed")
            )
            if record.category_id.requires_investigation and not approved:
                raise UserError(
                    _(
                        "Complaint %(name)s: at least one approved investigation "
                        "is required.",
                        name=record.name,
                    )
                )
            if pending:
                raise UserError(
                    _(
                        "Complaint %(name)s: investigations %(refs)s are not "
                        "finalised.",
                        name=record.name,
                        refs=", ".join(pending.mapped("name")),
                    )
                )

    def _check_can_close(self):
        """Raise unless every closure precondition is met.

        :raises UserError: when a child record is still open, when a required
            CAPA reference is missing or when a reportable adverse event has
            not been submitted.
        """
        for record in self:
            open_resolutions = record.resolution_ids.filtered(
                lambda resolution: resolution.state in ("draft", "in_progress")
            )
            if not record.resolution_ids:
                raise UserError(
                    _(
                        "Complaint %(name)s: at least one resolution must be "
                        "recorded before closure.",
                        name=record.name,
                    )
                )
            if open_resolutions:
                raise UserError(
                    _(
                        "Complaint %(name)s: resolutions %(refs)s are still open.",
                        name=record.name,
                        refs=", ".join(open_resolutions.mapped("display_name")),
                    )
                )
            open_events = record.adverse_event_ids.filtered(
                lambda event: event.state != "closed"
            )
            if open_events:
                raise UserError(
                    _(
                        "Complaint %(name)s: adverse events %(refs)s are not "
                        "closed.",
                        name=record.name,
                        refs=", ".join(open_events.mapped("name")),
                    )
                )
            if record.capa_required and not record.capa_reference:
                raise UserError(
                    _(
                        "Complaint %(name)s: the CAPA reference is mandatory "
                        "because a CAPA was declared as required.",
                        name=record.name,
                    )
                )

    def action_open_close_wizard(self):
        """Open the closure wizard for the current complaint."""
        self.ensure_one()
        self._ensure_state(("resolution",), _("Close"))
        self._check_can_close()
        return {
            "type": "ir.actions.act_window",
            "name": _("Close Complaint"),
            "res_model": "ls.complaint.close.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_complaint_id": self.id},
        }

    def action_open_cancel_wizard(self):
        """Open the cancellation wizard for the current complaint."""
        self.ensure_one()
        self._ensure_state(OPEN_STATES, _("Cancel"))
        return {
            "type": "ir.actions.act_window",
            "name": _("Cancel Complaint"),
            "res_model": "ls.complaint.cancel.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_complaint_id": self.id},
        }

    def action_close(self, closure_summary, reviewer, customer_notified=False):
        """Close the complaint after the wizard collected the closure data.

        :param str closure_summary: mandatory closure statement
        :param reviewer: ``res.users`` record performing the review
        :param bool customer_notified: whether the complainant was informed
        :return: ``True``
        :raises UserError: when a closure precondition is not met
        """
        self._ensure_state(("resolution",), _("Close"))
        self._check_can_close()
        if not closure_summary:
            raise UserError(_("A closure summary is mandatory."))
        for record in self:
            if reviewer and record.owner_id and reviewer == record.owner_id:
                raise UserError(
                    _(
                        "Complaint %(name)s: the reviewer must be different from "
                        "the responsible user (segregation of duties).",
                        name=record.name,
                    )
                )
        values = {
            "state": "closed",
            "date_closed": fields.Datetime.now(),
            "closed_by_id": self.env.user.id,
            "closure_summary": closure_summary,
            "reviewer_id": reviewer.id if reviewer else False,
            "customer_notified": customer_notified,
        }
        if customer_notified:
            values["customer_notification_date"] = fields.Date.context_today(self)
        super().write(values)
        for record in self:
            record.activity_unlink(["mail.mail_activity_data_todo"])
            record.message_post(body=_("Complaint closed."))
        return True

    def action_cancel(self, reason):
        """Cancel the complaint with a documented reason.

        :param str reason: mandatory cancellation justification
        :return: ``True``
        """
        self._ensure_state(OPEN_STATES, _("Cancel"))
        if not reason:
            raise UserError(_("A cancellation reason is mandatory."))
        super().write(
            {
                "state": "cancelled",
                "cancellation_reason": reason,
                "date_closed": fields.Datetime.now(),
                "closed_by_id": self.env.user.id,
            }
        )
        for record in self:
            record.activity_unlink(["mail.mail_activity_data_todo"])
            record.message_post(
                body=_("Complaint cancelled. Reason: %(reason)s", reason=reason)
            )
        return True

    def action_reset_to_received(self):
        """Return a cancelled complaint to the Received state."""
        self._ensure_state(("cancelled",), _("Reset to Received"))
        super().write(
            {
                "state": "received",
                "cancellation_reason": False,
                "date_closed": False,
                "closed_by_id": False,
            }
        )
        for record in self:
            record.message_post(body=_("Complaint reopened from cancellation."))
        return True

    # ------------------------------------------------------------------
    # Smart buttons
    # ------------------------------------------------------------------
    def _action_view_related(self, model, name, domain_field):
        """Build a window action listing the child records of ``model``.

        :param str model: technical name of the child model
        :param str name: window action title
        :param str domain_field: inverse field pointing to the complaint
        :return: an ``ir.actions.act_window`` dictionary
        """
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": name,
            "res_model": model,
            "view_mode": "list,form",
            "domain": [(domain_field, "=", self.id)],
            "context": {f"default_{domain_field}": self.id},
        }

    def action_view_investigations(self):
        """Open the investigations of the current complaint."""
        return self._action_view_related(
            "ls.complaint.investigation", _("Investigations"), "complaint_id"
        )

    def action_view_resolutions(self):
        """Open the resolutions of the current complaint."""
        return self._action_view_related(
            "ls.complaint.resolution", _("Resolutions"), "complaint_id"
        )

    def action_view_adverse_events(self):
        """Open the adverse events of the current complaint."""
        return self._action_view_related(
            "ls.complaint.adverse_event", _("Adverse Events"), "complaint_id"
        )

    # ------------------------------------------------------------------
    # Scheduled actions
    # ------------------------------------------------------------------
    @api.model
    def _cron_notify_overdue_complaints(self, limit=200):
        """Schedule a to-do activity on every overdue open complaint.

        :param int limit: maximum number of complaints processed per run
        :return: number of activities created
        """
        today = fields.Date.context_today(self)
        complaints = self.search(
            [
                ("state", "in", list(OPEN_STATES)),
                ("closure_due_date", "!=", False),
                ("closure_due_date", "<", today),
            ],
            limit=limit,
        )
        created = 0
        for complaint in complaints:
            existing = complaint.activity_ids.filtered(
                lambda activity: activity.summary == OVERDUE_ACTIVITY_SUMMARY
            )
            if existing:
                continue
            complaint.activity_schedule(
                act_type_xmlid="mail.mail_activity_data_todo",
                summary=OVERDUE_ACTIVITY_SUMMARY,
                note=_(
                    "The configured closure target (%(due)s) has passed.",
                    due=complaint.closure_due_date,
                ),
                user_id=(complaint.owner_id or complaint.received_by_id).id,
            )
            created += 1
        _logger.info("ls_complaint: %s overdue activities created", created)
        return created
