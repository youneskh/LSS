# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Medical device master record.

The device record is the anchor of the module. Every regulatory artefact
managed here -- UDI assignments, risk management files, clinical evaluations,
technical documentation, CE marking records, post-market surveillance plans and
periodic reports -- is attached to exactly one device.

Regulatory references applied on this model:

* MDR Article 10(8): retention period of the technical documentation.
* MDR Article 61(11): annual update of the PMCF evaluation report for class III
  and implantable devices.
* MDR Article 85 and Article 86: periodic post-market reporting obligations.
"""

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from . import constants


class LsMdDevice(models.Model):
    """Register entry for a medical device placed or to be placed on a market."""

    _name = "ls.md.device"
    _description = "Medical Device"
    _check_company_auto = True
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "reference desc, id desc"

    # ------------------------------------------------------------------
    # Identification
    # ------------------------------------------------------------------
    reference = fields.Char(required=True,
                            copy=False,
                            readonly=True,
                            default=lambda self: self.env._("New"),
                            tracking=True,
                            help="Internal reference of the device record, allocated on creation.",
                            )
    name = fields.Char(
        string="Device Name",
        required=True,
        tracking=True,
        help="Trade name or designation of the device.",
    )
    model_reference = fields.Char(
        string="Model or Catalogue Reference",
        tracking=True,
        help="Manufacturer model, type or catalogue reference of the device.",
    )
    basic_udi_di = fields.Char(
        string="Basic UDI-DI",
        tracking=True,
        copy=False,
        help=(
            "Basic UDI-DI assigned to the device, as defined in Part C of "
            "Annex VI of Regulation (EU) 2017/745. It groups devices sharing "
            "the same intended purpose, risk class, essential design and "
            "manufacturing characteristics."
        ),
    )
    gmdn_code = fields.Char(
        string="Nomenclature Code",
        help=(
            "Device nomenclature code used by the organisation, for example a "
            "GMDN or EMDN code. Recorded as free text because the applicable "
            "nomenclature depends on the target market."
        ),
    )
    product_id = fields.Many2one(comodel_name="product.product", ondelete="restrict",
                                 tracking=True,
                                 check_company=True,
                                 help=(
                                     "Product record used for inventory and manufacturing operations. "
                                     "Linking the device to a product enables lot and serial number "
                                     "traceability through the Inventory application."),
                                 )
    manufacturer_id = fields.Many2one(
        comodel_name="res.partner",
        string="Legal Manufacturer",
        tracking=True,
        help="Legal manufacturer under whose name the device is placed on the market.",
    )
    authorised_representative_id = fields.Many2one(comodel_name="res.partner", help=(
            "Authorised representative appointed for manufacturers established "
            "outside the market of placement."),
    )
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,
                                 index=True,
                                 help="Company owning this device record.",)
    active = fields.Boolean(default=True,
                            help="Uncheck to archive the device record without deleting it.",)

    # ------------------------------------------------------------------
    # Classification and characteristics
    # ------------------------------------------------------------------
    device_class_id = fields.Many2one(
        comodel_name="ls.md.device_class",
        string="Risk Class",
        required=True,
        ondelete="restrict",
        tracking=True,
        index=True,
        help="Risk class assigned to the device.",
    )
    classification_rule = fields.Char(tracking=True,
                                      help=(
                                          "Classification rule applied to reach the risk class, recorded as "
                                          "free text, for example 'Annex VIII, Rule 8'. Free text is used "
                                          "deliberately so that no rule set is asserted that has not been "
                                          "confirmed against the applicable regulation."),
                                      )
    classification_rationale = fields.Text(help="Justification of the classification decision.",)
    intended_purpose = fields.Text(tracking=True,
                                   help=(
                                       "Intended purpose of the device as stated by the manufacturer in "
                                       "the labelling, instructions for use and promotional material."),
                                   )
    is_implantable = fields.Boolean(
        string="Implantable",
        tracking=True,
        help=(
            "Implantable devices carry an extended technical documentation "
            "retention period and an annual PMCF evaluation update obligation."
        ),
    )
    is_sterile = fields.Boolean(
        string="Placed on the Market Sterile",
        help="The device is supplied in a sterile condition.",
    )
    is_measuring = fields.Boolean(
        string="Has a Measuring Function",
        help="The device has a measuring function.",
    )
    is_reusable_surgical = fields.Boolean(
        string="Reusable Surgical Instrument",
        help="The device is a reusable surgical instrument.",
    )
    is_software = fields.Boolean(
        string="Software",
        help="The device is software or contains software as a component.",
    )
    is_custom_made = fields.Boolean(
        string="Custom-Made",
        tracking=True,
        help="The device is custom-made for a particular patient or user.",
    )
    requires_direct_marking = fields.Boolean(compute="_compute_requires_direct_marking",
                                             store=True,
                                             readonly=False,
                                             help=(
                                                 "Reusable devices are subject to direct marking of the UDI carrier "
                                                 "on the device itself. The computed proposal may be overridden."),
                                             )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    state = fields.Selection(
        selection=constants.DEVICE_STATE_SELECTION,
        string="Status",
        default="draft",
        required=True,
        tracking=True,
        index=True,
        copy=False,
        help="Lifecycle status of the device record.",
    )
    state_change_reason = fields.Text(
        string="Last Status Change Reason",
        readonly=True,
        copy=False,
        help="Justification recorded for the most recent status change.",
    )
    market_placement_date = fields.Date(
        string="First Placed on the Market",
        tracking=True,
        copy=False,
        help="Date on which the device was first placed on the market.",
    )
    market_withdrawal_date = fields.Date(
        string="Withdrawn From the Market",
        tracking=True,
        copy=False,
        help="Date on which the last device was placed on the market.",
    )
    documentation_retention_years = fields.Integer(
        string="Documentation Retention (Years)",
        compute="_compute_documentation_retention",
        store=True,
        help=(
            "Number of years the technical documentation must remain available "
            "after the last device has been placed on the market, per Article "
            "10(8) of Regulation (EU) 2017/745."
        ),
    )
    documentation_retention_until = fields.Date(
        string="Retain Documentation Until",
        compute="_compute_documentation_retention",
        store=True,
        help=(
            "Computed end of the documentation retention period. Only "
            "available once the market withdrawal date has been recorded."
        ),
    )

    # ------------------------------------------------------------------
    # Related regulatory records
    # ------------------------------------------------------------------
    udi_ids = fields.One2many(
        comodel_name="ls.md.udi",
        inverse_name="device_id",
        string="UDI Assignments",
    )
    risk_assessment_ids = fields.One2many(
        comodel_name="ls.md.risk_assessment",
        inverse_name="device_id",
        string="Risk Management Files",
    )
    clinical_evaluation_ids = fields.One2many(
        comodel_name="ls.md.clinical_evaluation",
        inverse_name="device_id",
        string="Clinical Evaluations",
    )
    pmcf_evaluation_ids = fields.One2many(
        comodel_name="ls.md.pmcf_evaluation",
        inverse_name="device_id",
        string="PMCF Evaluation Reports",
    )
    technical_file_ids = fields.One2many(
        comodel_name="ls.md.technical_file",
        inverse_name="device_id",
        string="Technical Documentation",
    )
    ce_marking_ids = fields.One2many(
        comodel_name="ls.md.ce_marking",
        inverse_name="device_id",
        string="CE Marking Records",
    )
    pms_ids = fields.One2many(
        comodel_name="ls.md.pms",
        inverse_name="device_id",
        string="Post-Market Surveillance Plans",
    )
    pms_report_ids = fields.One2many(
        comodel_name="ls.md.pms_report",
        inverse_name="device_id",
        string="Periodic Post-Market Reports",
    )

    udi_count = fields.Integer(compute="_compute_related_counts")
    risk_assessment_count = fields.Integer(
        compute="_compute_related_counts", string="Risk File Count"
    )
    clinical_evaluation_count = fields.Integer(compute="_compute_related_counts")
    technical_file_count = fields.Integer(compute="_compute_related_counts")
    ce_marking_count = fields.Integer(compute="_compute_related_counts")
    pms_report_count = fields.Integer(
        compute="_compute_related_counts", string="Periodic Report Count"
    )

    # ------------------------------------------------------------------
    # Derived regulatory obligations
    # ------------------------------------------------------------------
    periodic_report_type = fields.Selection(selection=constants.PERIODIC_REPORT_TYPE_SELECTION, compute="_compute_periodic_report_obligation",
                                            store=True,
                                            help="Kind of periodic post-market report required for this device.",)
    periodic_report_interval_months = fields.Integer(
        string="Report Interval (Months)",
        compute="_compute_periodic_report_obligation",
        store=True,
        help=(
            "Maximum interval between two periodic post-market reports, taken "
            "from the risk class configuration."
        ),
    )
    annual_pmcf_update_required = fields.Boolean(compute="_compute_periodic_report_obligation",
                                                 store=True,
                                                 help=(
                                                     "True when the PMCF evaluation report must be updated at least "
                                                     "annually, which applies to class III devices and to implantable "
                                                     "devices under Article 61(11) of Regulation (EU) 2017/745."
                                                     ),
                                                 )
    notified_body_required = fields.Boolean(related="device_class_id.notified_body_required",
                                            store=True,
                                            help="Taken from the risk class configuration.",)
    last_periodic_report_date = fields.Date(
        string="Last Periodic Report",
        compute="_compute_periodic_report_status",
        store=True,
        help="End date of the most recent approved periodic post-market report.",
    )
    next_periodic_report_due = fields.Date(compute="_compute_periodic_report_status",
                                           store=True,
                                           help=(
                                               "Computed due date of the next periodic post-market report. Empty "
                                               "when no fixed maximum interval applies to the risk class."),
                                           )
    periodic_report_overdue = fields.Boolean(compute="_compute_periodic_report_status",
                                             store=True,
                                             help="True when the next periodic post-market report is past its due date.",)
    active_ce_marking_id = fields.Many2one(
        comodel_name="ls.md.ce_marking",
        string="Active Certificate",
        compute="_compute_active_ce_marking",
        store=True,
        help="Most recent CE marking record in a valid state.",
    )
    ce_certificate_expiry_date = fields.Date(
        string="Certificate Expiry",
        related="active_ce_marking_id.expiry_date",
        store=True,
        help="Expiry date of the active certificate.",
    )

    _reference_unique = models.Constraint(
        "UNIQUE(reference, company_id)",
        "The device reference must be unique within a company.",
    )
    _basic_udi_di_unique = models.Constraint(
        "UNIQUE(basic_udi_di, company_id)",
        "The Basic UDI-DI must be unique within a company.",
    )

    # ------------------------------------------------------------------
    # Compute methods
    # ------------------------------------------------------------------
    @api.depends("is_reusable_surgical", "is_software", "is_custom_made")
    def _compute_requires_direct_marking(self):
        """Propose direct marking for reusable surgical instruments.

        Article 27(4) of Regulation (EU) 2017/745 requires the UDI carrier to
        be placed on the device itself for reusable devices. The proposal is
        limited to reusable surgical instruments because that is the
        characteristic captured on this model; the field remains editable so
        that other reusable devices can be flagged manually.
        """
        for record in self:
            record.requires_direct_marking = bool(
                record.is_reusable_surgical
                and not record.is_software
                and not record.is_custom_made
            )

    @api.depends("is_implantable", "market_withdrawal_date")
    def _compute_documentation_retention(self):
        """Derive the documentation retention period and its end date."""
        for record in self:
            years = (
                constants.TECHNICAL_DOC_RETENTION_YEARS_IMPLANTABLE
                if record.is_implantable
                else constants.TECHNICAL_DOC_RETENTION_YEARS
            )
            record.documentation_retention_years = years
            if record.market_withdrawal_date:
                record.documentation_retention_until = (
                    record.market_withdrawal_date + relativedelta(years=years)
                )
            else:
                record.documentation_retention_until = False

    @api.depends(
        "device_class_id",
        "device_class_id.periodic_report_type",
        "device_class_id.periodic_report_interval_months",
        "device_class_id.annual_pmcf_update_required",
        "is_implantable",
    )
    def _compute_periodic_report_obligation(self):
        """Derive the post-market reporting obligations of the device."""
        for record in self:
            device_class = record.device_class_id
            record.periodic_report_type = device_class.periodic_report_type or False
            record.periodic_report_interval_months = (
                device_class.periodic_report_interval_months or 0
            )
            record.annual_pmcf_update_required = bool(
                device_class.annual_pmcf_update_required or record.is_implantable
            )

    @api.depends(
        "periodic_report_interval_months",
        "market_placement_date",
        "state",
        "pms_report_ids.state",
        "pms_report_ids.period_end",
    )
    def _compute_periodic_report_status(self):
        """Derive the last and next periodic post-market report dates."""
        today = fields.Date.context_today(self)
        for record in self:
            approved = record.pms_report_ids.filtered(
                lambda report: report.state == "approved" and report.period_end
            )
            last_date = max(approved.mapped("period_end")) if approved else False
            record.last_periodic_report_date = last_date
            interval = record.periodic_report_interval_months
            baseline = last_date or record.market_placement_date
            if interval > 0 and baseline and record.state in ("on_market", "suspended"):
                due = baseline + relativedelta(months=interval)
                record.next_periodic_report_due = due
                record.periodic_report_overdue = due < today
            else:
                record.next_periodic_report_due = False
                record.periodic_report_overdue = False

    @api.depends("ce_marking_ids.state", "ce_marking_ids.issue_date")
    def _compute_active_ce_marking(self):
        """Select the most recent certificate in an issued or valid state."""
        for record in self:
            candidates = record.ce_marking_ids.filtered(
                lambda marking: marking.state in ("issued", "valid")
            )
            record.active_ce_marking_id = (
                candidates.sorted(key=lambda m: (m.issue_date or fields.Date.today()))[
                    -1
                ]
                if candidates
                else False
            )

    @api.depends(
        "udi_ids",
        "risk_assessment_ids",
        "clinical_evaluation_ids",
        "technical_file_ids",
        "ce_marking_ids",
        "pms_report_ids",
    )
    def _compute_related_counts(self):
        """Count the regulatory records attached to each device."""
        for record in self:
            record.udi_count = len(record.udi_ids)
            record.risk_assessment_count = len(record.risk_assessment_ids)
            record.clinical_evaluation_count = len(record.clinical_evaluation_ids)
            record.technical_file_count = len(record.technical_file_ids)
            record.ce_marking_count = len(record.ce_marking_ids)
            record.pms_report_count = len(record.pms_report_ids)

    @api.depends("reference", "name")
    def _compute_display_name(self):
        """Combine the reference and the device name."""
        for record in self:
            if record.reference and record.reference != self.env._("New"):
                record.display_name = (
                    f"[{record.reference}] {record.name or ''}".strip()
                )
            else:
                record.display_name = record.name or ""

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("market_placement_date", "market_withdrawal_date")
    def _check_market_dates(self):
        """Reject a withdrawal date preceding the placement date."""
        for record in self:
            if (
                record.market_placement_date
                and record.market_withdrawal_date
                and record.market_withdrawal_date < record.market_placement_date
            ):
                raise ValidationError(
                    self.env._(
                        "Device '%(device)s': the market withdrawal date cannot "
                        "precede the date on which the device was first placed "
                        "on the market.",
                        device=record.display_name,
                    )
                )

    @api.constrains("state", "market_placement_date")
    def _check_on_market_requires_placement_date(self):
        """Require a placement date once the device is declared on the market."""
        for record in self:
            if record.state == "on_market" and not record.market_placement_date:
                raise ValidationError(
                    self.env._(
                        "Device '%(device)s' cannot be placed on the market "
                        "without a date of first placing on the market.",
                        device=record.display_name,
                    )
                )

    @api.constrains("is_custom_made", "is_implantable")
    def _check_custom_made_combination(self):
        """Record a combination that requires documented justification.

        A custom-made implantable device is possible but attracts distinct
        documentation obligations. The constraint does not forbid the
        combination; it requires the classification rationale to be filled in
        so that the decision is traceable.
        """
        for record in self:
            if (
                record.is_custom_made
                and record.is_implantable
                and not record.classification_rationale
            ):
                raise ValidationError(
                    self.env._(
                        "Device '%(device)s' is both custom-made and "
                        "implantable. Record the classification rationale "
                        "before saving.",
                        device=record.display_name,
                    )
                )

    # ------------------------------------------------------------------
    # ORM overrides
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Allocate the device reference from the dedicated sequence."""
        placeholder = self.env._("New")
        for vals in vals_list:
            if not vals.get("reference") or vals["reference"] == placeholder:
                company_id = vals.get("company_id") or self.env.company.id
                vals["reference"] = self.env["ir.sequence"].next_by_code(
                    "ls.md.device"
                ) or self.env._("DEV/UNSEQUENCED")
                vals.setdefault("company_id", company_id)
        return super().create(vals_list)

    def copy_data(self, default=None):
        """Reset identifiers and lifecycle data when duplicating a device."""
        default = dict(default or {})
        default.setdefault("reference", self.env._("New"))
        default.setdefault("basic_udi_di", False)
        default.setdefault("state", "draft")
        default.setdefault("market_placement_date", False)
        default.setdefault("market_withdrawal_date", False)
        return super().copy_data(default=default)

    # ------------------------------------------------------------------
    # Business methods
    # ------------------------------------------------------------------
    def _check_regulatory_authority(self):
        """Raise unless the current user holds regulatory authority.

        Authority is checked in Python rather than only in the user interface
        so that the restriction also applies to programmatic access.
        """
        for record in self:
            if not (
                self.env.user.has_group(constants.GROUP_REGULATORY)
                or self.env.user.has_group(constants.GROUP_MANAGER)
            ):
                raise UserError(
                    self.env._(
                        "Changing the market status of device '%(device)s' "
                        "requires the Medical Devices Regulatory Affairs or "
                        "Manager access level.",
                        device=record.display_name,
                    )
                )

    def _set_state(self, new_state, reason=None):
        """Apply a lifecycle transition and record its justification."""
        self._check_regulatory_authority()
        values = {"state": new_state}
        if reason:
            values["state_change_reason"] = reason
        self.write(values)
        for record in self:
            record.message_post(
                body=self.env._(
                    "Status changed to %(state)s. Reason: %(reason)s",
                    state=dict(constants.DEVICE_STATE_SELECTION).get(
                        new_state, new_state
                    ),
                    reason=reason or self.env._("not recorded"),
                )
            )
        return True

    def action_start_development(self):
        """Move a device into development.

        The transition is reachable from the draft status and from conformity
        assessment. The second case is the rework path declared in
        :data:`constants.DEVICE_ALLOWED_TRANSITIONS`: a device whose
        conformity assessment revealed a problem returns to development rather
        than staying in an assessment it can no longer complete.
        """
        allowed_sources = ("draft", "conformity_assessment")
        for record in self:
            if record.state not in allowed_sources:
                raise UserError(
                    self.env._(
                        "A device can only enter development from the draft "
                        "status or from conformity assessment. Device "
                        "'%(device)s' is in neither status.",
                        device=record.display_name,
                    )
                )
        return self._set_state("development")

    def action_start_conformity_assessment(self):
        """Move a device under development into conformity assessment."""
        for record in self:
            if record.state != "development":
                raise UserError(
                    self.env._(
                        "Only a device under development can enter conformity "
                        "assessment. Device '%(device)s' is not under "
                        "development.",
                        device=record.display_name,
                    )
                )
            if not record.intended_purpose:
                raise UserError(
                    self.env._(
                        "Record the intended purpose of device '%(device)s' "
                        "before entering conformity assessment.",
                        device=record.display_name,
                    )
                )
        return self._set_state("conformity_assessment")

    def action_place_on_market(self):
        """Declare the device placed on the market.

        The transition requires an approved technical documentation record and,
        where the risk class calls for notified body involvement, a certificate
        in an issued or valid state. Both checks reflect obligations the
        organisation must satisfy before placing a device on the market; they
        are enforced here so that the record cannot silently claim market
        status without the supporting evidence being present in the system.
        """
        today = fields.Date.context_today(self)
        for record in self:
            if record.state != "conformity_assessment":
                raise UserError(
                    self.env._(
                        "Device '%(device)s' must complete conformity "
                        "assessment before being placed on the market.",
                        device=record.display_name,
                    )
                )
            approved_files = record.technical_file_ids.filtered(
                lambda technical_file: technical_file.state == "approved"
            )
            if not approved_files:
                raise UserError(
                    self.env._(
                        "Device '%(device)s' has no approved technical "
                        "documentation record.",
                        device=record.display_name,
                    )
                )
            if record.notified_body_required and not record.active_ce_marking_id:
                raise UserError(
                    self.env._(
                        "Device '%(device)s' belongs to a risk class that "
                        "requires notified body involvement but has no "
                        "certificate in an issued or valid status.",
                        device=record.display_name,
                    )
                )
            if not record.market_placement_date:
                record.market_placement_date = today
        return self._set_state("on_market")

    def action_suspend(self):
        """Suspend a device that is on the market."""
        for record in self:
            if record.state != "on_market":
                raise UserError(
                    self.env._(
                        "Only a device on the market can be suspended. Device "
                        "'%(device)s' is not on the market.",
                        device=record.display_name,
                    )
                )
        return self._set_state("suspended")

    def action_resume(self):
        """Return a suspended device to the market."""
        for record in self:
            if record.state != "suspended":
                raise UserError(
                    self.env._(
                        "Only a suspended device can be returned to the "
                        "market. Device '%(device)s' is not suspended.",
                        device=record.display_name,
                    )
                )
        return self._set_state("on_market")

    def action_withdraw(self):
        """Withdraw the device from the market."""
        today = fields.Date.context_today(self)
        for record in self:
            if record.state not in ("on_market", "suspended"):
                raise UserError(
                    self.env._(
                        "Only a device on the market or suspended can be "
                        "withdrawn. Device '%(device)s' is in neither status.",
                        device=record.display_name,
                    )
                )
            if not record.market_withdrawal_date:
                record.market_withdrawal_date = today
        return self._set_state("withdrawn")

    def action_open_state_wizard(self):
        """Open the wizard used to record a justified status change."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Change Device Status"),
            "res_model": "ls.md.device.state.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_device_id": self.id},
        }

    def _action_open_related(self, model, name, extra_context=None):
        """Return an action listing the related records of one device."""
        self.ensure_one()
        context = {"default_device_id": self.id}
        context.update(extra_context or {})
        return {
            "type": "ir.actions.act_window",
            "name": name,
            "res_model": model,
            "view_mode": "list,form",
            "domain": [("device_id", "=", self.id)],
            "context": context,
        }

    def action_view_udi(self):
        """Open the UDI assignments of the device."""
        return self._action_open_related("ls.md.udi", self.env._("UDI Assignments"))

    def action_view_risk_assessments(self):
        """Open the risk management files of the device."""
        return self._action_open_related(
            "ls.md.risk_assessment", self.env._("Risk Management Files")
        )

    def action_view_clinical_evaluations(self):
        """Open the clinical evaluations of the device."""
        return self._action_open_related(
            "ls.md.clinical_evaluation", self.env._("Clinical Evaluations")
        )

    def action_view_technical_files(self):
        """Open the technical documentation records of the device."""
        return self._action_open_related(
            "ls.md.technical_file", self.env._("Technical Documentation")
        )

    def action_view_ce_markings(self):
        """Open the CE marking records of the device."""
        return self._action_open_related(
            "ls.md.ce_marking", self.env._("CE Marking Records")
        )

    def action_view_pms_reports(self):
        """Open the periodic post-market reports of the device."""
        return self._action_open_related(
            "ls.md.pms_report", self.env._("Periodic Post-Market Reports")
        )

    # ------------------------------------------------------------------
    # Scheduled processing
    # ------------------------------------------------------------------
    @api.model
    def _cron_check_post_market_obligations(self):
        """Raise activities for overdue post-market obligations.

        The job scans devices that are on the market or suspended and creates a
        to-do activity on each device whose periodic post-market report is past
        its due date, or whose active certificate has expired. An activity is
        created only when no open activity of the same kind already exists on
        the record, so that repeated runs do not accumulate duplicates.
        """
        today = fields.Date.context_today(self)
        devices = self.search(
            [
                ("state", "in", ("on_market", "suspended")),
                ("active", "=", True),
            ]
        )
        # ``periodic_report_overdue`` depends on the current date, which is
        # not an ORM dependency: it is recomputed and saved before use.
        periodic_fields = [
            name
            for name, field in self._fields.items()
            if field.store and field.compute == "_compute_periodic_report_status"
        ]
        for name in periodic_fields:
            self.env.add_to_compute(self._fields[name], devices)
        devices._recompute_recordset(periodic_fields)
        activity_type = self.env.ref(
            "mail.mail_activity_data_todo", raise_if_not_found=False
        )
        if not activity_type:
            return 0
        created = 0
        for device in devices:
            messages = []
            if device.periodic_report_overdue and device.next_periodic_report_due:
                messages.append(
                    self.env._(
                        "The periodic post-market report was due on %(due)s.",
                        due=device.next_periodic_report_due,
                    )
                )
            expiry = device.ce_certificate_expiry_date
            if expiry and expiry < today:
                messages.append(
                    self.env._(
                        "The active certificate expired on %(expiry)s.",
                        expiry=expiry,
                    )
                )
            if not messages:
                continue
            summary = self.env._("Post-market obligation overdue")
            existing = self.env["mail.activity"].search_count(
                [
                    ("res_model", "=", self._name),
                    ("res_id", "=", device.id),
                    ("summary", "=", summary),
                ]
            )
            if existing:
                continue
            device.activity_schedule(
                act_type_xmlid="mail.mail_activity_data_todo",
                summary=summary,
                note=" ".join(messages),
                user_id=device.create_uid.id or self.env.uid,
            )
            created += 1
        return created
