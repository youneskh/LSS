# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Standard operating procedures."""

from odoo import _, fields, models
from odoo.exceptions import UserError


class LsQmsSop(models.Model):
    """Controlled standard operating procedure."""

    _name = "ls.qms.sop"
    _description = "Standard Operating Procedure"
    _inherit = ["ls.qms.document.mixin"]
    _order = "reference, version desc"

    _ls_qms_sequence_code = "ls.qms.sop"

    _reference_version_uniq = models.Constraint(
        "UNIQUE (reference, version, company_id)",
        "The reference and version of a procedure must be unique per company.",
    )

    purpose = fields.Html(sanitize=True,
                          help="Objective of the procedure.",)
    scope = fields.Text(help="Activities, areas and personnel covered by the procedure.",)
    definitions = fields.Text(
        string="Definitions and Abbreviations",
    )
    responsibilities = fields.Html(sanitize=True,
                                   help="Roles accountable for each part of the procedure.",)
    procedure = fields.Html(sanitize=True,
                            help="Sequence of operations to be performed.",)
    reference_documents = fields.Text(help="Documents applied or cited by this procedure.",)
    training_required = fields.Boolean(default=True,
                                       help="Marks the procedure as requiring documented training before "
                                       "execution. The training records themselves are managed by the "
                                       "ls_training module of the Life Sciences Suite.",)
    previous_revision_id = fields.Many2one(comodel_name="ls.qms.sop", readonly=True,
                                           copy=False,
                                           index=True,)
    next_revision_ids = fields.One2many(
        comodel_name="ls.qms.sop",
        inverse_name="previous_revision_id",
        string="Following Revisions",
        readonly=True,
    )
    work_instruction_ids = fields.One2many(
        comodel_name="ls.qms.work_instruction",
        inverse_name="sop_id",
        string="Work Instructions",
        copy=False,
    )
    work_instruction_count = fields.Integer(
        string="Work Instructions",
        compute="_compute_work_instruction_count",
    )

    def _compute_work_instruction_count(self):
        """Count the work instructions attached to each procedure."""
        for sop in self:
            sop.work_instruction_count = len(sop.work_instruction_ids)

    def _ls_qms_content_fields(self):
        """Freeze the procedure body once the revision is published."""
        return super()._ls_qms_content_fields() + [
            "purpose",
            "scope",
            "definitions",
            "responsibilities",
            "procedure",
            "reference_documents",
        ]

    def action_submit_for_review(self):
        """Require purpose, scope and procedure before the review stage."""
        for sop in self:
            missing = []
            if not sop.purpose:
                missing.append(_("Purpose"))
            if not sop.scope:
                missing.append(_("Scope"))
            if not sop.procedure:
                missing.append(_("Procedure"))
            if missing:
                raise UserError(
                    _(
                        "The following sections of %(reference)s are empty: "
                        "%(sections)s.",
                        reference=sop.reference,
                        sections=", ".join(missing),
                    )
                )
        return super().action_submit_for_review()

    def action_view_work_instructions(self):
        """Open the work instructions attached to the procedure."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Work Instructions"),
            "res_model": "ls.qms.work_instruction",
            "view_mode": "list,form",
            "domain": [("sop_id", "=", self.id)],
            "context": {"default_sop_id": self.id},
        }
