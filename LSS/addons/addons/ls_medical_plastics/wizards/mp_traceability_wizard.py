# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Material traceability wizard.

Given a produced lot, a component or a date range, the wizard resolves the
moulding runs concerned and exposes the full genealogy: tool and cavities
used, parameter specification version applied, material grades and lots
consumed, and rejects recorded.

The wizard performs no destructive action. It resolves records and returns
either an on-screen result or a printable report.
"""

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class LsMpTraceabilityWizard(models.TransientModel):
    """Resolve the genealogy of moulded components."""

    _name = "ls.mp.traceability.wizard"
    _description = "Medical Plastics Traceability Enquiry"

    search_mode = fields.Selection(
        selection=[
            ("produced_lot", "By Produced Lot"),
            ("material_lot", "By Material Lot"),
            ("component", "By Component and Period"),
            ("tool", "By Tool and Period"),
        ],
        string="Search By",
        required=True,
        default="produced_lot",
    )
    lot_id = fields.Many2one(
        comodel_name="stock.lot",
        string="Produced Lot",
        help="Lot assigned to the moulded parts.",
    )
    material_lot_id = fields.Many2one(comodel_name="stock.lot", help="Resin or masterbatch lot to trace forward.",)
    component_id = fields.Many2one(comodel_name="ls.mp.component")
    tool_id = fields.Many2one(comodel_name="ls.mp.tool")
    date_from = fields.Date(string="From")
    date_to = fields.Date(string="To")
    include_open_runs = fields.Boolean(
        string="Include Runs in Progress",
        help="Include runs that have not yet been closed.",
    )

    run_ids = fields.Many2many(
        comodel_name="ls.mp.injection_molding",
        relation="ls_mp_traceability_wizard_run_rel",
        column1="wizard_id",
        column2="run_id",
        string="Matching Runs",
        readonly=True,
    )
    run_count = fields.Integer(string="Runs Found", readonly=True)

    @api.constrains("date_from", "date_to")
    def _check_period(self):
        """The period end cannot precede its start."""
        for wizard in self:
            if wizard.date_from and wizard.date_to and wizard.date_to < wizard.date_from:
                raise ValidationError(
                    self.env._("The end of the period precedes its start.")
                )

    def _build_domain(self):
        """Build the search domain matching the selected enquiry mode.

        :return: an Odoo domain selecting the moulding runs concerned.
        :rtype: list
        :raises ValidationError: when the mandatory criterion is missing.
        """
        self.ensure_one()
        domain = []
        if not self.include_open_runs:
            domain.append(("state", "=", "closed"))
        else:
            domain.append(("state", "!=", "cancelled"))

        if self.search_mode == "produced_lot":
            if not self.lot_id:
                raise ValidationError(self.env._("Select the produced lot to trace."))
            domain.append(("lot_id", "=", self.lot_id.id))
        elif self.search_mode == "material_lot":
            if not self.material_lot_id:
                raise ValidationError(self.env._("Select the material lot to trace."))
            domain.append(("material_line_ids.lot_id", "=", self.material_lot_id.id))
        elif self.search_mode == "component":
            if not self.component_id:
                raise ValidationError(self.env._("Select the component to trace."))
            domain.append(("component_id", "=", self.component_id.id))
        else:
            if not self.tool_id:
                raise ValidationError(self.env._("Select the tool to trace."))
            domain.append(("tool_id", "=", self.tool_id.id))

        if self.date_from:
            domain.append(("date_start", ">=", fields.Datetime.to_datetime(self.date_from)))
        if self.date_to:
            domain.append(("date_start", "<=", fields.Datetime.to_datetime(self.date_to)))
        return domain

    def action_search(self):
        """Resolve the matching runs and reopen the wizard with the result.

        :return: an action redisplaying this wizard.
        :rtype: dict
        """
        self.ensure_one()
        runs = self.env["ls.mp.injection_molding"].search(self._build_domain())
        self.write({"run_ids": [(6, 0, runs.ids)], "run_count": len(runs)})
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Traceability Enquiry"),
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_open_runs(self):
        """Open the matching runs in a list view.

        :return: an action listing the resolved runs.
        :rtype: dict
        """
        self.ensure_one()
        if not self.run_ids:
            raise ValidationError(
                self.env._("Run the enquiry before opening the results.")
            )
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Traceability Results"),
            "res_model": "ls.mp.injection_molding",
            "view_mode": "list,form",
            "domain": [("id", "in", self.run_ids.ids)],
        }

    def action_print(self):
        """Print the moulding run record for every matching run.

        :return: the report action for the resolved runs.
        :rtype: dict
        """
        self.ensure_one()
        if not self.run_ids:
            raise ValidationError(
                self.env._("Run the enquiry before printing the results.")
            )
        return self.env.ref(
            "ls_medical_plastics.action_report_mp_molding_run"
        ).report_action(self.run_ids)

    def _collect_genealogy(self):
        """Return the resolved genealogy of the matching runs.

        The structure is consumed by the traceability report template and by
        the automated tests.

        :return: one dictionary per run describing its full genealogy.
        :rtype: list of dict
        """
        self.ensure_one()
        genealogy = []
        for run in self.run_ids:
            genealogy.append(
                {
                    "run": run,
                    "component": run.component_id,
                    "tool": run.tool_id,
                    "cavities_blocked": run.blocked_cavity_ids,
                    "specification": run.parameter_spec_id,
                    "specification_version": run.parameter_spec_version,
                    "materials": run.material_line_ids,
                    "material_lots": run.material_line_ids.mapped("lot_id"),
                    "readings": run.reading_ids.filtered(
                        lambda reading: not reading.superseded_by_ids
                    ),
                    "scrap": run.scrap_line_ids,
                }
            )
        return genealogy
