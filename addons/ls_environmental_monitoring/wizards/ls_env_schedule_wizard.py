# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Wizard that generates scheduled samples from approved monitoring plans."""

from odoo import api, fields, models
from odoo.exceptions import UserError

from ..models.constants import (
    MAX_SAMPLES_PER_SCHEDULING_RUN,
    PLAN_APPROVED,
)


class LsEnvScheduleWizard(models.TransientModel):
    """Generate the samples due under the approved plans up to a horizon.

    Generation is idempotent: a sample that already exists for a given plan
    line and due date is not created a second time, so the wizard can be run
    repeatedly, or by both a person and the scheduled job, without producing
    duplicates.
    """

    _name = "ls.env.schedule.wizard"
    _description = "Generate Scheduled Environmental Monitoring Samples"

    date_to = fields.Date(
        string="Generate Until",
        required=True,
        default=fields.Date.context_today,
        help="Last due date for which samples are generated, inclusive.",
    )
    plan_ids = fields.Many2many(
        comodel_name="ls.env.plan",
        string="Plans",
        domain="[('state', '=', 'approved')]",
        help="Restrict generation to these plans. Leave empty for all "
        "approved plans of the current company.",
    )
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,)
    generated_count = fields.Integer(string="Samples Generated", readonly=True)

    def _plans(self):
        """Return the approved plans in scope for this run."""
        self.ensure_one()
        if self.plan_ids:
            return self.plan_ids.filtered(lambda p: p.state == PLAN_APPROVED)
        return self.env["ls.env.plan"].search(
            [
                ("state", "=", PLAN_APPROVED),
                ("company_id", "=", self.company_id.id),
            ]
        )

    def action_generate(self):
        """Create the outstanding samples and report how many were created."""
        self.ensure_one()
        samples = self.env["ls.env.sample"].generate_from_plans(
            self._plans(), self.date_to, MAX_SAMPLES_PER_SCHEDULING_RUN
        )
        self.generated_count = len(samples)
        if not samples:
            raise UserError(
                self.env._(
                    "No sample was due for generation up to %(date)s.",
                    date=self.date_to,
                )
            )
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Generated Samples"),
            "res_model": "ls.env.sample",
            "view_mode": "list,form",
            "domain": [("id", "in", samples.ids)],
            "context": {"search_default_filter_scheduled": 1},
        }

    @api.model
    def cron_generate_scheduled_samples(self):
        """Entry point for the scheduled job.

        Generates samples for every approved plan of every company up to the
        current date.
        """
        today = fields.Date.context_today(self)
        plans = self.env["ls.env.plan"].search([("state", "=", PLAN_APPROVED)])
        samples = self.env["ls.env.sample"].generate_from_plans(
            plans, today, MAX_SAMPLES_PER_SCHEDULING_RUN
        )
        return len(samples)
