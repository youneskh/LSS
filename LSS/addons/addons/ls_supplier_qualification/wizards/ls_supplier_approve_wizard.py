# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Wizard used to approve a supplier qualification dossier."""
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class LsSupplierApproveWizard(models.TransientModel):
    """Collect the approval decision, its validity and its justification.

    The wizard requires the approver to retype their own login. This confirms
    the intent of the person operating the session; it is not a
    re-authentication. See the scope statement of
    ``ls.supplier.signature``.
    """

    _name = "ls.supplier.approve.wizard"
    _description = "Life Sciences Supplier Qualification Approval Wizard"

    qualification_id = fields.Many2one(
        comodel_name="ls.supplier.qualification",
        required=True,
        ondelete="cascade",
        readonly=True,
    )
    partner_id = fields.Many2one(
        related="qualification_id.partner_id",
        readonly=True,
    )
    blocking_reasons = fields.Text(
        related="qualification_id.blocking_reasons",
        readonly=True,
    )
    latest_assessment_score = fields.Float(
        related="qualification_id.latest_assessment_score",
        readonly=True,
    )
    open_critical_finding_count = fields.Integer(
        related="qualification_id.open_critical_finding_count",
        readonly=True,
    )
    decision = fields.Selection(
        selection=[
            ("approved", "Approve"),
            ("conditional", "Approve with Conditions"),
        ],
        required=True,
        default="approved",
    )
    conditions = fields.Text()
    requalification_interval_months = fields.Integer(
        required=True,
        compute="_compute_interval",
        store=True,
        precompute=True,
        readonly=False,
    )
    expiry_date = fields.Date(
        string="Valid Until",
        required=True,
        compute="_compute_expiry_date",
        store=True,
        precompute=True,
        readonly=False,
    )
    reason = fields.Text(
        string="Justification",
        required=True,
        help="Recorded verbatim in the signature log.",
    )
    signature_login = fields.Char(
        string="Confirm Your Login",
        required=True,
        help="Retype the login of the connected user to confirm the "
             "signature intent.",
    )

    @api.depends("qualification_id")
    def _compute_interval(self):
        """Propose the interval configured on the dossier."""
        for wizard in self:
            wizard.requalification_interval_months = (
                wizard.qualification_id.requalification_interval_months or 36
            )

    @api.depends("requalification_interval_months")
    def _compute_expiry_date(self):
        """Derive the end of validity from the approval date and interval."""
        today = fields.Date.context_today(self)
        for wizard in self:
            months = wizard.requalification_interval_months or 36
            wizard.expiry_date = today + relativedelta(months=months)

    def action_confirm(self):
        """Validate the input and apply the approval to the dossier."""
        self.ensure_one()
        if self.qualification_id.state != "approval":
            raise UserError(
                _("Dossier %s is no longer pending approval.",
                  self.qualification_id.name)
            )
        if self.signature_login != self.env.user.login:
            raise UserError(
                _("The login you entered does not match the login of the "
                  "connected user.")
            )
        if self.decision == "conditional" and not (self.conditions or "").strip():
            raise UserError(
                _("Document the conditions attached to the approval.")
            )
        if self.expiry_date <= fields.Date.context_today(self):
            raise UserError(
                _("The end of validity must be a future date.")
            )
        self.qualification_id.write({
            "requalification_interval_months": (
                self.requalification_interval_months
            ),
        })
        self.qualification_id._apply_approval(
            decision=self.decision,
            conditions=self.conditions,
            expiry_date=self.expiry_date,
            reason=self.reason,
            login=self.signature_login,
        )
        return {"type": "ir.actions.act_window_close"}
