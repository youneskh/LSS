# Part of the Life Sciences Suite. See LICENSE file for full copyright and licensing details.
"""Laboratory sample registration and lifecycle."""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

OPEN_OOS_STATES = ("open", "phase1", "phase1_done", "phase2", "concluded")


class LsLabSample(models.Model):
    """A sample submitted to the laboratory for testing.

    Registration binds the sample to one approved specification version and
    generates one result line per specification line. The test list therefore
    cannot be shortened by the analyst.
    """

    _name = "ls.lab.sample"
    _description = "Laboratory Sample"
    _check_company_auto = True
    _inherit = ["ls.lab.signed.mixin", "mail.thread", "mail.activity.mixin"]
    _order = "received_date desc, name desc"

    name = fields.Char(
        string="Sample Reference",
        required=True,
        readonly=True,
        copy=False,
        default="New",
        tracking=True,
    )
    description = fields.Char(tracking=True)
    sample_type = fields.Selection(
        selection=[
            ("raw_material", "Raw Material"),
            ("packaging", "Packaging Material"),
            ("in_process", "In Process"),
            ("finished_product", "Finished Product"),
            ("stability", "Stability"),
            ("retain", "Retain"),
            ("water", "Water"),
            ("cleaning_verification", "Cleaning Verification"),
        ],
        default="finished_product",
        required=True,
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ("received", "Received"),
            ("in_progress", "In Progress"),
            ("testing", "Testing"),
            ("results_recorded", "Results Recorded"),
            ("reviewed", "Reviewed"),
            ("approved", "Approved"),
            ("reported", "Reported"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="received",
        required=True,
        copy=False,
        tracking=True,
    )
    product_id = fields.Many2one(comodel_name="product.product", required=True,
                                 index=True,
                                 tracking=True,)
    lot_id = fields.Many2one(
        comodel_name="stock.lot",
        string="Lot / Serial Number",
        index=True,
        tracking=True,
        check_company=True,
    )
    batch_reference = fields.Char(help="Manufacturing batch reference when the batch is not managed as "
                                  "a stock lot in this database.",)
    specification_id = fields.Many2one(comodel_name="ls.lab.specification", required=True,
                                       index=True,
                                       tracking=True,
                                       domain="[('state', '=', 'approved')]",
                                       help="The approved specification version against which this sample is "
                                       "evaluated. It is captured at registration and does not change.",
                                       )
    quantity = fields.Float(digits=(16, 4))
    uom_id = fields.Many2one(comodel_name="uom.uom", string="Unit of Measure")
    sampled_date = fields.Datetime(string="Sampling Date")
    received_date = fields.Datetime(
        string="Receipt Date",
        default=fields.Datetime.now,
        required=True,
        tracking=True,
    )
    due_date = fields.Date(tracking=True)
    priority = fields.Selection(
        selection=[("0", "Normal"), ("1", "Urgent")],
        default="0",
    )
    sampled_by_id = fields.Many2one(comodel_name="res.users")
    received_by_id = fields.Many2one(comodel_name="res.users", default=lambda self: self.env.user,)
    sampling_point = fields.Char()
    storage_condition_id = fields.Many2one(comodel_name="ls.lab.storage_condition")
    result_ids = fields.One2many(
        comodel_name="ls.lab.test_result",
        inverse_name="sample_id",
        string="Test Results",
    )
    result_count = fields.Integer(
        string="Results", compute="_compute_result_statistics"
    )
    pending_result_count = fields.Integer(
        string="Pending Results", compute="_compute_result_statistics"
    )
    overall_result = fields.Selection(
        selection=[
            ("pending", "Pending"),
            ("conform", "Conforms"),
            ("non_conform", "Does Not Conform"),
        ],
        compute="_compute_overall_result",
        store=True,
        tracking=True,
    )
    oos_ids = fields.One2many(
        comodel_name="ls.lab.oos",
        inverse_name="sample_id",
        string="OOS / OOT Investigations",
    )
    open_oos_count = fields.Integer(
        string="Open Investigations", compute="_compute_open_oos_count"
    )
    reviewed_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                     copy=False,
                                     tracking=True,)
    review_date = fields.Datetime(readonly=True, copy=False)
    approved_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                     copy=False,
                                     tracking=True,)
    approval_date = fields.Datetime(readonly=True, copy=False)
    reported_by_id = fields.Many2one(comodel_name="res.users", readonly=True, copy=False)
    report_date = fields.Datetime(readonly=True, copy=False)
    cancel_reason = fields.Text(string="Cancellation Reason", readonly=True, copy=False)
    cancelled_by_id = fields.Many2one(comodel_name="res.users", readonly=True, copy=False)
    stability_timepoint_id = fields.Many2one(
        comodel_name="ls.lab.stability_timepoint",
        string="Stability Time Point",
        readonly=True,
        copy=False,
        index=True,
    )
    coa_ids = fields.One2many(
        comodel_name="ls.lab.coa",
        inverse_name="sample_id",
        string="Certificates of Analysis",
    )
    coa_count = fields.Integer(string="Certificates", compute="_compute_coa_count")
    company_id = fields.Many2one(comodel_name="res.company", default=lambda self: self.env.company,
                                 index=True,)

    _name_uniq = models.Constraint(
        "UNIQUE (name)",
        "The sample reference must be unique.",
    )

    # ------------------------------------------------------------------
    # Computations
    # ------------------------------------------------------------------
    @api.depends("result_ids.state", "result_ids.specification_line_id")
    def _compute_result_statistics(self):
        """Count total results and those still awaiting entry."""
        for sample in self:
            results = sample.result_ids
            sample.result_count = len(results)
            sample.pending_result_count = len(
                results.filtered(
                    lambda res: res.state == "draft"
                    and res.specification_line_id.is_mandatory
                )
            )

    @api.depends("result_ids.evaluation", "result_ids.state")
    def _compute_overall_result(self):
        """Derive the sample verdict from its result lines.

        A sample conforms only when every mandatory, evaluated result conforms.
        Informative results never drive the verdict.
        """
        for sample in self:
            evaluated = sample.result_ids.filtered(
                lambda res: res.evaluation in ("conform", "non_conform")
            )
            mandatory = sample.result_ids.filtered(
                lambda res: res.specification_line_id.is_mandatory
            )
            if any(res.evaluation == "non_conform" for res in evaluated):
                sample.overall_result = "non_conform"
            elif mandatory and all(
                res.evaluation in ("conform", "informative") for res in mandatory
            ):
                sample.overall_result = "conform"
            else:
                sample.overall_result = "pending"

    @api.depends("oos_ids.state")
    def _compute_open_oos_count(self):
        """Count investigations on the sample that are not yet closed."""
        for sample in self:
            sample.open_oos_count = len(
                sample.oos_ids.filtered(lambda oos: oos.state in OPEN_OOS_STATES)
            )

    @api.depends("coa_ids")
    def _compute_coa_count(self):
        """Count certificates issued from the sample."""
        for sample in self:
            sample.coa_count = len(sample.coa_ids)

    @api.depends("name", "product_id")
    def _compute_display_name(self):
        """Show the sample reference with its product."""
        for sample in self:
            product = sample.product_id.display_name or ""
            sample.display_name = f"{sample.name} - {product}".strip(" -")

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("specification_id")
    def _check_specification_approved(self):
        """A sample must reference an approved specification (BRU-06)."""
        for sample in self:
            if sample.specification_id.state != "approved":
                raise ValidationError(
                    self.env._(
                        "Specification '%(spec)s' is not approved and cannot be "
                        "used for sample '%(sample)s'.",
                        spec=sample.specification_id.display_name,
                        sample=sample.name,
                    )
                )

    @api.constrains("reviewed_by_id", "result_ids")
    def _check_reviewer_segregation(self):
        """The sample reviewer may not have produced any of its results.

        Implements BRU-13, the second-person verification principle.
        """
        for sample in self.filtered("reviewed_by_id"):
            analysts = sample.result_ids.mapped("analyst_id")
            if sample.reviewed_by_id in analysts:
                raise ValidationError(
                    self.env._(
                        "User '%(user)s' entered results on sample '%(sample)s' "
                        "and therefore cannot also review it. A different user "
                        "must perform the review.",
                        user=sample.reviewed_by_id.display_name,
                        sample=sample.name,
                    )
                )

    @api.constrains("approved_by_id", "reviewed_by_id")
    def _check_approver_segregation(self):
        """The approver may not be the reviewer (BRU-14)."""
        for sample in self.filtered(lambda s: s.approved_by_id and s.reviewed_by_id):
            if sample.approved_by_id == sample.reviewed_by_id:
                raise ValidationError(
                    self.env._(
                        "User '%(user)s' reviewed sample '%(sample)s' and "
                        "therefore cannot also approve it.",
                        user=sample.approved_by_id.display_name,
                        sample=sample.name,
                    )
                )

    # ------------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Assign the sample reference and generate the test list."""
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "ls.lab.sample"
                ) or "New"
        samples = super().create(vals_list)
        samples._generate_result_lines()
        return samples

    def _generate_result_lines(self):
        """Create one result line per specification line, once.

        Lines already present are left untouched so that re-running this method
        can never disturb recorded data.
        """
        result_model = self.env["ls.lab.test_result"]
        for sample in self:
            existing = sample.result_ids.mapped("specification_line_id")
            missing = sample.specification_id.line_ids - existing
            result_model.create([
                {
                    "sample_id": sample.id,
                    "specification_line_id": line.id,
                    "uom_id": line.uom_id.id or line.test_method_id.default_uom_id.id,
                }
                for line in missing
            ])

    # ------------------------------------------------------------------
    # Workflow actions
    # ------------------------------------------------------------------
    def _assert_state(self, expected, action_label):
        """Raise unless every sample is in one of the expected states."""
        expected = expected if isinstance(expected, (list, tuple, set)) else (expected,)
        wrong = self.filtered(lambda rec: rec.state not in expected)
        if wrong:
            raise UserError(
                self.env._(
                    "Action '%(action)s' is not available for sample(s) "
                    "%(records)s in their current state.",
                    action=action_label,
                    records=", ".join(wrong.mapped("name")),
                )
            )

    def action_start(self):
        """Move a received sample into preparation."""
        self._assert_state("received", "Start")
        return self.write({"state": "in_progress"})

    def action_start_testing(self):
        """Open the sample for result entry."""
        self._assert_state("in_progress", "Start Testing")
        return self.write({"state": "testing"})

    def action_record_results(self):
        """Confirm that all mandatory results have been entered (BRU-11)."""
        self._assert_state("testing", "Record Results")
        for sample in self:
            outstanding = sample.result_ids.filtered(
                lambda res: res.specification_line_id.is_mandatory
                and res.state == "draft"
            )
            if outstanding:
                raise UserError(
                    self.env._(
                        "Sample '%(sample)s' still has %(count)s mandatory test(s) "
                        "without a recorded result.",
                        sample=sample.name,
                        count=len(outstanding),
                    )
                )
        return self.write({"state": "results_recorded"})

    def action_review(self):
        """Record second-person review of the sample (BRU-12)."""
        self._assert_state("results_recorded", "Review")
        for sample in self:
            unreviewed = sample.result_ids.filtered(
                lambda res: res.specification_line_id.is_mandatory
                and res.state != "reviewed"
            )
            if unreviewed:
                raise UserError(
                    self.env._(
                        "Sample '%(sample)s' has %(count)s mandatory result(s) "
                        "that have not been reviewed.",
                        sample=sample.name,
                        count=len(unreviewed),
                    )
                )
        return self.write({
            "state": "reviewed",
            "reviewed_by_id": self.env.user.id,
            "review_date": fields.Datetime.now(),
        })

    def action_approve(self):
        """Approve the sample, refusing while an investigation is open (BRU-15)."""
        self._assert_state("reviewed", "Approve")
        for sample in self:
            open_oos = sample.oos_ids.filtered(
                lambda oos: oos.state in OPEN_OOS_STATES
            )
            if open_oos:
                raise UserError(
                    self.env._(
                        "Sample '%(sample)s' cannot be approved while "
                        "%(count)s investigation(s) remain open: %(records)s.",
                        sample=sample.name,
                        count=len(open_oos),
                        records=", ".join(open_oos.mapped("name")),
                    )
                )
        return self.write({
            "state": "approved",
            "approved_by_id": self.env.user.id,
            "approval_date": fields.Datetime.now(),
        })

    def action_report(self):
        """Mark the sample as reported."""
        self._assert_state("approved", "Report")
        return self.write({
            "state": "reported",
            "reported_by_id": self.env.user.id,
            "report_date": fields.Datetime.now(),
        })

    def action_open_cancel_wizard(self):
        """Open the cancellation wizard, which requires a reason (BRU-26)."""
        self.ensure_one()
        self._assert_state(
            ("received", "in_progress", "testing", "results_recorded", "reviewed"),
            "Cancel",
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": "ls.lab.sample_cancel_wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_sample_id": self.id},
        }

    def action_view_results(self):
        """Open the result lines of this sample."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Test Results"),
            "res_model": "ls.lab.test_result",
            "view_mode": "list,form",
            "domain": [("sample_id", "=", self.id)],
            "context": {"default_sample_id": self.id},
        }

    def action_view_oos(self):
        """Open the investigations raised on this sample."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("OOS / OOT Investigations"),
            "res_model": "ls.lab.oos",
            "view_mode": "list,form",
            "domain": [("sample_id", "=", self.id)],
        }

    def action_view_coa(self):
        """Open the certificates issued from this sample."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Certificates of Analysis"),
            "res_model": "ls.lab.coa",
            "view_mode": "list,form",
            "domain": [("sample_id", "=", self.id)],
            "context": {"default_sample_id": self.id},
        }

    def action_open_approval_signature(self):
        """Open the signature-intent wizard for sample approval."""
        self.ensure_one()
        self._assert_state("reviewed", "Approve")
        return {
            "type": "ir.actions.act_window",
            "res_model": "ls.lab.signature_wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_res_model": self._name,
                "default_res_id": self.id,
                "default_meaning": "approved",
            },
        }

    def _signature_target_action(self):
        """Approve the sample once signature intent has been recorded."""
        return self.action_approve()

    # ------------------------------------------------------------------
    # Scheduled action
    # ------------------------------------------------------------------
    @api.model
    def _cron_notify_overdue_samples(self):
        """Post a notice on samples past their due date.

        This scheduled action is notification-only. It never changes a sample
        state or any other regulated field (BRU-29).
        """
        today = fields.Date.context_today(self)
        overdue = self.search([
            ("due_date", "<", today),
            ("state", "not in", ("approved", "reported", "cancelled")),
        ])
        for sample in overdue:
            sample.message_post(
                body=self.env._(
                    "Sample is past its due date of %(due_date)s and is still in "
                    "status '%(state)s'. This notice does not change the sample "
                    "status.",
                    due_date=sample.due_date,
                    state=sample.state,
                )
            )
        return len(overdue)

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
