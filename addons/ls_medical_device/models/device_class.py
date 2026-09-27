# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Device risk class configuration.

The risk class of a device drives several downstream obligations in this
module: whether a notified body is involved, which kind of periodic
post-market report is due, and how often that report must be updated.

Those obligations are held as *editable configuration* on this model rather
than as hard-coded behaviour, because the mapping between a class code and its
obligations is set by the applicable regulation and may be amended. The values
shipped in ``data/device_class_data.xml`` reflect Regulation (EU) 2017/745 as
described in the module documentation; the implementing organisation is
responsible for confirming them before use.
"""

from odoo import api, fields, models

from . import constants


class LsMdDeviceClass(models.Model):
    """Risk class of a medical device."""

    _name = "ls.md.device_class"
    _description = "Medical Device Risk Class"
    _order = "sequence, code"

    name = fields.Char(required=True,
                       translate=True,
                       help="Display name of the risk class, for example 'Class IIa'.",)
    code = fields.Char(required=True,
                       help="Short technical code of the risk class, for example 'IIa'.",)
    sequence = fields.Integer(default=10,
                              help="Ordering of the risk class in lists and selections.",)
    active = fields.Boolean(default=True,
                            help="Uncheck to hide the risk class without deleting it.",)
    description = fields.Text(translate=True,
                              help="Explanatory text describing the scope of the risk class.",)
    regulatory_framework = fields.Char(required=True,
                                       default="Regulation (EU) 2017/745",
                                       help=(
                                           "Framework under which this risk class is defined. Recorded so "
                                           "that classes originating from different frameworks can coexist."
                                           ),
                                       )
    notified_body_required = fields.Boolean(
        string="Notified Body Involvement Required",
        default=True,
        help=(
            "Indicates that conformity assessment for this risk class "
            "requires the involvement of a notified body. Confirm this value "
            "against the applicable regulation before use."
        ),
    )
    notified_body_scope_note = fields.Text(translate=True,
                                           help=(
                                               "Free text describing the extent of notified body involvement, "
                                               "for example a scope limited to specific aspects of the device."),
                                           )
    periodic_report_type = fields.Selection(
        selection=constants.PERIODIC_REPORT_TYPE_SELECTION,
        string="Periodic Post-Market Report",
        required=True,
        default=constants.PERIODIC_REPORT_PSUR,
        help=(
            "Kind of periodic post-market report required for devices of this "
            "risk class."
        ),
    )
    periodic_report_interval_months = fields.Integer(
        string="Maximum Report Interval (Months)",
        default=constants.PSUR_INTERVAL_MONTHS_ANNUAL,
        help=(
            "Maximum number of months between two consecutive periodic "
            "post-market reports. Set to zero when no fixed maximum interval "
            "applies and the report is updated when necessary."
        ),
    )
    annual_pmcf_update_required = fields.Boolean(
        string="Annual PMCF Evaluation Update Required",
        default=False,
        help=(
            "Indicates that the post-market clinical follow-up evaluation "
            "report must be updated at least annually for devices of this "
            "risk class."
        ),
    )
    device_ids = fields.One2many(
        comodel_name="ls.md.device",
        inverse_name="device_class_id",
        string="Devices",
        help="Devices registered under this risk class.",
    )
    device_count = fields.Integer(compute="_compute_device_count",
                                  help="Number of devices registered under this risk class.",)

    _code_unique = models.Constraint(
        "UNIQUE(code, regulatory_framework)",
        "The risk class code must be unique within a regulatory framework.",
    )
    _interval_non_negative = models.Constraint(
        "CHECK(periodic_report_interval_months >= 0)",
        "The maximum report interval cannot be negative.",
    )

    @api.depends("device_ids")
    def _compute_device_count(self):
        """Count the devices attached to each risk class."""
        grouped = self.env["ls.md.device"]._read_group(
            domain=[("device_class_id", "in", self.ids)],
            groupby=["device_class_id"],
            aggregates=["__count"],
        )
        counts = {device_class.id: count for device_class, count in grouped}
        for record in self:
            record.device_count = counts.get(record.id, 0)

    @api.depends("name", "code")
    def _compute_display_name(self):
        """Show the code alongside the name to disambiguate similar classes."""
        for record in self:
            if record.code and record.name and record.code not in record.name:
                record.display_name = f"{record.name} [{record.code}]"
            else:
                record.display_name = record.name or record.code or ""

    def action_view_devices(self):
        """Open the devices registered under the selected risk class."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Devices"),
            "res_model": "ls.md.device",
            "view_mode": "list,form",
            "domain": [("device_class_id", "=", self.id)],
            "context": {"default_device_class_id": self.id},
        }
