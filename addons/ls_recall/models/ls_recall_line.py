# Part of the Life Sciences Suite for Odoo 19 Community Edition.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Consignee line.

One line records what a single consignee received of a single lot, and
what has since been accounted for. The sum of the lines is the
reconciliation of the recall, which is the evidence that the recalled
quantity has been located.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError

from .constants import LINE_STATUS_SELECTION

#: Quantity fields whose modification is written to the recall chatter,
#: because they carry the reconciliation evidence.
AUDITED_QUANTITY_FIELDS = (
    "qty_shipped",
    "qty_returned",
    "qty_destroyed",
    "qty_not_recovered",
)


class LsRecallLine(models.Model):
    """Distribution and reconciliation for one consignee and one lot."""

    _name = "ls.recall.line"
    _description = "Recall Consignee Line"
    _order = "execution_id, partner_id, lot_id"
    _check_company_auto = True

    execution_id = fields.Many2one(
        comodel_name="ls.recall.execution",
        string="Recall",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(
        related="execution_id.company_id",
        store=True,
        index=True,
    )
    execution_state = fields.Selection(
        related="execution_id.state",
        store=True,
        string="Recall Status",
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Consignee",
        required=True,
        index=True,
    )
    lot_id = fields.Many2one(
        comodel_name="stock.lot",
        string="Lot / Serial Number",
        required=True,
        index=True,
        check_company=True,
    )
    product_id = fields.Many2one(related="lot_id.product_id",
                                 store=True)
    picking_ids = fields.Many2many(
        comodel_name="stock.picking",
        relation="ls_recall_line_picking_rel",
        column1="line_id",
        column2="picking_id",
        string="Source Transfers",
        help="Transfers from which the shipped quantity was traced.",
    )

    qty_shipped = fields.Float(
        string="Quantity Shipped",
        help="Quantity delivered to this consignee for this lot.",
    )
    qty_returned = fields.Float(
        string="Quantity Returned",
        help="Quantity physically returned to the organisation.",
    )
    qty_destroyed = fields.Float(
        string="Quantity Destroyed On Site",
        help="Quantity destroyed by the consignee under an agreed "
             "procedure, with destruction evidence retained.",
    )
    qty_not_recovered = fields.Float(
        string="Quantity Not Recoverable",
        help="Quantity the consignee has confirmed cannot be returned, "
             "for example because it was already administered or used.",
    )
    qty_accounted = fields.Float(compute="_compute_quantities", store=True)
    qty_outstanding = fields.Float(compute="_compute_quantities", store=True)

    notified = fields.Boolean(
        help="Set when this consignee has been sent a recall "
             "communication.",
    )
    notification_date = fields.Datetime()
    response_received = fields.Boolean()
    response_date = fields.Datetime()
    status = fields.Selection(
        selection=LINE_STATUS_SELECTION,
        compute="_compute_status",
        store=True,
        index=True,
    )
    notes = fields.Text()

    _partner_lot_uniq = models.Constraint(
        "UNIQUE(execution_id, partner_id, lot_id)",
        "A consignee can appear only once per lot on a recall.",
    )
    _quantities_positive = models.Constraint(
        "CHECK(qty_shipped >= 0 AND qty_returned >= 0"
        " AND qty_destroyed >= 0 AND qty_not_recovered >= 0)",
        "Recall quantities cannot be negative.",
    )

    @api.depends(
        "qty_shipped", "qty_returned", "qty_destroyed", "qty_not_recovered"
    )
    def _compute_quantities(self):
        """Derive the accounted and outstanding quantities."""
        for line in self:
            accounted = (
                line.qty_returned
                + line.qty_destroyed
                + line.qty_not_recovered
            )
            line.qty_accounted = accounted
            line.qty_outstanding = line.qty_shipped - accounted

    @api.depends(
        "notified",
        "response_received",
        "qty_shipped",
        "qty_accounted",
    )
    def _compute_status(self):
        """Derive the reconciliation status of the line.

        A line is reconciled when everything shipped is accounted for. It
        is a discrepancy when more has been accounted for than was
        shipped, which points at a data problem that must be resolved
        before the recall can be closed.
        """
        precision = self._quantity_precision()
        for line in self:
            difference = line.qty_accounted - line.qty_shipped
            if difference > precision:
                line.status = "discrepancy"
            elif line.qty_shipped and abs(difference) <= precision:
                line.status = "reconciled"
            elif line.response_received:
                line.status = "responded"
            elif line.notified:
                line.status = "notified"
            else:
                line.status = "pending"

    @api.model
    def _quantity_precision(self):
        """Return the tolerance used when comparing quantities.

        Quantities are stored as floats, so equality is evaluated within
        a fixed tolerance rather than exactly.
        """
        return 0.000001

    @api.onchange("qty_returned", "qty_destroyed", "qty_not_recovered")
    def _onchange_quantities(self):
        """Warn as soon as the accounted quantity exceeds the shipped one."""
        self.ensure_one()
        accounted = (
            self.qty_returned + self.qty_destroyed + self.qty_not_recovered
        )
        if accounted > self.qty_shipped + self._quantity_precision():
            return {
                "warning": {
                    "title": self.env._("Quantity discrepancy"),
                    "message": self.env._(
                        "The accounted quantity (%(accounted).2f) exceeds "
                        "the quantity shipped (%(shipped).2f) to this "
                        "consignee.",
                        accounted=accounted,
                        shipped=self.qty_shipped,
                    ),
                }
            }
        return None

    @api.onchange("response_received")
    def _onchange_response_received(self):
        """Stamp the response date when a response is registered."""
        for line in self:
            if line.response_received and not line.response_date:
                line.response_date = fields.Datetime.now()

    def write(self, vals):
        """Block edits on finalised recalls and audit quantity changes."""
        finalised = self.filtered(
            lambda line: line.execution_state in ("closed", "cancelled")
        )
        if finalised:
            raise UserError(
                self.env._(
                    "Recall %(name)s is finalised; its consignee lines "
                    "cannot be modified.",
                    name=finalised[0].execution_id.name,
                )
            )
        audited = [name for name in AUDITED_QUANTITY_FIELDS if name in vals]
        previous = {}
        if audited:
            previous = {
                line.id: {name: line[name] for name in audited}
                for line in self
            }
        result = super().write(vals)
        if audited:
            self._post_quantity_changes(audited, previous)
        return result

    def _post_quantity_changes(self, audited, previous):
        """Write quantity changes to the parent recall chatter.

        :param list audited: names of the quantity fields that changed.
        :param dict previous: values held before the write, keyed by id.
        """
        labels = {name: self._fields[name].string for name in audited}
        messages = {}
        for line in self:
            changes = []
            for name in audited:
                old = previous.get(line.id, {}).get(name, 0.0)
                new = line[name]
                if abs(new - old) <= self._quantity_precision():
                    continue
                changes.append(
                    self.env._(
                        "%(label)s: %(old).2f to %(new).2f",
                        label=labels[name],
                        old=old,
                        new=new,
                    )
                )
            if not changes:
                continue
            messages.setdefault(line.execution_id, []).append(
                self.env._(
                    "%(partner)s / lot %(lot)s - %(changes)s",
                    partner=line.partner_id.display_name,
                    lot=line.lot_id.display_name,
                    changes="; ".join(changes),
                )
            )
        for execution, entries in messages.items():
            execution.message_post(
                body=self.env._(
                    "Reconciliation updated:"
                ) + "<ul><li>" + "</li><li>".join(entries) + "</li></ul>"
            )

    def action_mark_notified(self):
        """Record that these consignees have been notified."""
        self.write(
            {"notified": True, "notification_date": fields.Datetime.now()}
        )
        return True
