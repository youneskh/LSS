# Part of the Life Sciences Suite. See LICENSE file for full copyright
# and licensing details.
"""Risk matrix configuration.

ISO 14971:2019 requires the manufacturer to establish objective criteria for
risk acceptability, and does not itself prescribe acceptable risk levels.
These models therefore hold the acceptability criteria as configuration data
that the organisation defines, approves and version-controls, rather than as
values built into the source code.

A matrix is made of:

* ordinal *severity* levels and ordinal *probability* levels
  (:class:`LsRiskMatrixLevel`), and
* one cell per (severity, probability) pair (:class:`LsRiskMatrixCell`) that
  carries the resulting risk band and the acceptability decision.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from . import constants


class LsRiskMatrix(models.Model):
    """A named, approvable set of risk acceptability criteria."""

    _name = "ls.risk.matrix"
    _description = "Risk Matrix"
    _inherit = ["mail.thread", "ls.risk.role.mixin"]
    _order = "sequence, name"

    name = fields.Char(required=True,
                       tracking=True,
                       help="Name of the risk matrix as referenced by the risk management plan.",)
    code = fields.Char(required=True,
                       tracking=True,
                       help="Short unique code of the matrix within the company.",)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,
                                 help="Company owning this set of acceptability criteria.",)
    state = fields.Selection(
        selection=constants.MATRIX_STATES,
        string="Status",
        default="draft",
        required=True,
        tracking=True,
        copy=False,
    )
    is_default = fields.Boolean(
        string="Default Matrix",
        tracking=True,
        help="Proposed by default on new risk register entries of this company.",
    )
    reference_document = fields.Char(help="Identifier of the controlled procedure or risk management plan "
                                     "that defines these acceptability criteria.",)
    description = fields.Text()
    approved_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                     copy=False,
                                     tracking=True,)
    approval_date = fields.Datetime(readonly=True, copy=False, tracking=True)
    obsolete_reason = fields.Text(string="Obsolescence Reason", readonly=True, copy=False)

    level_ids = fields.One2many(
        comodel_name="ls.risk.matrix.level",
        inverse_name="matrix_id",
        string="Levels",
    )
    severity_level_ids = fields.One2many(
        comodel_name="ls.risk.matrix.level",
        inverse_name="matrix_id",
        string="Severity Levels",
        domain=[("scale", "=", "severity")],
        context={"default_scale": "severity"},
    )
    probability_level_ids = fields.One2many(
        comodel_name="ls.risk.matrix.level",
        inverse_name="matrix_id",
        string="Probability Levels",
        domain=[("scale", "=", "probability")],
        context={"default_scale": "probability"},
    )
    cell_ids = fields.One2many(
        comodel_name="ls.risk.matrix.cell",
        inverse_name="matrix_id",
        string="Cells",
    )
    severity_level_count = fields.Integer(compute="_compute_level_counts")
    probability_level_count = fields.Integer(compute="_compute_level_counts")
    cell_count = fields.Integer(compute="_compute_level_counts")
    expected_cell_count = fields.Integer(compute="_compute_level_counts")
    is_complete = fields.Boolean(
        string="Complete",
        compute="_compute_level_counts",
        help="True when exactly one cell exists for every severity and "
        "probability combination.",
    )

    _code_company_uniq = models.Constraint(
        "UNIQUE(code, company_id)",
        "The matrix code must be unique per company.",
    )

    @api.depends("severity_level_ids", "probability_level_ids", "cell_ids")
    def _compute_level_counts(self):
        """Count levels and cells and derive matrix completeness."""
        for matrix in self:
            severity_count = len(matrix.severity_level_ids)
            probability_count = len(matrix.probability_level_ids)
            expected = severity_count * probability_count
            matrix.severity_level_count = severity_count
            matrix.probability_level_count = probability_count
            matrix.cell_count = len(matrix.cell_ids)
            matrix.expected_cell_count = expected
            matrix.is_complete = bool(expected) and matrix._has_all_cells()

    def _has_all_cells(self):
        """Return whether every (severity, probability) pair has one cell.

        :return: ``True`` when the cell set covers the full grid exactly once.
        :rtype: bool
        """
        self.ensure_one()
        expected_pairs = {
            (severity.value, probability.value)
            for severity in self.severity_level_ids
            for probability in self.probability_level_ids
        }
        actual_pairs = [
            (cell.severity_value, cell.probability_value) for cell in self.cell_ids
        ]
        return len(actual_pairs) == len(expected_pairs) and set(actual_pairs) == expected_pairs

    @api.depends("name", "code")
    def _compute_display_name(self):
        """Show the matrix code together with its name."""
        for matrix in self:
            matrix.display_name = f"[{matrix.code}] {matrix.name}" if matrix.code else matrix.name

    @api.constrains("is_default", "company_id", "active")
    def _check_single_default(self):
        """Forbid more than one active default matrix per company."""
        for matrix in self:
            if not (matrix.is_default and matrix.active):
                continue
            duplicate = self.search_count(
                [
                    ("id", "!=", matrix.id),
                    ("company_id", "=", matrix.company_id.id),
                    ("is_default", "=", True),
                    ("active", "=", True),
                ]
            )
            if duplicate:
                raise ValidationError(
                    self.env._(
                        "Company %(company)s already has an active default risk "
                        "matrix. Clear the existing default before setting a new one.",
                        company=matrix.company_id.display_name,
                    )
                )

    def get_cell(self, severity_value, probability_value):
        """Return the cell for a (severity, probability) pair.

        :param int severity_value: ordinal value of the severity level.
        :param int probability_value: ordinal value of the probability level.
        :return: the matching cell, or an empty recordset when the matrix does
            not define that combination.
        :rtype: :class:`odoo.models.Model`
        """
        self.ensure_one()
        return self.cell_ids.filtered(
            lambda cell: cell.severity_value == severity_value
            and cell.probability_value == probability_value
        )[:1]

    def action_generate_cells(self):
        """Create the missing cells of the grid, leaving existing cells intact.

        New cells are created with the lowest risk band and an
        ``acceptable`` decision so that the organisation must deliberately
        raise them; no acceptability threshold is inferred by the module.

        :return: ``True`` when the operation completed.
        :rtype: bool
        """
        cell_model = self.env["ls.risk.matrix.cell"]
        for matrix in self:
            if matrix.state != "draft":
                raise UserError(
                    self.env._("Cells can only be generated while the matrix is in Draft.")
                )
            existing = {
                (cell.severity_value, cell.probability_value) for cell in matrix.cell_ids
            }
            to_create = [
                {
                    "matrix_id": matrix.id,
                    "severity_value": severity.value,
                    "probability_value": probability.value,
                    "risk_level": constants.RISK_LEVEL_ORDER[0],
                    "acceptability": "acceptable",
                }
                for severity in matrix.severity_level_ids
                for probability in matrix.probability_level_ids
                if (severity.value, probability.value) not in existing
            ]
            if to_create:
                cell_model.create(to_create)
        return True

    def action_approve(self):
        """Approve the matrix so that it can be used on assessments.

        :raise UserError: when the matrix is not in draft, is incomplete, or
            has no levels defined.
        :return: ``True`` when all matrices were approved.
        :rtype: bool
        """
        self._ensure_risk_manager(self.env._("approve a risk matrix"))
        for matrix in self:
            if matrix.state != "draft":
                raise UserError(
                    self.env._("Only a draft risk matrix can be approved.")
                )
            if not matrix.severity_level_ids or not matrix.probability_level_ids:
                raise UserError(
                    self.env._(
                        "Matrix %(name)s must define at least one severity level "
                        "and one probability level before approval.",
                        name=matrix.display_name,
                    )
                )
            if not matrix._has_all_cells():
                raise UserError(
                    self.env._(
                        "Matrix %(name)s is incomplete: every severity and "
                        "probability combination must have exactly one cell. "
                        "Use 'Generate Missing Cells' and review each cell.",
                        name=matrix.display_name,
                    )
                )
            matrix.write(
                {
                    "state": "approved",
                    "approved_by_id": self.env.user.id,
                    "approval_date": fields.Datetime.now(),
                }
            )
        return True

    def action_set_obsolete(self):
        """Mark the matrix obsolete, preventing its use on new assessments.

        Existing assessments keep their matrix reference so that historical
        records remain interpretable.

        :raise UserError: when the matrix is not approved.
        :return: ``True`` when all matrices were made obsolete.
        :rtype: bool
        """
        self._ensure_risk_manager(self.env._("make a risk matrix obsolete"))
        for matrix in self:
            if matrix.state != "approved":
                raise UserError(
                    self.env._("Only an approved risk matrix can be made obsolete.")
                )
            matrix.write({"state": "obsolete", "is_default": False})
        return True


class LsRiskMatrixLevel(models.Model):
    """One ordinal level of a severity or probability scale."""

    _name = "ls.risk.matrix.level"
    _description = "Risk Matrix Level"
    _order = "matrix_id, scale, value"

    matrix_id = fields.Many2one(comodel_name="ls.risk.matrix", required=True,
                                ondelete="cascade",
                                index=True,)
    scale = fields.Selection(selection=constants.MATRIX_SCALES, required=True,)
    value = fields.Integer(required=True,
                           help="Ordinal value of this level. Higher values denote higher "
                           "severity or higher probability.",)
    name = fields.Char(string="Label", required=True)
    description = fields.Text(
        string="Definition",
        help="Objective definition of this level, as recorded in the risk "
        "management plan.",
    )
    company_id = fields.Many2one(comodel_name="res.company", related="matrix_id.company_id",
                                 store=True,
                                 readonly=True,
                                 index=True,)

    _value_uniq = models.Constraint(
        "UNIQUE(matrix_id, scale, value)",
        "Each level value may appear only once per scale within a matrix.",
    )
    _value_positive = models.Constraint(
        "CHECK(value > 0)",
        "A risk matrix level value must be strictly positive.",
    )

    @api.depends("name", "value", "scale")
    def _compute_display_name(self):
        """Show the ordinal value alongside the label."""
        for level in self:
            level.display_name = f"{level.value} - {level.name}"


class LsRiskMatrixCell(models.Model):
    """The risk band and acceptability decision for one matrix cell."""

    _name = "ls.risk.matrix.cell"
    _description = "Risk Matrix Cell"
    _order = "matrix_id, severity_value desc, probability_value desc"

    matrix_id = fields.Many2one(comodel_name="ls.risk.matrix", required=True,
                                ondelete="cascade",
                                index=True,)
    severity_value = fields.Integer(required=True)
    probability_value = fields.Integer(required=True)
    risk_level = fields.Selection(selection=constants.RISK_LEVELS, required=True,
                                  default=constants.RISK_LEVEL_ORDER[0],)
    acceptability = fields.Selection(selection=constants.ACCEPTABILITY, required=True,
                                     default="acceptable",
                                     help="Acceptability decision defined by the organisation for this "
                                     "combination of severity and probability.",)
    company_id = fields.Many2one(comodel_name="res.company", related="matrix_id.company_id",
                                 store=True,
                                 readonly=True,
                                 index=True,)

    _cell_uniq = models.Constraint(
        "UNIQUE(matrix_id, severity_value, probability_value)",
        "Only one cell may exist per severity and probability combination.",
    )
    _severity_positive = models.Constraint(
        "CHECK(severity_value > 0)",
        "The severity value of a matrix cell must be strictly positive.",
    )
    _probability_positive = models.Constraint(
        "CHECK(probability_value > 0)",
        "The probability value of a matrix cell must be strictly positive.",
    )

    @api.constrains("severity_value", "probability_value", "matrix_id")
    def _check_values_exist(self):
        """Ensure a cell only references levels declared on its matrix."""
        for cell in self:
            severity_values = cell.matrix_id.severity_level_ids.mapped("value")
            probability_values = cell.matrix_id.probability_level_ids.mapped("value")
            if cell.severity_value not in severity_values:
                raise ValidationError(
                    self.env._(
                        "Severity value %(value)s is not defined on matrix %(name)s.",
                        value=cell.severity_value,
                        name=cell.matrix_id.display_name,
                    )
                )
            if cell.probability_value not in probability_values:
                raise ValidationError(
                    self.env._(
                        "Probability value %(value)s is not defined on matrix %(name)s.",
                        value=cell.probability_value,
                        name=cell.matrix_id.display_name,
                    )
                )

    @api.depends("severity_value", "probability_value", "risk_level")
    def _compute_display_name(self):
        """Show the coordinates and resulting band of the cell."""
        labels = dict(constants.RISK_LEVELS)
        for cell in self:
            cell.display_name = (
                f"S{cell.severity_value} / P{cell.probability_value} "
                f"- {labels.get(cell.risk_level, cell.risk_level)}"
            )
