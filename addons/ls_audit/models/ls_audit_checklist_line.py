# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Checklist question.

A checklist line is a single question of a checklist template.  Lines are
copied into an audit as ``ls.audit.response`` records when the checklist is
loaded, so that later template changes never alter an executed audit.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class LsAuditChecklistLine(models.Model):
    """Single question belonging to a checklist template."""

    _name = "ls.audit.checklist.line"
    _description = "Audit Checklist Question"
    _order = "checklist_id, sequence, id"

    checklist_id = fields.Many2one(comodel_name="ls.audit.checklist", required=True,
                                   ondelete="cascade",
                                   index=True,
                                   help="Checklist template this question belongs to.",)
    sequence = fields.Integer(default=10,
                              help="Order of the question inside the checklist.",)
    name = fields.Text(
        string="Question",
        required=True,
        translate=True,
        help="Question or requirement the auditor has to assess.",
    )
    reference_clause = fields.Char(
        string="Reference",
        help="Reference of the requirement being verified, for example a "
             "clause number of a standard or a section of an internal "
             "procedure. No standard text is distributed with this module.",
    )
    guidance = fields.Text(
        string="Auditor Guidance",
        translate=True,
        help="Guidance for the auditor on what evidence to look for.",
    )
    is_mandatory = fields.Boolean(
        string="Mandatory",
        default=True,
        help="Mandatory questions must be assessed before the audit can be "
             "completed.",
    )
    company_id = fields.Many2one(comodel_name="res.company", related="checklist_id.company_id",
                                 store=True,
                                 readonly=True,
                                 help="Company owning this question, inherited from the checklist.",)

    def _check_editable(self):
        """Forbid modification of a question of an approved checklist.

        :raise UserError: when at least one line belongs to a checklist that
            is no longer in draft status.
        """
        locked = self.filtered(
            lambda line: line.checklist_id.state != "draft"
        )
        if locked:
            raise UserError(
                _(
                    "Questions of an approved or obsolete checklist cannot "
                    "be modified. Create a new checklist version instead. "
                    "Affected checklist(s): %(names)s.",
                    names=", ".join(
                        set(locked.mapped("checklist_id.display_name"))
                    ),
                )
            )

    @api.model_create_multi
    def create(self, vals_list):
        """Create questions and refuse creation on a locked checklist.

        :param vals_list: list of value dictionaries.
        :return: the created recordset.
        :rtype: recordset
        """
        lines = super().create(vals_list)
        lines._check_editable()
        return lines

    def write(self, vals):
        """Write questions and refuse modification on a locked checklist.

        :param vals: values to write.
        :return: ``True``.
        :rtype: bool
        """
        self._check_editable()
        result = super().write(vals)
        # The checklist of the line may have been changed by this write.
        self._check_editable()
        return result

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_audit_checklist_line(self):
        """Delete questions and refuse deletion on a locked checklist.

        :return: ``True``.
        :rtype: bool
        """
        self._check_editable()
