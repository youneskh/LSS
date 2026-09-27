# Copyright 2026 Life Sciences Suite
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""GxP deviation record.

The state machine implemented here follows the workflow defined in the Life
Sciences Suite Functional Specification section 7.5::

    Reported -> Assessed -> Investigation -> Disposition -> CAPA Required -> Closed

Two documented extensions to that specification are implemented:

``cancelled``
    A terminal state reachable from every non-terminal state. A deviation that
    was raised in error must be traceably voided rather than deleted, because
    deletion would break the continuity of the numbering sequence.

backward transitions
    ``assessed -> reported``, ``investigation -> assessed``,
    ``disposition -> investigation`` and ``capa_required -> disposition`` allow
    a reviewer to send a record back for rework. Every backward transition
    requires a reason which is written to :class:`~odoo.addons.ls_deviation.
    models.ls_deviation_stage_log.LsDeviationStageLog`.

Both extensions are rationalised in ``docs/05_architecture_review.md``.
"""

from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

#: Ordered workflow states. The order is used to render the status bar and to
#: determine whether a transition moves the record forwards or backwards.
STATE_SELECTION = [
    ("reported", "Reported"),
    ("assessed", "Assessed"),
    ("investigation", "Investigation"),
    ("disposition", "Disposition"),
    ("capa_required", "CAPA Required"),
    ("closed", "Closed"),
    ("cancelled", "Cancelled"),
]

#: Allowed transitions of the state machine, keyed by source state.
STATE_TRANSITIONS = {
    "reported": ("assessed", "cancelled"),
    "assessed": ("investigation", "reported", "cancelled"),
    "investigation": ("disposition", "assessed", "cancelled"),
    "disposition": ("capa_required", "closed", "investigation", "cancelled"),
    "capa_required": ("closed", "disposition", "cancelled"),
    "closed": (),
    "cancelled": (),
}

#: States in which the record is no longer editable by non-managers.
TERMINAL_STATES = ("closed", "cancelled")

SEVERITY_SELECTION = [
    ("minor", "Minor"),
    ("major", "Major"),
    ("critical", "Critical"),
]


class LsDeviation(models.Model):
    """A recorded departure from an approved procedure, specification or
    expected outcome, together with its assessment, investigation, product
    disposition and closure evidence.
    """

    _name = "ls.deviation"
    _description = "GxP Deviation"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "detection_date desc, id desc"
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
        help="Sequence-generated unique reference of the deviation record.",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
        help="Company owning this deviation record.",
    )
    active = fields.Boolean(default=True)
    color = fields.Integer(string="Colour Index")

    title = fields.Char(
        required=True,
        tracking=True,
        help="Short unambiguous description of what departed from the "
        "approved procedure, specification or expected outcome.",
    )
    description = fields.Text(
        required=True,
        tracking=True,
        help="Factual account of the event: what happened, where, when and "
        "how it was detected. Conclusions belong in the investigation.",
    )
    justification = fields.Text(
        tracking=True,
        help="Justification of the deviation as required by 21 CFR 211.100(b), "
        "which states that any deviation from written production and process "
        "control procedures shall be recorded and justified.",
    )

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------
    deviation_type_id = fields.Many2one(comodel_name="ls.deviation.type", required=True,
                                        tracking=True,
                                        ondelete="restrict",
                                        check_company=True,)
    category_id = fields.Many2one(comodel_name="ls.deviation.category", required=True,
                                  tracking=True,
                                  ondelete="restrict",
                                  check_company=True,)
    tag_ids = fields.Many2many(
        comodel_name="ls.deviation.tag",
        string="Tags",
    )
    severity = fields.Selection(
        selection=SEVERITY_SELECTION,
        tracking=True,
        help="Critical: deviation that has or may have an impact on patient "
        "safety, product efficacy or regulatory commitments. "
        "Major: deviation affecting product quality without direct patient "
        "safety impact. "
        "Minor: deviation with no impact on product quality.",
    )
    is_planned = fields.Boolean(
        string="Planned Deviation",
        tracking=True,
        help="A planned deviation is authorised before the event occurs. It "
        "must be justified and approved prior to execution.",
    )

    # ------------------------------------------------------------------
    # Chronology
    # ------------------------------------------------------------------
    occurrence_date = fields.Datetime(
        required=True,
        tracking=True,
        help="Date and time at which the deviating event actually occurred.",
    )
    detection_date = fields.Datetime(
        required=True,
        default=fields.Datetime.now,
        tracking=True,
        help="Date and time at which the deviation was detected.",
    )
    report_date = fields.Datetime(
        readonly=True,
        copy=False,
        default=fields.Datetime.now,
        help="Date and time at which the deviation was recorded in the system.",
    )
    due_date = fields.Date(
        string="Target Closure Date",
        tracking=True,
        copy=False,
        help="Date by which the deviation is expected to be closed. Computed "
        "from the severity when the severity is first set, and thereafter "
        "changeable only through the due date extension wizard.",
    )
    closure_date = fields.Datetime(readonly=True, copy=False, tracking=True)

    days_open = fields.Integer(
        compute="_compute_days_open",
        help="Whole days between detection and closure, or between detection "
        "and today for a record that is still open.",
    )
    is_overdue = fields.Boolean(
        compute="_compute_is_overdue",
        search="_search_is_overdue",
        help="Set when an open deviation has passed its target closure date.",
    )

    # ------------------------------------------------------------------
    # People
    # ------------------------------------------------------------------
    reporter_id = fields.Many2one(
        comodel_name="res.users",
        string="Reported By",
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
        ondelete="restrict",
    )
    owner_id = fields.Many2one(
        comodel_name="res.users",
        string="Assigned Investigator",
        tracking=True,
        ondelete="restrict",
        help="User accountable for progressing the investigation.",
    )
    qa_reviewer_id = fields.Many2one(
        comodel_name="res.users",
        string="QA Reviewer",
        tracking=True,
        ondelete="restrict",
        help="Quality Assurance representative accountable for the closure "
        "decision.",
    )
    department_id = fields.Many2one(comodel_name="hr.department", tracking=True,
                                    ondelete="restrict",
                                    check_company=True,
                                    help="Department in which the deviation occurred.",)

    # ------------------------------------------------------------------
    # Subject of the deviation
    # ------------------------------------------------------------------
    product_id = fields.Many2one(comodel_name="product.product", tracking=True,
                                 ondelete="restrict",
                                 check_company=True,)
    lot_ids = fields.Many2many(
        comodel_name="stock.lot",
        relation="ls_deviation_affected_lot_rel",
        column1="deviation_id",
        column2="lot_id",
        string="Affected Lots/Serials",
        check_company=True,
        help="Lots or serial numbers directly affected by the deviation.",
    )
    other_batches_lot_ids = fields.Many2many(
        comodel_name="stock.lot",
        relation="ls_deviation_other_lot_rel",
        column1="deviation_id",
        column2="lot_id",
        string="Other Batches Evaluated",
        check_company=True,
        help="Other batches evaluated for association with this deviation. "
        "21 CFR 211.192 requires the investigation to extend to other batches "
        "of the same drug product and to other drug products that may have "
        "been associated with the specific failure or discrepancy.",
    )
    extension_rationale = fields.Text(help="Documented rationale for the scope of the extension to other "
                                      "batches and products, including the rationale where no extension was "
                                      "considered necessary (21 CFR 211.192).",
                                      )
    production_id = fields.Many2one(
        comodel_name="mrp.production",
        string="Manufacturing Order",
        tracking=True,
        ondelete="restrict",
        check_company=True,
    )
    equipment_id = fields.Many2one(comodel_name="maintenance.equipment", tracking=True,
                                   ondelete="restrict",
                                   check_company=True,)
    location_id = fields.Many2one(comodel_name="stock.location", tracking=True,
                                  ondelete="restrict",
                                  check_company=True,)
    quantity_affected = fields.Float(
        digits="Product Unit of Measure",
        help="Quantity of product affected, expressed in the unit of measure "
        "of the product.",
    )
    product_uom_id = fields.Many2one(
        comodel_name="uom.uom",
        string="Unit of Measure",
        compute="_compute_product_uom_id",
        store=True,
        readonly=True,
    )

    # ------------------------------------------------------------------
    # Impact assessment
    # ------------------------------------------------------------------
    impact_patient_safety = fields.Boolean(tracking=True)
    impact_product_quality = fields.Boolean(tracking=True)
    impact_regulatory = fields.Boolean(tracking=True)
    impact_validation = fields.Boolean(tracking=True)
    impact_other_batches = fields.Boolean(tracking=True)
    impact_assessment = fields.Text(
        help="Reasoned assessment supporting the impact flags above.",
    )
    impact_assessed_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                            copy=False,
                                            ondelete="restrict",)
    impact_assessment_date = fields.Datetime(readonly=True, copy=False)
    has_impact = fields.Boolean(
        compute="_compute_has_impact",
        store=True,
        help="Set when at least one impact flag is set. Drives the "
        "requirement for a product disposition.",
    )

    # ------------------------------------------------------------------
    # Related records
    # ------------------------------------------------------------------
    immediate_action_ids = fields.One2many(
        comodel_name="ls.deviation.action",
        inverse_name="deviation_id",
        string="Immediate Actions",
    )
    investigation_ids = fields.One2many(
        comodel_name="ls.deviation.investigation",
        inverse_name="deviation_id",
        string="Investigations",
    )
    disposition_ids = fields.One2many(
        comodel_name="ls.deviation.disposition",
        inverse_name="deviation_id",
        string="Dispositions",
    )
    stage_log_ids = fields.One2many(
        comodel_name="ls.deviation.stage.log",
        inverse_name="deviation_id",
        string="Transition Log",
        readonly=True,
    )
    investigation_count = fields.Integer(compute="_compute_related_counts")
    disposition_count = fields.Integer(compute="_compute_related_counts")
    action_count = fields.Integer(compute="_compute_related_counts")

    # ------------------------------------------------------------------
    # CAPA linkage
    # ------------------------------------------------------------------
    capa_required = fields.Boolean(tracking=True,
                                   help="Set when the investigation concludes that corrective and/or "
                                   "preventive action beyond the immediate actions is necessary.",)
    capa_decision_rationale = fields.Text(
        help="Rationale for requiring, or for not requiring, a CAPA.",
    )
    capa_reference = fields.Char(tracking=True,
                                 help="External reference of the CAPA record. This module does not "
                                 "depend on a CAPA module; see docs/04_technical_specification.md for "
                                 "the documented integration hook.",)

    # ------------------------------------------------------------------
    # Closure
    # ------------------------------------------------------------------
    conclusion = fields.Text(
        help="Conclusions of the investigation. 21 CFR 211.192 requires a "
        "written record of the investigation including the conclusions and "
        "follow-up.",
    )
    followup = fields.Text(
        string="Follow-up",
        help="Follow-up recorded with the conclusions (21 CFR 211.192).",
    )
    closed_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                   copy=False,
                                   ondelete="restrict",)
    cancel_reason = fields.Text(readonly=True, copy=False)

    state = fields.Selection(
        selection=STATE_SELECTION,
        required=True,
        default="reported",
        tracking=True,
        copy=False,
        index=True,
        group_expand="_group_expand_state",
    )

    _name_company_uniq = models.Constraint(
        "UNIQUE(name, company_id)",
        "The deviation reference must be unique per company.",
    )
    _quantity_affected_positive = models.Constraint(
        "CHECK(quantity_affected >= 0)",
        "The affected quantity cannot be negative.",
    )

    # ------------------------------------------------------------------
    # Compute methods
    # ------------------------------------------------------------------
    @api.depends("product_id")
    def _compute_product_uom_id(self):
        """Mirror the product unit of measure onto the deviation."""
        for record in self:
            record.product_uom_id = record.product_id.uom_id

    @api.depends(
        "impact_patient_safety",
        "impact_product_quality",
        "impact_regulatory",
        "impact_validation",
        "impact_other_batches",
    )
    def _compute_has_impact(self):
        """Set :attr:`has_impact` when any individual impact flag is set."""
        for record in self:
            record.has_impact = any(
                (
                    record.impact_patient_safety,
                    record.impact_product_quality,
                    record.impact_regulatory,
                    record.impact_validation,
                    record.impact_other_batches,
                )
            )

    @api.depends("detection_date", "closure_date")
    def _compute_days_open(self):
        """Compute elapsed days between detection and closure or today."""
        now = fields.Datetime.now()
        for record in self:
            if not record.detection_date:
                record.days_open = 0
                continue
            end = record.closure_date or now
            record.days_open = max((end - record.detection_date).days, 0)

    @api.depends("due_date", "state")
    def _compute_is_overdue(self):
        """Flag open records whose target closure date has passed."""
        today = fields.Date.context_today(self)
        for record in self:
            record.is_overdue = bool(
                record.due_date
                and record.state not in TERMINAL_STATES
                and record.due_date < today
            )

    def _search_is_overdue(self, operator, value):
        """Search implementation for the non-stored :attr:`is_overdue`."""
        if operator not in ("=", "!="):
            raise UserError(
                _("The Overdue filter only supports the = and != operators.")
            )
        overdue_domain = [
            ("due_date", "<", fields.Date.context_today(self)),
            ("due_date", "!=", False),
            ("state", "not in", list(TERMINAL_STATES)),
        ]
        looking_for_overdue = (operator == "=") == bool(value)
        if looking_for_overdue:
            return overdue_domain
        return ["!"] + overdue_domain

    @api.depends("investigation_ids", "disposition_ids", "immediate_action_ids")
    def _compute_related_counts(self):
        """Compute smart-button counters."""
        for record in self:
            record.investigation_count = len(record.investigation_ids)
            record.disposition_count = len(record.disposition_ids)
            record.action_count = len(record.immediate_action_ids)

    @api.model
    def _group_expand_state(self, states, domain):
        """Always display every workflow column in the kanban view."""
        return [key for key, _label in STATE_SELECTION]

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("occurrence_date", "detection_date", "report_date")
    def _check_chronology(self):
        """Occurrence must precede detection, which must precede reporting."""
        for record in self:
            if record.occurrence_date > record.detection_date:
                raise ValidationError(
                    _(
                        "Deviation %(ref)s: the occurrence date cannot be later "
                        "than the detection date.",
                        ref=record.name,
                    )
                )
            if record.report_date and record.detection_date > record.report_date:
                raise ValidationError(
                    _(
                        "Deviation %(ref)s: the detection date cannot be later "
                        "than the date the deviation was recorded.",
                        ref=record.name,
                    )
                )

    @api.constrains("is_planned", "justification")
    def _check_planned_justification(self):
        """A planned deviation must carry its justification from the start."""
        for record in self:
            if record.is_planned and not (record.justification or "").strip():
                raise ValidationError(
                    _(
                        "Deviation %(ref)s is flagged as planned and therefore "
                        "requires a justification recorded before execution.",
                        ref=record.name,
                    )
                )

    @api.constrains("quantity_affected", "product_id")
    def _check_quantity_requires_product(self):
        """An affected quantity is meaningless without a product."""
        for record in self:
            if record.quantity_affected and not record.product_id:
                raise ValidationError(
                    _(
                        "Deviation %(ref)s: an affected quantity requires a "
                        "product to be selected.",
                        ref=record.name,
                    )
                )

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Assign the per-company sequence and log the initial state."""
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                company_id = vals.get("company_id", self.env.company.id)
                sequence = (
                    self.env["ir.sequence"]
                    .with_company(company_id)
                    .next_by_code("ls.deviation")
                )
                vals["name"] = sequence or _("New")
        records = super().create(vals_list)
        for record in records:
            record._log_transition(False, record.state, _("Deviation recorded"))
        return records

    def write(self, vals):
        """Block edition of terminal records except for managers."""
        protected = self.filtered(lambda rec: rec.state in TERMINAL_STATES)
        if protected and not self.env.user.has_group(
            "ls_deviation.group_ls_deviation_manager"
        ):
            allowed = {"message_follower_ids", "activity_ids", "color"}
            if set(vals) - allowed:
                raise UserError(
                    _(
                        "Deviation %(ref)s is %(state)s and can no longer be "
                        "modified.",
                        ref=protected[0].name,
                        state=protected[0].state,
                    )
                )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_not_reported(self):
        """Prevent destruction of the GxP record trail.

        Only a deviation still in ``reported`` state may be deleted, and only
        by a manager. Anything further along the workflow must be cancelled so
        that the reference number and its history remain traceable.
        """
        for record in self:
            if record.state != "reported":
                raise UserError(
                    _(
                        "Deviation %(ref)s cannot be deleted because it has "
                        "progressed beyond the Reported state. Cancel it "
                        "instead so that the record remains traceable.",
                        ref=record.name,
                    )
                )

    def copy_data(self, default=None):
        """Reset workflow evidence when duplicating a deviation."""
        default = dict(default or {})
        vals_list = super().copy_data(default=default)
        for vals in vals_list:
            vals.setdefault("state", "reported")
            vals.setdefault("name", _("New"))
        return vals_list

    # ------------------------------------------------------------------
    # State machine
    # ------------------------------------------------------------------
    def _log_transition(self, from_state, to_state, reason):
        """Write an immutable transition log entry."""
        self.ensure_one()
        self.env["ls.deviation.stage.log"].sudo().create(
            {
                "deviation_id": self.id,
                "from_state": from_state or False,
                "to_state": to_state,
                "user_id": self.env.user.id,
                "reason": reason,
            }
        )

    def _check_transition_allowed(self, target_state):
        """Raise when ``target_state`` is not reachable from the current one."""
        self.ensure_one()
        allowed = STATE_TRANSITIONS.get(self.state, ())
        if target_state not in allowed:
            raise UserError(
                _(
                    "Deviation %(ref)s cannot move from %(source)s to "
                    "%(target)s.",
                    ref=self.name,
                    source=self.state,
                    target=target_state,
                )
            )

    def _apply_transition(self, target_state, reason):
        """Validate, perform and log a state transition."""
        for record in self:
            record._check_transition_allowed(target_state)
            source = record.state
            record.state = target_state
            record._log_transition(source, target_state, reason)
        return True

    def action_assess(self):
        """Move from ``reported`` to ``assessed``.

        Requires the severity, the impact assessment narrative and an assigned
        investigator, which together constitute the assessment record.
        """
        for record in self:
            if not record.severity:
                raise UserError(
                    _(
                        "Deviation %(ref)s requires a severity before it can be "
                        "assessed.",
                        ref=record.name,
                    )
                )
            if not (record.impact_assessment or "").strip():
                raise UserError(
                    _(
                        "Deviation %(ref)s requires a documented impact "
                        "assessment before it can be assessed.",
                        ref=record.name,
                    )
                )
            if not record.owner_id:
                raise UserError(
                    _(
                        "Deviation %(ref)s requires an assigned investigator "
                        "before it can be assessed.",
                        ref=record.name,
                    )
                )
            record.write(
                {
                    "impact_assessed_by_id": self.env.user.id,
                    "impact_assessment_date": fields.Datetime.now(),
                }
            )
        return self._apply_transition("assessed", _("Impact assessment completed"))

    def action_start_investigation(self):
        """Move from ``assessed`` to ``investigation``."""
        for record in self:
            if not record.investigation_ids:
                raise UserError(
                    _(
                        "Deviation %(ref)s requires at least one investigation "
                        "record before the investigation can start.",
                        ref=record.name,
                    )
                )
        return self._apply_transition("investigation", _("Investigation started"))

    def action_disposition(self):
        """Move from ``investigation`` to ``disposition``.

        The investigation must be complete, and where the deviation was
        assessed as having an impact a product disposition must exist. The
        extension rationale required by 21 CFR 211.192 is mandatory.
        """
        for record in self:
            unfinished = record.investigation_ids.filtered(
                lambda inv: inv.state != "completed"
            )
            if unfinished:
                raise UserError(
                    _(
                        "Deviation %(ref)s has an investigation that is not "
                        "completed.",
                        ref=record.name,
                    )
                )
            if not (record.extension_rationale or "").strip():
                raise UserError(
                    _(
                        "Deviation %(ref)s requires a documented rationale for "
                        "the extension of the investigation to other batches "
                        "and products.",
                        ref=record.name,
                    )
                )
            if record.has_impact and not record.disposition_ids:
                raise UserError(
                    _(
                        "Deviation %(ref)s was assessed as having an impact and "
                        "therefore requires at least one product disposition.",
                        ref=record.name,
                    )
                )
        return self._apply_transition("disposition", _("Disposition stage entered"))

    def action_require_capa(self):
        """Move from ``disposition`` to ``capa_required``."""
        for record in self:
            if not (record.capa_decision_rationale or "").strip():
                raise UserError(
                    _(
                        "Deviation %(ref)s requires a rationale for the CAPA "
                        "decision.",
                        ref=record.name,
                    )
                )
            record.capa_required = True
        return self._apply_transition("capa_required", _("CAPA required"))

    def action_send_back(self):
        """Open the wizard used to return a record to the previous state."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Send Back"),
            "res_model": "ls.deviation.cancel.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_deviation_id": self.id,
                "default_mode": "send_back",
            },
        }

    def action_open_close_wizard(self):
        """Open the closure wizard."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Close Deviation"),
            "res_model": "ls.deviation.close.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_deviation_id": self.id},
        }

    def action_open_cancel_wizard(self):
        """Open the cancellation wizard."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Cancel Deviation"),
            "res_model": "ls.deviation.cancel.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_deviation_id": self.id,
                "default_mode": "cancel",
            },
        }

    def action_open_due_date_wizard(self):
        """Open the target closure date extension wizard."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Extend Target Closure Date"),
            "res_model": "ls.deviation.due.date.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_deviation_id": self.id},
        }

    # ------------------------------------------------------------------
    # Messaging
    # ------------------------------------------------------------------
    def _track_subtype(self, init_values):
        """Route closure and cancellation to their dedicated subtypes.

        Followers may subscribe to closures and cancellations without
        receiving every intermediate workflow notification.
        """
        self.ensure_one()
        if "state" in init_values:
            if self.state == "closed":
                return self.env.ref("ls_deviation.mt_deviation_closed")
            if self.state == "cancelled":
                return self.env.ref("ls_deviation.mt_deviation_cancelled")
        return super()._track_subtype(init_values)

    # ------------------------------------------------------------------
    # Onchange
    # ------------------------------------------------------------------
    @api.onchange("severity")
    def _onchange_severity_set_due_date(self):
        """Propose a target closure date derived from company settings."""
        for record in self:
            if not record.severity or record.due_date:
                continue
            days = record.company_id._ls_deviation_target_days(record.severity)
            base = record.detection_date or fields.Datetime.now()
            record.due_date = fields.Date.to_date(base) + timedelta(days=days)

    @api.onchange("production_id")
    def _onchange_production_id(self):
        """Default the product from the selected manufacturing order."""
        for record in self:
            if record.production_id and not record.product_id:
                record.product_id = record.production_id.product_id

    # ------------------------------------------------------------------
    # Scheduled actions
    # ------------------------------------------------------------------
    @api.model
    def _cron_notify_overdue(self):
        """Notify owners and QA reviewers of overdue open deviations.

        Called by the ``ir.cron`` record defined in
        ``data/ir_cron_data.xml``. Returns the number of deviations notified so
        that the behaviour is assertable from tests.
        """
        overdue = self.search(
            [
                ("state", "not in", list(TERMINAL_STATES)),
                ("due_date", "!=", False),
                ("due_date", "<", fields.Date.context_today(self)),
            ]
        )
        template = self.env.ref(
            "ls_deviation.mail_template_deviation_overdue",
            raise_if_not_found=False,
        )
        for record in overdue:
            recipients = record.owner_id | record.qa_reviewer_id
            if recipients:
                record.message_subscribe(partner_ids=recipients.partner_id.ids)
            if template:
                template.send_mail(record.id)
        return len(overdue)
