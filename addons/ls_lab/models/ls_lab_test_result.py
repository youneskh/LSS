# Part of the Life Sciences Suite. See LICENSE file for full copyright and licensing details.
"""Individual analytical test results."""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

SAMPLE_STATES_OPEN_FOR_ENTRY = ("in_progress", "testing")


class LsLabTestResult(models.Model):
    """One test result for one specification line of one sample.

    The ``evaluation`` field is computed from the approved specification line
    and stored. It is not writable through any view, so conformity cannot be
    asserted by a user; it is always derived from the recorded value and the
    approved acceptance criterion.
    """

    _name = "ls.lab.test_result"
    _description = "Laboratory Test Result"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sample_id, sequence, id"

    sample_id = fields.Many2one(comodel_name="ls.lab.sample", required=True,
                                ondelete="cascade",
                                index=True,)
    specification_line_id = fields.Many2one(
        comodel_name="ls.lab.specification_line",
        string="Specification Line",
        required=True,
        ondelete="restrict",
        index=True,
    )
    test_method_id = fields.Many2one(related="specification_line_id.test_method_id", store=True,
                                     index=True,)
    sequence = fields.Integer(related="specification_line_id.sequence", store=True,)
    criterion_display = fields.Char(
        related="specification_line_id.criterion_display",
        string="Acceptance Criterion",
        store=True,
    )
    result_type = fields.Selection(related="specification_line_id.result_type", store=True,)
    criterion_type = fields.Selection(related="specification_line_id.criterion_type", store=True,)
    is_mandatory = fields.Boolean(
        related="specification_line_id.is_mandatory",
        string="Mandatory",
        store=True,
    )
    product_id = fields.Many2one(related="sample_id.product_id", store=True,
                                 index=True,)
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("entered", "Entered"),
            ("reviewed", "Reviewed"),
        ],
        string="Status",
        default="draft",
        required=True,
        copy=False,
        tracking=True,
    )
    result_numeric = fields.Float(
        string="Numeric Result",
        digits=(16, 6),
        tracking=True,
    )
    result_text = fields.Char(string="Text Result", tracking=True)
    result_boolean = fields.Selection(
        selection=[("pass", "Pass"), ("fail", "Fail")],
        string="Pass / Fail Result",
        tracking=True,
    )
    result_display = fields.Char(
        string="Result",
        compute="_compute_result_display",
        store=True,
        help="Rendering of the recorded result for listings and reports.",
    )
    uom_id = fields.Many2one(comodel_name="uom.uom", string="Unit of Measure")
    evaluation = fields.Selection(
        selection=[
            ("pending", "Pending"),
            ("conform", "Conforms"),
            ("non_conform", "Out Of Specification"),
            ("informative", "Informative"),
        ],
        compute="_compute_evaluation",
        store=True,
        readonly=True,
        tracking=True,
        help="Derived from the approved specification. This field is computed "
             "and cannot be set by a user.",
    )
    is_oot = fields.Boolean(
        string="Out Of Trend",
        tracking=True,
        help="Asserted by the analyst or reviewer. This module performs no "
             "statistical trend analysis; the determination is made outside "
             "the system and recorded here with its justification.",
    )
    oot_justification = fields.Text(string="Out Of Trend Justification")
    analyst_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                 copy=False,
                                 tracking=True,)
    test_date = fields.Datetime(tracking=True)
    instrument_reference = fields.Char(help="Free-text reference to the instrument used. Calibration records "
                                       "are held in the calibration management module.",)
    reviewed_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                     copy=False,
                                     tracking=True,)
    review_date = fields.Datetime(readonly=True, copy=False)
    oos_id = fields.Many2one(
        comodel_name="ls.lab.oos",
        string="Investigation",
        readonly=True,
        copy=False,
        index=True,
    )
    is_retest = fields.Boolean(readonly=True, copy=False)
    retest_of_id = fields.Many2one(comodel_name="ls.lab.test_result", readonly=True,
                                   copy=False,)
    remarks = fields.Text()
    company_id = fields.Many2one(related="sample_id.company_id", store=True,
                                 index=True,)

    _sequence_positive = models.Constraint(
        "CHECK (sequence >= 0)",
        "The test result sequence must be zero or positive.",
    )

    # ------------------------------------------------------------------
    # Computations
    # ------------------------------------------------------------------
    @api.depends(
        "state",
        "result_numeric",
        "result_text",
        "result_boolean",
        "specification_line_id",
        "specification_line_id.criterion_type",
        "specification_line_id.min_value",
        "specification_line_id.max_value",
        "specification_line_id.text_criterion",
    )
    def _compute_evaluation(self):
        """Derive conformity from the approved specification line.

        A result that has not been entered is always ``pending``, so that a
        default numeric value of zero is never mistaken for a real measurement.
        """
        for result in self:
            if result.state == "draft" or not result.specification_line_id:
                result.evaluation = "pending"
                continue
            result.evaluation = result.specification_line_id._evaluate(
                result.result_numeric,
                result.result_text,
                result.result_boolean,
            )

    @api.depends(
        "result_numeric",
        "result_text",
        "result_boolean",
        "result_type",
        "uom_id",
        "state",
        "specification_line_id.decimal_precision",
    )
    def _compute_result_display(self):
        """Render the recorded result as readable text."""
        for result in self:
            if result.state == "draft":
                result.result_display = ""
                continue
            if result.result_type == "numeric":
                precision = max(result.specification_line_id.decimal_precision, 0)
                unit = f" {result.uom_id.name}" if result.uom_id else ""
                result.result_display = f"{result.result_numeric:.{precision}f}{unit}"
            elif result.result_type == "boolean":
                mapping = {"pass": self.env._("Pass"), "fail": self.env._("Fail")}
                result.result_display = mapping.get(result.result_boolean, "")
            else:
                result.result_display = result.result_text or ""

    @api.depends("sample_id", "test_method_id")
    def _compute_display_name(self):
        """Show the sample reference with the method name."""
        for result in self:
            sample = result.sample_id.name or ""
            method = result.test_method_id.name or ""
            result.display_name = f"{sample} / {method}".strip(" /")

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("analyst_id", "reviewed_by_id")
    def _check_reviewer_segregation(self):
        """The reviewer of a result may not be its analyst (BRU-10)."""
        for result in self.filtered(lambda r: r.analyst_id and r.reviewed_by_id):
            if result.analyst_id == result.reviewed_by_id:
                raise ValidationError(
                    self.env._(
                        "User '%(user)s' performed test '%(test)s' and therefore "
                        "cannot also review it. Second-person review requires a "
                        "different user.",
                        user=result.analyst_id.display_name,
                        test=result.display_name,
                    )
                )

    @api.constrains("is_oot", "oot_justification")
    def _check_oot_justified(self):
        """An out-of-trend assertion requires a justification (BRU-28)."""
        for result in self.filtered("is_oot"):
            if not result.oot_justification:
                raise ValidationError(
                    self.env._(
                        "Result '%(test)s' is flagged out of trend but carries no "
                        "justification. Record the basis of the determination.",
                        test=result.display_name,
                    )
                )

    @api.constrains("specification_line_id", "sample_id")
    def _check_line_belongs_to_specification(self):
        """A result must reference a line of its sample's specification."""
        for result in self:
            if result.specification_line_id.specification_id != result.sample_id.specification_id:
                raise ValidationError(
                    self.env._(
                        "Result '%(test)s' references a criterion that does not "
                        "belong to the specification of sample '%(sample)s'.",
                        test=result.display_name,
                        sample=result.sample_id.name,
                    )
                )

    # ------------------------------------------------------------------
    # Creation and modification guards
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Guard manual creation and enforce retest authorisation (BRU-17)."""
        for vals in vals_list:
            if vals.get("is_retest"):
                self._assert_retest_authorised(vals)
            sample = self.env["ls.lab.sample"].browse(vals.get("sample_id"))
            if sample and sample.state in ("approved", "reported", "cancelled"):
                raise UserError(
                    self.env._(
                        "No further result can be added to sample '%(sample)s' "
                        "because it is in status '%(state)s'.",
                        sample=sample.name,
                        state=sample.state,
                    )
                )
        return super().create(vals_list)

    @api.model
    def _assert_retest_authorised(self, vals):
        """Refuse a retest result unless its investigation authorised one."""
        investigation = self.env["ls.lab.oos"].browse(vals.get("oos_id"))
        if not investigation or not investigation.retest_authorised:
            raise UserError(
                self.env._(
                    "A retest result cannot be recorded without a documented "
                    "retest authorisation on the related investigation. Record "
                    "the justification and authorise the retest first."
                )
            )

    def write(self, vals):
        """Refuse modification of a reviewed result."""
        protected = {
            "result_numeric",
            "result_text",
            "result_boolean",
            "uom_id",
            "test_date",
            "instrument_reference",
            "specification_line_id",
        }
        if protected & set(vals):
            reviewed = self.filtered(lambda res: res.state == "reviewed")
            if reviewed:
                raise UserError(
                    self.env._(
                        "%(count)s result(s) have been reviewed and can no longer "
                        "be modified. Record a retest under an investigation "
                        "instead.",
                        count=len(reviewed),
                    )
                )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_lab_test_result(self):
        """Refuse deletion of a result that carries recorded data."""
        recorded = self.filtered(lambda res: res.state != "draft")
        if recorded:
            raise UserError(
                self.env._(
                    "%(count)s result(s) carry recorded data and cannot be "
                    "deleted. The audit history must be preserved.",
                    count=len(recorded),
                )
            )

    # ------------------------------------------------------------------
    # Workflow actions
    # ------------------------------------------------------------------
    def action_enter(self):
        """Record the result, evaluate it, and raise an OOS on failure."""
        for result in self:
            if result.state != "draft":
                raise UserError(
                    self.env._(
                        "Result '%(test)s' has already been entered.",
                        test=result.display_name,
                    )
                )
            if result.sample_id.state not in SAMPLE_STATES_OPEN_FOR_ENTRY:
                raise UserError(
                    self.env._(
                        "Sample '%(sample)s' is in status '%(state)s' and is not "
                        "open for result entry.",
                        sample=result.sample_id.name,
                        state=result.sample_id.state,
                    )
                )
            result.write({
                "state": "entered",
                "analyst_id": self.env.user.id,
                "test_date": result.test_date or fields.Datetime.now(),
            })
        self._raise_investigations()
        return True

    def _raise_investigations(self):
        """Create an investigation for each non-conforming or OOT result.

        Implements BRU-16. One investigation is created per result; results
        already linked to an investigation are skipped.

        The investigation is opened on behalf of the analyst who entered the
        result, with superuser rights: analysts may not create investigations
        by hand, but a failing result must always open one. The analyst is
        recorded as the investigator.
        """
        investigation_model = self.env["ls.lab.oos"].sudo()
        for result in self:
            if result.oos_id:
                continue
            if result.evaluation == "non_conform":
                oos_type = "oos"
            elif result.is_oot:
                oos_type = "oot"
            else:
                continue
            investigation = investigation_model.create({
                "test_result_id": result.id,
                "oos_type": oos_type,
                "investigator_id": self.env.user.id,
                "description": self.env._(
                    "Automatically raised from result '%(test)s'. Recorded value: "
                    "%(value)s. Acceptance criterion: %(criterion)s.",
                    test=result.display_name,
                    value=result.result_display or "",
                    criterion=result.criterion_display or "",
                ),
            })
            result.oos_id = investigation.id
            result.sample_id.message_post(
                body=self.env._(
                    "Investigation %(investigation)s raised for test "
                    "'%(test)s'.",
                    investigation=investigation.name,
                    test=result.test_method_id.name or "",
                )
            )

    def action_review(self):
        """Record second-person review of the result (BRU-10)."""
        for result in self:
            if result.state != "entered":
                raise UserError(
                    self.env._(
                        "Only entered results can be reviewed. Result "
                        "'%(test)s' is in status '%(state)s'.",
                        test=result.display_name,
                        state=result.state,
                    )
                )
            if result.analyst_id == self.env.user:
                raise UserError(
                    self.env._(
                        "You performed test '%(test)s' and cannot review your "
                        "own result.",
                        test=result.display_name,
                    )
                )
        return self.write({
            "state": "reviewed",
            "reviewed_by_id": self.env.user.id,
            "review_date": fields.Datetime.now(),
        })

    def action_reset_draft(self):
        """Return an entered result to draft, before any review."""
        for result in self:
            if result.state != "entered":
                raise UserError(
                    self.env._(
                        "Only entered results can be reset. Result '%(test)s' is "
                        "in status '%(state)s'.",
                        test=result.display_name,
                        state=result.state,
                    )
                )
            if result.oos_id:
                raise UserError(
                    self.env._(
                        "Result '%(test)s' is linked to investigation "
                        "'%(investigation)s' and cannot be reset.",
                        test=result.display_name,
                        investigation=result.oos_id.name,
                    )
                )
        return self.write({"state": "draft", "analyst_id": False})
