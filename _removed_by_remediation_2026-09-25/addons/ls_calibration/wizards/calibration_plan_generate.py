# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Wizard generating scheduled calibration records from approved plans."""

from odoo import api, fields, models
from odoo.exceptions import UserError

from ..models import constants


class LsCalibrationPlanGenerate(models.TransientModel):
    """Create scheduled calibration records up to a horizon date."""

    _name = "ls.calibration.plan.generate"
    _description = "Generate Scheduled Calibrations"

    horizon_date = fields.Date(
        string="Generate Up To",
        required=True,
        default=lambda self: self._default_horizon_date(),
        help="Latest scheduled date for which calibration records are "
        "created. Every approved plan effective on or before this date "
        "contributes.",
    )
    plan_ids = fields.Many2many(
        comodel_name="ls.calibration.plan",
        string="Restrict to Plans",
        domain="[('state', '=', 'approved'), ('company_id', '=', company_id)]",
        help="Leave empty to consider every approved plan of the company.",
    )
    category_id = fields.Many2one(
        comodel_name="ls.calibration.instrument.category",
        string="Restrict to Category",
    )
    criticality = fields.Selection(
        selection=constants.CRITICALITY_SELECTION,
        string="Restrict to Criticality",
    )
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,)
    generated_count = fields.Integer(string="Generated Records", readonly=True)

    @api.model
    def _default_horizon_date(self):
        """Default the horizon to the end of the current calendar year."""
        today = fields.Date.context_today(self)
        return today.replace(month=12, day=31)

    def _get_candidate_plans(self):
        """Return the approved plans matching the wizard restrictions."""
        self.ensure_one()
        if self.plan_ids:
            plans = self.plan_ids
        else:
            plans = self.env["ls.calibration.plan"].search(
                [
                    ("state", "=", constants.PLAN_STATE_APPROVED),
                    ("active", "=", True),
                    ("company_id", "=", self.company_id.id),
                ]
            )
        if self.category_id:
            plans = plans.filtered(
                lambda plan: plan.category_id == self.category_id
            )
        if self.criticality:
            plans = plans.filtered(
                lambda plan: plan.instrument_id.criticality == self.criticality
            )
        return plans.filtered(
            lambda plan: plan.instrument_id.state
            != constants.INSTRUMENT_STATE_RETIRED
        )

    def action_generate(self) -> dict:
        """Generate the records and open the resulting list."""
        self.ensure_one()
        plans = self._get_candidate_plans()
        if not plans:
            raise UserError(
                self.env._(
                    "No approved calibration plan matches the selected "
                    "criteria."
                )
            )
        created = plans._generate_records_until(self.horizon_date)
        if not created:
            raise UserError(
                self.env._(
                    "Every selected plan is already scheduled up to "
                    "%(horizon)s. No record was created.",
                    horizon=self.horizon_date,
                )
            )
        self.generated_count = len(created)
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "ls_calibration.action_ls_calibration_record"
        )
        action["domain"] = [("id", "in", created.ids)]
        action["context"] = {}
        return action
