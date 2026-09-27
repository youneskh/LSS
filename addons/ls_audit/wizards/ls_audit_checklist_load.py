# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Checklist load wizard.

Copies the questions of an approved checklist template into an audit. The
question text is copied rather than referenced so that later template changes
never alter the record of an executed audit.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class LsAuditChecklistLoad(models.TransientModel):
    """Wizard loading an approved checklist into an audit."""

    _name = "ls.audit.checklist.load"
    _description = "Load Audit Checklist"

    audit_id = fields.Many2one(comodel_name="ls.audit.schedule", required=True,
                               ondelete="cascade",
                               help="Audit the checklist is loaded into.",)
    checklist_id = fields.Many2one(comodel_name="ls.audit.checklist", required=True,
                                   domain="[('state', '=', 'approved'),"
                                   " ('company_id', '=', company_id)]",
                                   help="Approved checklist template to load.",
                                   )
    company_id = fields.Many2one(comodel_name="res.company", related="audit_id.company_id",
                                 readonly=True,
                                 help="Company of the audit, used to filter the checklists.",)
    replace_existing = fields.Boolean(
        string="Replace Existing Questions",
        help="Remove the questions already loaded into the audit before "
             "loading the selected checklist.",
    )
    existing_count = fields.Integer(
        string="Existing Questions",
        related="audit_id.response_count",
        readonly=True,
        help="Number of questions already loaded into the audit.",
    )

    @api.onchange("audit_id")
    def _onchange_audit_id(self):
        """Propose the default checklist of the audit type."""
        if not self.audit_id:
            return
        default_checklist = self.audit_id.audit_type_id.default_checklist_id
        if default_checklist and default_checklist.state == "approved":
            self.checklist_id = default_checklist

    def action_load(self):
        """Copy the checklist questions into the audit.

        :return: an action closing the wizard window.
        :rtype: dict
        :raise UserError: when the audit does not accept a checklist or when
            the selected checklist is not approved.
        """
        self.ensure_one()
        audit = self.audit_id
        if audit.state not in ("planned", "scheduled"):
            raise UserError(
                _(
                    "A checklist can only be loaded while audit %(ref)s is "
                    "planned or scheduled.",
                    ref=audit.reference,
                )
            )
        if self.checklist_id.state != "approved":
            raise UserError(
                _(
                    "Checklist '%(name)s' is not approved and cannot be "
                    "loaded into an audit.",
                    name=self.checklist_id.display_name,
                )
            )
        if audit.response_ids and not self.replace_existing:
            raise UserError(
                _(
                    "Audit %(ref)s already contains %(count)s question(s). "
                    "Tick 'Replace Existing Questions' to load a different "
                    "checklist.",
                    ref=audit.reference,
                    count=len(audit.response_ids),
                )
            )
        if audit.response_ids:
            audit.response_ids.unlink()
        response_model = self.env["ls.audit.response"]
        response_model.create(
            [
                {
                    "audit_id": audit.id,
                    "checklist_line_id": line.id,
                    "sequence": line.sequence,
                    "name": line.name,
                    "reference_clause": line.reference_clause,
                    "guidance": line.guidance,
                    "is_mandatory": line.is_mandatory,
                }
                for line in self.checklist_id.line_ids
            ]
        )
        audit.checklist_id = self.checklist_id.id
        audit.message_post(
            body=_(
                "Checklist %(name)s loaded with %(count)s question(s).",
                name=self.checklist_id.display_name,
                count=len(self.checklist_id.line_ids),
            )
        )
        return {"type": "ir.actions.act_window_close"}
