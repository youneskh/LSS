# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Wizard generating the calibration records of the plans that are due."""

from odoo import api, fields, models
from odoo.exceptions import UserError


class LsCalibrationRecordGenerate(models.TransientModel):
    """Bulk creation of calibration records from active calibration plans."""

    _name = "ls.calibration.record.generate"
    _description = "Generate Calibration Records"

    date_to = fields.Date(
        string="Due Until",
        required=True,
        default=fields.Date.context_today,
        help="Calibration records are generated for the active plans whose "
        "next due date is earlier than or equal to this date.",
    )
    plan_ids = fields.Many2many(
        comodel_name="ls.calibration.plan",
        string="Calibration Plans",
        domain="[('state', '=', 'active')]",
        help="Leave empty to consider every active calibration plan.",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.company,
    )

    @api.model
    def default_get(self, fields_list):
        """Preselect the plans the wizard has been started from."""
        values = super().default_get(fields_list)
        context = self.env.context
        if context.get("active_model") == "ls.calibration.plan" and context.get(
            "active_ids"
        ):
            values["plan_ids"] = [
                fields.Command.set(list(context["active_ids"]))
            ]
        return values

    def _get_candidate_plans(self):
        """Return the active plans that are due at the selected date.

        :return: a ``ls.calibration.plan`` recordset.
        """
        self.ensure_one()
        domain = [
            ("state", "=", "active"),
            ("company_id", "=", self.company_id.id),
            ("next_due_date", "!=", False),
            ("next_due_date", "<=", self.date_to),
        ]
        if self.plan_ids:
            domain.append(("id", "in", self.plan_ids.ids))
        return self.env["ls.calibration.plan"].search(domain)

    def action_generate(self):
        """Create one calibration record per due plan without open record.

        :return: an act_window action showing the created records.
        """
        self.ensure_one()
        plans = self._get_candidate_plans()
        if not plans:
            raise UserError(
                self.env._(
                    "No active calibration plan is due until %s.", self.date_to
                )
            )
        record_model = self.env["ls.calibration.record"]
        created = record_model
        for plan in plans:
            if plan._get_open_records():
                continue
            created |= record_model.create(plan._prepare_record_values())
        if not created:
            raise UserError(
                self.env._(
                    "Every due calibration plan already has an open "
                    "calibration record."
                )
            )
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "ls_calibration.ls_calibration_record_action"
        )
        action["domain"] = [("id", "in", created.ids)]
        action["context"] = {}
        return action
