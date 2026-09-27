# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Injection moulding run execution record.

A run is the production record of one moulding campaign: which component was
moulded, on which tool and machine, against which approved parameter
specification, from which material lots, with which recorded process values
and which rejects.

The record advances through a controlled state machine. Once closed it is
frozen: no field may be modified and it cannot be deleted. Review is subject
to segregation of duties, so the operator or setter of a run may not review
it.
"""

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from ..constants import (
    PARAMETER_SPEC_EFFECTIVE_STATE,
    PRODUCTION_SHIFTS,
    QUANTITY_DIGITS,
    RUN_CANCELLABLE_STATES,
    RUN_DELETABLE_STATES,
    RUN_LOCKED_STATES,
    RUN_STATES,
    STARTUP_REQUIRED_FREQUENCIES,
    TOOL_PRODUCTION_STATE,
)


class LsMpInjectionMolding(models.Model):
    """Execution record of an injection moulding run."""

    _name = "ls.mp.injection_molding"
    _description = "Medical Plastics Injection Moulding Run"
    _check_company_auto = True
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_start desc, id desc"

    name = fields.Char(
        string="Reference",
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: self.env._("New"),
    )
    state = fields.Selection(
        selection=RUN_STATES,
        string="Status",
        default="draft",
        required=True,
        tracking=True,
        copy=False,
    )

    # -- Production context -------------------------------------------------
    component_id = fields.Many2one(comodel_name="ls.mp.component", required=True,
                                   ondelete="restrict",
                                   index=True,
                                   tracking=True,)
    tool_id = fields.Many2one(comodel_name="ls.mp.tool", required=True,
                              ondelete="restrict",
                              index=True,
                              tracking=True,)
    workcenter_id = fields.Many2one(
        comodel_name="mrp.workcenter",
        string="Work Centre",
        ondelete="restrict",
        tracking=True,
    )
    production_id = fields.Many2one(
        comodel_name="mrp.production",
        string="Manufacturing Order",
        ondelete="restrict",
        index=True,
        tracking=True,
        help="Manufacturing order the run contributes to, where one is used.",
    )
    parameter_spec_id = fields.Many2one(
        comodel_name="ls.mp.molding_parameter",
        string="Parameter Specification",
        ondelete="restrict",
        index=True,
        tracking=True,
        help="Approved moulding parameter specification applied to this run.",
    )
    parameter_spec_version = fields.Integer(
        string="Specification Version",
        readonly=True,
        copy=False,
        help="Version of the specification frozen when the run entered setup.",
    )
    lot_id = fields.Many2one(
        comodel_name="stock.lot",
        string="Produced Lot",
        ondelete="restrict",
        index=True,
        tracking=True,
        help="Lot or batch number assigned to the parts produced by this run.",
        check_company=True,
    )

    # -- Timing and personnel ----------------------------------------------
    date_start = fields.Datetime(string="Start", copy=False, tracking=True)
    date_end = fields.Datetime(string="End", copy=False, tracking=True)
    shift = fields.Selection(selection=PRODUCTION_SHIFTS)
    operator_id = fields.Many2one(comodel_name="res.users", required=True,
                                  default=lambda self: self.env.user,
                                  ondelete="restrict",
                                  tracking=True,)
    setter_id = fields.Many2one(comodel_name="res.users", ondelete="restrict",
                                tracking=True,
                                help="Technician who performed the tool setup for this run.",)

    # -- Counters -----------------------------------------------------------
    shot_count_start = fields.Integer(string="Shot Counter at Start", copy=False)
    shot_count_end = fields.Integer(string="Shot Counter at End", copy=False)
    shot_count = fields.Integer(
        string="Shots",
        compute="_compute_shot_count",
        store=True,
        help="Shots produced by this run, used to advance the tool counter.",
    )
    qty_produced = fields.Float(
        string="Quantity Produced",
        digits=QUANTITY_DIGITS,
        copy=False,
        help="Total number of parts removed from the machine, including rejects.",
    )
    qty_rejected = fields.Float(
        string="Quantity Rejected",
        digits=QUANTITY_DIGITS,
        compute="_compute_quantities",
        store=True,
    )
    qty_startup_scrap = fields.Float(
        string="Start-up Scrap",
        digits=QUANTITY_DIGITS,
        compute="_compute_quantities",
        store=True,
    )
    qty_good = fields.Float(
        string="Quantity Accepted",
        digits=QUANTITY_DIGITS,
        compute="_compute_quantities",
        store=True,
    )
    reject_rate = fields.Float(
        string="Reject Rate (%)",
        digits=(5, 2),
        compute="_compute_quantities",
        store=True,
        help=(
            "Rejected parts excluding start-up scrap, divided by the parts "
            "produced excluding start-up scrap, expressed from 0 to 100."
        ),
    )

    # -- Detail lines -------------------------------------------------------
    material_line_ids = fields.One2many(
        comodel_name="ls.mp.injection_molding.material",
        inverse_name="run_id",
        string="Material Consumption",
        copy=False,
    )
    reading_ids = fields.One2many(
        comodel_name="ls.mp.injection_molding.reading",
        inverse_name="run_id",
        string="Parameter Readings",
        copy=False,
    )
    scrap_line_ids = fields.One2many(comodel_name="ls.mp.injection_molding.scrap",
                                     inverse_name="run_id", copy=False,)
    blocked_cavity_ids = fields.Many2many(
        comodel_name="ls.mp.tool.cavity",
        relation="ls_mp_run_blocked_cavity_rel",
        column1="run_id",
        column2="cavity_id",
        string="Cavities Blocked During Run",
        domain="[('tool_id', '=', tool_id)]",
    )
    active_cavity_count = fields.Integer(
        string="Cavities in Production",
        compute="_compute_active_cavity_count",
        store=True,
    )

    reading_count = fields.Integer(compute="_compute_reading_statistics", store=True)
    out_of_tolerance_count = fields.Integer(
        string="Out of Tolerance",
        compute="_compute_reading_statistics",
        store=True,
    )
    critical_out_of_tolerance_count = fields.Integer(
        string="Critical Out of Tolerance",
        compute="_compute_reading_statistics",
        store=True,
    )
    has_deviation = fields.Boolean(
        string="Deviation Recorded",
        compute="_compute_reading_statistics",
        store=True,
    )
    deviation_reference = fields.Char(tracking=True,
                                      help=(
                                          "Reference of the deviation record raised under the site procedure. "
                                          "Recorded as free text: this module does not implement deviation "
                                          "management and does not depend on a module that does."),
                                      )

    # -- Review and closure -------------------------------------------------
    setup_by_id = fields.Many2one(comodel_name="res.users", readonly=True, copy=False,
                                  ondelete="restrict",)
    setup_date = fields.Datetime(string="Setup Completed On", readonly=True, copy=False)
    startup_verified_by_id = fields.Many2one(
        comodel_name="res.users",
        string="Start-up Verified By",
        readonly=True,
        copy=False,
        ondelete="restrict",
    )
    startup_verification_date = fields.Datetime(
        string="Start-up Verified On", readonly=True, copy=False
    )
    reviewed_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                     copy=False,
                                     ondelete="restrict",
                                     tracking=True,)
    review_date = fields.Datetime(string="Reviewed On", readonly=True, copy=False)
    review_comment = fields.Text(copy=False)
    closed_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                   copy=False,
                                   ondelete="restrict",
                                   tracking=True,)
    close_date = fields.Datetime(string="Closed On", readonly=True, copy=False)
    cancellation_reason = fields.Text(copy=False)

    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 index=True,
                                 default=lambda self: self.env.company,)
    note = fields.Text(string="Internal Notes")

    _shot_counters_non_negative = models.Constraint(
        "CHECK(shot_count_start >= 0 AND shot_count_end >= 0)",
        "Shot counters cannot be negative.",
    )
    _quantities_non_negative = models.Constraint(
        "CHECK(qty_produced >= 0)",
        "The produced quantity cannot be negative.",
    )
    _dates_consistent = models.Constraint(
        "CHECK(date_end IS NULL OR date_start IS NULL OR date_end >= date_start)",
        "The run end date cannot precede its start date.",
    )

    # -- Computes -----------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        """Assign the run reference from the sequence."""
        placeholder = self.env._("New")
        for vals in vals_list:
            if not vals.get("name") or vals.get("name") == placeholder:
                company_id = vals.get("company_id") or self.env.company.id
                vals["name"] = self.env["ir.sequence"].with_company(company_id).next_by_code(
                    "ls.mp.injection_molding"
                ) or placeholder
        return super().create(vals_list)

    @api.depends("shot_count_start", "shot_count_end")
    def _compute_shot_count(self):
        """Derive the shots produced from the machine counter readings."""
        for run in self:
            delta = run.shot_count_end - run.shot_count_start
            run.shot_count = delta if delta > 0 else 0

    @api.depends(
        "qty_produced",
        "scrap_line_ids.quantity",
        "scrap_line_ids.is_startup",
    )
    def _compute_quantities(self):
        """Split produced parts into accepted, rejected and start-up scrap."""
        for run in self:
            startup = sum(
                line.quantity for line in run.scrap_line_ids if line.is_startup
            )
            rejected = sum(
                line.quantity for line in run.scrap_line_ids if not line.is_startup
            )
            run.qty_startup_scrap = startup
            run.qty_rejected = rejected
            run.qty_good = run.qty_produced - startup - rejected
            base = run.qty_produced - startup
            run.reject_rate = (rejected / base * 100.0) if base > 0 else 0.0

    @api.depends(
        "reading_ids.in_tolerance",
        "reading_ids.is_critical",
        "reading_ids.superseded_by_ids",
    )
    def _compute_reading_statistics(self):
        """Count effective readings and out-of-tolerance results.

        Superseded readings are excluded: only the currently effective value of
        each captured reading contributes to the statistics.
        """
        for run in self:
            effective = run.reading_ids.filtered(
                lambda reading: not reading.superseded_by_ids
            )
            out_of_tolerance = effective.filtered(lambda reading: not reading.in_tolerance)
            run.reading_count = len(effective)
            run.out_of_tolerance_count = len(out_of_tolerance)
            run.critical_out_of_tolerance_count = len(
                out_of_tolerance.filtered(lambda reading: reading.is_critical)
            )
            run.has_deviation = bool(out_of_tolerance)

    @api.depends("tool_id.active_cavity_count", "blocked_cavity_ids")
    def _compute_active_cavity_count(self):
        """Cavities producing parts during the run."""
        for run in self:
            run.active_cavity_count = max(
                run.tool_id.active_cavity_count - len(run.blocked_cavity_ids), 0
            )

    @api.depends("name", "component_id.code")
    def _compute_display_name(self):
        """Render the run as ``REFERENCE - COMPONENT``."""
        for run in self:
            component_code = run.component_id.code
            run.display_name = f"{run.name} - {component_code}" if component_code else run.name

    # -- Onchange -----------------------------------------------------------

    @api.onchange("component_id")
    def _onchange_component_id(self):
        """Restrict the tool selection to tools declared for the component."""
        self.tool_id = False
        self.parameter_spec_id = False
        if self.component_id:
            return {"domain": {"tool_id": [("id", "in", self.component_id.tool_ids.ids)]}}
        return {"domain": {"tool_id": []}}

    @api.onchange("tool_id")
    def _onchange_tool_id(self):
        """Default the work centre and preselect the approved specification."""
        self.parameter_spec_id = False
        if self.tool_id:
            if not self.workcenter_id:
                self.workcenter_id = self.tool_id.workcenter_id
            self.parameter_spec_id = self._find_effective_specification()

    def _find_effective_specification(self):
        """Return the approved specification applicable to this run context.

        A specification bound to the run work centre takes precedence over a
        specification applicable to any work centre.

        :return: the applicable specification, or an empty recordset.
        :rtype: recordset of ``ls.mp.molding_parameter``
        """
        spec_model = self.env["ls.mp.molding_parameter"]
        if not (self.component_id and self.tool_id):
            return spec_model.browse()
        base_domain = [
            ("state", "=", PARAMETER_SPEC_EFFECTIVE_STATE),
            ("component_id", "=", self.component_id.id),
            ("tool_id", "=", self.tool_id.id),
        ]
        if self.workcenter_id:
            specific = spec_model.search(
                base_domain + [("workcenter_id", "=", self.workcenter_id.id)], limit=1
            )
            if specific:
                return specific
        return spec_model.search(base_domain + [("workcenter_id", "=", False)], limit=1)

    # -- Constraints --------------------------------------------------------

    @api.constrains("component_id", "tool_id")
    def _check_tool_produces_component(self):
        """The tool must be declared as producing the component."""
        for run in self:
            if run.component_id not in run.tool_id.component_ids:
                raise ValidationError(
                    self.env._(
                        "Tool %(tool)s is not declared as producing component "
                        "%(component)s.",
                        tool=run.tool_id.display_name,
                        component=run.component_id.display_name,
                    )
                )

    @api.constrains("parameter_spec_id", "component_id", "tool_id")
    def _check_specification_matches_context(self):
        """The specification must belong to the same component and tool."""
        for run in self:
            spec = run.parameter_spec_id
            if not spec:
                continue
            if spec.component_id != run.component_id or spec.tool_id != run.tool_id:
                raise ValidationError(
                    self.env._(
                        "Specification %(spec)s does not apply to component "
                        "%(component)s on tool %(tool)s.",
                        spec=spec.name,
                        component=run.component_id.display_name,
                        tool=run.tool_id.display_name,
                    )
                )
            if spec.workcenter_id and run.workcenter_id and spec.workcenter_id != run.workcenter_id:
                raise ValidationError(
                    self.env._(
                        "Specification %(spec)s is restricted to work centre "
                        "%(spec_workcenter)s and cannot be used on %(workcenter)s.",
                        spec=spec.name,
                        spec_workcenter=spec.workcenter_id.display_name,
                        workcenter=run.workcenter_id.display_name,
                    )
                )

    @api.constrains("shot_count_start", "shot_count_end", "state")
    def _check_shot_counter_progression(self):
        """The end counter cannot be lower than the start counter."""
        for run in self:
            if run.state in ("completed", "reviewed", "closed"):
                if run.shot_count_end < run.shot_count_start:
                    raise ValidationError(
                        self.env._(
                            "Run %(name)s has an end shot counter lower than its "
                            "start counter.",
                            name=run.name,
                        )
                    )

    @api.constrains("qty_produced", "scrap_line_ids")
    def _check_scrap_not_exceeding_production(self):
        """Rejected parts cannot exceed the parts produced."""
        for run in self:
            total_scrap = sum(run.scrap_line_ids.mapped("quantity"))
            if run.qty_produced and total_scrap > run.qty_produced:
                raise ValidationError(
                    self.env._(
                        "Run %(name)s records %(scrap)s rejected parts but only "
                        "%(produced)s produced.",
                        name=run.name,
                        scrap=total_scrap,
                        produced=run.qty_produced,
                    )
                )

    @api.constrains("company_id", "component_id", "tool_id")
    def _check_company_consistency(self):
        """Component and tool must belong to the run company."""
        for run in self:
            if run.component_id.company_id != run.company_id:
                raise ValidationError(
                    self.env._(
                        "Component %(component)s belongs to another company.",
                        component=run.component_id.display_name,
                    )
                )
            if run.tool_id.company_id != run.company_id:
                raise ValidationError(
                    self.env._(
                        "Tool %(tool)s belongs to another company.",
                        tool=run.tool_id.display_name,
                    )
                )

    # -- Workflow -----------------------------------------------------------

    def action_start_setup(self):
        """Move the run into setup and freeze the applicable specification."""
        for run in self:
            if run.state != "draft":
                raise ValidationError(
                    self.env._("Run %(name)s is not in draft.", name=run.name)
                )
            if run.component_id.state != "released":
                raise ValidationError(
                    self.env._(
                        "Component %(component)s is not released for production.",
                        component=run.component_id.display_name,
                    )
                )
            if run.tool_id.state != TOOL_PRODUCTION_STATE:
                raise ValidationError(
                    self.env._(
                        "Tool %(tool)s is not in service and cannot be used for "
                        "production.",
                        tool=run.tool_id.display_name,
                    )
                )
            spec = run.parameter_spec_id or run._find_effective_specification()
            if not spec:
                raise ValidationError(
                    self.env._(
                        "No approved moulding parameter specification exists for "
                        "component %(component)s on tool %(tool)s.",
                        component=run.component_id.display_name,
                        tool=run.tool_id.display_name,
                    )
                )
            if spec.state != PARAMETER_SPEC_EFFECTIVE_STATE:
                raise ValidationError(
                    self.env._(
                        "Specification %(spec)s is not approved and cannot be used.",
                        spec=spec.name,
                    )
                )
            run.write(
                {
                    "state": "setup",
                    "parameter_spec_id": spec.id,
                    "parameter_spec_version": spec.version,
                    "setter_id": run.setter_id.id or self.env.user.id,
                    "shot_count_start": run.shot_count_start or run.tool_id.total_shot_count,
                }
            )
        return True

    def action_start_startup_check(self):
        """Move the run from setup into start-up verification."""
        for run in self:
            if run.state != "setup":
                raise ValidationError(
                    self.env._("Run %(name)s is not in setup.", name=run.name)
                )
            run.write(
                {
                    "state": "startup_check",
                    "setup_by_id": self.env.user.id,
                    "setup_date": fields.Datetime.now(),
                }
            )
        return True

    def action_confirm_startup(self):
        """Confirm start-up verification and release the run to production."""
        for run in self:
            if run.state != "startup_check":
                raise ValidationError(
                    self.env._(
                        "Run %(name)s is not under start-up verification.",
                        name=run.name,
                    )
                )
            missing = run._missing_startup_parameters()
            if missing:
                raise ValidationError(
                    self.env._(
                        "Start-up verification of run %(name)s is incomplete. "
                        "Missing readings: %(missing)s.",
                        name=run.name,
                        missing=", ".join(missing),
                    )
                )
            if not run.material_line_ids:
                raise ValidationError(
                    self.env._(
                        "Run %(name)s cannot start without recorded material "
                        "consumption.",
                        name=run.name,
                    )
                )
            failing = run._failing_critical_startup_readings()
            if failing:
                raise ValidationError(
                    self.env._(
                        "Run %(name)s cannot start: critical parameters are out of "
                        "tolerance at start-up: %(params)s.",
                        name=run.name,
                        params=", ".join(failing),
                    )
                )
            run.write(
                {
                    "state": "running",
                    "startup_verified_by_id": self.env.user.id,
                    "startup_verification_date": fields.Datetime.now(),
                    "date_start": run.date_start or fields.Datetime.now(),
                }
            )
        return True

    def _missing_startup_parameters(self):
        """Return the names of parameters still awaiting a start-up reading.

        :rtype: list of str
        """
        self.ensure_one()
        required = self.parameter_spec_id.line_ids.filtered(
            lambda line: line.record_required
            and line.monitoring_frequency in STARTUP_REQUIRED_FREQUENCIES
        )
        captured = self.reading_ids.filtered(
            lambda reading: reading.reading_type in ("setup", "startup")
            and not reading.superseded_by_ids
        )
        captured_lines = captured.mapped("parameter_line_id")
        return [line.name for line in required if line not in captured_lines]

    def _failing_critical_startup_readings(self):
        """Return critical parameters that are out of tolerance at start-up.

        :rtype: list of str
        """
        self.ensure_one()
        failing = self.reading_ids.filtered(
            lambda reading: reading.reading_type in ("setup", "startup")
            and reading.is_critical
            and not reading.in_tolerance
            and not reading.superseded_by_ids
        )
        return failing.mapped("parameter_name")

    def action_complete(self):
        """Complete the run and stop production."""
        for run in self:
            if run.state != "running":
                raise ValidationError(
                    self.env._("Run %(name)s is not running.", name=run.name)
                )
            if not run.shot_count_end:
                raise ValidationError(
                    self.env._(
                        "Run %(name)s cannot be completed without the end shot "
                        "counter.",
                        name=run.name,
                    )
                )
            if run.shot_count_end < run.shot_count_start:
                raise ValidationError(
                    self.env._(
                        "Run %(name)s has an end shot counter lower than its start "
                        "counter.",
                        name=run.name,
                    )
                )
            run.write(
                {
                    "state": "completed",
                    "date_end": run.date_end or fields.Datetime.now(),
                }
            )
        return True

    def action_review(self):
        """Record the quality review of a completed run.

        Segregation of duties is enforced: the operator or setter of the run
        may not review it.
        """
        for run in self:
            if run.state != "completed":
                raise ValidationError(
                    self.env._(
                        "Run %(name)s must be completed before review.", name=run.name
                    )
                )
            if self.env.user in (run.operator_id | run.setter_id):
                raise ValidationError(
                    self.env._(
                        "The operator or setter of run %(name)s cannot review it.",
                        name=run.name,
                    )
                )
            if run.has_deviation and not run.deviation_reference:
                raise ValidationError(
                    self.env._(
                        "Run %(name)s has out-of-tolerance readings. A deviation "
                        "reference must be recorded before review.",
                        name=run.name,
                    )
                )
            run.write(
                {
                    "state": "reviewed",
                    "reviewed_by_id": self.env.user.id,
                    "review_date": fields.Datetime.now(),
                }
            )
        return True

    def action_close(self):
        """Close and freeze the run, advancing the tool shot counter."""
        for run in self:
            if run.state != "reviewed":
                raise ValidationError(
                    self.env._(
                        "Run %(name)s must be reviewed before it can be closed.",
                        name=run.name,
                    )
                )
            run.write(
                {
                    "state": "closed",
                    "closed_by_id": self.env.user.id,
                    "close_date": fields.Datetime.now(),
                }
            )
            run.tool_id._ls_recompute_stored("_compute_shot_counts")
            run.tool_id._ls_recompute_stored("_compute_maintenance_status")
        return True

    def action_return_to_draft(self):
        """Return a run in setup or start-up verification to draft."""
        for run in self:
            if run.state not in ("setup", "startup_check"):
                raise ValidationError(
                    self.env._(
                        "Run %(name)s cannot be returned to draft from status "
                        "%(state)s.",
                        name=run.name,
                        state=dict(RUN_STATES)[run.state],
                    )
                )
        return self.write(
            {
                "state": "draft",
                "setup_by_id": False,
                "setup_date": False,
                "parameter_spec_version": 0,
            }
        )

    def action_reject_review(self):
        """Send a completed run back for correction instead of reviewing it."""
        for run in self:
            if run.state != "completed":
                raise ValidationError(
                    self.env._(
                        "Only completed runs can be sent back for correction. Run "
                        "%(name)s is not completed.",
                        name=run.name,
                    )
                )
            if not run.review_comment:
                raise ValidationError(
                    self.env._(
                        "A review comment is required to send run %(name)s back for "
                        "correction.",
                        name=run.name,
                    )
                )
        return self.write({"state": "running"})

    def action_cancel(self):
        """Cancel a run that has not yet produced parts."""
        for run in self:
            if run.state not in RUN_CANCELLABLE_STATES:
                raise ValidationError(
                    self.env._(
                        "Run %(name)s is in status %(state)s and can no longer be "
                        "cancelled.",
                        name=run.name,
                        state=dict(RUN_STATES)[run.state],
                    )
                )
            if not run.cancellation_reason:
                raise ValidationError(
                    self.env._(
                        "A cancellation reason is required for run %(name)s.",
                        name=run.name,
                    )
                )
        return self.write({"state": "cancelled"})

    def action_open_reading_wizard(self):
        """Open the wizard used to capture a set of parameter readings."""
        self.ensure_one()
        if self.state not in ("setup", "startup_check", "running", "completed"):
            raise ValidationError(
                self.env._(
                    "Readings cannot be captured for run %(name)s in status "
                    "%(state)s.",
                    name=self.name,
                    state=dict(RUN_STATES)[self.state],
                )
            )
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Record Parameter Readings"),
            "res_model": "ls.mp.reading.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_run_id": self.id},
        }

    def action_view_readings(self):
        """Open the readings captured for this run."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Parameter Readings"),
            "res_model": "ls.mp.injection_molding.reading",
            "view_mode": "list,form",
            "domain": [("run_id", "=", self.id)],
        }

    # -- Immutability -------------------------------------------------------

    def write(self, vals):
        """Freeze closed runs against any further modification."""
        locked = self.filtered(lambda run: run.state in RUN_LOCKED_STATES)
        if locked and set(vals) - {"state"}:
            raise ValidationError(
                self.env._(
                    "Run %(name)s is closed and cannot be modified.",
                    name=locked[0].name,
                )
            )
        if locked and vals.get("state") in RUN_LOCKED_STATES:
            raise ValidationError(
                self.env._(
                    "Run %(name)s is closed and its status cannot be changed.",
                    name=locked[0].name,
                )
            )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_mp_injection_molding(self):
        """Allow deletion only for runs that never produced a record of value."""
        for run in self:
            if run.state not in RUN_DELETABLE_STATES:
                raise ValidationError(
                    self.env._(
                        "Run %(name)s is in status %(state)s and cannot be deleted. "
                        "Production records are retained.",
                        name=run.name,
                        state=dict(RUN_STATES)[run.state],
                    )
                )

    @api.constrains("lot_id", "production_id")
    def _check_lot_id_matches_product(self):
        """The lot must belong to the product of the manufacturing order of the record.

        :raise ValidationError: when the lot was created for another product.
        """
        for record in self:
            product = record.production_id.product_id
            if record.lot_id and product and record.lot_id.product_id != product:
                raise ValidationError(
                    self.env._(
                        "Lot %(lot)s belongs to product %(lot_product)s, not to "
                        "%(product)s.",
                        lot=record.lot_id.display_name,
                        lot_product=record.lot_id.product_id.display_name,
                        product=product.display_name,
                    )
                )
