# Part of the Life Sciences Suite for Odoo 19 Community Edition.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Recall communication.

Every message issued in the course of a field action is recorded here:
recall notices to consignees, field safety notices to users,
notifications to competent authorities, public warnings, reminders,
status updates and the closure notice.

Before a recall notice can be recorded as sent, the five content
confirmations must be ticked. They correspond to the elements that
21 CFR 7.49(a) states a recall communication is to contain. The
confirmations do not inspect the text; they record that a named person
checked the text against those elements and, in doing so, make the check
itself auditable.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from .constants import (
    COMMUNICATION_CHANNEL_SELECTION,
    COMMUNICATION_CONTENT_FLAGS,
    COMMUNICATION_STATE_SELECTION,
    COMMUNICATION_TYPE_SELECTION,
)

#: Communication types for which the content confirmations are mandatory.
CONTENT_CONTROLLED_TYPES = ("recall_notice", "field_safety_notice")


class LsRecallCommunication(models.Model):
    """One outgoing communication belonging to a recall."""

    _name = "ls.recall.communication"
    _description = "Recall Communication"
    _inherit = ["mail.thread"]
    _order = "execution_id, sent_date desc, id desc"
    _check_company_auto = True

    name = fields.Char(
        string="Reference",
        readonly=True,
        copy=False,
        index=True,
        default=lambda self: self.env._("New"),
    )
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
    communication_type = fields.Selection(
        selection=COMMUNICATION_TYPE_SELECTION,
        required=True,
        default="recall_notice",
        tracking=True,
    )
    channel = fields.Selection(
        selection=COMMUNICATION_CHANNEL_SELECTION,
        required=True,
        default="email",
        tracking=True,
    )
    urgent = fields.Boolean(
        help="Marks the communication as urgent. 21 CFR 7.49(b) states "
             "that recall communications should be marked 'urgent' for "
             "class I and class II recalls and, when appropriate, for "
             "class III recalls.",
    )
    partner_ids = fields.Many2many(
        comodel_name="res.partner",
        relation="ls_recall_communication_partner_rel",
        column1="communication_id",
        column2="partner_id",
        string="Recipients",
    )
    recipient_count = fields.Integer(
        compute="_compute_recipient_count", store=True
    )
    subject = fields.Char(required=True, tracking=True)
    body = fields.Html(sanitize=True, tracking=True)
    state = fields.Selection(
        selection=COMMUNICATION_STATE_SELECTION,
        default="draft",
        required=True,
        copy=False,
        tracking=True,
        index=True,
    )

    planned_date = fields.Date(default=fields.Date.context_today)
    approved_by_user_id = fields.Many2one(
        comodel_name="res.users", readonly=True, copy=False, tracking=True
    )
    approval_date = fields.Datetime(readonly=True, copy=False)
    sent_date = fields.Datetime(readonly=True, copy=False, tracking=True)
    sent_by_user_id = fields.Many2one(
        comodel_name="res.users", readonly=True, copy=False
    )
    acknowledged_date = fields.Datetime(readonly=True, copy=False)
    acknowledgement_note = fields.Text()

    content_identifies_product = fields.Boolean(
        string="Identifies the product",
        help="The text identifies the product, size, lot or serial "
             "numbers and any other information needed for immediate "
             "identification.",
    )
    content_states_reason = fields.Boolean(
        string="States the reason and the hazard",
        help="The text explains the reason for the action and the "
             "hazard involved, if any.",
    )
    content_gives_instructions = fields.Boolean(
        string="Gives instructions",
        help="The text tells the recipient what to do with the product.",
    )
    content_requests_response = fields.Boolean(
        string="Requests a response",
        help="The text asks the recipient to report back, which is what "
             "makes reconciliation and effectiveness checking possible.",
    )
    content_gives_contact = fields.Boolean(
        string="Gives a contact point",
        help="The text names a contact for questions.",
    )
    content_complete = fields.Boolean(
        compute="_compute_content_complete", store=True
    )

    _name_uniq = models.Constraint(
        "UNIQUE(name)",
        "The communication reference must be unique.",
    )

    @api.depends("partner_ids")
    def _compute_recipient_count(self):
        """Count the addressees of the communication."""
        for communication in self:
            communication.recipient_count = len(communication.partner_ids)

    @api.depends(*COMMUNICATION_CONTENT_FLAGS)
    def _compute_content_complete(self):
        """Set when every content element has been confirmed."""
        for communication in self:
            communication.content_complete = all(
                communication[flag] for flag in COMMUNICATION_CONTENT_FLAGS
            )

    @api.constrains("communication_type", "partner_ids")
    def _check_recipients(self):
        """A directed communication must have at least one addressee.

        A public warning is addressed to the public through the media and
        therefore has no partner list.
        """
        for communication in self:
            if communication.communication_type == "public_warning":
                continue
            if not communication.partner_ids:
                raise ValidationError(
                    self.env._(
                        "Communication %(name)s has no recipient.",
                        name=communication.name,
                    )
                )

    @api.model_create_multi
    def create(self, vals_list):
        """Allocate the communication reference from the sequence."""
        new_label = self.env._("New")
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == new_label:
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code(
                        "ls.recall.communication"
                    )
                    or new_label
                )
        return super().create(vals_list)

    def write(self, vals):
        """Freeze a communication once it has been recorded as sent."""
        sent = self.filtered(lambda c: c.state in ("sent", "acknowledged"))
        if sent:
            allowed = {
                "state",
                "acknowledged_date",
                "acknowledgement_note",
                "message_follower_ids",
                "message_ids",
                "message_main_attachment_id",
            }
            forbidden = set(vals) - allowed
            if forbidden:
                raise UserError(
                    self.env._(
                        "Communication %(name)s has been sent and is part "
                        "of the recall record. The following cannot be "
                        "changed: %(fields)s.",
                        name=sent[0].name,
                        fields=", ".join(sorted(forbidden)),
                    )
                )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_only_draft(self):
        """Only an unsent communication may be deleted."""
        blocked = self.filtered(lambda c: c.state != "draft")
        if blocked:
            raise UserError(
                self.env._(
                    "Communication %(name)s is no longer a draft and "
                    "cannot be deleted.",
                    name=blocked[0].name,
                )
            )

    def action_approve(self):
        """Approve the text of a draft communication."""
        for communication in self:
            if communication.state != "draft":
                raise UserError(
                    self.env._("Only a draft communication can be approved.")
                )
            if not communication.body:
                raise UserError(
                    self.env._(
                        "Communication %(name)s has no text.",
                        name=communication.name,
                    )
                )
            communication._check_content_confirmations()
        self.write(
            {
                "state": "approved",
                "approved_by_user_id": self.env.user.id,
                "approval_date": fields.Datetime.now(),
            }
        )
        return True

    def action_mark_sent(self):
        """Record that the communication has been issued.

        The recipients' consignee lines are marked as notified, and an
        authority notification updates the recall header so that the fact
        of notification is visible without opening the communication.
        """
        now = fields.Datetime.now()
        for communication in self:
            if communication.state != "approved":
                raise UserError(
                    self.env._(
                        "Communication %(name)s must be approved before "
                        "it can be recorded as sent.",
                        name=communication.name,
                    )
                )
            communication._check_content_confirmations()
        self.write(
            {
                "state": "sent",
                "sent_date": now,
                "sent_by_user_id": self.env.user.id,
            }
        )
        for communication in self:
            communication._propagate_notification(now)
        return True

    def action_acknowledge(self):
        """Record that a recipient acknowledged the communication."""
        for communication in self:
            if communication.state != "sent":
                raise UserError(
                    self.env._(
                        "Only a sent communication can be acknowledged."
                    )
                )
        self.write(
            {
                "state": "acknowledged",
                "acknowledged_date": fields.Datetime.now(),
            }
        )
        return True

    def action_cancel(self):
        """Cancel a communication that was never sent."""
        for communication in self:
            if communication.state in ("sent", "acknowledged"):
                raise UserError(
                    self.env._(
                        "Communication %(name)s has been sent and cannot "
                        "be cancelled.",
                        name=communication.name,
                    )
                )
        self.write({"state": "cancelled"})
        return True

    def _check_content_confirmations(self):
        """Verify the content confirmations for controlled notices."""
        self.ensure_one()
        if self.communication_type not in CONTENT_CONTROLLED_TYPES:
            return
        missing = [
            self._fields[flag].string
            for flag in COMMUNICATION_CONTENT_FLAGS
            if not self[flag]
        ]
        if missing:
            raise UserError(
                self.env._(
                    "The following content elements of %(name)s have not "
                    "been confirmed: %(missing)s.",
                    name=self.name,
                    missing=", ".join(missing),
                )
            )

    def _propagate_notification(self, sent_on):
        """Update the recall and its consignee lines after sending.

        :param datetime sent_on: the moment the communication was sent.
        """
        self.ensure_one()
        execution = self.execution_id
        if self.communication_type == "authority_notification":
            execution._register_authority_notification(sent_on)
        lines = execution.line_ids.filtered(
            lambda line: line.partner_id in self.partner_ids
            and not line.notified
        )
        if lines:
            lines.write({"notified": True, "notification_date": sent_on})
        execution.message_post(
            body=self.env._(
                "Communication %(name)s (%(type)s) recorded as sent to "
                "%(count)s recipients.",
                name=self.name,
                type=dict(COMMUNICATION_TYPE_SELECTION).get(
                    self.communication_type, self.communication_type
                ),
                count=len(self.partner_ids),
            )
        )
