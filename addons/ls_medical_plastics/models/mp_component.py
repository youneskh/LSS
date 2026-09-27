# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Medical plastic component master data.

A component is the regulated identity of a moulded article: which product it
corresponds to in inventory, which material grades it may be made from, its
criticality classification and whether it contacts the medicinal product.
Moulding parameter specifications and moulding runs are always attached to a
component.
"""

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from ..constants import (
    CODE_MAX_LENGTH,
    COMPONENT_CATEGORIES,
    COMPONENT_STATES,
    CRITICALITY_LEVELS,
    MEASUREMENT_DIGITS,
    PARAMETER_SPEC_EFFECTIVE_STATE,
    PRIMARY_PACKAGING_CATEGORIES,
    STERILIZATION_METHODS,
)


class LsMpComponent(models.Model):
    """Moulded component master record."""

    _name = "ls.mp.component"
    _description = "Medical Plastics Component"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "code, name"

    name = fields.Char(string="Component Name", required=True, tracking=True)
    code = fields.Char(
        string="Component Code",
        required=True,
        size=CODE_MAX_LENGTH,
        index=True,
        tracking=True,
    )
    product_id = fields.Many2one(comodel_name="product.product", required=True,
                                 ondelete="restrict",
                                 tracking=True,
                                 help="Inventory product representing the moulded component.",)
    category = fields.Selection(
        selection=COMPONENT_CATEGORIES,
        string="Component Category",
        required=True,
        tracking=True,
    )
    is_primary_packaging = fields.Boolean(
        string="Primary Packaging",
        compute="_compute_is_primary_packaging",
        store=True,
        help=(
            "Computed from the component category. Primary packaging "
            "components are those categories that form part of the container "
            "closure system."
        ),
    )
    criticality = fields.Selection(selection=CRITICALITY_LEVELS, required=True,
                                   default="major",
                                   tracking=True,
                                   help=(
                                       "Criticality classification assigned by the organisation during "
                                       "risk assessment. The module stores the classification; it does "
                                       "not derive it."),
                                   )
    drug_contact = fields.Boolean(
        string="Direct Drug Contact",
        tracking=True,
        help="The component comes into direct contact with the medicinal product.",
    )
    sterile_supply = fields.Boolean(
        string="Supplied Sterile",
        tracking=True,
    )
    sterilization_method = fields.Selection(
        selection=STERILIZATION_METHODS,
        string="Sterilisation Method",
        default="none",
        tracking=True,
    )

    # -- Materials ----------------------------------------------------------
    material_grade_ids = fields.Many2many(
        comodel_name="ls.mp.material.grade",
        relation="ls_mp_component_material_grade_rel",
        column1="component_id",
        column2="grade_id",
        string="Approved Material Grades",
        help="Grades approved for moulding this component.",
    )
    primary_material_grade_id = fields.Many2one(comodel_name="ls.mp.material.grade", ondelete="restrict",
                                                tracking=True,)
    nominal_part_weight = fields.Float(digits=MEASUREMENT_DIGITS,
                                       help="Nominal mass of a single moulded part.",)
    part_weight_tolerance = fields.Float(digits=MEASUREMENT_DIGITS,
                                         help="Permitted deviation, expressed in the same unit as the nominal weight.",)
    part_weight_uom = fields.Char(string="Weight Unit", default="g")

    # -- Documentation ------------------------------------------------------
    customer_id = fields.Many2one(comodel_name="res.partner", ondelete="restrict",
                                  help="Customer for whom the component is manufactured, where applicable.",)
    drawing_reference = fields.Char(tracking=True)
    drawing_revision = fields.Char(tracking=True)
    specification_reference = fields.Char(tracking=True,
                                          help="Reference of the controlled specification document for this component.",)

    # -- Relations ----------------------------------------------------------
    tool_ids = fields.Many2many(
        comodel_name="ls.mp.tool",
        relation="ls_mp_tool_component_rel",
        column1="component_id",
        column2="tool_id",
        string="Tools",
    )
    tool_count = fields.Integer(compute="_compute_counts")
    parameter_spec_ids = fields.One2many(
        comodel_name="ls.mp.molding_parameter",
        inverse_name="component_id",
        string="Moulding Parameter Specifications",
    )
    parameter_spec_count = fields.Integer(
        string="Specification Count",
        compute="_compute_counts",
    )
    approved_spec_count = fields.Integer(
        string="Approved Specification Count",
        compute="_compute_counts",
    )
    run_ids = fields.One2many(
        comodel_name="ls.mp.injection_molding",
        inverse_name="component_id",
        string="Moulding Runs",
    )
    run_count = fields.Integer(compute="_compute_counts")

    state = fields.Selection(
        selection=COMPONENT_STATES,
        string="Status",
        default="draft",
        required=True,
        tracking=True,
        copy=False,
    )
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 index=True,
                                 default=lambda self: self.env.company,)
    active = fields.Boolean(default=True)
    note = fields.Text(string="Internal Notes")

    _code_company_unique = models.Constraint(
        "UNIQUE(code, company_id)",
        "The component code must be unique per company.",
    )
    _part_weight_positive = models.Constraint(
        "CHECK(nominal_part_weight >= 0 AND part_weight_tolerance >= 0)",
        "Part weight and tolerance cannot be negative.",
    )

    @api.depends("category")
    def _compute_is_primary_packaging(self):
        """Flag components whose category belongs to the container closure system."""
        for component in self:
            component.is_primary_packaging = component.category in PRIMARY_PACKAGING_CATEGORIES

    @api.depends("tool_ids", "parameter_spec_ids", "parameter_spec_ids.state", "run_ids")
    def _compute_counts(self):
        """Compute the smart-button counters shown on the component form."""
        for component in self:
            component.tool_count = len(component.tool_ids)
            component.parameter_spec_count = len(component.parameter_spec_ids)
            component.approved_spec_count = len(
                component.parameter_spec_ids.filtered(
                    lambda spec: spec.state == PARAMETER_SPEC_EFFECTIVE_STATE
                )
            )
            component.run_count = len(component.run_ids)

    @api.depends("code", "name")
    def _compute_display_name(self):
        """Show the component code together with its name."""
        for component in self:
            component.display_name = (
                f"[{component.code}] {component.name}" if component.code else component.name
            )

    @api.constrains("primary_material_grade_id", "material_grade_ids")
    def _check_primary_grade_is_approved(self):
        """The primary grade must also appear among the approved grades."""
        for component in self:
            grade = component.primary_material_grade_id
            if grade and grade not in component.material_grade_ids:
                raise ValidationError(
                    self.env._(
                        "The primary material grade %(grade)s is not listed among "
                        "the approved grades of component %(component)s.",
                        grade=grade.display_name,
                        component=component.display_name,
                    )
                )

    @api.constrains("sterile_supply", "sterilization_method")
    def _check_sterilization_method(self):
        """A component supplied sterile must declare a sterilisation method."""
        for component in self:
            if component.sterile_supply and component.sterilization_method in (False, "none"):
                raise ValidationError(
                    self.env._(
                        "Component %(component)s is supplied sterile and must "
                        "declare a sterilisation method.",
                        component=component.display_name,
                    )
                )

    @api.constrains("product_id", "company_id")
    def _check_product_company(self):
        """The linked product must belong to the same company, when restricted."""
        for component in self:
            product_company = component.product_id.company_id
            if product_company and product_company != component.company_id:
                raise ValidationError(
                    self.env._(
                        "Product %(product)s belongs to another company and cannot "
                        "be linked to component %(component)s.",
                        product=component.product_id.display_name,
                        component=component.display_name,
                    )
                )

    @api.onchange("sterile_supply")
    def _onchange_sterile_supply(self):
        """Clear the sterilisation method when the component is not sterile."""
        if not self.sterile_supply:
            self.sterilization_method = "none"

    def action_release(self):
        """Release the component for production use."""
        for component in self:
            if component.state not in ("draft", "on_hold"):
                raise ValidationError(
                    self.env._(
                        "Component %(component)s cannot be released from status "
                        "%(state)s.",
                        component=component.display_name,
                        state=dict(COMPONENT_STATES)[component.state],
                    )
                )
            if not component.material_grade_ids:
                raise ValidationError(
                    self.env._(
                        "Component %(component)s cannot be released without at "
                        "least one approved material grade.",
                        component=component.display_name,
                    )
                )
        return self.write({"state": "released"})

    def action_hold(self):
        """Place a released component on hold."""
        for component in self:
            if component.state != "released":
                raise ValidationError(
                    self.env._(
                        "Only released components can be placed on hold. "
                        "Component %(component)s is not released.",
                        component=component.display_name,
                    )
                )
        return self.write({"state": "on_hold"})

    def action_set_obsolete(self):
        """Mark the component obsolete."""
        for component in self:
            if component.state == "obsolete":
                raise ValidationError(
                    self.env._(
                        "Component %(component)s is already obsolete.",
                        component=component.display_name,
                    )
                )
        return self.write({"state": "obsolete"})

    def action_reset_to_draft(self):
        """Return an obsolete or held component to draft."""
        for component in self:
            if component.state not in ("on_hold", "obsolete"):
                raise ValidationError(
                    self.env._(
                        "Component %(component)s cannot be reset to draft from "
                        "status %(state)s.",
                        component=component.display_name,
                        state=dict(COMPONENT_STATES)[component.state],
                    )
                )
        return self.write({"state": "draft"})

    def action_view_tools(self):
        """Open the tools able to produce this component."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Tools"),
            "res_model": "ls.mp.tool",
            "view_mode": "list,form",
            "domain": [("id", "in", self.tool_ids.ids)],
            "context": {"default_component_ids": [(6, 0, self.ids)]},
        }

    def action_view_parameter_specs(self):
        """Open the moulding parameter specifications of this component."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Moulding Parameter Specifications"),
            "res_model": "ls.mp.molding_parameter",
            "view_mode": "list,form",
            "domain": [("component_id", "=", self.id)],
            "context": {"default_component_id": self.id},
        }

    def action_view_runs(self):
        """Open the moulding runs recorded for this component."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Moulding Runs"),
            "res_model": "ls.mp.injection_molding",
            "view_mode": "list,form",
            "domain": [("component_id", "=", self.id)],
            "context": {"default_component_id": self.id},
        }
