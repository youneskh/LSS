# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Validation item: the equipment, process, method or system being validated.

The item is the inventory entry that carries the *current validation status*
of a subject. The status is derived from the approved Validation Summary
Reports linked to the item, never entered manually, so that the status shown
in the system is always traceable to an approved and signed report.
"""

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from .ls_validation_constants import (
    CRITICALITY,
    DEFAULT_EXPIRY_NOTICE_DAYS,
    GXP_IMPACT,
    ITEM_TYPES,
    PARAM_EXPIRY_NOTICE_DAYS,
    VALIDATION_STATE,
)


class LsValidationItem(models.Model):
    """Subject of a validation lifecycle."""

    _name = "ls.validation.item"
    _description = "Validation Item"
    _inherit = [
        "mail.thread",
        "mail.activity.mixin",
        "ls.validation.signature.mixin",
    ]
    _order = "code, id"
    _check_company_auto = True

    code = fields.Char(
        string="Identification Code",
        required=True,
        tracking=True,
        help="Unique identification of the item, for example the equipment "
             "number used on the shop floor.",
    )
    name = fields.Char(
        string="Designation",
        required=True,
        tracking=True,
    )
    active = fields.Boolean(default=True)
    item_type = fields.Selection(selection=ITEM_TYPES, required=True,
                                 default="equipment",
                                 tracking=True,)
    description = fields.Text()
    gxp_impact = fields.Selection(selection=GXP_IMPACT, required=True,
                                  default="direct",
                                  tracking=True,
                                  help="Result of the impact assessment. Items with a direct impact on "
                                  "product quality or patient safety require qualification.",)
    criticality = fields.Selection(selection=CRITICALITY, required=True,
                                   default="medium",
                                   tracking=True,)
    manufacturer = fields.Char()
    model_reference = fields.Char(string="Model")
    serial_number = fields.Char()
    location = fields.Char()
    department = fields.Char()
    responsible_user_id = fields.Many2one(
        comodel_name="res.users",
        string="System Owner",
        tracking=True,
        default=lambda self: self.env.user,
    )
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,)

    revalidation_interval_months = fields.Integer(
        string="Periodic Review Interval (months)",
        default=36,
        tracking=True,
        help="Interval used to propose the next periodic review date. "
             "Set to 0 when no periodic review is applicable.",
    )
    retired = fields.Boolean(tracking=True, copy=False)
    retirement_date = fields.Date(tracking=True, copy=False)
    retirement_reason = fields.Text(copy=False)

    protocol_ids = fields.One2many(
        comodel_name="ls.validation.protocol",
        inverse_name="item_id",
        string="Protocols",
    )
    protocol_count = fields.Integer(compute="_compute_protocol_count",)
    report_ids = fields.One2many(
        comodel_name="ls.validation.report",
        inverse_name="item_id",
        string="Validation Reports",
    )
    report_count = fields.Integer(compute="_compute_report_count",)
    current_report_id = fields.Many2one(
        comodel_name="ls.validation.report",
        string="Current Validation Report",
        compute="_compute_validation_status",
        store=True,
        help="Latest approved Validation Summary Report that grants the "
             "current validated status.",
    )
    valid_from = fields.Date(compute="_compute_validation_status",
                             store=True,)
    valid_until = fields.Date(compute="_compute_validation_status",
                              store=True,)
    validation_state = fields.Selection(
        selection=VALIDATION_STATE,
        string="Validation Status",
        compute="_compute_validation_status",
        store=True,
        default="not_validated",
        tracking=True,
    )
    days_to_expiry = fields.Integer(compute="_compute_days_to_expiry",)

    _unique_code_company = models.Constraint(
        "UNIQUE(code, company_id)",
        "The identification code must be unique per company.",
    )
    _positive_interval = models.Constraint(
        "CHECK(revalidation_interval_months >= 0)",
        "The periodic review interval cannot be negative.",
    )

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------
    @api.depends("code", "name")
    def _compute_display_name(self):
        """Display the item as ``[CODE] Designation``."""
        for item in self:
            item.display_name = "[%s] %s" % (item.code or "", item.name or "")

    @api.depends("protocol_ids")
    def _compute_protocol_count(self):
        """Count the protocols attached to the item."""
        data = self.env["ls.validation.protocol"]._read_group(
            [("item_id", "in", self.ids)], groupby=["item_id"], aggregates=["__count"]
        )
        mapped = {item.id: count for item, count in data}
        for item in self:
            item.protocol_count = mapped.get(item.id, 0)

    @api.depends("report_ids")
    def _compute_report_count(self):
        """Count the validation summary reports attached to the item."""
        data = self.env["ls.validation.report"]._read_group(
            [("item_id", "in", self.ids)], groupby=["item_id"], aggregates=["__count"]
        )
        mapped = {item.id: count for item, count in data}
        for item in self:
            item.report_count = mapped.get(item.id, 0)

    @api.model
    def _expiry_notice_days(self):
        """Return the number of days before expiry raising a warning status."""
        value = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(PARAM_EXPIRY_NOTICE_DAYS, DEFAULT_EXPIRY_NOTICE_DAYS)
        )
        try:
            return int(value)
        except (TypeError, ValueError):
            return DEFAULT_EXPIRY_NOTICE_DAYS

    @api.depends(
        "retired",
        "report_ids.state",
        "report_ids.conclusion",
        "report_ids.valid_from",
        "report_ids.valid_until",
        "protocol_ids.state",
    )
    def _compute_validation_status(self):
        """Derive the validation status from approved reports and protocols.

        Precedence, evaluated in this order:

        1. ``retired``    - the item was formally retired;
        2. ``validated``  - an approved report is in force today;
        3. ``expiring``   - an approved report is in force but expires within
           the configured notice period;
        4. ``expired``    - the last approved report is no longer in force;
        5. ``in_validation`` - at least one protocol is approved or under
           execution;
        6. ``not_validated`` - none of the above.
        """
        today = fields.Date.context_today(self)
        notice_days = self._expiry_notice_days()
        for item in self:
            item.current_report_id = False
            item.valid_from = False
            item.valid_until = False
            if item.retired:
                item.validation_state = "retired"
                continue
            approved = item.report_ids.filtered(
                lambda report: report.state == "approved"
                and report.conclusion in ("validated", "validated_restricted")
            ).sorted(key=lambda report: (report.valid_from or today, report.id))
            current = approved[-1] if approved else False
            if current:
                item.current_report_id = current
                item.valid_from = current.valid_from
                item.valid_until = current.valid_until
                if current.valid_until and current.valid_until < today:
                    item.validation_state = "expired"
                elif (
                    current.valid_until
                    and (current.valid_until - today).days <= notice_days
                ):
                    item.validation_state = "expiring"
                else:
                    item.validation_state = "validated"
                continue
            in_progress = item.protocol_ids.filtered(
                lambda protocol: protocol.state in ("approved", "execution", "executed")
            )
            item.validation_state = (
                "in_validation" if in_progress else "not_validated"
            )

    @api.depends("valid_until")
    def _compute_days_to_expiry(self):
        """Number of days remaining before the validated status expires."""
        today = fields.Date.context_today(self)
        for item in self:
            item.days_to_expiry = (
                (item.valid_until - today).days if item.valid_until else 0
            )

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("retired", "retirement_date")
    def _check_retirement(self):
        """A retired item must carry a retirement date."""
        for item in self:
            if item.retired and not item.retirement_date:
                raise ValidationError(
                    _("A retirement date is required to retire item %s.")
                    % item.display_name
                )

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def action_retire(self):
        """Retire the item and log the decision in the chatter."""
        for item in self:
            if item.retired:
                raise UserError(
                    _("Item %s is already retired.") % item.display_name
                )
            item.write(
                {
                    "retired": True,
                    "retirement_date": fields.Date.context_today(item),
                }
            )
            item.message_post(body=_("Item retired."))
        return True

    def action_reinstate(self):
        """Cancel the retirement of an item."""
        for item in self:
            if not item.retired:
                raise UserError(
                    _("Item %s is not retired.") % item.display_name
                )
            item.write({"retired": False, "retirement_date": False})
            item.message_post(body=_("Retirement cancelled."))
        return True

    def action_view_protocols(self):
        """Open the protocols of the item."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Protocols"),
            "res_model": "ls.validation.protocol",
            "view_mode": "list,form",
            "domain": [("item_id", "=", self.id)],
            "context": {"default_item_id": self.id},
        }

    def action_view_reports(self):
        """Open the validation summary reports of the item."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Validation Reports"),
            "res_model": "ls.validation.report",
            "view_mode": "list,form",
            "domain": [("item_id", "=", self.id)],
            "context": {"default_item_id": self.id},
        }

    def action_plan_revalidation(self):
        """Open the revalidation wizard for the selected items."""
        return {
            "type": "ir.actions.act_window",
            "name": _("Plan Revalidation"),
            "res_model": "ls.validation.revalidation.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_item_id": self.id if len(self) == 1 else False},
        }

    # ------------------------------------------------------------------
    # Scheduled action
    # ------------------------------------------------------------------
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
    def _cron_refresh_validation_status(self):
        """Refresh statuses and schedule activities for expiring validations.

        ``validation_state`` depends on the current date, therefore a stored
        computed field must be refreshed daily. The method then schedules one
        activity per item entering the notice window or already expired, and
        avoids creating a second activity when one is already open.

        :return: the number of items whose status changed.
        :rtype: int
        """
        items = self.search([("retired", "=", False)])
        previous = {item.id: item.validation_state for item in items}
        items._ls_recompute_stored("_compute_validation_status")
        self.env.flush_all()
        changed = 0
        for item in items:
            if previous.get(item.id) != item.validation_state:
                changed += 1
            if item.validation_state in ("expiring", "expired"):
                item._schedule_revalidation_activity()
        return changed

    def _schedule_revalidation_activity(self):
        """Schedule a to-do activity for the system owner, once per period."""
        self.ensure_one()
        activity_type = self.env.ref(
            "mail.mail_activity_data_todo", raise_if_not_found=False
        )
        if not activity_type:
            return False
        existing = self.env["mail.activity"].search_count(
            [
                ("res_model", "=", self._name),
                ("res_id", "=", self.id),
                ("activity_type_id", "=", activity_type.id),
                ("summary", "=", _("Revalidation due")),
            ]
        )
        if existing:
            return False
        deadline = self.valid_until or fields.Date.context_today(self)
        self.activity_schedule(
            act_type_xmlid="mail.mail_activity_data_todo",
            date_deadline=deadline,
            summary=_("Revalidation due"),
            note=_(
                "The validated status of this item expires on %s. "
                "Plan the revalidation activities."
            )
            % (deadline,),
            user_id=(self.responsible_user_id or self.env.user).id,
        )
        return True

    def _next_review_date(self):
        """Return the proposed next periodic review date."""
        self.ensure_one()
        if not self.revalidation_interval_months:
            return False
        anchor = self.valid_from or fields.Date.context_today(self)
        return anchor + relativedelta(months=self.revalidation_interval_months)
