# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Quality policy: the top level document of the quality management system."""

from odoo import _, fields, models
from odoo.exceptions import UserError


class LsQmsPolicy(models.Model):
    """Controlled quality policy with revision and periodic review."""

    _name = "ls.qms.policy"
    _description = "Quality Policy"
    _inherit = ["ls.qms.document.mixin"]
    _order = "reference, version desc"

    _ls_qms_sequence_code = "ls.qms.policy"

    _reference_version_uniq = models.Constraint(
        "UNIQUE (reference, version, company_id)",
        "The reference and version of a quality policy must be unique per"
        " company.",
    )

    policy_statement = fields.Html(sanitize=True,
                                   help="Statement of intent and direction issued by top management.",)
    scope = fields.Text(help="Sites, products and processes covered by the policy.",)
    commitment = fields.Html(
        string="Commitments",
        sanitize=True,
        help="Commitments made by the organisation, for example to satisfy"
        " applicable requirements and to continually improve the quality"
        " management system.",
    )
    communication_method = fields.Text(help="How the policy is communicated internally and made available"
                                       " to interested parties.",)
    previous_revision_id = fields.Many2one(comodel_name="ls.qms.policy", readonly=True,
                                           copy=False,
                                           index=True,)
    next_revision_ids = fields.One2many(
        comodel_name="ls.qms.policy",
        inverse_name="previous_revision_id",
        string="Following Revisions",
        readonly=True,
    )
    objective_ids = fields.One2many(
        comodel_name="ls.qms.objective",
        inverse_name="policy_id",
        string="Quality Objectives",
        copy=False,
    )
    objective_count = fields.Integer(
        string="Objectives",
        compute="_compute_objective_count",
    )

    def _compute_objective_count(self):
        """Count the quality objectives derived from each policy."""
        for policy in self:
            policy.objective_count = len(policy.objective_ids)

    def _ls_qms_content_fields(self):
        """Freeze the policy body once the revision is published."""
        return super()._ls_qms_content_fields() + [
            "policy_statement",
            "scope",
            "commitment",
            "communication_method",
        ]

    def action_submit_for_review(self):
        """Require a policy statement before the review stage."""
        for policy in self:
            if not policy.policy_statement:
                raise UserError(
                    _(
                        "The policy statement of %(reference)s is empty. "
                        "Complete it before submitting the document for "
                        "review.",
                        reference=policy.reference,
                    )
                )
        return super().action_submit_for_review()

    def action_view_objectives(self):
        """Open the quality objectives derived from the policy."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Quality Objectives"),
            "res_model": "ls.qms.objective",
            "view_mode": "list,form,graph,pivot",
            "domain": [("policy_id", "=", self.id)],
            "context": {"default_policy_id": self.id},
        }
