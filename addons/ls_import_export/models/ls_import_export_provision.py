# Part of the Life Sciences Suite for Odoo 19 Community Edition.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Cited regulatory provision.

A provision is the atomic unit of the registry: a record of a
regulatory text, cited to an official source, with an effective date
and a status. Every enforceable behaviour of the module references one
or more provisions; a requirement whose provisions are not ``in_force``
is never enforced (the engine returns *registry gap* instead).

The model ships empty. No provision is asserted as in force by the
module itself; each entry is created by a human who has read the
source, cited it and dated it. This is the operational form of the
suite's Truth Protocol for this module.
"""

from odoo import _, api, fields, models

from .constants import (
    AUTHORITY_SELECTION,
    INSTRUMENT_TYPE_SELECTION,
    OPERATION_TYPE_SCOPE_SELECTION,
    PROVISION_STATUS_SELECTION,
)


class LsImportExportProvision(models.Model):
    """A cited regulatory text; the trusted root of the registry."""

    _name = "ls.import_export.provision"
    _description = "Import & Export Compliance Provision"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "code desc, id desc"
    _check_company_auto = True

    # --- Identification ------------------------------------------------
    name = fields.Char(
        string="Title",
        required=True,
        tracking=True,
        help="Short human title of the provision, for example "
             "'Import authorisation for pharmaceutical products'.",
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

    # --- Source --------------------------------------------------------
    authority = fields.Selection(
        selection=AUTHORITY_SELECTION,
        required=True,
        tracking=True,
        help="Issuing body. This is master data listing bodies the "
             "registry can hold; it asserts nothing about any specific "
             "provision issued by that body.",
    )
    instrument_type = fields.Selection(
        selection=INSTRUMENT_TYPE_SELECTION,
        required=True,
        tracking=True,
    )
    reference = fields.Char(
        string="Official Reference",
        required=True,
        tracking=True,
        help="The official reference number or citation of the text.",
    )
    source_url = fields.Char(help="Official URL of the text.",)
    source_attachment_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="Archived Source",
        help="Archived copy of the source (e.g. PDF) for durability "
             "in case the official URL changes or disappears.",
    )

    # --- Lifecycle -----------------------------------------------------
    effective_date = fields.Date(required=True,
                                 tracking=True,
                                 help="Date of entry into force of the provision.",)
    end_date = fields.Date(tracking=True,
                           help="Date of abrogation or replacement, if any. If set, the "
                           "provision is no longer evaluated as in force after this "
                           "date.",)
    status = fields.Selection(
        selection=PROVISION_STATUS_SELECTION,
        default="under_review",
        required=True,
        tracking=True,
        index=True,
        help="Only provisions with status 'In Force' are evaluated by "
             "the compliance engine; any other status yields a "
             "registry gap.",
    )
    jurisdiction = fields.Char(default="Algeria",
                               tracking=True,)

    # --- Scope ---------------------------------------------------------
    product_category_ids = fields.Many2many(
        comodel_name="product.category",
        relation="ls_import_export_provision_category_rel",
        column1="provision_id",
        column2="category_id",
        string="Product Categories",
        help="Product categories the provision applies to. Leave empty "
             "if it is not scoped by category.",
    )
    operation_type_scope = fields.Selection(
        selection=OPERATION_TYPE_SCOPE_SELECTION,
        default="none",
        required=True,
        tracking=True,
    )

    # --- Content -------------------------------------------------------
    summary = fields.Text(help="Neutral paraphrase of what the provision requires. This "
                          "is never a claim that the provision is currently in "
                          "force unless status is 'In Force'.",)
    citation_ids = fields.One2many(
        comodel_name="ls.import_export.provision.citation",
        inverse_name="provision_id",
        string="Citations",
    )
    # Requirements cite provisions through a many2many (see
    # ls_import_export_compliance_requirement.py). The reverse relation
    # is therefore computed, not a plain one2many inverse.
    requirement_ids = fields.Many2many(
        comodel_name="ls.import_export.compliance.requirement",
        relation="ls_import_export_requirement_provision_rel",
        column1="provision_id",
        column2="requirement_id",
        string="Requirements Citing This Provision",
    )

    # --- Counters for smart-buttons ------------------------------------
    citation_count = fields.Integer(
        compute="_compute_citation_count",
    )
    requirement_count = fields.Integer(
        compute="_compute_requirement_count",
    )

    # --- Constraints ---------------------------------------------------
    _reference_uniq = models.Constraint(
        "UNIQUE(reference, company_id)",
        "The official reference must be unique per company.",
    )
    _end_date_after_effective = models.Constraint(
        "CHECK (end_date IS NULL OR end_date >= effective_date)",
        "The end date, if set, must be on or after the effective date.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Allocate the provision reference sequence on creation."""
        new_label = self.env._("New")
        for vals in vals_list:
            if vals.get("code", new_label) == new_label:
                vals["code"] = self.env["ir.sequence"].next_by_code(
                    "ls.import_export.provision"
                ) or new_label
        return super().create(vals_list)

    @api.depends("code", "name")
    def _compute_display_name(self):
        """Show code and title for readability."""
        for rec in self:
            rec.display_name = f"[{rec.code}] {rec.name}"

    @api.depends("citation_ids")
    def _compute_citation_count(self):
        for provision in self:
            provision.citation_count = len(provision.citation_ids)

    @api.depends("requirement_ids")
    def _compute_requirement_count(self):
        for provision in self:
            provision.requirement_count = len(provision.requirement_ids)

    def action_view_citations(self):
        """Smart-button: open citations of this provision."""
        self.ensure_one()
        return {
            "name": _("Citations"),
            "type": "ir.actions.act_window",
            "res_model": "ls.import_export.provision.citation",
            "view_mode": "tree,form",
            "domain": [("provision_id", "=", self.id)],
            "context": {
                "default_provision_id": self.id,
                "search_default_group_provision_id": self.id,
            },
        }

    def action_view_requirements(self):
        """Smart-button: open requirements citing this provision."""
        self.ensure_one()
        return {
            "name": _("Requirements"),
            "type": "ir.actions.act_window",
            "res_model": "ls.import_export.compliance.requirement",
            "view_mode": "tree,form",
            "domain": [("provision_ids", "=", self.id)],
        }
