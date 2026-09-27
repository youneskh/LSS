# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""In-process parameter readings captured during a moulding run.

Readings are append-only. An erroneous reading is never edited: a new reading
is created that supersedes it and records the reason for the correction, so
that the original value remains visible in the record.

Each reading freezes the acceptance criteria that were in force at the moment
of capture. A later revision of the moulding parameter specification therefore
cannot retroactively change whether a historical reading was in tolerance.
"""

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from ..constants import (
    MEASUREMENT_DIGITS,
    PARAMETER_VALUE_TYPES,
    READING_TYPES,
)

#: Stored computed fields the ORM is allowed to write after creation.
_SYSTEM_WRITABLE_FIELDS = frozenset({"in_tolerance", "company_id"})


class LsMpInjectionMoldingReading(models.Model):
    """One captured value of one moulding parameter."""

    _name = "ls.mp.injection_molding.reading"
    _description = "Medical Plastics Moulding Parameter Reading"
    _order = "run_id, capture_date, id"

    run_id = fields.Many2one(
        comodel_name="ls.mp.injection_molding",
        string="Moulding Run",
        required=True,
        ondelete="cascade",
        index=True,
    )
    parameter_line_id = fields.Many2one(
        comodel_name="ls.mp.molding_parameter.line",
        string="Specification Parameter",
        required=True,
        ondelete="restrict",
        index=True,
    )
    reading_type = fields.Selection(selection=READING_TYPES, required=True,
                                    default="in_process",)
    capture_date = fields.Datetime(
        string="Captured On",
        required=True,
        default=fields.Datetime.now,
        readonly=True,
    )
    recorded_by_id = fields.Many2one(comodel_name="res.users", required=True,
                                     default=lambda self: self.env.user,
                                     ondelete="restrict",
                                     readonly=True,)

    # -- Captured values ----------------------------------------------------
    value_numeric = fields.Float(string="Measured Value", digits=MEASUREMENT_DIGITS)
    value_text = fields.Char(string="Observed Value")

    # -- Frozen acceptance criteria ----------------------------------------
    parameter_name = fields.Char(string="Parameter", required=True, readonly=True)
    parameter_code = fields.Char(required=True, readonly=True)
    parameter_uom = fields.Char(string="Unit", readonly=True)
    value_type = fields.Selection(selection=PARAMETER_VALUE_TYPES, required=True,
                                  readonly=True,)
    target_value = fields.Float(
        string="Target", digits=MEASUREMENT_DIGITS, readonly=True
    )
    min_value = fields.Float(
        string="Minimum", digits=MEASUREMENT_DIGITS, readonly=True
    )
    max_value = fields.Float(
        string="Maximum", digits=MEASUREMENT_DIGITS, readonly=True
    )
    expected_text = fields.Char(string="Expected Value", readonly=True)
    is_critical = fields.Boolean(string="Critical Parameter", readonly=True)

    in_tolerance = fields.Boolean(compute="_compute_in_tolerance",
                                  store=True,
                                  readonly=True,)

    # -- Corrections --------------------------------------------------------
    supersedes_id = fields.Many2one(
        comodel_name="ls.mp.injection_molding.reading",
        string="Supersedes Reading",
        ondelete="restrict",
        readonly=True,
        help="The earlier reading that this entry corrects.",
    )
    superseded_by_ids = fields.One2many(comodel_name="ls.mp.injection_molding.reading",
                                        inverse_name="supersedes_id", readonly=True,)
    is_superseded = fields.Boolean(
        string="Superseded",
        compute="_compute_is_superseded",
        search="_search_is_superseded",
        help="A later reading has corrected this entry.",
    )
    correction_reason = fields.Char(
        string="Reason for Correction",
        readonly=True,
        help="Mandatory when the reading supersedes an earlier one.",
    )
    comment = fields.Char(readonly=True)

    company_id = fields.Many2one(comodel_name="res.company", related="run_id.company_id",
                                 store=True,
                                 index=True,
                                 readonly=True,)

    @api.depends(
        "value_type",
        "value_numeric",
        "value_text",
        "min_value",
        "max_value",
        "expected_text",
    )
    def _compute_in_tolerance(self):
        """Evaluate the captured value against the frozen acceptance criteria."""
        for reading in self:
            if reading.value_type == "numeric":
                reading.in_tolerance = (
                    reading.min_value <= reading.value_numeric <= reading.max_value
                )
            else:
                expected = (reading.expected_text or "").strip().lower()
                observed = (reading.value_text or "").strip().lower()
                reading.in_tolerance = bool(observed) and observed == expected

    @api.depends("superseded_by_ids")
    def _compute_is_superseded(self):
        """Flag readings that have been corrected by a later entry.

        The field is deliberately not stored: storing it would require the ORM
        to write onto an append-only record whenever a correction is captured.
        """
        for reading in self:
            reading.is_superseded = bool(reading.superseded_by_ids)

    @api.model
    def _search_is_superseded(self, operator, value):
        """Translate a search on ``is_superseded`` into one on the inverse field.

        :param str operator: comparison operator supplied by the search engine.
        :param value: value compared against.
        :return: an Odoo domain restricted to the matching readings.
        :rtype: list
        """
        if operator not in ("=", "!="):
            raise ValidationError(
                self.env._("Unsupported operator for the superseded filter.")
            )
        positive = bool(value) if operator == "=" else not bool(value)
        return [("superseded_by_ids", "!=" if positive else "=", False)]

    @api.depends("parameter_name", "capture_date")
    def _compute_display_name(self):
        """Render the reading as ``Parameter @ timestamp``."""
        for reading in self:
            reading.display_name = f"{reading.parameter_name} @ {reading.capture_date}"

    @api.constrains("supersedes_id", "correction_reason")
    def _check_correction_reason(self):
        """A correcting reading must record why the earlier value was wrong."""
        for reading in self:
            if reading.supersedes_id and not reading.correction_reason:
                raise ValidationError(
                    self.env._(
                        "A reading that corrects an earlier one must record the "
                        "reason for the correction."
                    )
                )

    @api.constrains("supersedes_id", "run_id", "parameter_line_id")
    def _check_correction_consistency(self):
        """A correction must target the same run and parameter."""
        for reading in self:
            superseded = reading.supersedes_id
            if not superseded:
                continue
            if superseded.run_id != reading.run_id:
                raise ValidationError(
                    self.env._(
                        "A correcting reading must belong to the same moulding run "
                        "as the reading it supersedes."
                    )
                )
            if superseded.parameter_line_id != reading.parameter_line_id:
                raise ValidationError(
                    self.env._(
                        "A correcting reading must address the same parameter as "
                        "the reading it supersedes."
                    )
                )

    @api.constrains("value_type", "value_text")
    def _check_qualitative_value(self):
        """A qualitative reading must carry an observed value."""
        for reading in self:
            if reading.value_type == "qualitative" and not (reading.value_text or "").strip():
                raise ValidationError(
                    self.env._(
                        "Parameter %(name)s is qualitative and requires an observed "
                        "value.",
                        name=reading.parameter_name,
                    )
                )

    @api.model_create_multi
    def create(self, vals_list):
        """Freeze the acceptance criteria and validate the run state."""
        line_model = self.env["ls.mp.molding_parameter.line"]
        for vals in vals_list:
            line = line_model.browse(vals["parameter_line_id"])
            vals.update(line._snapshot_values())
        readings = super().create(vals_list)
        readings._check_run_accepts_readings()
        return readings

    def _check_run_accepts_readings(self):
        """Reject readings captured against a closed or cancelled run."""
        for reading in self:
            if reading.run_id.state in ("closed", "cancelled"):
                raise ValidationError(
                    self.env._(
                        "Moulding run %(run)s is %(state)s and cannot accept new "
                        "readings.",
                        run=reading.run_id.name,
                        state=reading.run_id.state,
                    )
                )
        return True

    def write(self, vals):
        """Block modification of captured readings.

        Only stored computed fields maintained by the ORM may be written. Any
        other change is refused: corrections are made by creating a superseding
        reading.
        """
        forbidden = set(vals) - _SYSTEM_WRITABLE_FIELDS
        if forbidden:
            raise ValidationError(
                self.env._(
                    "Moulding parameter readings cannot be modified. To correct a "
                    "value, capture a new reading that supersedes it. Rejected "
                    "fields: %(fields)s.",
                    fields=", ".join(sorted(forbidden)),
                )
            )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_mp_injection_molding_reading(self):
        """Block deletion of captured readings."""
        raise ValidationError(
            self.env._(
                "Moulding parameter readings cannot be deleted. To correct a value, "
                "capture a new reading that supersedes it."
            )
        )
