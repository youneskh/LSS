# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Moulding tool register.

The tool register is the authoritative record of every mould, insert and
fixture used to produce medical plastic components. It carries the tool
lifecycle state, the cavity register, cumulative shot counting and the
preventive maintenance and requalification schedules.

Shot counting is derived from closed moulding runs plus an opening counter,
so the cumulative count cannot be edited directly once runs exist.
"""

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from ..constants import (
    CODE_MAX_LENGTH,
    DUE_SOON_DAYS,
    MAINTENANCE_WARNING_RATIO,
    TOOL_MAINTENANCE_STATUS,
    TOOL_PRODUCTION_STATE,
    TOOL_STATES,
    TOOL_TYPES,
)


class LsMpTool(models.Model):
    """Moulding tool master record."""

    _name = "ls.mp.tool"
    _description = "Medical Plastics Moulding Tool"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "code, name"

    name = fields.Char(string="Tool Name", required=True, tracking=True)
    code = fields.Char(
        string="Tool Code",
        required=True,
        size=CODE_MAX_LENGTH,
        index=True,
        copy=False,
        default=lambda self: self.env._("New"),
        tracking=True,
    )
    tool_type = fields.Selection(selection=TOOL_TYPES, required=True,
                                 default="injection_mold",
                                 tracking=True,)
    state = fields.Selection(
        selection=TOOL_STATES,
        string="Status",
        default="draft",
        required=True,
        tracking=True,
        copy=False,
    )

    # -- Identification -----------------------------------------------------
    manufacturer_id = fields.Many2one(
        comodel_name="res.partner",
        string="Tool Maker",
        ondelete="restrict",
        tracking=True,
    )
    serial_no = fields.Char(string="Manufacturer Serial Number", tracking=True)
    acquisition_date = fields.Date()
    steel_grade = fields.Char(string="Steel / Material of Construction")
    storage_location = fields.Char(help="Physical location where the tool is stored when not mounted.",)
    workcenter_id = fields.Many2one(
        comodel_name="mrp.workcenter",
        string="Default Work Centre",
        ondelete="restrict",
        tracking=True,
        help="Moulding machine on which the tool is normally mounted.",
    )
    component_ids = fields.Many2many(
        comodel_name="ls.mp.component",
        relation="ls_mp_tool_component_rel",
        column1="tool_id",
        column2="component_id",
        string="Components Produced",
    )

    # -- Cavities -----------------------------------------------------------
    cavity_count = fields.Integer(required=True,
                                  default=1,
                                  tracking=True,
                                  help="Total number of cavities designed into the tool.",)
    cavity_ids = fields.One2many(
        comodel_name="ls.mp.tool.cavity",
        inverse_name="tool_id",
        string="Cavity Register",
    )
    active_cavity_count = fields.Integer(
        string="Active Cavities",
        compute="_compute_cavity_statistics",
        store=True,
    )
    blocked_cavity_count = fields.Integer(
        string="Blocked Cavities",
        compute="_compute_cavity_statistics",
        store=True,
    )

    # -- Shot counting ------------------------------------------------------
    opening_shot_count = fields.Integer(default=0,
                                        tracking=True,
                                        help=(
                                            "Cumulative shot count carried over from before the tool was "
                                            "registered in this system. Recorded once at registration."),
                                        )
    recorded_shot_count = fields.Integer(
        string="Recorded Shots",
        compute="_compute_shot_counts",
        store=True,
        help="Shots accumulated from closed moulding runs on this tool.",
    )
    total_shot_count = fields.Integer(compute="_compute_shot_counts",
                                      store=True,
                                      help="Opening shot count plus shots recorded on closed moulding runs.",)
    shot_count_at_last_maintenance = fields.Integer(
        string="Shots at Last Maintenance",
        default=0,
        readonly=True,
        copy=False,
        tracking=True,
    )
    shots_since_maintenance = fields.Integer(compute="_compute_maintenance_status",
                                             store=True,)
    shots_to_next_maintenance = fields.Integer(compute="_compute_maintenance_status",
                                               store=True,)

    # -- Preventive maintenance --------------------------------------------
    maintenance_interval_shots = fields.Integer(
        string="Maintenance Interval (shots)",
        default=0,
        tracking=True,
        help="Zero disables shot-based preventive maintenance scheduling.",
    )
    maintenance_interval_months = fields.Integer(
        string="Maintenance Interval (months)",
        default=0,
        tracking=True,
        help="Zero disables calendar-based preventive maintenance scheduling.",
    )
    last_maintenance_date = fields.Date(
        string="Last Maintenance",
        readonly=True,
        copy=False,
        tracking=True,
    )
    next_maintenance_date = fields.Date(
        string="Next Maintenance Due",
        compute="_compute_maintenance_status",
        store=True,
    )
    maintenance_status = fields.Selection(selection=TOOL_MAINTENANCE_STATUS, compute="_compute_maintenance_status",
                                          store=True,)

    # -- Qualification ------------------------------------------------------
    qualification_date = fields.Date(string="Qualified On", tracking=True, copy=False)
    requalification_interval_months = fields.Integer(
        string="Requalification Interval (months)",
        default=0,
        tracking=True,
        help="Zero disables periodic requalification scheduling.",
    )
    requalification_due_date = fields.Date(
        string="Requalification Due",
        compute="_compute_requalification_due",
        store=True,
    )
    requalification_overdue = fields.Boolean(compute="_compute_requalification_due",
                                             store=True,)

    # -- Relations ----------------------------------------------------------
    maintenance_ids = fields.One2many(
        comodel_name="ls.mp.tool.maintenance",
        inverse_name="tool_id",
        string="Maintenance History",
    )
    maintenance_count = fields.Integer(compute="_compute_relation_counts",)
    run_ids = fields.One2many(
        comodel_name="ls.mp.injection_molding",
        inverse_name="tool_id",
        string="Moulding Runs",
    )
    run_count = fields.Integer(compute="_compute_relation_counts")

    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 index=True,
                                 default=lambda self: self.env.company,)
    active = fields.Boolean(default=True)
    note = fields.Text(string="Internal Notes")

    _code_company_unique = models.Constraint(
        "UNIQUE(code, company_id)",
        "The tool code must be unique per company.",
    )
    _cavity_count_positive = models.Constraint(
        "CHECK(cavity_count > 0)",
        "A tool must declare at least one cavity.",
    )
    _counters_non_negative = models.Constraint(
        "CHECK(opening_shot_count >= 0 AND shot_count_at_last_maintenance >= 0)",
        "Shot counters cannot be negative.",
    )
    _intervals_non_negative = models.Constraint(
        "CHECK("
        "maintenance_interval_shots >= 0 "
        "AND maintenance_interval_months >= 0 "
        "AND requalification_interval_months >= 0)",
        "Maintenance and requalification intervals cannot be negative.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Assign the tool code from the sequence and build the cavity register."""
        placeholder = self.env._("New")
        for vals in vals_list:
            if not vals.get("code") or vals.get("code") == placeholder:
                company_id = vals.get("company_id") or self.env.company.id
                vals["code"] = self.env["ir.sequence"].with_company(company_id).next_by_code(
                    "ls.mp.tool"
                ) or placeholder
        tools = super().create(vals_list)
        tools._synchronise_cavity_register()
        return tools

    def write(self, vals):
        """Keep the cavity register aligned with the declared cavity count."""
        result = super().write(vals)
        if "cavity_count" in vals:
            self._synchronise_cavity_register()
        return result

    def _synchronise_cavity_register(self):
        """Create the missing cavity records up to the declared cavity count.

        Existing cavities are never deleted, because a cavity that has already
        produced parts must remain traceable. Reducing the cavity count below
        the number of existing cavities is rejected by a constraint instead.
        """
        cavity_model = self.env["ls.mp.tool.cavity"]
        to_create = []
        for tool in self:
            existing_numbers = set(tool.cavity_ids.mapped("number"))
            for number in range(1, tool.cavity_count + 1):
                if number not in existing_numbers:
                    to_create.append({"tool_id": tool.id, "number": number})
        if to_create:
            cavity_model.create(to_create)
        return True

    @api.constrains("cavity_count", "cavity_ids")
    def _check_cavity_count_not_reduced(self):
        """Refuse a cavity count lower than the cavities already registered."""
        for tool in self:
            registered = tool.cavity_ids.mapped("number")
            if registered and max(registered) > tool.cavity_count:
                raise ValidationError(
                    self.env._(
                        "Tool %(tool)s already has cavity number %(number)s "
                        "registered. The cavity count cannot be reduced below it "
                        "because produced parts remain traceable to that cavity.",
                        tool=tool.display_name,
                        number=max(registered),
                    )
                )

    @api.depends("cavity_ids.state")
    def _compute_cavity_statistics(self):
        """Count active and blocked cavities."""
        for tool in self:
            tool.active_cavity_count = len(
                tool.cavity_ids.filtered(lambda cavity: cavity.state == "active")
            )
            tool.blocked_cavity_count = len(
                tool.cavity_ids.filtered(lambda cavity: cavity.state == "blocked")
            )

    @api.depends("opening_shot_count", "run_ids.shot_count", "run_ids.state")
    def _compute_shot_counts(self):
        """Accumulate shots from closed runs only.

        Only closed runs contribute, so that a run still open for correction
        cannot inflate the cumulative counter that drives maintenance.
        """
        for tool in self:
            recorded = sum(
                run.shot_count for run in tool.run_ids if run.state == "closed"
            )
            tool.recorded_shot_count = recorded
            tool.total_shot_count = tool.opening_shot_count + recorded

    @api.depends(
        "total_shot_count",
        "shot_count_at_last_maintenance",
        "maintenance_interval_shots",
        "maintenance_interval_months",
        "last_maintenance_date",
    )
    def _compute_maintenance_status(self):
        """Derive maintenance counters, due date and traffic-light status."""
        today = fields.Date.context_today(self)
        for tool in self:
            tool.shots_since_maintenance = (
                tool.total_shot_count - tool.shot_count_at_last_maintenance
            )
            if tool.maintenance_interval_shots > 0:
                tool.shots_to_next_maintenance = (
                    tool.maintenance_interval_shots - tool.shots_since_maintenance
                )
            else:
                tool.shots_to_next_maintenance = 0

            if tool.maintenance_interval_months > 0 and tool.last_maintenance_date:
                tool.next_maintenance_date = tool.last_maintenance_date + relativedelta(
                    months=tool.maintenance_interval_months
                )
            else:
                tool.next_maintenance_date = False

            tool.maintenance_status = tool._evaluate_maintenance_status(today)

    def _evaluate_maintenance_status(self, today):
        """Return the maintenance traffic-light value for this tool.

        :param datetime.date today: reference date used for the calendar rule.
        :return: one of the values declared in ``TOOL_MAINTENANCE_STATUS``.
        :rtype: str
        """
        self.ensure_one()
        shot_rule = self.maintenance_interval_shots > 0
        date_rule = self.maintenance_interval_months > 0 and bool(self.next_maintenance_date)
        if not shot_rule and not date_rule:
            return "not_applicable"

        overdue = False
        due_soon = False
        if shot_rule:
            if self.shots_since_maintenance >= self.maintenance_interval_shots:
                overdue = True
            elif self.shots_since_maintenance >= (
                self.maintenance_interval_shots * MAINTENANCE_WARNING_RATIO
            ):
                due_soon = True
        if date_rule:
            if self.next_maintenance_date <= today:
                overdue = True
            elif (self.next_maintenance_date - today).days <= DUE_SOON_DAYS:
                due_soon = True

        if overdue:
            return "overdue"
        return "due_soon" if due_soon else "ok"

    @api.depends("qualification_date", "requalification_interval_months")
    def _compute_requalification_due(self):
        """Derive the requalification due date and overdue flag."""
        today = fields.Date.context_today(self)
        for tool in self:
            if tool.qualification_date and tool.requalification_interval_months > 0:
                due = tool.qualification_date + relativedelta(
                    months=tool.requalification_interval_months
                )
                tool.requalification_due_date = due
                tool.requalification_overdue = due <= today
            else:
                tool.requalification_due_date = False
                tool.requalification_overdue = False

    @api.depends("maintenance_ids", "run_ids")
    def _compute_relation_counts(self):
        """Compute smart-button counters."""
        for tool in self:
            tool.maintenance_count = len(tool.maintenance_ids)
            tool.run_count = len(tool.run_ids)

    @api.depends("code", "name")
    def _compute_display_name(self):
        """Show the tool code together with its name."""
        for tool in self:
            tool.display_name = f"[{tool.code}] {tool.name}" if tool.code else tool.name

    @api.constrains("state", "qualification_date")
    def _check_qualification_recorded(self):
        """A tool cannot enter service without a recorded qualification date."""
        for tool in self:
            if tool.state in ("qualified", "in_service") and not tool.qualification_date:
                raise ValidationError(
                    self.env._(
                        "Tool %(tool)s cannot be qualified or placed in service "
                        "without a qualification date.",
                        tool=tool.display_name,
                    )
                )

    # -- Lifecycle actions --------------------------------------------------

    def action_qualify(self):
        """Record the tool as qualified."""
        for tool in self:
            if tool.state not in ("draft", "quarantined"):
                raise ValidationError(
                    self.env._(
                        "Tool %(tool)s cannot be qualified from status %(state)s.",
                        tool=tool.display_name,
                        state=dict(TOOL_STATES)[tool.state],
                    )
                )
            tool.write(
                {
                    "state": "qualified",
                    "qualification_date": tool.qualification_date
                    or fields.Date.context_today(tool),
                }
            )
        return True

    def action_place_in_service(self):
        """Release the tool for production."""
        for tool in self:
            if tool.state not in ("qualified", "maintenance"):
                raise ValidationError(
                    self.env._(
                        "Tool %(tool)s cannot be placed in service from status "
                        "%(state)s.",
                        tool=tool.display_name,
                        state=dict(TOOL_STATES)[tool.state],
                    )
                )
            if not tool.cavity_ids.filtered(lambda cavity: cavity.state == "active"):
                raise ValidationError(
                    self.env._(
                        "Tool %(tool)s has no active cavity and cannot be placed "
                        "in service.",
                        tool=tool.display_name,
                    )
                )
        return self.write({"state": TOOL_PRODUCTION_STATE})

    def action_send_to_maintenance(self):
        """Take the tool out of production for maintenance."""
        for tool in self:
            if tool.state not in ("in_service", "qualified"):
                raise ValidationError(
                    self.env._(
                        "Tool %(tool)s cannot be sent to maintenance from status "
                        "%(state)s.",
                        tool=tool.display_name,
                        state=dict(TOOL_STATES)[tool.state],
                    )
                )
            if tool._has_open_runs():
                raise ValidationError(
                    self.env._(
                        "Tool %(tool)s still has moulding runs in progress and "
                        "cannot be sent to maintenance.",
                        tool=tool.display_name,
                    )
                )
        return self.write({"state": "maintenance"})

    def action_quarantine(self):
        """Quarantine the tool, blocking any further production."""
        for tool in self:
            if tool.state == "decommissioned":
                raise ValidationError(
                    self.env._(
                        "Tool %(tool)s is decommissioned and cannot be quarantined.",
                        tool=tool.display_name,
                    )
                )
            if tool._has_open_runs():
                raise ValidationError(
                    self.env._(
                        "Tool %(tool)s still has moulding runs in progress and "
                        "cannot be quarantined.",
                        tool=tool.display_name,
                    )
                )
        return self.write({"state": "quarantined"})

    def action_decommission(self):
        """Permanently withdraw the tool from service."""
        for tool in self:
            if tool.state == "decommissioned":
                raise ValidationError(
                    self.env._(
                        "Tool %(tool)s is already decommissioned.",
                        tool=tool.display_name,
                    )
                )
            if tool._has_open_runs():
                raise ValidationError(
                    self.env._(
                        "Tool %(tool)s still has moulding runs in progress and "
                        "cannot be decommissioned.",
                        tool=tool.display_name,
                    )
                )
        return self.write({"state": "decommissioned", "active": False})

    def action_open_service_wizard(self):
        """Open the wizard used to return the tool to service after maintenance."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Return Tool to Service"),
            "res_model": "ls.mp.tool.service.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_tool_id": self.id},
        }

    def _has_open_runs(self):
        """Return whether the tool has runs in progress.

        A draft run has not started: the tool is not in use and the run
        cannot start its setup while the tool is not in service. Closed and
        cancelled runs are finished.

        :rtype: bool
        """
        self.ensure_one()
        return bool(
            self.env["ls.mp.injection_molding"].search_count(
                [
                    ("tool_id", "=", self.id),
                    ("state", "not in", ("draft", "closed", "cancelled")),
                ]
            )
        )

    def action_view_runs(self):
        """Open the moulding runs executed with this tool."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Moulding Runs"),
            "res_model": "ls.mp.injection_molding",
            "view_mode": "list,form",
            "domain": [("tool_id", "=", self.id)],
            "context": {"default_tool_id": self.id},
        }

    def action_view_maintenance(self):
        """Open the maintenance history of this tool."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Tool Maintenance"),
            "res_model": "ls.mp.tool.maintenance",
            "view_mode": "list,form",
            "domain": [("tool_id", "=", self.id)],
            "context": {"default_tool_id": self.id},
        }

    def _ls_recompute_stored(self, method_name):
        """Recompute and save the stored fields computed by ``method_name``.

        Calling a compute method directly does not persist the values of
        stored computed fields; the recomputation is therefore scheduled and
        run through the ORM so that the new values are written.

        :param str method_name: name of the compute method.
        """
        names = [
            name
            for name, field in self._fields.items()
            if field.store and field.compute == method_name
        ]
        for name in names:
            self.env.add_to_compute(self._fields[name], self)
        self._recompute_recordset(names)

    @api.model
    def _cron_check_tool_status(self):
        """Scheduled action flagging tools due for maintenance or requalification.

        The job recomputes the stored maintenance status of every active tool
        and logs a message on each tool whose status is overdue, so that the
        condition is visible in the record history rather than only in a view.

        :return: ``True`` once processing has completed.
        :rtype: bool
        """
        tools = self.search([("state", "in", ("qualified", "in_service"))])
        if not tools:
            return True
        tools._ls_recompute_stored("_compute_maintenance_status")
        tools._ls_recompute_stored("_compute_requalification_due")
        for tool in tools:
            messages = []
            if tool.maintenance_status == "overdue":
                messages.append(
                    self.env._("Preventive maintenance is overdue for this tool.")
                )
            if tool.requalification_overdue:
                messages.append(self.env._("Requalification is overdue for this tool."))
            if messages:
                tool.message_post(body=" ".join(messages))
        return True
