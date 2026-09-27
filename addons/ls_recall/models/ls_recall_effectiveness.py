# Part of the Life Sciences Suite for Odoo 19 Community Edition.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Effectiveness check.

An effectiveness check is a record that one consignee was contacted and
what the contact established. 21 CFR 7.42(b)(3) describes the purpose of
effectiveness checks as verifying that all consignees at the recall depth
specified by the strategy have received notification and have taken
appropriate action, and names personal visits, telephone calls and
letters as the contact methods.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from .constants import (
    EFFECTIVENESS_METHOD_SELECTION,
    EFFECTIVENESS_OUTCOME_SELECTION,
    EFFECTIVENESS_STATE_SELECTION,
)


class LsRecallEffectiveness(models.Model):
    """A single documented contact with one consignee."""

    _name = "ls.recall.effectiveness"
    _description = "Recall Effectiveness Check"
    _order = "execution_id, partner_id, attempt_number, id"
    _check_company_auto = True

    execution_id = fields.Many2one(
        comodel_name="ls.recall.execution",
        string="Recall",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(
        related="execution_id.company_id", store=True, index=True
    )
    execution_state = fields.Selection(
        related="execution_id.state", store=True, string="Recall Status"
    )
    line_id = fields.Many2one(
        comodel_name="ls.recall.line",
        string="Consignee Line",
        ondelete="cascade",
        index=True,
        domain="[('execution_id', '=', execution_id)]",
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Consignee",
        required=True,
        compute="_compute_partner_id",
        store=True,
        precompute=True,
        readonly=False,
        index=True,
    )
    check_level = fields.Selection(
        related="execution_id.effectiveness_level",
        store=True,
        string="Level",
    )
    method = fields.Selection(
        selection=EFFECTIVENESS_METHOD_SELECTION,
        required=True,
        default="phone",
    )
    attempt_number = fields.Integer(
        default=1,
        required=True,
        help="Sequential number of the contact attempt with this "
             "consignee for this recall.",
    )
    planned_date = fields.Date(default=fields.Date.context_today)
    performed_date = fields.Datetime(readonly=True, copy=False)
    performed_by_user_id = fields.Many2one(
        comodel_name="res.users", readonly=True, copy=False
    )
    outcome = fields.Selection(selection=EFFECTIVENESS_OUTCOME_SELECTION)
    state = fields.Selection(
        selection=EFFECTIVENESS_STATE_SELECTION,
        default="planned",
        required=True,
        copy=False,
        index=True,
    )
    notes = fields.Text()

    _attempt_positive = models.Constraint(
        "CHECK(attempt_number > 0)",
        "The attempt number must be greater than zero.",
    )

    @api.depends("line_id.partner_id")
    def _compute_partner_id(self):
        """Default the consignee from the linked consignee line."""
        for check in self:
            if check.line_id:
                check.partner_id = check.line_id.partner_id
            elif not check.partner_id:
                check.partner_id = False

    @api.constrains("line_id", "execution_id")
    def _check_line_belongs_to_execution(self):
        """The consignee line must belong to the same recall."""
        for check in self.filtered("line_id"):
            if check.line_id.execution_id != check.execution_id:
                raise ValidationError(
                    self.env._(
                        "The consignee line does not belong to recall "
                        "%(name)s.",
                        name=check.execution_id.name,
                    )
                )

    @api.constrains("state", "outcome", "performed_date")
    def _check_performed_complete(self):
        """A performed check must state what it established and when."""
        for check in self.filtered(lambda c: c.state == "performed"):
            if not check.outcome or not check.performed_date:
                raise ValidationError(
                    self.env._(
                        "A performed effectiveness check must record an "
                        "outcome and the date it was performed."
                    )
                )

    def write(self, vals):
        """Prevent edits once the parent recall is finalised."""
        finalised = self.filtered(
            lambda c: c.execution_state in ("closed", "cancelled")
        )
        if finalised:
            raise UserError(
                self.env._(
                    "Recall %(name)s is finalised; its effectiveness "
                    "checks cannot be modified.",
                    name=finalised[0].execution_id.name,
                )
            )
        return super().write(vals)

    def action_perform(self):
        """Record the check as performed.

        The outcome must already be set, because the outcome is what the
        check exists to capture.
        """
        for check in self:
            if check.state != "planned":
                raise UserError(
                    self.env._(
                        "Only a planned check can be recorded as "
                        "performed."
                    )
                )
            if not check.outcome:
                raise UserError(
                    self.env._(
                        "Record the outcome of the contact with "
                        "%(partner)s before marking the check as "
                        "performed.",
                        partner=check.partner_id.display_name,
                    )
                )
        self.write(
            {
                "state": "performed",
                "performed_date": fields.Datetime.now(),
                "performed_by_user_id": self.env.user.id,
            }
        )
        for check in self:
            if check.line_id and not check.line_id.response_received:
                check.line_id.write(
                    {
                        "response_received": True,
                        "response_date": check.performed_date,
                    }
                )
        return True

    def action_escalate(self):
        """Escalate a check and plan a further attempt.

        Used when a consignee cannot be reached. A new planned check is
        created with the attempt number incremented, so that the record
        shows how many times contact was attempted.
        """
        follow_ups = self.browse()
        for check in self:
            if check.state not in ("planned", "performed"):
                raise UserError(
                    self.env._("This check cannot be escalated.")
                )
            check.state = "escalated"
            follow_ups |= check.copy(
                {
                    "attempt_number": check.attempt_number + 1,
                    "state": "planned",
                    "outcome": False,
                    "planned_date": fields.Date.context_today(self),
                }
            )
            check.execution_id.message_post(
                body=self.env._(
                    "Effectiveness check with %(partner)s escalated; "
                    "attempt %(attempt)s planned.",
                    partner=check.partner_id.display_name,
                    attempt=check.attempt_number + 1,
                )
            )
        return True
