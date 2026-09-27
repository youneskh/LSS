# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Polymer and masterbatch grade register.

A material grade is the qualified identity of a resin or colorant used to
mould medical plastic components. Traceability of a moulded component back to
the exact resin grade and resin lot is the reason this register exists: the
moulding run records consumption against grades declared here.
"""

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from ..constants import (
    CODE_MAX_LENGTH,
    MATERIAL_QUALIFICATION_STATES,
    MEASUREMENT_DIGITS,
    POLYMER_TYPES,
)


class LsMpMaterialGrade(models.Model):
    """Qualified polymer or masterbatch grade."""

    _name = "ls.mp.material.grade"
    _description = "Medical Plastics Material Grade"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "code, name"

    name = fields.Char(
        string="Grade Name",
        required=True,
        tracking=True,
        help="Commercial designation of the resin or masterbatch grade.",
    )
    code = fields.Char(
        string="Internal Code",
        required=True,
        size=CODE_MAX_LENGTH,
        index=True,
        tracking=True,
        help="Unique internal identifier of the grade within the company.",
    )
    polymer_type = fields.Selection(selection=POLYMER_TYPES, required=True,
                                    tracking=True,)
    manufacturer_id = fields.Many2one(
        comodel_name="res.partner",
        string="Resin Manufacturer",
        ondelete="restrict",
        tracking=True,
        help="Organisation that produces the grade.",
    )
    supplier_ids = fields.Many2many(
        comodel_name="res.partner",
        relation="ls_mp_material_grade_supplier_rel",
        column1="grade_id",
        column2="partner_id",
        string="Approved Suppliers",
        help="Distributors or suppliers approved to deliver this grade.",
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Inventory Product",
        ondelete="restrict",
        tracking=True,
        help="Stockable product used to purchase and consume this grade.",
    )

    # -- Intended use -------------------------------------------------------
    drug_contact = fields.Boolean(
        string="Direct Drug Contact",
        tracking=True,
        help=(
            "The moulded part made from this grade is intended to come into "
            "direct contact with the medicinal product."
        ),
    )
    food_contact = fields.Boolean()
    regulatory_reference = fields.Text(
        string="Regulatory / Compendial References",
        help=(
            "Free-text field for the references the organisation relies on "
            "for this grade, for example supplier declarations, compendial "
            "chapters or master file numbers. No content is pre-populated: "
            "the applicable references must be determined and entered by the "
            "organisation."
        ),
    )
    master_file_reference = fields.Char(help="Supplier master file or type file reference, where one exists.",)
    change_notification_agreement = fields.Boolean(tracking=True,
                                                   help=(
                                                       "A written agreement is in place obliging the supplier to notify "
                                                       "changes to the grade before implementation."),
                                                   )

    # -- Technical data -----------------------------------------------------
    melt_flow_index = fields.Float(digits=MEASUREMENT_DIGITS,)
    melt_flow_index_uom = fields.Char(
        string="MFI Unit",
        default="g/10 min",
        help="Unit label for the melt flow index, recorded as free text.",
    )
    density = fields.Float(digits=MEASUREMENT_DIGITS)
    density_uom = fields.Char(string="Density Unit", default="g/cm3")
    recycled_content = fields.Float(
        string="Recycled Content (%)",
        digits=(5, 2),
        help="Declared recycled content expressed as a percentage from 0 to 100.",
    )
    default_quantity_uom = fields.Char(
        string="Consumption Unit",
        default="kg",
        required=True,
        help=(
            "Unit label used when recording consumption of this grade on a "
            "moulding run. Recorded as free text because moulding "
            "consumption units are configured per site."
        ),
    )

    # -- Qualification ------------------------------------------------------
    qualification_state = fields.Selection(
        selection=MATERIAL_QUALIFICATION_STATES,
        string="Qualification Status",
        default="draft",
        required=True,
        tracking=True,
        copy=False,
    )
    qualification_date = fields.Date(string="Qualified On", tracking=True, copy=False)
    requalification_date = fields.Date(
        string="Requalification Due",
        tracking=True,
        copy=False,
        help="Date at which the grade qualification must be reviewed.",
    )
    qualification_note = fields.Text(string="Qualification Notes")

    # -- Housekeeping -------------------------------------------------------
    component_ids = fields.Many2many(
        comodel_name="ls.mp.component",
        relation="ls_mp_component_material_grade_rel",
        column1="grade_id",
        column2="component_id",
        string="Components",
    )
    component_count = fields.Integer(compute="_compute_component_count",)
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 index=True,
                                 default=lambda self: self.env.company,)
    active = fields.Boolean(default=True)
    note = fields.Text(string="Internal Notes")

    _code_company_unique = models.Constraint(
        "UNIQUE(code, company_id)",
        "The material grade internal code must be unique per company.",
    )
    _recycled_content_range = models.Constraint(
        "CHECK(recycled_content >= 0 AND recycled_content <= 100)",
        "The recycled content must be a percentage between 0 and 100.",
    )

    @api.depends("component_ids")
    def _compute_component_count(self):
        """Count the components declaring this grade."""
        for grade in self:
            grade.component_count = len(grade.component_ids)

    @api.depends("code", "name")
    def _compute_display_name(self):
        """Show the internal code together with the commercial name."""
        for grade in self:
            grade.display_name = f"[{grade.code}] {grade.name}" if grade.code else grade.name

    @api.constrains("qualification_state", "qualification_date")
    def _check_qualification_date(self):
        """A qualified grade must carry the date on which it was qualified."""
        for grade in self:
            if grade.qualification_state in ("qualified", "conditionally_qualified"):
                if not grade.qualification_date:
                    raise ValidationError(
                        self.env._(
                            "Grade %(name)s cannot be set to a qualified status "
                            "without a qualification date.",
                            name=grade.display_name,
                        )
                    )

    @api.constrains("qualification_date", "requalification_date")
    def _check_requalification_after_qualification(self):
        """Requalification cannot be scheduled before qualification."""
        for grade in self:
            if (
                grade.qualification_date
                and grade.requalification_date
                and grade.requalification_date < grade.qualification_date
            ):
                raise ValidationError(
                    self.env._(
                        "The requalification date of grade %(name)s precedes its "
                        "qualification date.",
                        name=grade.display_name,
                    )
                )

    def action_set_under_evaluation(self):
        """Move draft grades into evaluation."""
        self._assert_state_transition(("draft", "rejected"))
        return self.write({"qualification_state": "under_evaluation"})

    def action_qualify(self):
        """Qualify the grade, stamping today's date when none is set."""
        self._assert_state_transition(("draft", "under_evaluation", "conditionally_qualified"))
        for grade in self:
            grade.write(
                {
                    "qualification_state": "qualified",
                    "qualification_date": grade.qualification_date
                    or fields.Date.context_today(grade),
                }
            )
        return True

    def action_qualify_conditionally(self):
        """Qualify the grade subject to conditions recorded in the notes."""
        self._assert_state_transition(("draft", "under_evaluation"))
        for grade in self:
            if not grade.qualification_note:
                raise ValidationError(
                    self.env._(
                        "Conditional qualification of grade %(name)s requires the "
                        "conditions to be recorded in the qualification notes.",
                        name=grade.display_name,
                    )
                )
            grade.write(
                {
                    "qualification_state": "conditionally_qualified",
                    "qualification_date": grade.qualification_date
                    or fields.Date.context_today(grade),
                }
            )
        return True

    def action_reject(self):
        """Reject the grade."""
        self._assert_state_transition(("draft", "under_evaluation"))
        return self.write({"qualification_state": "rejected"})

    def action_set_obsolete(self):
        """Mark the grade obsolete so that it can no longer be consumed."""
        self._assert_state_transition(("qualified", "conditionally_qualified", "rejected"))
        return self.write({"qualification_state": "obsolete"})

    def action_reset_to_draft(self):
        """Return a rejected or obsolete grade to draft for rework."""
        self._assert_state_transition(("rejected", "obsolete"))
        return self.write({"qualification_state": "draft"})

    def _assert_state_transition(self, allowed_states):
        """Raise when any record is not in one of ``allowed_states``.

        :param tuple allowed_states: qualification states permitted as source.
        :raises ValidationError: if a record is in a different state.
        """
        for grade in self:
            if grade.qualification_state not in allowed_states:
                raise ValidationError(
                    self.env._(
                        "This action is not allowed for grade %(name)s in status "
                        "%(state)s.",
                        name=grade.display_name,
                        state=dict(MATERIAL_QUALIFICATION_STATES)[grade.qualification_state],
                    )
                )
