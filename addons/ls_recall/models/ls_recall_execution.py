# Part of the Life Sciences Suite for Odoo 19 Community Edition.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Recall execution.

The execution record is a single field action: a recall, a market
withdrawal, a stock recovery, a field safety corrective action or a mock
recall. It carries the decision (why, how far, how urgently), the traced
distribution, the communications issued, the effectiveness checks
performed and the reports produced.

The state machine is deliberately gated: each forward transition asserts
that the evidence required by the next phase already exists in the
database, so that the sequence of states is a factual record of what was
done rather than a label a user can set at will.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from .constants import (
    ACTION_TYPE_SELECTION,
    CLASSIFICATION_HELP,
    CLASSIFICATION_SELECTION,
    DEPTH_SELECTION,
    EFFECTIVENESS_LEVEL_COVERAGE,
    EFFECTIVENESS_LEVEL_SELECTION,
    EFFECTIVENESS_SUCCESS_OUTCOMES,
    EXECUTION_FINAL_STATES,
    EXECUTION_FORWARD_PATH,
    EXECUTION_LOCKED_AFTER_INITIATION,
    EXECUTION_STATE_SELECTION,
    PUBLIC_WARNING_SELECTION,
    REAL_ACTION_TYPES,
)

#: Location usages that represent product having left the organisation's
#: direct control. A stock recovery, by definition (21 CFR 7.3(k)),
#: concerns product that has *not* left that control and therefore does
#: not use this list.
EXTERNAL_LOCATION_USAGES = ("customer",)


