# Part of the Life Sciences Suite for Odoo 19 Community Edition.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Compliance requirement.

A compliance requirement is an enforceable expectation (a required
document, a mandatory authorisation, a cost component, a threshold, a
deadline, a procedure) backed by one or more cited provisions. It is
the unit the compliance engine evaluates.

The Truth Protocol guard lives here: a requirement with no backing
provision cannot exist. The model-level constraint and the create/write
overrides together enforce this. This is what makes it structurally
impossible for the module to enforce a rule that has not been recorded
and cited.
"""

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from .constants import (
    OPERATION_TYPE_SCOPE_SELECTION,
    REQUIREMENT_TYPE_SELECTION,
)


class LsImportExportComplianceRequirement(models.Model):
    """An enforceable requirement, backed by cited provisions."""

    _name = "ls.import_export.compliance.requirement"
    _description = "Import & Export Compliance Requirement"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "code desc, id desc"
    _check_company_auto = True

    # --- Identification ------------------------------------------------
    name = fields.Char(
        string="Title",
        required=True,
        tracking=True,
    )
    code = fields.Char(
        string="Reference",
        readonly=True,
        copy=False,
        index=True,
        default="New",
        help="Unique reference allocated automatically on creation.",
    )
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )

    # --- Type and scope ------------------------------------------------
    requirement_type = fields.Selection(
        selection=REQUIREMENT_TYPE_SELECTION,
        required=True,
        tracking=True,
        help="The kind of enforceable expectation. The engine evaluates "
             "the requirement according to its type.",
    )
    operation_type_scope = fields.Selection(
        selection=OPERATION_TYPE_SCOPE_SELECTION,
        default="both",
        required=True,
        tracking=True,
    )
    product_category_ids = fields.Many2many(
        comodel_name="product.category",
        relation="ls_import_export_requirement_category_rel",
        column1="requirement_id",
        column2="category_id",
        string="Product Categories",
    )

    # --- Truth Protocol: backing provisions ----------------------------
    provision_ids = fields.Many2many(
        comodel_name="ls.import_export.provision",
        relation="ls_import_export_requirement_provision_rel",
        column1="requirement_id",
        column2="provision_id",
        string="Cited Provisions",
        help="The cited provisions that establish this requirement. At "
             "least one provision in force is required for the engine "
             "to evaluate the requirement; otherwise a registry gap is "
             "raised.",
    )
    in_force = fields.Boolean(
        string="Backed In Force",
        compute="_compute_in_force",
        store=True,
        help="True when at least one cited provision is in force.",
    )

    # --- Engine configuration (opaque in Phase 1) ----------------------
    config = fields.Text(
        string="Configuration",
        help="Engine-specific configuration for this requirement. Kept "
             "opaque in Phase 1; typed per requirement type in later "
             "phases.",
    )
    note = fields.Text()

    # --- Constraints ---------------------------------------------------
    # NOTE: a NOT NULL on a many2many column cannot be expressed as a
    # table CHECK, because the relation lives in a separate table. The
    # guard is therefore enforced in Python (create/write), which is
    # the form used across the suite for cross-table invariants.

    @api.depends("provision_ids", "provision_ids.status")
    def _compute_in_force(self):
        """A requirement is backed in force when at least one of its
        cited provisions has status 'in_force'.
        """
        for requirement in self:
            requirement.in_force = any(
                p.status == "in_force" for p in requirement.provision_ids
            )

    @api.model_create_multi
    def create(self, vals_list):
        """Allocate the requirement reference and enforce the Truth
        Protocol guard: a requirement must cite at least one provision.
        """
        new_label = self.env._("New")
        for vals in vals_list:
            if vals.get("code", new_label) == new_label:
                vals["code"] = self.env["ir.sequence"].next_by_code(
                    "ls.import_export.compliance.requirement"
                ) or new_label
            if not vals.get("provision_ids"):
                raise ValidationError(_(
                    "A compliance requirement must cite at least one "
                    "provision. A requirement without a cited provision "
                    "cannot exist (Truth Protocol)."
                ))
        return super().create(vals_list)

    def write(self, vals):
        """On any write, re-check that the requirement still cites at
        least one provision.
        """
        res = super().write(vals)
        if "provision_ids" in vals:
            for requirement in self:
                if not requirement.provision_ids:
                    raise ValidationError(_(
                        "A compliance requirement must cite at least "
                        "one provision. Removing the last cited "
                        "provision is not allowed (Truth Protocol)."
                    ))
        return res

    def name_get(self):
        return [(rec.id, f"[{rec.code}] {rec.name}") for rec in self]
