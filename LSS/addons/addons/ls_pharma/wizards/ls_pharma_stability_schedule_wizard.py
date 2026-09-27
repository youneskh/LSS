# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Wizard used to generate the time point schedule of a stability study."""

from odoo import api, fields, models
from odoo.exceptions import UserError


class LsPharmaStabilityScheduleWizard(models.TransientModel):
    """Propose and create the time points of a stability study.

    The wizard previews the months that would be created for each selected
    storage condition before any record is written, so that the study owner
    can adjust the duration or the conditions first.
    """

    _name = "ls.pharma.stability.schedule.wizard"
    _description = "Stability Schedule Generation Wizard"

    study_id = fields.Many2one(comodel_name="ls.pharma.stability_study", required=True,
                               readonly=True,)
    duration_months = fields.Integer(string="Duration (Months)", required=True)
    condition_ids = fields.Many2many(
        comodel_name="ls.pharma.stability.condition",
        relation="ls_stability_sched_wiz_cond_rel",
        column1="wizard_id",
        column2="condition_id",
        string="Storage Conditions",
        required=True,
        )
    preview = fields.Text(
        string="Proposed Schedule",
        compute="_compute_preview",
        help=(
            "Months at which testing would be scheduled for each condition, "
            "following the frequencies published in ICH Q1A(R2). Time points "
            "that already exist are not repeated."
        ),
    )

    @api.model
    def default_get(self, fields_list):
        """Pre-fill the wizard from the study it was opened on."""
        values = super().default_get(fields_list)
        study_id = values.get("study_id") or self.env.context.get(
            "default_study_id"
        )
        if study_id:
            study = self.env["ls.pharma.stability_study"].browse(study_id)
            values.setdefault("duration_months", study.duration_months)
            values.setdefault("condition_ids", [(6, 0, study.condition_ids.ids)])
        return values

    @api.depends("study_id", "duration_months", "condition_ids")
    def _compute_preview(self):
        """Build a textual preview of the schedule that would be created."""
        study_model = self.env["ls.pharma.stability_study"]
        for wizard in self:
            if not wizard.study_id or wizard.duration_months <= 0:
                wizard.preview = ""
                continue
            existing = {
                (point.condition_id.id, point.month)
                for point in wizard.study_id.timepoint_ids
            }
            lines = []
            for condition in wizard.condition_ids:
                if condition.condition_type == "long_term":
                    duration = wizard.duration_months
                else:
                    duration = min(
                        wizard.duration_months, condition.default_duration_months
                    )
                months = study_model._ich_timepoint_months(
                    condition.condition_type, duration
                )
                new_months = [
                    month
                    for month in months
                    if (condition.id, month) not in existing
                ]
                lines.append(
                    self.env._(
                        "%(condition)s: months %(months)s (new: %(new)s)",
                        condition=condition.display_name,
                        months=", ".join(str(month) for month in months) or "-",
                        new=", ".join(str(month) for month in new_months) or "-",
                    )
                )
            wizard.preview = "\n".join(lines)

    def action_generate(self):
        """Apply the duration and the conditions, then generate the schedule.

        :returns: an action listing the time points of the study.
        :rtype: dict
        """
        self.ensure_one()
        if self.duration_months <= 0:
            raise UserError(
                self.env._("The duration must be strictly positive.")
            )
        self.study_id.write(
            {
                "duration_months": self.duration_months,
                "condition_ids": [(6, 0, self.condition_ids.ids)],
            }
        )
        self.study_id.action_generate_schedule()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Time Points"),
            "res_model": "ls.pharma.stability.timepoint",
            "view_mode": "list,form",
            "domain": [("study_id", "=", self.study_id.id)],
            "context": {"default_study_id": self.study_id.id},
        }
