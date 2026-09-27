# Part of the Life Sciences Suite. See LICENSE file for full copyright details.
"""Routing of signature requests to the persons expected to sign."""

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class LsSignatureRequest(models.Model):
    """A request asking one or more persons to execute a signature.

    A request never becomes a signature by itself. It is a work item that
    routes, reminds and expires. The signature is only created when a signer
    presents their credentials in the signature wizard, which is what
    21 CFR 11.200(a)(2) means by an electronic signature being used only by its
    genuine owner.
    """

    _name = "ls.signature.request"
    _description = "Electronic Signature Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "deadline asc, id desc"

    name = fields.Char(required=True, readonly=True, default="/", copy=False)
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("pending", "Awaiting Signature"),
            ("signed", "Signed"),
            ("declined", "Declined"),
            ("expired", "Expired"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        required=True,
        tracking=True,
        index=True,
    )
    res_model = fields.Char(string="Record Model", required=True, index=True)
    res_id = fields.Integer(string="Record ID", required=True, index=True)
    res_name = fields.Char(string="Record", readonly=True)
    meaning_id = fields.Many2one(
        comodel_name="ls.signature.meaning",
        required=True,
        ondelete="restrict",
        tracking=True,
    )
    policy_id = fields.Many2one(
        comodel_name="ls.signature.policy",
        ondelete="restrict",
    )
    requested_by_id = fields.Many2one(
        comodel_name="res.users",
        required=True,
        default=lambda self: self.env.user,
        ondelete="restrict",
    )
    signer_ids = fields.Many2many(
        comodel_name="res.users",
        relation="ls_signature_request_user_rel",
        column1="request_id",
        column2="user_id",
        string="Expected Signers",
        required=True,
    )
    deadline = fields.Datetime(tracking=True)
    instructions = fields.Text()
    log_id = fields.Many2one(
        comodel_name="ls.signature.log",
        string="Signature",
        readonly=True,
        ondelete="restrict",
    )
    decline_reason = fields.Text(readonly=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
        ondelete="restrict",
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Assign the human readable reference and resolve the record label."""
        for vals in vals_list:
            if vals.get("name", "/") == "/":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("ls.signature.request")
                    or "/"
                )
            if not vals.get("res_name") and vals.get("res_model") and vals.get("res_id"):
                model = self.env.get(vals["res_model"])
                if model is not None:
                    record = model.browse(vals["res_id"]).exists()
                    vals["res_name"] = record.display_name if record else False
        return super().create(vals_list)

    @api.constrains("res_model")
    def _check_res_model(self):
        """Refuse requests targeting a model that cannot be signed."""
        for request in self:
            model = self.env.get(request.res_model)
            if model is None or not getattr(model, "_ls_signature_enabled", False):
                raise ValidationError(
                    _(
                        "Model '%(model)s' cannot carry electronic signatures.",
                        model=request.res_model,
                    )
                )

    def action_send(self):
        """Move the request to pending and notify the expected signers."""
        for request in self:
            if request.state != "draft":
                raise UserError(
                    _(
                        "Request %(name)s is not in draft and cannot be sent.",
                        name=request.name,
                    )
                )
            request.state = "pending"
            request.message_subscribe(
                partner_ids=request.signer_ids.partner_id.ids
            )
            template = self.env.ref(
                "ls_electronic_signature.mail_template_signature_request",
                raise_if_not_found=False,
            )
            if template:
                template.sudo().send_mail(request.id, force_send=False)
        return True

    def action_open_wizard(self):
        """Open the signature wizard pre-filled from this request."""
        self.ensure_one()
        if self.state != "pending":
            raise UserError(
                _(
                    "Request %(name)s is not awaiting a signature.",
                    name=self.name,
                )
            )
        if self.env.user not in self.signer_ids:
            raise UserError(
                _("You are not among the expected signers of this request.")
            )
        return {
            "type": "ir.actions.act_window",
            "res_model": "ls.signature.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_res_model": self.res_model,
                "default_res_id": self.res_id,
                "default_meaning_id": self.meaning_id.id,
                "default_policy_id": self.policy_id.id,
                "default_request_id": self.id,
            },
        }

    def action_decline(self):
        """Open the decline wizard for the selected request."""
        self.ensure_one()
        if self.state != "pending":
            raise UserError(
                _("Only a pending request can be declined.")
            )
        return {
            "type": "ir.actions.act_window",
            "res_model": "ls.signature.decline.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_request_id": self.id},
        }

    def action_cancel(self):
        """Cancel the selected requests."""
        for request in self:
            if request.state in ("signed", "cancelled"):
                raise UserError(
                    _(
                        "Request %(name)s is %(state)s and cannot be "
                        "cancelled.",
                        name=request.name,
                        state=request.state,
                    )
                )
            request.state = "cancelled"
        return True

    def _mark_signed(self, signature):
        """Close the request once its signature has been executed.

        :param signature: The created ``ls.signature.log`` recordset.
        """
        self.ensure_one()
        self.write({"state": "signed", "log_id": signature.id})
        self.message_post(
            body=_(
                "Signed by %(signer)s with meaning %(meaning)s.",
                signer=signature.signer_name,
                meaning=signature.meaning_name,
            )
        )
        return True

    @api.model
    def _cron_expire_requests(self):
        """Move overdue pending requests to the expired state."""
        overdue = self.sudo().search(
            [
                ("state", "=", "pending"),
                ("deadline", "!=", False),
                ("deadline", "<", fields.Datetime.now()),
            ]
        )
        if overdue:
            overdue.write({"state": "expired"})
            _logger.info("Expired %d electronic signature request(s).", len(overdue))
        return len(overdue)

    def action_open_record(self):
        """Open the record the signature is requested on."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": self.res_model,
            "res_id": self.res_id,
            "view_mode": "form",
            "target": "current",
        }
