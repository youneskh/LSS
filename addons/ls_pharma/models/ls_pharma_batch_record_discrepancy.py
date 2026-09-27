# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Discrepancies and their investigations, recorded in a batch record."""

from odoo import fields, models
from odoo.exceptions import UserError

from ..constants import DISCREPANCY_STATES

DISCREPANCY_CLASSIFICATIONS = [
    ("critical", "Critical"),
    ("major", "Major"),
    ("minor", "Minor"),
]


class LsPharmaBatchRecordDiscrepancy(models.Model):
    """An unexplained discrepancy and the investigation it triggered.

    21 CFR 211.192 requires that any unexplained discrepancy, including a
    percentage of theoretical yield outside the established limits, or the
    failure of a batch or of any of its components to meet a specification,
    be thoroughly investigated whether or not the batch has already been
    distributed; that the investigation extend to other batches of the same
    drug product and to other drug products that may have been associated
    with the failure; and that a written record of the investigation be made
    including its conclusions and follow-up.  Each of those elements is a
    field of this model, and closure is refused while one of them is missing.

    21 CFR 211.188(b)(12) requires that any investigation made according to
    211.192 appear in the batch production and control record; the
    investigation is therefore stored as a line of the batch record rather
    than as an independent document.
    """

    _name = "ls.pharma.batch_record.discrepancy"
    _description = "Batch Record Discrepancy and Investigation"
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
    name = fields.Char(string="Discrepancy", required=True)
    classification = fields.Selection(selection=DISCREPANCY_CLASSIFICATIONS, required=True,
                                      default="minor",)
    description = fields.Text(required=True)
    date_detected = fields.Datetime(
        string="Detected On", default=fields.Datetime.now, required=True
    )
    detected_by_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Detected By",
        default=lambda self: self.env.user,
    )
    investigation = fields.Text(help="Written record of the investigation required by 21 CFR 211.192.",)
    extended_to_other_batches = fields.Boolean(help=(
            "Records that the investigation was extended to other batches of "
            "the same drug product and to other drug products that may have "
            "been associated with the failure, as required by "
            "21 CFR 211.192."),
    )
    extension_scope = fields.Text(help="Identification of the other batches and products examined.",)
    conclusion = fields.Text()
    follow_up = fields.Text(string="Follow-Up")
    external_reference = fields.Char(help=(
            "Reference of the deviation or corrective and preventive action "
            "record raised in another system for this discrepancy."),
    )
    investigated_by_user_id = fields.Many2one(
        comodel_name="res.users", string="Investigated By", readonly=True, copy=False
    )
    date_closed = fields.Datetime(string="Closed On", readonly=True, copy=False)
    state = fields.Selection(
        selection=DISCREPANCY_STATES,
        string="Status",
        default="open",
        required=True,
        index=True,
        copy=False,
    )

    def action_start_investigation(self):
        """Move the selected discrepancies to the investigation state."""
        for discrepancy in self:
            if discrepancy.state != "open":
                raise UserError(
                    self.env._(
                        "Discrepancy %(name)s is not open.",
                        name=discrepancy.name,
                    )
                )
        self.write({"state": "under_investigation"})
        return True

    def action_close(self):
        """Close the selected discrepancies.

        Closure is refused unless every element required by 21 CFR 211.192 is
        present: the written investigation, the confirmation that the
        investigation was extended where required, the conclusion and the
        follow-up.
        """
        for discrepancy in self:
            if discrepancy.state == "closed":
                raise UserError(
                    self.env._(
                        "Discrepancy %(name)s is already closed.",
                        name=discrepancy.name,
                    )
                )
            missing = []
            if not discrepancy.investigation:
                missing.append(self.env._("the written investigation"))
            if not discrepancy.conclusion:
                missing.append(self.env._("the conclusion"))
            if not discrepancy.follow_up:
                missing.append(self.env._("the follow-up"))
            if (
                discrepancy.extended_to_other_batches
                and not discrepancy.extension_scope
            ):
                missing.append(self.env._("the scope of the extension"))
            if missing:
                raise UserError(
                    self.env._(
                        "Discrepancy %(name)s cannot be closed because "
                        "%(missing)s is missing. 21 CFR 211.192 requires a "
                        "written record of the investigation including its "
                        "conclusions and follow-up.",
                        name=discrepancy.name,
                        missing=", ".join(missing),
                    )
                )
            discrepancy.write(
                {
                    "state": "closed",
                    "investigated_by_user_id": self.env.user.id,
                    "date_closed": fields.Datetime.now(),
                }
            )
        return True

    def action_reopen(self):
        """Reopen the selected discrepancies."""
        self.write(
            {
                "state": "under_investigation",
                "date_closed": False,
            }
        )
        return True
