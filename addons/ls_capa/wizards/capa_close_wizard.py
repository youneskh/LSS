# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Wizard used to capture the closure summary of a CAPA."""

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class LsCapaCloseWizard(models.TransientModel):
    """Collect the closure summary and close the CAPA in one step.

    Routing closure through a wizard keeps the mandatory closure summary in
    front of the user at the moment of the decision, rather than relying on
    the summary having been filled in earlier in the form.
    """

    _name = "ls.capa.close.wizard"
    _description = "CAPA Closure Wizard"

    issue_id = fields.Many2one(
        comodel_name="ls.capa.issue",
        string="CAPA",
        required=True,
        ondelete="cascade",
        readonly=True,
    )
    issue_reference = fields.Char(
        string="Reference",
        related="issue_id.name",
        readonly=True,
    )
    action_count = fields.Integer(
        string="Actions",
        related="issue_id.action_count",
        readonly=True,
    )
    effectiveness_count = fields.Integer(
        string="Effectiveness Checks",
        related="issue_id.effectiveness_count",
        readonly=True,
    )
    closure_summary = fields.Text(required=True,
                                  help="Summary justifying closure, including confirmation that the "
                                  "actions were implemented and verified as effective.",)

    @api.model
    def default_get(self, fields_list):
        """Pre-fill the wizard from the CAPA in context.

        :param list fields_list: fields requested by the client.
        :return: dictionary of default values.
        :rtype: dict
        """
        defaults = super().default_get(fields_list)
        issue_id = defaults.get("issue_id") or self.env.context.get(
            "default_issue_id"
        )
        if issue_id and "closure_summary" in fields_list:
            issue = self.env["ls.capa.issue"].browse(issue_id)
            if issue.closure_summary:
                defaults["closure_summary"] = issue.closure_summary
        return defaults

    def action_confirm_close(self):
        """Write the summary onto the CAPA and close it.

        :return: an action closing the wizard dialog.
        :rtype: dict
        """
        self.ensure_one()
        if not self.closure_summary.strip():
            raise UserError(_("The closure summary cannot be empty."))
        self.issue_id.write({"closure_summary": self.closure_summary})
        self.issue_id.action_close()
        return {"type": "ir.actions.act_window_close"}
