# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Pharmaceutical manufacturing batch."""

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..constants import (
    BATCH_CANCELLABLE_STATES,
    BATCH_CLOSED_STATES,
    BATCH_STATES,
    BATCH_TYPES,
)


class LsPharmaBatch(models.Model):
    """A batch of a pharmaceutical product.

    The batch is the record around which the module is organised.  It carries
    the identity of the product, the genealogy that links a packaging batch to
    the bulk batch it was packed from, the yield figures required by
    21 CFR 211.103, and the state machine that governs when quality assurance
    may take a release decision.

    The batch may be linked to a manufacturing order and to an inventory lot,
    but neither link is mandatory.  The module deliberately does not read or
    write the state of a manufacturing order: the batch keeps its own state so
    that the release control remains enforceable irrespective of how the
    physical production was recorded.
    """

    _name = "ls.pharma.batch"
    _description = "Pharmaceutical Manufacturing Batch"
    _check_company_auto = True
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_manufacture desc, name desc"

    _name_company_uniq = models.Constraint(
        "UNIQUE(name, company_id)",
        "The batch reference must be unique per company.",
    )

    # ------------------------------------------------------------------
    # Identification
    # ------------------------------------------------------------------
    name = fields.Char(
        string="Batch Reference",
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: self.env._("New"),
        tracking=True,
    )
    batch_type = fields.Selection(selection=BATCH_TYPES, required=True,
                                  default="finished",
                                  tracking=True,
                                  help=(
                                      "A bulk batch carries the manufactured intermediate. A packaging "
                                      "batch carries the primary and secondary packaging operation and "
                                      "is linked to its bulk batch through the parent batch field."),
                                  )
    product_id = fields.Many2one(comodel_name="product.product", required=True,
                                 tracking=True,
                                 index=True,)
    lot_id = fields.Many2one(
        comodel_name="stock.lot",
        string="Inventory Lot",
        tracking=True,
        copy=False,
        help=(
            "Inventory lot that carries the physical stock of this batch. The "
            "field is optional so that a batch can be recorded before the lot "
            "exists."
        ),
        check_company=True,
    )
    production_id = fields.Many2one(
        comodel_name="mrp.production",
        string="Manufacturing Order",
        tracking=True,
        copy=False,
        help=(
            "Manufacturing order that executed this batch. The link is "
            "informational: the state of this batch is never derived from the "
            "state of the manufacturing order."
        ),
    )
    bom_id = fields.Many2one(
        comodel_name="mrp.bom",
        string="Bill of Materials",
        help="Bill of materials used as the formulation reference.",
    )
    warehouse_id = fields.Many2one(
        comodel_name="stock.warehouse",
        string="Manufacturing Site",
        tracking=True,
    )
    parent_batch_id = fields.Many2one(
        comodel_name="ls.pharma.batch",
        string="Bulk Batch",
        index=True,
        copy=False,
        help=(
            "Bulk batch from which this packaging batch was produced. It "
            "establishes the genealogy between a bulk batch and every "
            "packaging batch derived from it."
        ),
    )
    child_batch_ids = fields.One2many(
        comodel_name="ls.pharma.batch",
        inverse_name="parent_batch_id",
        string="Derived Batches",
    )
    child_batch_count = fields.Integer(
        string="Derived Batch Count",
        compute="_compute_child_batch_count",
    )

    # ------------------------------------------------------------------
    # Quantities and yield -- 21 CFR 211.103, 21 CFR 211.186(b)(7)
    # ------------------------------------------------------------------
    uom_id = fields.Many2one(
        comodel_name="uom.uom",
        string="Unit of Measure",
        required=True,
        default=lambda self: self._default_uom_id(),
    )
    planned_qty = fields.Float(
        string="Planned Quantity",
        digits="Product Unit of Measure",
        tracking=True,
    )
    theoretical_yield_qty = fields.Float(
        string="Theoretical Yield",
        digits="Product Unit of Measure",
        tracking=True,
        help=(
            "Quantity that would be obtained if no material were lost. It is "
            "the denominator of the percentage of theoretical yield."
        ),
    )
    actual_yield_qty = fields.Float(
        string="Actual Yield",
        digits="Product Unit of Measure",
        tracking=True,
        copy=False,
    )
    yield_percentage = fields.Float(
        string="Yield (%)",
        compute="_compute_yield_percentage",
        store=True,
        digits=(16, 2),
        help=(
            "Actual yield expressed as a percentage of the theoretical yield. "
            "This field holds a percentage between 0 and 100 and is therefore "
            "displayed without the ratio widget."
        ),
    )
    yield_min_percentage = fields.Float(
        string="Minimum Yield (%)",
        digits=(16, 2),
        help=(
            "Lower percentage of theoretical yield beyond which an "
            "investigation is required. Defaulted from the product."
        ),
    )
    yield_max_percentage = fields.Float(
        string="Maximum Yield (%)",
        digits=(16, 2),
        help=(
            "Upper percentage of theoretical yield beyond which an "
            "investigation is required. Defaulted from the product."
        ),
    )
    yield_investigation_required = fields.Boolean(compute="_compute_yield_investigation_required",
                                                  store=True,
                                                  help=(
                                                      "Set when the percentage of theoretical yield falls outside the "
                                                      "established limits. 21 CFR 211.192 requires that such a "
                                                      "discrepancy be thoroughly investigated."),
                                                  )
    yield_investigation_reference = fields.Char(copy=False,
                                                help=(
                                                    "Reference of the written record of the investigation opened "
                                                    "because the yield fell outside its limits."),
                                                )

    # ------------------------------------------------------------------
    # Dates
    # ------------------------------------------------------------------
    date_start = fields.Datetime(string="Production Start", copy=False, tracking=True)
    date_end = fields.Datetime(string="Production End", copy=False, tracking=True)
    date_manufacture = fields.Date(
        string="Manufacturing Date",
        copy=False,
        tracking=True,
        index=True,
    )
    shelf_life_months = fields.Integer(
        string="Shelf Life (Months)",
        help="Shelf life used to compute the expiry date from the manufacturing date.",
    )
    date_expiry = fields.Date(
        string="Expiry Date",
        copy=False,
        tracking=True,
        index=True,
    )
    date_retest = fields.Date(
        string="Retest Date",
        copy=False,
        help="Date on which the batch must be re-examined, where applicable.",
    )

    # ------------------------------------------------------------------
    # Composition and execution records
    # ------------------------------------------------------------------
    component_ids = fields.One2many(
        comodel_name="ls.pharma.batch.component",
        inverse_name="batch_id",
        string="Components",
        help=(
            "Specific identification of each batch of component or in-process "
            "material used, with its weight or measure, as required by "
            "21 CFR 211.188(b)(3) and 21 CFR 211.188(b)(4)."
        ),
    )
    equipment_ids = fields.One2many(
        comodel_name="ls.pharma.batch.equipment",
        inverse_name="batch_id",
        string="Equipment and Lines",
        help=(
            "Identity of the individual major equipment and lines used, as "
            "required by 21 CFR 211.188(b)(2)."
        ),
    )
    coproduct_ids = fields.One2many(
        comodel_name="ls.pharma.batch.coproduct",
        inverse_name="batch_id",
        string="Co-Products",
        help="Additional products obtained from the same manufacturing run.",
    )
    batch_record_ids = fields.One2many(
        comodel_name="ls.pharma.batch_record",
        inverse_name="batch_id",
        string="Batch Records",
    )
    batch_record_count = fields.Integer(compute="_compute_batch_record_count",)
    stability_study_ids = fields.One2many(
        comodel_name="ls.pharma.stability_study",
        inverse_name="batch_id",
        string="Stability Studies",
    )
    stability_study_count = fields.Integer(compute="_compute_stability_study_count",)
    serialization_ids = fields.One2many(
        comodel_name="ls.pharma.serialization",
        inverse_name="batch_id",
        string="Serialised Units",
    )
    serialization_count = fields.Integer(
        string="Serialised Unit Count",
        compute="_compute_serialization_count",
    )
    release_id = fields.Many2one(
        comodel_name="ls.pharma.batch.release",
        string="Release Decision",
        readonly=True,
        copy=False,
        ondelete="set null",
    )

    # ------------------------------------------------------------------
    # Accountability
    # ------------------------------------------------------------------
    user_manufactured_id = fields.Many2one(
        comodel_name="res.users",
        string="Manufactured By",
        readonly=True,
        copy=False,
        tracking=True,
        help=(
            "User who declared the manufacturing complete. This user may not "
            "take the release decision, so that the independence of the "
            "quality unit is preserved."
        ),
    )
    user_reviewed_id = fields.Many2one(
        comodel_name="res.users",
        string="Submitted for Review By",
        readonly=True,
        copy=False,
        tracking=True,
    )
    state = fields.Selection(
        selection=BATCH_STATES,
        string="Status",
        default="draft",
        required=True,
        copy=False,
        tracking=True,
        index=True,
    )
    note = fields.Text(string="Internal Notes")
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,
                                 index=True,)
    active = fields.Boolean(default=True)

    # ------------------------------------------------------------------
    # Defaults
    # ------------------------------------------------------------------
    @api.model
    def _default_uom_id(self):
        """Return the reference unit of the first unit-of-measure category.

        The unit of measure is mandatory on a batch.  Rather than assume the
        external identifier of a specific unit, which is not guaranteed to be
        present in every database, the first reference unit found is used as a
        default and the user may change it.
        """
        return self.env["uom.uom"].search([], limit=1)

    # ------------------------------------------------------------------
    # Computed fields
    # ------------------------------------------------------------------
    @api.depends("actual_yield_qty", "theoretical_yield_qty")
    def _compute_yield_percentage(self):
        """Compute the percentage of theoretical yield."""
        for batch in self:
            if batch.theoretical_yield_qty:
                batch.yield_percentage = (
                    batch.actual_yield_qty / batch.theoretical_yield_qty
                ) * 100.0
            else:
                batch.yield_percentage = 0.0

    @api.depends(
        "yield_percentage",
        "yield_min_percentage",
        "yield_max_percentage",
        "actual_yield_qty",
        "theoretical_yield_qty",
    )
    def _compute_yield_investigation_required(self):
        """Flag a yield that falls outside the established limits."""
        for batch in self:
            if not batch.theoretical_yield_qty or not batch.actual_yield_qty:
                batch.yield_investigation_required = False
                continue
            below = (
                batch.yield_min_percentage
                and batch.yield_percentage < batch.yield_min_percentage
            )
            above = (
                batch.yield_max_percentage
                and batch.yield_percentage > batch.yield_max_percentage
            )
            batch.yield_investigation_required = bool(below or above)

    @api.depends("child_batch_ids")
    def _compute_child_batch_count(self):
        """Count the packaging batches derived from this batch."""
        for batch in self:
            batch.child_batch_count = len(batch.child_batch_ids)

    @api.depends("batch_record_ids")
    def _compute_batch_record_count(self):
        """Count the batch records attached to this batch."""
        for batch in self:
            batch.batch_record_count = len(batch.batch_record_ids)

    @api.depends("stability_study_ids")
    def _compute_stability_study_count(self):
        """Count the stability studies that cover this batch."""
        for batch in self:
            batch.stability_study_count = len(batch.stability_study_ids)

    @api.depends("serialization_ids")
    def _compute_serialization_count(self):
        """Count the serialised units generated for this batch."""
        for batch in self:
            batch.serialization_count = len(batch.serialization_ids)

    @api.depends("name", "product_id")
    def _compute_display_name(self):
        """Show the batch reference together with the product name."""
        for batch in self:
            if batch.product_id:
                batch.display_name = "%s - %s" % (batch.name, batch.product_id.name)
            else:
                batch.display_name = batch.name or ""

    # ------------------------------------------------------------------
    # Onchange
    # ------------------------------------------------------------------
    @api.onchange("product_id")
    def _onchange_product_id(self):
        """Default the yield limits, shelf life and unit from the product."""
        for batch in self:
            product = batch.product_id
            if not product:
                continue
            template = product.product_tmpl_id
            batch.uom_id = product.uom_id
            if template.pharma_yield_min_percentage:
                batch.yield_min_percentage = template.pharma_yield_min_percentage
            if template.pharma_yield_max_percentage:
                batch.yield_max_percentage = template.pharma_yield_max_percentage
            if template.pharma_shelf_life_months:
                batch.shelf_life_months = template.pharma_shelf_life_months

    @api.onchange("date_manufacture", "shelf_life_months")
    def _onchange_expiry_inputs(self):
        """Derive the expiry date from the manufacturing date and shelf life."""
        for batch in self:
            if batch.date_manufacture and batch.shelf_life_months > 0:
                batch.date_expiry = batch.date_manufacture + relativedelta(
                    months=batch.shelf_life_months
                )

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("date_manufacture", "date_expiry")
    def _check_expiry_after_manufacture(self):
        """Reject an expiry date that precedes the manufacturing date."""
        for batch in self:
            if (
                batch.date_manufacture
                and batch.date_expiry
                and batch.date_expiry <= batch.date_manufacture
            ):
                raise ValidationError(
                    self.env._(
                        "The expiry date of batch %(name)s must be later than "
                        "its manufacturing date.",
                        name=batch.name,
                    )
                )

    @api.constrains("date_start", "date_end")
    def _check_production_window(self):
        """Reject a production end that precedes the production start."""
        for batch in self:
            if (
                batch.date_start
                and batch.date_end
                and batch.date_end < batch.date_start
            ):
                raise ValidationError(
                    self.env._(
                        "The production end of batch %(name)s cannot precede "
                        "its production start.",
                        name=batch.name,
                    )
                )

    @api.constrains("yield_min_percentage", "yield_max_percentage")
    def _check_yield_limits(self):
        """Reject yield limits that cannot describe an acceptance range."""
        for batch in self:
            if batch.yield_min_percentage < 0.0 or batch.yield_max_percentage < 0.0:
                raise ValidationError(
                    self.env._("Yield limits cannot be negative.")
                )
            if (
                batch.yield_min_percentage
                and batch.yield_max_percentage
                and batch.yield_min_percentage > batch.yield_max_percentage
            ):
                raise ValidationError(
                    self.env._(
                        "The minimum yield of batch %(name)s cannot exceed its "
                        "maximum yield.",
                        name=batch.name,
                    )
                )

    @api.constrains("planned_qty", "theoretical_yield_qty", "actual_yield_qty")
    def _check_quantities(self):
        """Reject negative quantities."""
        for batch in self:
            negative = (
                batch.planned_qty < 0.0
                or batch.theoretical_yield_qty < 0.0
                or batch.actual_yield_qty < 0.0
            )
            if negative:
                raise ValidationError(
                    self.env._(
                        "The quantities of batch %(name)s cannot be negative.",
                        name=batch.name,
                    )
                )

    @api.constrains("parent_batch_id")
    def _check_parent_batch(self):
        """Reject a genealogy that would form a loop.

        The ancestor chain is walked explicitly rather than through a private
        framework helper, so that the check does not depend on an internal
        application programming interface whose signature could change.
        """
        for batch in self:
            seen_ids = set()
            ancestor = batch.parent_batch_id
            while ancestor:
                if ancestor.id == batch.id or ancestor.id in seen_ids:
                    raise ValidationError(
                        self.env._(
                            "Batch %(name)s cannot be its own ancestor.",
                            name=batch.name,
                        )
                    )
                seen_ids.add(ancestor.id)
                ancestor = ancestor.parent_batch_id

    @api.constrains("batch_type", "parent_batch_id")
    def _check_parent_batch_type(self):
        """Require a packaging batch to descend from a bulk batch."""
        for batch in self:
            parent = batch.parent_batch_id
            if parent and parent.batch_type != "bulk":
                raise ValidationError(
                    self.env._(
                        "The parent of batch %(name)s must be a bulk batch.",
                        name=batch.name,
                    )
                )

    # ------------------------------------------------------------------
    # Overrides
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Assign the batch reference from the dedicated sequence."""
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == self.env._("New"):
                company_id = vals.get("company_id") or self.env.company.id
                sequence = (
                    self.env["ir.sequence"]
                    .with_company(company_id)
                    .next_by_code("ls.pharma.batch")
                )
                vals["name"] = sequence or self.env._("New")
        return super().create(vals_list)

    def write(self, vals):
        """Protect production data once a release decision has been taken.

        A batch that has been released or rejected records a quality decision.
        The fields that the decision was based upon are therefore frozen.  The
        state itself and the free-text notes remain writable so that the
        record can still be archived and annotated.
        """
        protected = {
            "product_id",
            "lot_id",
            "batch_type",
            "planned_qty",
            "theoretical_yield_qty",
            "actual_yield_qty",
            "yield_min_percentage",
            "yield_max_percentage",
            "date_manufacture",
            "date_expiry",
            "parent_batch_id",
            "company_id",
        }
        touched = protected.intersection(vals)
        if touched:
            for batch in self:
                if batch.state in BATCH_CLOSED_STATES:
                    raise UserError(
                        self.env._(
                            "Batch %(name)s is in state %(state)s. The fields "
                            "%(fields)s can no longer be modified because a "
                            "quality decision has been recorded against them.",
                            name=batch.name,
                            state=batch.state,
                            fields=", ".join(sorted(touched)),
                        )
                    )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_pharma_batch(self):
        """Forbid the deletion of a batch that carries a quality decision."""
        for batch in self:
            if batch.state != "draft":
                raise UserError(
                    self.env._(
                        "Batch %(name)s has left the draft state and can no "
                        "longer be deleted. Cancel it instead so that the "
                        "record is retained.",
                        name=batch.name,
                    )
                )

    def copy_data(self, default=None):
        """Reset the execution data when a batch is duplicated."""
        default = dict(default or {})
        default.setdefault("state", "draft")
        default.setdefault("name", self.env._("New"))
        return super().copy_data(default=default)

    # ------------------------------------------------------------------
    # State machine
    # ------------------------------------------------------------------
    def _assert_state(self, expected_states, action_label):
        """Raise unless every record is in one of ``expected_states``.

        :param tuple expected_states: technical states that permit the action.
        :param str action_label: label used in the error message.
        :raises UserError: when a record is in an unexpected state.
        """
        for batch in self:
            if batch.state not in expected_states:
                raise UserError(
                    self.env._(
                        "Batch %(name)s is in state %(state)s and the action "
                        "%(action)s is not permitted from that state.",
                        name=batch.name,
                        state=batch.state,
                        action=action_label,
                    )
                )

    def action_start(self):
        """Start production of the selected batches."""
        self._assert_state(("draft",), self.env._("Start Production"))
        for batch in self:
            batch.write(
                {
                    "state": "in_process",
                    "date_start": batch.date_start or fields.Datetime.now(),
                }
            )
        return True

    def action_complete(self):
        """Declare manufacturing complete and record who declared it."""
        self._assert_state(("in_process",), self.env._("Complete Manufacturing"))
        for batch in self:
            if batch.actual_yield_qty <= 0.0:
                raise UserError(
                    self.env._(
                        "The actual yield of batch %(name)s must be recorded "
                        "before manufacturing can be declared complete. "
                        "21 CFR 211.103 requires that actual yields be "
                        "determined at the conclusion of each appropriate "
                        "phase of manufacturing.",
                        name=batch.name,
                    )
                )
            batch.write(
                {
                    "state": "manufactured",
                    "date_end": batch.date_end or fields.Datetime.now(),
                    "user_manufactured_id": self.env.user.id,
                }
            )
            if batch.yield_investigation_required:
                batch.message_post(
                    body=self.env._(
                        "The percentage of theoretical yield is %(value).2f%% "
                        "and falls outside the established limits. "
                        "21 CFR 211.192 requires a thorough investigation "
                        "before the batch is released.",
                        value=batch.yield_percentage,
                    )
                )
        return True

    def action_quarantine(self):
        """Place the selected batches in quarantine."""
        self._assert_state(
            ("manufactured", "under_review"), self.env._("Place in Quarantine")
        )
        self.write({"state": "quarantine"})
        return True

    def action_submit_review(self):
        """Submit the selected batches to the quality unit for record review.

        21 CFR 211.192 requires that all production and control records be
        reviewed and approved by the quality control unit before a batch is
        released or distributed.
        """
        self._assert_state(
            ("manufactured", "quarantine"), self.env._("Submit for QA Review")
        )
        for batch in self:
            if not batch.batch_record_ids:
                raise UserError(
                    self.env._(
                        "Batch %(name)s has no batch record. "
                        "21 CFR 211.188 requires that batch production and "
                        "control records be prepared for each batch produced.",
                        name=batch.name,
                    )
                )
            batch.write(
                {"state": "under_review", "user_reviewed_id": self.env.user.id}
            )
        return True

    def action_open_release_wizard(self):
        """Open the wizard that records the release decision.

        :returns: an action descriptor opening the release wizard.
        :rtype: dict
        """
        self.ensure_one()
        self._assert_state(("under_review",), self.env._("Release Decision"))
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Batch Release Decision"),
            "res_model": "ls.pharma.batch.release.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_batch_id": self.id},
        }

    def action_cancel(self):
        """Cancel the selected batches."""
        self._assert_state(BATCH_CANCELLABLE_STATES, self.env._("Cancel"))
        self.write({"state": "cancelled"})
        return True

    def action_set_draft(self):
        """Return a cancelled batch to the draft state."""
        self._assert_state(("cancelled",), self.env._("Reset to Draft"))
        self.write({"state": "draft"})
        return True

    # ------------------------------------------------------------------
    # Navigation helpers
    # ------------------------------------------------------------------
    def _action_open_related(self, model, domain, name):
        """Return an action listing the records of ``model`` in ``domain``.

        :param str model: technical name of the target model.
        :param list domain: search domain applied to the target model.
        :param str name: title of the resulting action.
        :rtype: dict
        """
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": name,
            "res_model": model,
            "view_mode": "list,form",
            "domain": domain,
            "context": {"default_batch_id": self.id},
        }

    def action_view_batch_records(self):
        """Open the batch records attached to this batch."""
        return self._action_open_related(
            "ls.pharma.batch_record",
            [("batch_id", "=", self.id)],
            self.env._("Batch Records"),
        )

    def action_view_stability_studies(self):
        """Open the stability studies that cover this batch."""
        return self._action_open_related(
            "ls.pharma.stability_study",
            [("batch_id", "=", self.id)],
            self.env._("Stability Studies"),
        )

    def action_view_serialization(self):
        """Open the serialised units generated for this batch."""
        return self._action_open_related(
            "ls.pharma.serialization",
            [("batch_id", "=", self.id)],
            self.env._("Serialised Units"),
        )

    def action_view_child_batches(self):
        """Open the packaging batches derived from this batch."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Derived Batches"),
            "res_model": "ls.pharma.batch",
            "view_mode": "list,form",
            "domain": [("parent_batch_id", "=", self.id)],
            "context": {"default_parent_batch_id": self.id},
        }

    # ------------------------------------------------------------------
    # Scheduled action
    # ------------------------------------------------------------------
    @api.model
    def cron_notify_expiring_batches(self):
        """Post a message on released batches that are approaching expiry.

        The horizon is taken from the company configuration.  A message is
        posted rather than an activity so that the notification never depends
        on a responsible user being configured.

        :returns: the number of batches that were notified.
        :rtype: int
        """
        today = fields.Date.context_today(self)
        notified = 0
        for company in self.env["res.company"].search([]):
            horizon = company.pharma_batch_expiry_alert_days
            if horizon <= 0:
                continue
            limit_date = today + relativedelta(days=horizon)
            batches = self.search(
                [
                    ("company_id", "=", company.id),
                    ("state", "=", "released"),
                    ("date_expiry", "!=", False),
                    ("date_expiry", "<=", limit_date),
                    ("date_expiry", ">=", today),
                ]
            )
            for batch in batches:
                batch.message_post(
                    body=self.env._(
                        "Released batch %(name)s expires on %(date)s, which "
                        "is within the configured alert horizon of %(days)s "
                        "days.",
                        name=batch.name,
                        date=batch.date_expiry,
                        days=horizon,
                    )
                )
                notified += 1
        return notified

    @api.constrains("lot_id", "product_id")
    def _check_lot_id_matches_product(self):
        """The lot must belong to the product of the record.

        :raise ValidationError: when the lot was created for another product.
        """
        for record in self:
            product = record.product_id
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
