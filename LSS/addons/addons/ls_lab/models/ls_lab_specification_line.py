# Part of the Life Sciences Suite. See LICENSE file for full copyright and licensing details.
"""One acceptance criterion within a product specification."""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

FROZEN_SPECIFICATION_STATES = ("approved", "obsolete")


class LsLabSpecificationLine(models.Model):
    """A single test and its acceptance criterion.

    The criterion recorded here is the sole basis on which a test result is
    evaluated. Because the parent specification is frozen once approved, the
    criterion cannot drift away from results already evaluated against it.
    """

    _name = "ls.lab.specification_line"
    _description = "Laboratory Specification Line"
    _order = "specification_id, sequence, id"

    specification_id = fields.Many2one(comodel_name="ls.lab.specification", required=True,
                                       ondelete="cascade",
                                       index=True,)
    sequence = fields.Integer(default=10)
    test_method_id = fields.Many2one(comodel_name="ls.lab.test_method", required=True,
                                     index=True,
                                     domain="[('state', '=', 'approved')]",
                                     )
    result_type = fields.Selection(related="test_method_id.result_type", store=True,
                                   readonly=True,)
    criterion_type = fields.Selection(
        selection=[
            ("range", "Between Min and Max"),
            ("min", "Not Less Than"),
            ("max", "Not More Than"),
            ("text", "Text Match"),
            ("boolean", "Pass / Fail"),
            ("informative", "Informative Only"),
        ],
        default="range",
        required=True,
        help="Determines how the recorded result is evaluated. "
             "'Informative Only' records a value without evaluating conformity.",
    )
    min_value = fields.Float(string="Minimum", digits=(16, 6))
    max_value = fields.Float(string="Maximum", digits=(16, 6))
    target_value = fields.Float(string="Target", digits=(16, 6))
    text_criterion = fields.Char(
        string="Expected Text",
        help="Expected result text. Comparison is case-insensitive and ignores "
             "leading and trailing whitespace.",
    )
    uom_id = fields.Many2one(
        comodel_name="uom.uom",
        string="Unit of Measure",
    )
    decimal_precision = fields.Integer(string="Decimal Places", default=2)
    is_mandatory = fields.Boolean(
        string="Mandatory",
        default=True,
        help="Mandatory tests must carry a result before the sample can move "
             "to Results Recorded.",
    )
    report_on_coa = fields.Boolean(
        string="Show On CoA",
        default=True,
        help="Include this test on the Certificate of Analysis.",
    )
    criterion_display = fields.Char(
        string="Acceptance Criterion",
        compute="_compute_criterion_display",
        store=True,
        help="Human readable rendering of the acceptance criterion, used in "
             "listings and on the Certificate of Analysis.",
    )
    company_id = fields.Many2one(related="specification_id.company_id", store=True,
                                 index=True,)

    _sequence_positive = models.Constraint(
        "CHECK (sequence >= 0)",
        "The specification line sequence must be zero or positive.",
    )

    @api.depends(
        "criterion_type",
        "min_value",
        "max_value",
        "text_criterion",
        "uom_id",
        "decimal_precision",
    )
    def _compute_criterion_display(self):
        """Render the acceptance criterion as readable text."""
        for line in self:
            unit = f" {line.uom_id.name}" if line.uom_id else ""
            precision = max(line.decimal_precision, 0)
            if line.criterion_type == "range":
                line.criterion_display = (
                    f"{line.min_value:.{precision}f} - "
                    f"{line.max_value:.{precision}f}{unit}"
                )
            elif line.criterion_type == "min":
                line.criterion_display = f">= {line.min_value:.{precision}f}{unit}"
            elif line.criterion_type == "max":
                line.criterion_display = f"<= {line.max_value:.{precision}f}{unit}"
            elif line.criterion_type == "text":
                line.criterion_display = line.text_criterion or ""
            elif line.criterion_type == "boolean":
                line.criterion_display = self.env._("Pass")
            else:
                line.criterion_display = self.env._("Informative only")

    @api.depends("test_method_id", "criterion_display")
    def _compute_display_name(self):
        """Show the method name with its criterion."""
        for line in self:
            method = line.test_method_id.name or ""
            line.display_name = f"{method}: {line.criterion_display or ''}".strip()

    @api.constrains("test_method_id")
    def _check_method_approved(self):
        """Only approved test methods may be referenced (BRU-04)."""
        for line in self:
            if line.test_method_id.state != "approved":
                raise ValidationError(
                    self.env._(
                        "Test method '%(method)s' is not approved and cannot be "
                        "used in a specification.",
                        method=line.test_method_id.display_name,
                    )
                )

    @api.constrains("criterion_type", "min_value", "max_value", "text_criterion")
    def _check_criterion_consistency(self):
        """Each criterion type must carry the values it needs (BRU-30)."""
        for line in self:
            if line.criterion_type == "range":
                if line.min_value > line.max_value:
                    raise ValidationError(
                        self.env._(
                            "On '%(line)s' the minimum (%(minimum)s) is greater "
                            "than the maximum (%(maximum)s).",
                            line=line.display_name,
                            minimum=line.min_value,
                            maximum=line.max_value,
                        )
                    )
            elif line.criterion_type == "text" and not line.text_criterion:
                raise ValidationError(
                    self.env._(
                        "A text criterion requires the expected text on "
                        "'%(line)s'.",
                        line=line.display_name,
                    )
                )

    # ------------------------------------------------------------------
    # Parent immutability
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Refuse creation of a line on a frozen specification (BRU-03)."""
        specification_ids = [
            vals["specification_id"] for vals in vals_list if vals.get("specification_id")
        ]
        self._assert_parent_editable(
            self.env["ls.lab.specification"].browse(specification_ids)
        )
        return super().create(vals_list)

    def write(self, vals):
        """Refuse modification of a line on a frozen specification (BRU-03)."""
        self._assert_parent_editable(self.mapped("specification_id"))
        if vals.get("specification_id"):
            self._assert_parent_editable(
                self.env["ls.lab.specification"].browse(vals["specification_id"])
            )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_lab_specification_line(self):
        """Refuse deletion of a line on a frozen specification (BRU-03)."""
        self._assert_parent_editable(self.mapped("specification_id"))

    @api.model
    def _assert_parent_editable(self, specifications):
        """Raise if any given specification is approved or obsolete."""
        frozen = specifications.filtered(
            lambda spec: spec.state in FROZEN_SPECIFICATION_STATES
        )
        if frozen:
            raise UserError(
                self.env._(
                    "Specification(s) %(records)s are approved and their "
                    "acceptance criteria can no longer be changed. Create a new "
                    "version instead.",
                    records=", ".join(frozen.mapped("display_name")),
                )
            )

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------
    def _evaluate(self, result_numeric, result_text, result_boolean):
        """Return the conformity verdict for a recorded result.

        Returns one of ``pending``, ``conform``, ``non_conform`` or
        ``informative``. This is the single point at which conformity is
        decided; extending modules add criterion types by overriding it.
        """
        self.ensure_one()
        if self.criterion_type == "informative":
            return "informative"
        if self.criterion_type == "boolean":
            if not result_boolean:
                return "pending"
            return "conform" if result_boolean == "pass" else "non_conform"
        if self.criterion_type == "text":
            if not result_text:
                return "pending"
            expected = (self.text_criterion or "").strip().lower()
            actual = result_text.strip().lower()
            return "conform" if actual == expected else "non_conform"
        if result_numeric is None:
            return "pending"
        if self.criterion_type == "range":
            conform = self.min_value <= result_numeric <= self.max_value
        elif self.criterion_type == "min":
            conform = result_numeric >= self.min_value
        elif self.criterion_type == "max":
            conform = result_numeric <= self.max_value
        else:
            return "pending"
        return "conform" if conform else "non_conform"
