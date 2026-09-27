# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Approval records of a controlled document.

One approval record is created per approver and per review cycle. Approvals
are requested in parallel: the document reaches the Approved status once every
pending approval of the current version has been granted.

This model records who decided, when, and with which comment. It does not
implement an electronic signature within the meaning of FDA 21 CFR Part 11
subpart C; that capability belongs to the separate ``ls_electronic_signature``
module of the Life Sciences Suite.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class LsDocumentApproval(models.Model):
    """Decision of one approver on one version of a document."""

    _name = "ls.document.approval"
    _description = "Life Sciences Document Approval"
    _order = "document_id, create_date desc, id desc"

    document_id = fields.Many2one(comodel_name="ls.document.document", required=True,
                                  index=True,
                                  ondelete="cascade",)
    version_id = fields.Many2one(comodel_name="ls.document.version", required=True,
                                 index=True,
                                 ondelete="cascade",)
    company_id = fields.Many2one(comodel_name="res.company", related="document_id.company_id",
                                 store=True,
                                 index=True,)
    approver_id = fields.Many2one(comodel_name="res.users", required=True,
                                  index=True,
                                  ondelete="restrict",)
    state = fields.Selection(
        selection=[
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
            ("cancelled", "Cancelled"),
        ],
        string="Decision",
        required=True,
        default="pending",
        index=True,
    )
    decision_date = fields.Datetime(readonly=True,
                                    copy=False,)
    comment = fields.Text()

    # A partial unique index is used instead of a plain UNIQUE constraint so
    # that a document rejected and then resubmitted can request a decision
    # from the same approver on the same version again, while the previous
    # decisions remain in the history.
    _pending_approver_uniq = models.UniqueIndex(
        "(document_id, version_id, approver_id) WHERE state = 'pending'"
    )

    @api.depends("document_id.reference", "approver_id.name", "state")
    def _compute_display_name(self):
        """Display the approval as ``NUMBER - Approver (Decision)``."""
        state_labels = dict(self._fields["state"].selection)
        for approval in self:
            approval.display_name = "%s - %s (%s)" % (
                approval.document_id.reference or "",
                approval.approver_id.name or "",
                state_labels.get(approval.state, ""),
            )

    def _check_decision_allowed(self):
        """Verify that the current user may record this decision.

        :raises UserError: when the approval is not pending or when the
            current user is not the designated approver.
        """
        for approval in self:
            if approval.state != "pending":
                raise UserError(
                    _(
                        "This approval has already been decided and cannot be "
                        "changed."
                    )
                )
            if approval.approver_id != self.env.user and not self.env.user.has_group(
                "ls_document_management.group_ls_document_manager"
            ):
                raise UserError(
                    _(
                        "Only %(approver)s can record a decision on this "
                        "approval.",
                        approver=approval.approver_id.name,
                    )
                )

    def write(self, vals):
        """Enforce the approver identity check on any recorded decision.

        The check is applied in ``write`` and not only in the action methods
        so that it cannot be bypassed by a direct RPC call.
        """
        if vals.get("state") in ("approved", "rejected"):
            self._check_decision_allowed()
        return super().write(vals)

    def action_approve(self):
        """Grant the approval and evaluate the document status."""
        self._check_decision_allowed()
        self.write(
            {
                "state": "approved",
                "decision_date": fields.Datetime.now(),
            }
        )
        for approval in self:
            approval.document_id.message_post(
                body=_(
                    "Approval granted by %(approver)s on version "
                    "%(version)s.",
                    approver=approval.approver_id.name,
                    version=approval.version_id.version_number,
                )
            )
            approval.document_id._evaluate_approvals()
        return True

    def action_reject(self):
        """Refuse the approval and return the document to draft."""
        self._check_decision_allowed()
        self.write(
            {
                "state": "rejected",
                "decision_date": fields.Datetime.now(),
            }
        )
        for approval in self:
            document = approval.document_id
            document.approval_ids.filtered(
                lambda pending: pending.state == "pending"
            ).write({"state": "cancelled"})
            document.state = "draft"
            document.message_post(
                body=_(
                    "Approval refused by %(approver)s on version "
                    "%(version)s. The document returns to draft.",
                    approver=approval.approver_id.name,
                    version=approval.version_id.version_number,
                )
            )
        return True

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_document_approval(self):
        """Forbid deletion of decided approvals."""
        for approval in self:
            if approval.state in ("approved", "rejected"):
                raise UserError(
                    _(
                        "A recorded approval decision cannot be deleted "
                        "(document '%(reference)s').",
                        reference=approval.document_id.reference,
                    )
                )