class LsRecallExecution(models.Model):
    """A single recall, withdrawal, field action or rehearsal."""

    _name = "ls.recall.execution"
    _description = "Recall Execution"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "decision_date desc, id desc"
    _check_company_auto = True

    # --- Identification --------------------------------------------------
    name = fields.Char(
        string="Reference",
        readonly=True,
        copy=False,
        index=True,
        default=lambda self: self.env._("New"),
    )
    plan_id = fields.Many2one(
        comodel_name="ls.recall.plan",
        string="Recall Plan",
        domain="[('state', '=', 'approved'), "
               "('company_id', '=', company_id)]",
        check_company=True,
        tracking=True,
        help="Approved plan under which this action is conducted.",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    active = fields.Boolean(default=True)
    state = fields.Selection(
        selection=EXECUTION_STATE_SELECTION,
        default="planned",
        required=True,
        copy=False,
        tracking=True,
        index=True,
    )

    # --- Decision ---------------------------------------------------------
    action_type = fields.Selection(
        selection=ACTION_TYPE_SELECTION,
        default="recall",
        required=True,
        tracking=True,
        help="Nature of the field action. 'Recall', 'Market Withdrawal' "
             "and 'Stock Recovery' are separately defined in 21 CFR 7.3; "
             "'Field Safety Corrective Action' is defined in Regulation "
             "(EU) 2017/745 Article 2(68).",
    )
    is_mock = fields.Boolean(
        compute="_compute_is_mock",
        store=True,
        help="Technical flag excluding rehearsals from regulatory "
             "reporting and from the closure quality gates.",
    )
    classification = fields.Selection(
        selection=CLASSIFICATION_SELECTION,
        default="not_classified",
        required=True,
        tracking=True,
        help=CLASSIFICATION_HELP,
    )
    depth = fields.Selection(
        selection=DEPTH_SELECTION,
        tracking=True,
        help="Level in the distribution chain to which the action "
             "extends, per 21 CFR 7.42(b)(1).",
    )
    public_warning = fields.Selection(
        selection=PUBLIC_WARNING_SELECTION,
        default="none",
        required=True,
        tracking=True,
        help="Whether a public warning forms part of the strategy, per "
             "21 CFR 7.42(b)(2).",
    )
    effectiveness_level = fields.Selection(
        selection=EFFECTIVENESS_LEVEL_SELECTION,
        default="a",
        required=True,
        tracking=True,
        help="Proportion of consignees to be contacted during "
             "effectiveness checks, per 21 CFR 7.42(b)(3).",
    )
    effectiveness_sample_pct = fields.Float(
        string="Level B Sample (%)",
        default=50.0,
        help="Percentage of consignees to contact when level B is "
             "selected. Level B is defined as greater than 10% and less "
             "than 100%.",
    )

    # --- Subject ----------------------------------------------------------
    product_id = fields.Many2one(comodel_name="product.product", required=True,
                                 index=True,
                                 check_company=True,
                                 tracking=True,)
    lot_ids = fields.Many2many(
        comodel_name="stock.lot",
        relation="ls_recall_execution_lot_rel",
        column1="execution_id",
        column2="lot_id",
        string="Affected Lots / Serial Numbers",
        check_company=True,
        tracking=True,
        help="Lots subject to the action. Distribution tracing reads "
             "stock movements for exactly these lots.",
    )
    lot_count = fields.Integer(compute="_compute_lot_count")
    reason = fields.Text(tracking=True,
                         help="Quality defect or safety concern that triggered the "
                         "action, in terms that can be communicated to consignees.",)
    defect_reference = fields.Char(
        string="Quality Defect Reference",
        tracking=True,
        help="Reference of the deviation, complaint or investigation "
             "record in which the defect was raised.",
    )
    capa_reference = fields.Char(tracking=True,
                                 help="Reference of the corrective and preventive action opened "
                                 "for the root cause. Recorded as a free reference so that "
                                 "this module does not require a CAPA module to be present.",)
    root_cause = fields.Text(tracking=True)

    # --- Health hazard evaluation ----------------------------------------
    health_hazard_evaluation = fields.Html(
        sanitize=True,
        help="Assessment of the health hazard presented by the product. "
             "21 CFR 7.41(a) lists the factors such an evaluation "
             "considers.",
    )
    hhe_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Hazard Evaluation By",
        tracking=True,
    )
    hhe_date = fields.Datetime(string="Hazard Evaluation Date", tracking=True)

    # --- Dates and people --------------------------------------------------
    decision_date = fields.Datetime(
        tracking=True,
        help="Moment at which the organisation decided to act.",
    )
    initiation_date = fields.Datetime(
        readonly=True,
        copy=False,
        tracking=True,
        help="Moment at which the action moved to the Initiated state.",
    )
    first_communication_date = fields.Datetime(
        compute="_compute_communication_metrics",
        store=True,
        help="Date on which the first communication was recorded as sent.",
    )
    initiation_delay_hours = fields.Float(
        compute="_compute_communication_metrics",
        store=True,
        help="Hours between the decision and the first communication.",
    )
    target_completion_date = fields.Date(tracking=True)
    closure_date = fields.Datetime(readonly=True, copy=False, tracking=True)
    responsible_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Recall Coordinator",
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
    )

    # --- Authority notification --------------------------------------------
    authority_notified = fields.Boolean(
        readonly=True,
        copy=False,
        tracking=True,
        help="Set when an authority notification communication is "
             "recorded as sent.",
    )
    authority_notification_date = fields.Datetime(
        readonly=True, copy=False, tracking=True
    )
    authority_reference = fields.Char(tracking=True,
                                      help="Reference allocated by the competent authority, where one "
                                      "has been received.",)

    # --- Related records -----------------------------------------------------
    line_ids = fields.One2many(
        comodel_name="ls.recall.line",
        inverse_name="execution_id",
        string="Consignees",
    )
    communication_ids = fields.One2many(
        comodel_name="ls.recall.communication",
        inverse_name="execution_id",
        string="Communications",
    )
    effectiveness_ids = fields.One2many(
        comodel_name="ls.recall.effectiveness",
        inverse_name="execution_id",
        string="Effectiveness Checks",
    )
    report_ids = fields.One2many(
        comodel_name="ls.recall.report",
        inverse_name="execution_id",
        string="Reports",
    )
    line_count = fields.Integer(compute="_compute_related_counts")
    communication_count = fields.Integer(compute="_compute_related_counts")
    effectiveness_count = fields.Integer(compute="_compute_related_counts")
    report_count = fields.Integer(compute="_compute_related_counts")

    # --- Quantities and rates -------------------------------------------------
    qty_distributed = fields.Float(
        compute="_compute_quantities",
        store=True,
        help="Total quantity shipped to consignees for the affected "
             "lots, as traced from stock movements.",
    )
    qty_returned = fields.Float(compute="_compute_quantities", store=True)
    qty_destroyed = fields.Float(compute="_compute_quantities", store=True)
    qty_not_recovered = fields.Float(
        compute="_compute_quantities",
        store=True,
        help="Quantity that consignees have confirmed cannot be "
             "returned, for example because it was already administered "
             "or used.",
    )
    qty_accounted = fields.Float(
        compute="_compute_quantities",
        store=True,
        help="Returned plus destroyed plus confirmed not recoverable.",
    )
    qty_outstanding = fields.Float(compute="_compute_quantities", store=True)
    reconciliation_rate = fields.Float(
        compute="_compute_quantities",
        store=True,
        string="Reconciliation Rate (%)",
        help="Accounted quantity as a percentage of the distributed "
             "quantity.",
    )
    consignee_count = fields.Integer(compute="_compute_rates", store=True)
    consignee_responded_count = fields.Integer(
        compute="_compute_rates", store=True
    )
    response_rate = fields.Float(
        compute="_compute_rates", store=True, string="Response Rate (%)"
    )
    effectiveness_planned_count = fields.Integer(
        compute="_compute_rates", store=True
    )
    effectiveness_performed_count = fields.Integer(
        compute="_compute_rates", store=True
    )
    effectiveness_success_count = fields.Integer(
        compute="_compute_rates", store=True
    )
    effectiveness_required_count = fields.Integer(
        compute="_compute_rates",
        store=True,
        help="Number of consignees to be contacted, derived from the "
             "effectiveness check level and the number of consignees.",
    )
    effectiveness_coverage = fields.Float(
        compute="_compute_rates",
        store=True,
        string="Effectiveness Coverage (%)",
        help="Consignees contacted as a percentage of the number "
             "required by the selected level.",
    )

    # --- Closure ---------------------------------------------------------------
    closure_justification = fields.Text(readonly=True, copy=False)
    closure_attestation = fields.Char(readonly=True, copy=False)
    closed_by_user_id = fields.Many2one(
        comodel_name="res.users", readonly=True, copy=False
    )
    cancellation_reason = fields.Text(readonly=True, copy=False)

    _name_uniq = models.Constraint(
        "UNIQUE(name)",
        "The recall reference must be unique.",
    )
    _sample_pct_range = models.Constraint(
        "CHECK(effectiveness_sample_pct >= 0"
        " AND effectiveness_sample_pct <= 100)",
        "The level B sample percentage must be between 0 and 100.",
    )

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------
    @api.depends("action_type")
    def _compute_is_mock(self):
        """Flag rehearsals so they can be excluded from regulatory KPIs."""
        for execution in self:
            execution.is_mock = execution.action_type == "mock_recall"

    @api.depends("lot_ids")
    def _compute_lot_count(self):
        """Count the affected lots."""
        for execution in self:
            execution.lot_count = len(execution.lot_ids)

    @api.depends(
        "line_ids",
        "communication_ids",
        "effectiveness_ids",
        "report_ids",
    )
    def _compute_related_counts(self):
        """Count related records for the smart buttons."""
        for execution in self:
            execution.line_count = len(execution.line_ids)
            execution.communication_count = len(execution.communication_ids)
            execution.effectiveness_count = len(execution.effectiveness_ids)
            execution.report_count = len(execution.report_ids)

    @api.depends(
        "line_ids.qty_shipped",
        "line_ids.qty_returned",
        "line_ids.qty_destroyed",
        "line_ids.qty_not_recovered",
    )
    def _compute_quantities(self):
        """Aggregate the consignee lines into the recall totals."""
        for execution in self:
            lines = execution.line_ids
            distributed = sum(lines.mapped("qty_shipped"))
            returned = sum(lines.mapped("qty_returned"))
            destroyed = sum(lines.mapped("qty_destroyed"))
            not_recovered = sum(lines.mapped("qty_not_recovered"))
            accounted = returned + destroyed + not_recovered
            execution.qty_distributed = distributed
            execution.qty_returned = returned
            execution.qty_destroyed = destroyed
            execution.qty_not_recovered = not_recovered
            execution.qty_accounted = accounted
            execution.qty_outstanding = distributed - accounted
            execution.reconciliation_rate = (
                accounted / distributed * 100.0 if distributed else 0.0
            )

    @api.depends(
        "line_ids.partner_id",
        "line_ids.response_received",
        "effectiveness_level",
        "effectiveness_sample_pct",
        "effectiveness_ids.state",
        "effectiveness_ids.outcome",
        "effectiveness_ids.partner_id",
    )
    def _compute_rates(self):
        """Derive consignee response and effectiveness coverage rates.

        Consignees are counted as distinct partners, because one partner
        may appear on several lines when several lots were shipped.
        """
        for execution in self:
            lines = execution.line_ids
            consignees = lines.mapped("partner_id")
            responded = lines.filtered("response_received").mapped(
                "partner_id"
            )
            execution.consignee_count = len(consignees)
            execution.consignee_responded_count = len(responded)
            execution.response_rate = (
                len(responded) / len(consignees) * 100.0 if consignees else 0.0
            )

            checks = execution.effectiveness_ids.filtered(
                lambda c: c.state != "cancelled"
            )
            performed = checks.filtered(lambda c: c.state == "performed")
            successful = performed.filtered(
                lambda c: c.outcome in EFFECTIVENESS_SUCCESS_OUTCOMES
            )
            execution.effectiveness_planned_count = len(checks)
            execution.effectiveness_performed_count = len(performed)
            execution.effectiveness_success_count = len(successful)

            required = execution._required_effectiveness_checks(
                len(consignees)
            )
            execution.effectiveness_required_count = required
            contacted = len(performed.mapped("partner_id"))
            execution.effectiveness_coverage = (
                contacted / required * 100.0 if required else 0.0
            )

    @api.depends("decision_date", "communication_ids.sent_date")
    def _compute_communication_metrics(self):
        """Record when the first communication went out and how fast."""
        for execution in self:
            sent_dates = execution.communication_ids.filtered(
                lambda c: c.sent_date
            ).mapped("sent_date")
            first = min(sent_dates) if sent_dates else False
            execution.first_communication_date = first
            if first and execution.decision_date:
                delta = first - execution.decision_date
                execution.initiation_delay_hours = (
                    delta.total_seconds() / 3600.0
                )
            else:
                execution.initiation_delay_hours = 0.0

    @api.depends("name", "product_id.display_name", "action_type")
    def _compute_display_name(self):
        """Show the reference together with the product."""
        labels = dict(ACTION_TYPE_SELECTION)
        for execution in self:
            product = execution.product_id.display_name or ""
            label = labels.get(execution.action_type, "")
            execution.display_name = f"{execution.name} - {label} - {product}"

    def _required_effectiveness_checks(self, consignee_count):
        """Return how many consignees must be contacted.

        :param int consignee_count: number of distinct consignees.
        :return: the number of consignees to contact, rounded up, per the
            coverage attached to the selected level.
        :rtype: int
        """
        self.ensure_one()
        if not consignee_count:
            return 0
        if self.effectiveness_level == "b":
            percentage = self.effectiveness_sample_pct
        else:
            percentage = EFFECTIVENESS_LEVEL_COVERAGE.get(
                self.effectiveness_level, 0.0
            )
        if not percentage:
            return 0
        exact = consignee_count * percentage / 100.0
        rounded = int(exact)
        return rounded + 1 if exact > rounded else rounded

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("effectiveness_level", "effectiveness_sample_pct")
    def _check_level_b_sample(self):
        """Level B is defined as strictly between 10% and 100%."""
        for execution in self.filtered(
            lambda e: e.effectiveness_level == "b"
        ):
            if not 10.0 < execution.effectiveness_sample_pct < 100.0:
                raise ValidationError(
                    self.env._(
                        "Level B requires a sample greater than 10%% and "
                        "less than 100%%. Recall %(name)s has %(pct).2f%%.",
                        name=execution.name,
                        pct=execution.effectiveness_sample_pct,
                    )
                )

    @api.constrains("lot_ids", "product_id")
    def _check_lots_match_product(self):
        """Every affected lot must belong to the recalled product."""
        for execution in self:
            wrong = execution.lot_ids.filtered(
                lambda lot: lot.product_id != execution.product_id
            )
            if wrong:
                raise ValidationError(
                    self.env._(
                        "Lot %(lot)s does not belong to product "
                        "%(product)s.",
                        lot=wrong[0].display_name,
                        product=execution.product_id.display_name,
                    )
                )

    @api.constrains("decision_date", "target_completion_date")
    def _check_dates(self):
        """The target completion date cannot precede the decision."""
        for execution in self:
            if not (execution.decision_date and
                    execution.target_completion_date):
                continue
            if execution.target_completion_date < execution.decision_date.date():
                raise ValidationError(
                    self.env._(
                        "The target completion date of %(name)s precedes "
                        "its decision date.",
                        name=execution.name,
                    )
                )

    # ------------------------------------------------------------------
    # ORM
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Allocate the recall reference from the dedicated sequence."""
        new_label = self.env._("New")
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == new_label:
                company_id = vals.get("company_id") or self.env.company.id
                sequence = self.env["ir.sequence"].with_company(company_id)
                vals["name"] = (
                    sequence.next_by_code("ls.recall.execution") or new_label
                )
        executions = super().create(vals_list)
        for execution in executions:
            execution.message_post(
                body=self.env._("Recall record created.")
            )
        return executions

    def write(self, vals):
        """Enforce the two write restrictions the workflow depends on.

        1. A closed or cancelled record is evidence and is not editable.
        2. The fields that define the regulatory decision are frozen once
           the action has been initiated.
        """
        workflow_fields = self._workflow_writable_fields()
        final = self.filtered(lambda e: e.state in EXECUTION_FINAL_STATES)
        if final and set(vals) - workflow_fields:
            raise UserError(
                self.env._(
                    "Recall %(name)s is %(state)s and can no longer be "
                    "modified.",
                    name=final[0].name,
                    state=final[0].state,
                )
            )
        locked_fields = set(vals) & set(EXECUTION_LOCKED_AFTER_INITIATION)
        if locked_fields:
            started = self.filtered(lambda e: e.state != "planned")
            if started:
                raise UserError(
                    self.env._(
                        "Recall %(name)s has been initiated. The "
                        "following fields are under change control and "
                        "cannot be modified: %(fields)s.",
                        name=started[0].name,
                        fields=", ".join(sorted(locked_fields)),
                    )
                )
        return super().write(vals)

    @api.model
    def _workflow_writable_fields(self):
        """Return fields that stay writable on a finalised record."""
        return {
            "active",
            "message_follower_ids",
            "message_ids",
            "message_main_attachment_id",
            "activity_ids",
        }

    @api.ondelete(at_uninstall=False)
    def _unlink_only_planned(self):
        """Only a record that was never initiated may be deleted."""
        blocked = self.filtered(lambda e: e.state != "planned")
        if blocked:
            raise UserError(
                self.env._(
                    "Recall %(name)s has been initiated and cannot be "
                    "deleted. Cancel it instead so that the decision "
                    "remains on record.",
                    name=blocked[0].name,
                )
            )

    # ------------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------------
    def action_initiate(self):
        """Move from Planned to Initiated.

        Gate: the decision must be documented. A real action additionally
        requires a health hazard evaluation, a classification and a depth,
        because those three determine the strategy that follows.
        """
        for execution in self:
            execution._assert_transition("initiated")
            if not execution.reason:
                raise UserError(
                    self.env._(
                        "Record the reason for %(name)s before "
                        "initiating it.",
                        name=execution.name,
                    )
                )
            if not execution.lot_ids:
                raise UserError(
                    self.env._(
                        "List the affected lots of %(name)s before "
                        "initiating it.",
                        name=execution.name,
                    )
                )
            if execution.action_type in REAL_ACTION_TYPES:
                execution._assert_strategy_defined()
        self.write(
            {
                "state": "initiated",
                "initiation_date": fields.Datetime.now(),
            }
        )
        for execution in self:
            if not execution.decision_date:
                execution.decision_date = execution.initiation_date
        return True

    def action_trace_and_start(self):
        """Move from Initiated to In Progress.

        Tracing runs first, so the transition is only possible when the
        distribution of the affected lots is actually known.
        """
        for execution in self:
            execution._assert_transition("in_progress")
            execution.action_trace_distribution()
            if not execution.line_ids:
                raise UserError(
                    self.env._(
                        "No distribution was found for the lots of "
                        "%(name)s. Add the consignees manually if the "
                        "product was distributed outside this system.",
                        name=execution.name,
                    )
                )
        self.write({"state": "in_progress"})
        return True

    def action_start_communication(self):
        """Move from In Progress to Communication.

        Gate: at least one communication must have been recorded as sent.
        """
        for execution in self:
            execution._assert_transition("communication")
            if not execution.communication_ids.filtered(
                lambda c: c.state in ("sent", "acknowledged")
            ):
                raise UserError(
                    self.env._(
                        "Record at least one communication as sent for "
                        "%(name)s before moving to the communication "
                        "phase.",
                        name=execution.name,
                    )
                )
        self.write({"state": "communication"})
        return True

    def action_start_effectiveness(self):
        """Move from Communication to Effectiveness Check.

        Gate: the number of planned checks must reach the number required
        by the selected level. Level E requires none by definition.
        """
        for execution in self:
            execution._assert_transition("effectiveness_check")
            required = execution.effectiveness_required_count
            planned = execution.effectiveness_planned_count
            if required and planned < required:
                raise UserError(
                    self.env._(
                        "Level %(level)s requires %(required)s consignee "
                        "checks for %(name)s; only %(planned)s are "
                        "planned.",
                        level=execution.effectiveness_level.upper(),
                        required=required,
                        planned=planned,
                        name=execution.name,
                    )
                )
        self.write({"state": "effectiveness_check"})
        return True

    def action_open_close_wizard(self):
        """Open the closure wizard for a single recall."""
        self.ensure_one()
        self._assert_transition("closed")
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Close Recall"),
            "res_model": "ls.recall.close.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_execution_id": self.id},
        }

    def action_cancel(self):
        """Open the cancellation wizard.

        Cancellation is available at any point before closure and always
        requires a documented reason, so that a reversed decision is
        recorded rather than erased.
        """
        self.ensure_one()
        if self.state in EXECUTION_FINAL_STATES:
            raise UserError(
                self.env._("Recall %(name)s is already finalised.",
                           name=self.name)
            )
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Cancel Recall"),
            "res_model": "ls.recall.close.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_execution_id": self.id,
                "default_mode": "cancel",
            },
        }

    def action_reset_to_planned(self):
        """Return an initiated record to Planned.

        Only available immediately after initiation and before any
        consignee, communication or check exists, so that a mistaken
        initiation can be corrected without leaving orphan evidence.
        """
        for execution in self:
            if execution.state != "initiated":
                raise UserError(
                    self.env._(
                        "Only a recall in the Initiated state can be "
                        "reset. %(name)s is in state %(state)s.",
                        name=execution.name,
                        state=execution.state,
                    )
                )
            if (
                execution.line_ids
                or execution.communication_ids
                or execution.effectiveness_ids
            ):
                raise UserError(
                    self.env._(
                        "Recall %(name)s already has related records and "
                        "cannot be reset. Cancel it instead.",
                        name=execution.name,
                    )
                )
        self.write({"state": "planned", "initiation_date": False})
        return True

    # ------------------------------------------------------------------
    # Distribution tracing
    # ------------------------------------------------------------------
    def action_trace_distribution(self):
        """Rebuild the consignee lines from recorded stock movements.

        The scan reads completed stock move lines for the affected lots
        whose destination is a customer location, and aggregates the
        shipped quantity per consignee and lot.

        The operation is idempotent with respect to user data: shipped
        quantities and source documents are refreshed, while returned,
        destroyed and not-recovered quantities entered by users are never
        overwritten.

        :return: True.
        """
        line_model = self.env["ls.recall.line"]
        for execution in self:
            if execution.state in EXECUTION_FINAL_STATES:
                raise UserError(
                    self.env._(
                        "Recall %(name)s is finalised; its distribution "
                        "can no longer be re-traced.",
                        name=execution.name,
                    )
                )
            traced, unassigned_qty = execution._scan_move_lines()
            existing = {
                (line.partner_id.id, line.lot_id.id): line
                for line in execution.line_ids
            }
            created = 0
            updated = 0
            for key, data in traced.items():
                line = existing.get(key)
                values = {
                    "qty_shipped": data["quantity"],
                    "picking_ids": [(6, 0, sorted(data["picking_ids"]))],
                }
                if line:
                    line.write(values)
                    updated += 1
                else:
                    values.update(
                        {
                            "execution_id": execution.id,
                            "partner_id": key[0],
                            "lot_id": key[1],
                        }
                    )
                    line_model.create(values)
                    created += 1
            execution._post_trace_summary(created, updated, unassigned_qty)
            derived = execution._ls_lots_with_descendants() - execution.lot_ids
            if derived:
                execution.message_post(
                    body=self.env._(
                        "Lots produced from the recalled lots were included "
                        "in the trace: %(lots)s.",
                        lots=", ".join(derived.mapped("display_name")),
                    )
                )
        return True

    def _scan_move_lines(self):
        """Return traced quantities per consignee and lot.

        The scan covers the recalled lots and every lot produced from
        them, recursively, through the consumption links that stock
        records on completed manufacturing (``produce_line_ids``). A
        recall of a component therefore reaches the consignees of the
        finished lots that contain it.

        Stock data is read with superuser rights, restricted to the
        company of the recall: a recall coordinator must be able to
        trace distribution without holding inventory rights.

        Quantities are summed in the unit of measure of the product
        (``quantity_product_uom``), so deliveries made in different
        units are added correctly.

        :return: a tuple ``(traced, unassigned_qty)`` where ``traced``
            maps ``(partner_id, lot_id)`` to a dict holding the summed
            quantity and the set of source picking ids, and
            ``unassigned_qty`` is the quantity that could not be
            attributed to a consignee.
        :rtype: tuple
        """
        self.ensure_one()
        traced = {}
        unassigned_qty = 0.0
        if not self.lot_ids:
            return traced, unassigned_qty
        lots = self._ls_lots_with_descendants()
        move_lines = self.env["stock.move.line"].sudo().search(
            [
                ("lot_id", "in", lots.ids),
                ("state", "=", "done"),
                ("location_dest_id.usage", "in", EXTERNAL_LOCATION_USAGES),
                ("company_id", "=", self.company_id.id),
            ]
        )
        for move_line in move_lines:
            partner = move_line.picking_id.partner_id
            quantity = move_line.quantity_product_uom
            if not partner:
                unassigned_qty += quantity
                continue
            key = (partner.id, move_line.lot_id.id)
            entry = traced.setdefault(
                key, {"quantity": 0.0, "picking_ids": set()}
            )
            entry["quantity"] += quantity
            if move_line.picking_id:
                entry["picking_ids"].add(move_line.picking_id.id)
        return traced, unassigned_qty

    def _ls_lots_with_descendants(self):
        """Return the recalled lots and every lot produced from them.

        The genealogy is followed downstream through the completed move
        lines that consumed a lot (``produce_line_ids`` of the consumed
        line lists the move lines it was used to produce). The walk
        stops when no new lot is found, which also protects against
        cycles.

        :return: a ``stock.lot`` recordset (superuser environment).
        """
        self.ensure_one()
        move_line_model = self.env["stock.move.line"].sudo()
        lots = self.lot_ids.sudo()
        frontier = lots
        while frontier:
            consumed = move_line_model.search(
                [
                    ("lot_id", "in", frontier.ids),
                    ("state", "=", "done"),
                    ("produce_line_ids", "!=", False),
                ]
            )
            produced = consumed.produce_line_ids.filtered(
                lambda line: line.state == "done" and line.lot_id
            ).lot_id
            frontier = produced - lots
            lots |= frontier
        return lots

    def _post_trace_summary(self, created, updated, unassigned_qty):
        """Post the outcome of a tracing run to the chatter."""
        self.ensure_one()
        body = self.env._(
            "Distribution traced: %(created)s consignee lines created, "
            "%(updated)s updated.",
            created=created,
            updated=updated,
        )
        if unassigned_qty:
            body += " " + self.env._(
                "A quantity of %(qty).2f could not be attributed to a "
                "consignee because the source transfer has no partner. "
                "Add the consignee manually.",
                qty=unassigned_qty,
            )
        self.message_post(body=body)

    # ------------------------------------------------------------------
    # Actions opening related records
    # ------------------------------------------------------------------
    def _action_open_related(self, model, name, extra_context=None):
        """Return a window action listing records related to this recall.

        :param str model: the technical model name to open.
        :param str name: the title of the action.
        :param dict extra_context: additional default values.
        """
        self.ensure_one()
        context = {"default_execution_id": self.id}
        context.update(extra_context or {})
        return {
            "type": "ir.actions.act_window",
            "name": name,
            "res_model": model,
            "view_mode": "list,form",
            "domain": [("execution_id", "=", self.id)],
            "context": context,
        }

    def action_view_lines(self):
        """Open the consignee lines."""
        return self._action_open_related(
            "ls.recall.line", self.env._("Consignees")
        )

    def action_view_communications(self):
        """Open the communications."""
        return self._action_open_related(
            "ls.recall.communication", self.env._("Communications")
        )

    def action_view_effectiveness(self):
        """Open the effectiveness checks."""
        return self._action_open_related(
            "ls.recall.effectiveness", self.env._("Effectiveness Checks")
        )

    def action_view_reports(self):
        """Open the recall reports."""
        return self._action_open_related(
            "ls.recall.report", self.env._("Reports")
        )

    def action_generate_effectiveness_checks(self):
        """Create one planned effectiveness check per consignee.

        Checks are created for consignees that do not already have one,
        so the action can be run again after new consignees are added.
        """
        check_model = self.env["ls.recall.effectiveness"]
        created = check_model.browse()
        for execution in self:
            if execution.state in EXECUTION_FINAL_STATES:
                raise UserError(
                    self.env._(
                        "Recall %(name)s is finalised.", name=execution.name
                    )
                )
            covered = execution.effectiveness_ids.mapped("line_id")
            for line in execution.line_ids - covered:
                created |= check_model.create(
                    {
                        "execution_id": execution.id,
                        "line_id": line.id,
                        "partner_id": line.partner_id.id,
                        "method": "phone",
                    }
                )
            execution.message_post(
                body=self.env._(
                    "%(count)s effectiveness checks planned.",
                    count=len(created),
                )
            )
        return True

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _assert_transition(self, target_state):
        """Validate a forward transition of the state machine.

        :param str target_state: the state being moved to.
        :raise UserError: when the record is not in the state that
            immediately precedes ``target_state``.
        """
        self.ensure_one()
        if self.state in EXECUTION_FINAL_STATES:
            raise UserError(
                self.env._(
                    "Recall %(name)s is finalised and cannot change "
                    "state.",
                    name=self.name,
                )
            )
        target_index = EXECUTION_FORWARD_PATH.index(target_state)
        expected = EXECUTION_FORWARD_PATH[target_index - 1]
        if self.state != expected:
            raise UserError(
                self.env._(
                    "Recall %(name)s must be in state '%(expected)s' to "
                    "move to '%(target)s'. It is in '%(current)s'.",
                    name=self.name,
                    expected=expected,
                    target=target_state,
                    current=self.state,
                )
            )

    def _assert_strategy_defined(self):
        """Check the elements a real field action needs before starting."""
        self.ensure_one()
        missing = []
        if self.classification == "not_classified":
            missing.append(self.env._("health hazard classification"))
        if not self.depth:
            missing.append(self.env._("depth of recall"))
        if not self.health_hazard_evaluation:
            missing.append(self.env._("health hazard evaluation"))
        if missing:
            raise UserError(
                self.env._(
                    "Recall %(name)s cannot be initiated. Missing: "
                    "%(missing)s.",
                    name=self.name,
                    missing=", ".join(missing),
                )
            )

    def _register_authority_notification(self, notification_date):
        """Record that a competent authority has been notified.

        Called by the communication model when an authority notification
        is recorded as sent.

        :param datetime notification_date: when the notification was sent.
        """
        self.ensure_one()
        if self.authority_notified:
            return
        # Written with sudo because a coordinator may record the sending
        # of a notification without holding write access to the recall
        # header fields, which are reserved to the recall manager.
        self.sudo().write(
            {
                "authority_notified": True,
                "authority_notification_date": notification_date,
            }
        )

    def _evaluate_closure_gates(self):
        """Evaluate the conditions expected before a recall is closed.

        The gates are returned rather than raised, so the closure wizard
        can show the user the whole picture at once instead of one error
        at a time.

        A rehearsal is held to a reduced set: it has no real consignees
        to reconcile and no report to submit to an authority.

        :return: a list of ``(passed, label)`` tuples.
        :rtype: list
        """
        self.ensure_one()
        lines = self.line_ids
        results = []

        not_notified = lines.filtered(lambda line: not line.notified)
        results.append(
            (
                not not_notified,
                self.env._(
                    "All %(total)s consignees notified (%(open)s "
                    "outstanding)",
                    total=len(lines),
                    open=len(not_notified),
                ),
            )
        )

        discrepancies = lines.filtered(
            lambda line: line.status == "discrepancy"
        )
        results.append(
            (
                not discrepancies,
                self.env._(
                    "No quantity discrepancy on consignee lines "
                    "(%(count)s found)",
                    count=len(discrepancies),
                ),
            )
        )

        required = self.effectiveness_required_count
        performed = self.effectiveness_performed_count
        results.append(
            (
                performed >= required,
                self.env._(
                    "Effectiveness checks performed: %(performed)s of "
                    "%(required)s required at level %(level)s",
                    performed=performed,
                    required=required,
                    level=(self.effectiveness_level or "").upper(),
                ),
            )
        )

        if self.is_mock:
            return results

        target = (
            self.plan_id.target_reconciliation_rate
            if self.plan_id
            else 100.0
        )
        results.append(
            (
                self.reconciliation_rate >= target,
                self.env._(
                    "Reconciliation rate %(actual).2f%% reaches the "
                    "target of %(target).2f%%",
                    actual=self.reconciliation_rate,
                    target=target,
                ),
            )
        )

        final_report = self.report_ids.filtered(
            lambda report: report.report_type == "final"
            and report.state in ("approved", "submitted")
        )
        results.append(
            (
                bool(final_report),
                self.env._("An approved final report exists"),
            )
        )

        if (
            self.action_type == "recall"
            and self.classification in ("class_i", "class_ii")
        ):
            results.append(
                (
                    self.authority_notified,
                    self.env._(
                        "Competent authority notified, as expected for a "
                        "class I or class II recall"
                    ),
                )
            )
        return results

    @api.model
    def _cron_monitor_open_recalls(self):
        """Raise activities on recalls that need attention.

        Scheduled action. Two conditions are monitored: a real action
        that has passed its target completion date without being closed,
        and a real action that has been initiated without any
        communication having been sent.

        :return: the number of recalls an activity was created on.
        """
        today = fields.Date.context_today(self)
        candidates = self.search(
            [
                ("state", "not in", list(EXECUTION_FINAL_STATES)),
                ("action_type", "in", list(REAL_ACTION_TYPES)),
            ]
        )
        flagged = 0
        for execution in candidates:
            if execution.activity_ids:
                continue
            overdue = (
                execution.target_completion_date
                and execution.target_completion_date < today
            )
            silent = (
                execution.state in ("initiated", "in_progress")
                and not execution.first_communication_date
            )
            if not (overdue or silent):
                continue
            if overdue:
                summary = self.env._("Recall past its target date")
            else:
                summary = self.env._("Recall initiated, nothing sent yet")
            execution.activity_schedule(
                act_type_xmlid="mail.mail_activity_data_todo",
                summary=summary,
                user_id=execution.responsible_user_id.id,
            )
            flagged += 1
        return flagged
