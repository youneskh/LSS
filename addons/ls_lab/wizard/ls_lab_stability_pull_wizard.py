# Part of the Life Sciences Suite. See LICENSE file for full copyright and licensing details.
"""Wizard creating the pull sample for a stability time point."""

from odoo import api, fields, models
from odoo.exceptions import UserError


class LsLabStabilityPullWizard(models.TransientModel):
    """Creates the sample drawn at a stability time point (BRU-24)."""

    _name = "ls.lab.stability_pull_wizard"
    _description = "Laboratory Stability Pull Wizard"

    timepoint_id = fields.Many2one(
        comodel_name="ls.lab.stability_timepoint",
        string="Time Point",
        required=True,
        readonly=True,
    )
    study_id = fields.Many2one(
        related="timepoint_id.study_id", string="Stability Study", readonly=True
    )
    product_id = fields.Many2one(related="timepoint_id.study_id.product_id", readonly=True)
    scheduled_date = fields.Date(related="timepoint_id.scheduled_date", readonly=True)
    specification_id = fields.Many2one(comodel_name="ls.lab.specification", required=True,
                                       domain="[('state', '=', 'approved')]",
                                       )
    storage_condition_id = fields.Many2one(comodel_name="ls.lab.storage_condition")
    pull_date = fields.Date(
        string="Actual Pull Date", required=True, default=fields.Date.context_today
    )
    quantity = fields.Float(digits=(16, 4))
    uom_id = fields.Many2one(comodel_name="uom.uom", string="Unit of Measure")
    due_date = fields.Date(string="Testing Due Date")

    @api.onchange("timepoint_id")
    def _onchange_timepoint_id(self):
        """Default the specification and storage condition from the study."""
        for wizard in self:
            study = wizard.timepoint_id.study_id
            if study.specification_id:
                wizard.specification_id = study.specification_id
            if study.storage_condition_id:
                wizard.storage_condition_id = study.storage_condition_id

    def action_confirm(self):
        """Create the pull sample and link it to the time point."""
        self.ensure_one()
        timepoint = self.timepoint_id
        if timepoint.state != "planned":
            raise UserError(
                self.env._(
                    "Time point '%(timepoint)s' is in status '%(state)s' and no "
                    "sample can be generated from it.",
                    timepoint=timepoint.display_name,
                    state=timepoint.state,
                )
            )
        if timepoint.study_id.state != "ongoing":
            raise UserError(
                self.env._(
                    "Stability study '%(study)s' is not ongoing, so no pull "
                    "sample can be generated.",
                    study=timepoint.study_id.name,
                )
            )
        study = timepoint.study_id
        sample = self.env["ls.lab.sample"].create({
            "description": self.env._(
                "Stability pull: %(study)s / %(timepoint)s",
                study=study.name,
                timepoint=timepoint.name,
            ),
            "sample_type": "stability",
            "product_id": study.product_id.id,
            "lot_id": study.lot_id.id,
            "batch_reference": study.batch_reference,
            "specification_id": self.specification_id.id,
            "storage_condition_id": self.storage_condition_id.id,
            "quantity": self.quantity,
            "uom_id": self.uom_id.id,
            "sampled_date": fields.Datetime.now(),
            "due_date": self.due_date,
            "stability_timepoint_id": timepoint.id,
        })
        timepoint.write({
            "state": "sampled",
            "sample_id": sample.id,
            "actual_pull_date": self.pull_date,
        })
        study.message_post(
            body=self.env._(
                "Pull sample %(sample)s created for time point %(timepoint)s.",
                sample=sample.name,
                timepoint=timepoint.name,
            )
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": "ls.lab.sample",
            "res_id": sample.id,
            "view_mode": "form",
            "target": "current",
        }
