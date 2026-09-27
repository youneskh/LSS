# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Significant manufacturing steps recorded in a batch record."""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

STEP_STATES = [
    ("pending", "Pending"),
    ("in_progress", "In Progress"),
    ("done", "Completed"),
    ("not_applicable", "Not Applicable"),
]


class LsPharmaBatchRecordStep(models.Model):
    """A significant step in the manufacture, processing, packing or holding.

    21 CFR 211.188(b) requires documentation that each significant step was
    accomplished, including the dates of 211.188(b)(1) and, under
    211.188(b)(11), the identification of the persons performing and directly
    supervising or checking each significant step, or, where the step is
    performed by automated equipment, the identification of the person
    checking the step performed by that equipment.
    """

    _name = "ls.pharma.batch_record.step"
    _description = "Batch Record Manufacturing Step"
    _order = "record_id, sequence, id"

    sequence = fields.Integer(default=10)
    record_id = fields.Many2one(
        comodel_name="ls.pharma.batch_record",
        string="Batch Record",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(comodel_name="res.company", related="record_id.company_id",
                                 store=True,
                                 index=True,)
    name = fields.Char(string="Step", required=True)
    instruction = fields.Text(help="Instruction reproduced from the master production and control record.",)
    is_significant = fields.Boolean(
        string="Significant Step",
        default=True,
        help=(
            "A significant step requires attribution and a date under "
            "21 CFR 211.188(b). Steps that are not significant may be "
            "recorded for completeness without attribution."
        ),
    )
    is_automated = fields.Boolean(
        string="Performed by Automated Equipment",
        help=(
            "When set, 21 CFR 211.188(b)(11) requires the identification of "
            "the person checking the step rather than of the person "
            "performing it."
        ),
    )
    performed_by_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Performed By",
    )
    checked_by_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Checked or Supervised By",
    )
    date_performed = fields.Datetime(help="Date required by 21 CFR 211.188(b)(1).",
                                     )
    recorded_value = fields.Char(help="Process value read at this step, such as a temperature or a duration.",)
    recorded_uom = fields.Char(string="Value Unit")
    state = fields.Selection(
        selection=STEP_STATES,
        string="Status",
        default="pending",
        required=True,
        index=True,
    )
    remark = fields.Text()

    @api.constrains(
        "state",
        "is_significant",
        "is_automated",
        "performed_by_user_id",
        "checked_by_user_id",
        "date_performed",
    )
    def _check_attribution(self):
        """Enforce the attribution required by 21 CFR 211.188(b)."""
        for step in self:
            if step.state != "done" or not step.is_significant:
                continue
            if not step.date_performed:
                raise ValidationError(
                    self.env._(
                        "Step %(name)s cannot be completed without a date. "
                        "21 CFR 211.188(b)(1) requires that dates be "
                        "documented.",
                        name=step.name,
                    )
                )
            if step.is_automated:
                if not step.checked_by_user_id:
                    raise ValidationError(
                        self.env._(
                            "Step %(name)s was performed by automated "
                            "equipment. 21 CFR 211.188(b)(11) requires the "
                            "identification of the person checking that step.",
                            name=step.name,
                        )
                    )
            elif not step.performed_by_user_id:
                raise ValidationError(
                    self.env._(
                        "Step %(name)s cannot be completed without "
                        "identifying the person who performed it, as required "
                        "by 21 CFR 211.188(b)(11).",
                        name=step.name,
                    )
                )

    def action_start(self):
        """Mark the selected steps as being in progress."""
        self.write({"state": "in_progress"})
        return True

    def action_done(self):
        """Complete the selected steps and stamp the executing user."""
        for step in self:
            values = {"state": "done"}
            if not step.date_performed:
                values["date_performed"] = fields.Datetime.now()
            if step.is_automated:
                if not step.checked_by_user_id:
                    values["checked_by_user_id"] = self.env.user.id
            elif not step.performed_by_user_id:
                values["performed_by_user_id"] = self.env.user.id
            step.write(values)
        return True

    def action_not_applicable(self):
        """Mark the selected steps as not applicable to this batch."""
        for step in self:
            if not step.remark:
                raise UserError(
                    self.env._(
                        "A remark is required to justify why step %(name)s is "
                        "not applicable to this batch.",
                        name=step.name,
                    )
                )
        self.write({"state": "not_applicable"})
        return True
