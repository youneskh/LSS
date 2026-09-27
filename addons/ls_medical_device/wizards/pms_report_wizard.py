# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Wizard that opens the next periodic post-market reporting period.

The wizard computes the reporting period from the end of the last approved
report of the device, or from the date the device was first placed on the
market when no report exists yet, and creates a draft report for that period.
Creating the record does not produce its content: the analysis remains the work
of the person preparing the report.
"""

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..models import constants


class LsMdPmsReportWizard(models.TransientModel):
    """Transient record collecting the parameters of the new report."""

    _name = "ls.md.pms.report.wizard"
    _description = "Periodic Post-Market Report Wizard"

    device_ids = fields.Many2many(
        comodel_name="ls.md.device",
        string="Devices",
        required=True,
        help="Devices for which a draft periodic report is to be opened.",
    )
    period_start = fields.Date(help=(
            "Start of the reporting period. Left empty, it is computed per "
            "device from the end of the last approved report."),
    )
    period_end = fields.Date(required=True,
                             default=fields.Date.context_today,
                             help="End of the reporting period, common to all selected devices.",)
    use_device_interval = fields.Boolean(
        string="Derive Start From Report Interval",
        default=True,
        help=(
            "When set, the period start of each device is derived from the "
            "end of its last approved report, or from the report interval of "
            "its risk class when no approved report exists."
        ),
    )
    created_report_ids = fields.Many2many(
        comodel_name="ls.md.pms_report",
        string="Created Reports",
        readonly=True,
    )

    @api.constrains("period_start", "period_end")
    def _check_period(self):
        """Reject a period whose end precedes its start."""
        for wizard in self:
            if (
                wizard.period_start
                and wizard.period_end
                and wizard.period_end < wizard.period_start
            ):
                raise ValidationError(
                    self.env._("The period end cannot precede the period start.")
                )

    def _compute_period_start_for(self, device):
        """Return the period start to use for one device.

        The explicit start entered on the wizard takes precedence. Otherwise
        the start is the day after the end of the last approved report; where
        no approved report exists, it is the date the device was first placed
        on the market; where that is unknown, it is the report interval of the
        risk class counted back from the period end.
        """
        if self.period_start:
            return self.period_start
        if device.last_periodic_report_date:
            return device.last_periodic_report_date + relativedelta(days=1)
        if device.market_placement_date:
            return device.market_placement_date
        interval = (
            device.periodic_report_interval_months
            or constants.PSUR_INTERVAL_MONTHS_ANNUAL
        )
        return self.period_end - relativedelta(months=interval)

    def action_create_reports(self):
        """Create one draft periodic report per selected device."""
        self.ensure_one()
        report_model = self.env["ls.md.pms_report"]
        values_list = []
        for device in self.device_ids:
            if device.state not in ("on_market", "suspended", "withdrawn"):
                raise UserError(
                    self.env._(
                        "Device '%(device)s' has not been placed on the "
                        "market, so no periodic post-market report is due for "
                        "it.",
                        device=device.display_name,
                    )
                )
            period_start = self._compute_period_start_for(device)
            if period_start > self.period_end:
                raise UserError(
                    self.env._(
                        "Device '%(device)s': the computed period start "
                        "%(start)s is later than the period end %(end)s.",
                        device=device.display_name,
                        start=period_start,
                        end=self.period_end,
                    )
                )
            plan = device.pms_ids.filtered(
                lambda record: record.state == "approved"
            )[:1]
            values_list.append(
                {
                    "device_id": device.id,
                    "pms_id": plan.id if plan else False,
                    "report_type": (
                        device.periodic_report_type or constants.PERIODIC_REPORT_PSUR
                    ),
                    "period_start": period_start,
                    "period_end": self.period_end,
                    "notified_body_submission_required": bool(device.is_implantable),
                }
            )
        reports = report_model.create(values_list)
        self.created_report_ids = reports
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Periodic Post-Market Reports"),
            "res_model": "ls.md.pms_report",
            "view_mode": "list,form",
            "domain": [("id", "in", reports.ids)],
        }
