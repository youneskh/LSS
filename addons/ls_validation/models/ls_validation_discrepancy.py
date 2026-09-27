# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Discrepancy raised during the execution of a validation protocol.

A discrepancy documents any departure from the pre-approved acceptance
criteria or procedure observed while executing a protocol. It must be
investigated, resolved and closed before the execution record can be approved.

Scope note
----------
This model covers execution discrepancies only. A GMP deviation raised on a
manufacturing operation belongs to the ``ls_deviation`` module of the Life
Sciences Suite; the field ``capa_reference`` is the documented integration
point until that module is available.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .ls_validation_constants import DISCREPANCY_CLASSIFICATION

DISCREPANCY_STATES = [
    ("open", "Open"),
    ("investigation", "Under Investigation"),
    ("resolved", "Resolved"),
    ("closed", "Closed"),
    ("cancelled", "Cancelled"),
]


class LsValidationDiscrepancy(models.Model):
    """Execution discrepancy with investigation and closure."""

    _name = "ls.validation.discrepancy"
    _description = "Validation Execution Discrepancy"
    _inherit = [
        "mail.thread",
        "mail.activity.mixin",
        "ls.validation.signature.mixin",
    ]
    _order = "reference desc"
    _check_company_auto = True

    _ls_signable_callbacks = ("_ls_do_close",)

    reference = fields.Char(required=True,
                            readonly=True,
                            copy=False,
                            default=lambda self: _("New"),
                            index=True,
                            )
    name = fields.Char(string="Title", required=True, tracking=True)
    execution_id = fields.Many2one(
        comodel_name="ls.validation.execution",
        string="Execution Record",
        required=True,
        ondelete="cascade",
        tracking=True,
        check_company=True,
    )
    protocol_id = fields.Many2one(comodel_name="ls.validation.protocol", related="execution_id.protocol_id",
                                  store=True,
                                  readonly=True,)
    item_id = fields.Many2one(
        comodel_name="ls.validation.item",
        string="Validation Item",
        related="execution_id.item_id",
        store=True,
        readonly=True,
    )
    result_ids = fields.One2many(
        comodel_name="ls.validation.execution.result",
        inverse_name="discrepancy_id",
        string="Impacted Test Cases",
    )
    classification = fields.Selection(selection=DISCREPANCY_CLASSIFICATION, required=True,
                                      default="minor",
                                      tracking=True,)
    state = fields.Selection(
        selection=DISCREPANCY_STATES,
        string="Status",
        default="open",
        required=True,
        tracking=True,
        copy=False,
    )
    description = fields.Text(required=True)
    immediate_action = fields.Text()
    root_cause = fields.Text()
    corrective_action = fields.Text()
    impact_assessment = fields.Text(help="Assessment of the impact on the validated state, on product "
                                    "quality and on patient safety.",)
    requires_capa = fields.Boolean(string="CAPA Required", tracking=True)
    capa_reference = fields.Char(help="External reference of the CAPA record raised in the quality "
                                 "system.",)
    raised_by_id = fields.Many2one(
        comodel_name="res.users",
        string="Raised by",
        default=lambda self: self.env.user,
        tracking=True,
    )
    raised_date = fields.Datetime(
        string="Raised On", default=fields.Datetime.now, readonly=True
    )
    closed_by_id = fields.Many2one(
        comodel_name="res.users",
        string="Closed by",
        readonly=True,
        copy=False,
        tracking=True,
    )
    closed_date = fields.Datetime(string="Closed On", readonly=True, copy=False)
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,)

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------
    @api.depends("reference", "name")
    def _compute_display_name(self):
        """Display the discrepancy as ``REFERENCE - Title``."""
        for discrepancy in self:
            discrepancy.display_name = "%s - %s" % (
                discrepancy.reference or "",
                discrepancy.name or "",
            )

    # ------------------------------------------------------------------
    # ORM
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Assign the discrepancy sequence on creation."""
        for vals in vals_list:
            if vals.get("reference", _("New")) == _("New"):
                company_id = vals.get("company_id", self.env.company.id)
                vals["reference"] = self.env["ir.sequence"].with_company(
                    company_id
                ).next_by_code("ls.validation.discrepancy") or _("New")
        return super().create(vals_list)

    def write(self, vals):
        """Prevent the modification of a closed discrepancy."""
        protected_fields = {
            "name",
            "description",
            "classification",
            "root_cause",
            "corrective_action",
            "impact_assessment",
            "immediate_action",
        }
        if protected_fields.intersection(vals):
            for discrepancy in self:
                if discrepancy.state == "closed":
                    raise UserError(
                        _("Closed discrepancy %s can no longer be modified.")
                        % discrepancy.display_name
                    )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_validation_discrepancy(self):
        """Only open discrepancies without impacted test case may be deleted."""
        for discrepancy in self:
            if discrepancy.state != "open":
                raise UserError(
                    _(
                        "Discrepancy %s cannot be deleted because it is under "
                        "investigation or closed."
                    )
                    % discrepancy.display_name
                )

    # ------------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------------
    def action_start_investigation(self):
        """Move an open discrepancy to the investigation state."""
        for discrepancy in self:
            if discrepancy.state != "open":
                raise UserError(
                    _("Only an open discrepancy can enter investigation.")
                )
            discrepancy.state = "investigation"
            discrepancy.message_post(body=_("Investigation started."))
        return True

    def action_resolve(self):
        """Mark a discrepancy as resolved once the analysis is documented."""
        for discrepancy in self:
            if discrepancy.state != "investigation":
                raise UserError(
                    _("Only a discrepancy under investigation can be resolved.")
                )
            if not discrepancy.root_cause:
                raise UserError(
                    _("The root cause must be documented before resolution.")
                )
            if not discrepancy.corrective_action:
                raise UserError(
                    _(
                        "The corrective action must be documented before "
                        "resolution."
                    )
                )
            if not discrepancy.impact_assessment:
                raise UserError(
                    _(
                        "The impact assessment must be documented before "
                        "resolution."
                    )
                )
            discrepancy.state = "resolved"
            discrepancy.message_post(body=_("Discrepancy resolved."))
        return True

    def action_close(self):
        """Open the electronic signature wizard to close the discrepancy."""
        self.ensure_one()
        if self.state != "resolved":
            raise UserError(
                _("Only a resolved discrepancy can be closed.")
            )
        if self.requires_capa and not self.capa_reference:
            raise UserError(
                _(
                    "A CAPA reference is required because this discrepancy is "
                    "flagged as requiring a CAPA."
                )
            )
        return self._ls_open_sign_wizard(
            meaning="closed",
            callback="_ls_do_close",
            title=_("Close Discrepancy"),
        )

    def _ls_do_close(self):
        """Apply the closure once the electronic signature is recorded."""
        self.ensure_one()
        if self.state != "resolved":
            raise UserError(_("Only a resolved discrepancy can be closed."))
        self.write(
            {
                "state": "closed",
                "closed_by_id": self.env.user.id,
                "closed_date": fields.Datetime.now(),
            }
        )
        self.message_post(body=_("Discrepancy closed and signed electronically."))
        return True

    def action_cancel(self):
        """Cancel a discrepancy raised by mistake."""
        for discrepancy in self:
            if discrepancy.state == "closed":
                raise UserError(
                    _("A closed discrepancy cannot be cancelled.")
                )
            discrepancy.state = "cancelled"
            discrepancy.message_post(body=_("Discrepancy cancelled."))
        return True
