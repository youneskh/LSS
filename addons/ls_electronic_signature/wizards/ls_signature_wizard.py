# Part of the Life Sciences Suite. See LICENSE file for full copyright details.
"""The dialog in which a signer executes an electronic signature.

The wizard is the only supported path to creating a signature. It performs, in
this order and without exception:

1. lockout check, per 21 CFR 11.300(d);
2. identity check, so that a signature is executed by the account that is
   logged in, per 21 CFR 11.200(a)(2);
3. component check, deciding whether all signature components are required or
   whether the session qualifies for the reduced set permitted by
   21 CFR 11.200(a)(1)(i);
4. password verification;
5. authorisation check against the meaning and the policy;
6. mandatory reason check;
7. creation of the immutable signature record.

Every outcome, successful or not, produces a ``ls.signature.attempt`` row.
"""

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..tools import credentials, hashing

_logger = logging.getLogger(__name__)

#: Statement shown when the organisation has not configured its own.
DEFAULT_BINDING_STATEMENT = (
    "By entering my identification code and password below I execute an "
    "electronic signature which my organisation has certified to be the "
    "legally binding equivalent of my handwritten signature."
)


class LsSignatureWizard(models.TransientModel):
    """Collects credentials and meaning, then records a signature."""

    _name = "ls.signature.wizard"
    _description = "Execute Electronic Signature"

    res_model = fields.Char(required=True, readonly=True)
    res_id = fields.Integer(required=True, readonly=True)
    res_name = fields.Char(string="Record", compute="_compute_res_name", readonly=True)
    policy_id = fields.Many2one(
        comodel_name="ls.signature.policy",
        readonly=True,
    )
    request_id = fields.Many2one(
        comodel_name="ls.signature.request",
        readonly=True,
    )
    meaning_id = fields.Many2one(comodel_name="ls.signature.meaning", required=True,
                                 domain="[('id', 'in', available_meaning_ids)]",
                                 )
    available_meaning_ids = fields.Many2many(
        comodel_name="ls.signature.meaning",
        compute="_compute_available_meaning_ids",
    )
    meaning_description = fields.Text(
        related="meaning_id.description",
        readonly=True,
    )
    reason_required = fields.Boolean(
        related="meaning_id.require_reason",
        readonly=True,
    )
    reason = fields.Text()
    login = fields.Char(
        string="Identification Code",
        required=True,
        default=lambda self: self.env.user.login,
    )
    # The password is never stored. ``password`` is a non-stored field whose
    # inverse verifies the submitted value against the credential of the
    # current user as soon as the dialog is saved, and keeps only the outcome
    # of that verification. The outcome fields are restricted to the settings
    # group so that they cannot be used by the signer as a password oracle;
    # the outcome is disclosed and logged only through ``action_sign``.
    password = fields.Char(
        compute="_compute_password",
        inverse="_inverse_password",
        store=False,
    )
    password_check = fields.Selection(
        selection=[
            ("ok", "Verified"),
            ("bad", "Rejected"),
            ("error", "Verification error"),
        ],
        readonly=True,
        copy=False,
        groups="base.group_system",
    )
    password_check_uid = fields.Many2one(
        comodel_name="res.users",
        readonly=True,
        copy=False,
        groups="base.group_system",
    )
    password_check_error = fields.Char(
        readonly=True,
        copy=False,
        groups="base.group_system",
    )
    require_password = fields.Boolean(
        compute="_compute_require_password",
        help="False only when a signature was already executed with all "
             "components during the current continuous period of controlled "
             "system access and the applicable policy permits the reduced set.",
    )
    binding_statement = fields.Text(
        compute="_compute_binding_statement",
        readonly=True,
    )
    consent = fields.Boolean(
        string="I acknowledge the statement above",
        default=False,
    )

    # ------------------------------------------------------------------
    # Computes
    # ------------------------------------------------------------------
    @api.depends("res_model", "res_id")
    def _compute_res_name(self):
        """Resolve the display name of the record being signed."""
        for wizard in self:
            record = wizard._target_record(raise_if_missing=False)
            wizard.res_name = record.display_name if record else False

    @api.depends("res_model", "res_id", "policy_id")
    def _compute_available_meaning_ids(self):
        """Restrict the selectable meanings to those the signer may apply."""
        meaning_model = self.env["ls.signature.meaning"]
        for wizard in self:
            if wizard.policy_id:
                candidates = wizard.policy_id.meaning_id
            else:
                candidates = meaning_model.search(
                    [("company_id", "=", self.env.company.id)]
                )
            wizard.available_meaning_ids = candidates.is_available_to(self.env.user)

    def _compute_password(self):
        """Never return a password: the submitted value is not kept."""
        for wizard in self:
            wizard.password = False

    def _inverse_password(self):
        """Verify the submitted password and keep only the outcome.

        The verification is skipped while the identification code is locked
        out, so a locked-out signer cannot keep testing passwords.
        """
        attempt_model = self.env["ls.signature.attempt"]
        user = self.env.user
        for wizard in self:
            submitted = wizard.password
            values = {
                "password_check": False,
                "password_check_uid": False,
                "password_check_error": False,
            }
            if submitted and not attempt_model.is_locked_out(wizard.login):
                try:
                    verified = credentials.verify_password(user, submitted)
                    values["password_check"] = "ok" if verified else "bad"
                except credentials.CredentialApiError as error:
                    values["password_check"] = "error"
                    values["password_check_error"] = str(error)
                values["password_check_uid"] = user.id
            wizard.sudo().write(values)

    @api.depends("policy_id")
    def _compute_require_password(self):
        """Decide whether all signature components must be presented.

        21 CFR 11.200(a)(1)(i) permits subsequent signings inside a single
        continuous period of controlled system access to present only one
        component. The module treats the identification code as the component
        always presented and the password as the one that may be omitted, and
        only when the applicable policy allows it.
        """
        session_model = self.env["ls.signature.session"]
        token_hash = session_model._current_token_hash()
        continuous = session_model.is_continuous(self.env.user, token_hash)
        for wizard in self:
            policy_allows = bool(wizard.policy_id) and not wizard.policy_id.require_full_credentials
            wizard.require_password = not (continuous and policy_allows)

    @api.depends_context("uid")
    def _compute_binding_statement(self):
        """Return the configured binding statement, or the default one."""
        configured = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("ls_electronic_signature.binding_statement")
        )
        for wizard in self:
            wizard.binding_statement = configured or _(DEFAULT_BINDING_STATEMENT)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _target_record(self, raise_if_missing=True):
        """Return the record being signed.

        :param bool raise_if_missing: Raise instead of returning an empty
            recordset when the record cannot be resolved.
        :returns: A recordset of ``res_model``.
        :raises UserError: When the record is missing and ``raise_if_missing``.
        """
        self.ensure_one()
        model = self.env.get(self.res_model) if self.res_model else None
        record = model.browse(self.res_id).exists() if model is not None else None
        if not record:
            if raise_if_missing:
                raise UserError(
                    _(
                        "The record %(model)s,%(res_id)s to be signed does not "
                        "exist.",
                        model=self.res_model,
                        res_id=self.res_id,
                    )
                )
            return self.env[self.res_model].browse() if model is not None else None
        if not getattr(model, "_ls_signature_enabled", False):
            raise UserError(
                _(
                    "Model '%(model)s' cannot carry electronic signatures.",
                    model=self.res_model,
                )
            )
        return record

    def _request_context(self):
        """Return the network context of the current request.

        :returns tuple: ``(ip_address, user_agent)``, each possibly ``False``.
        """
        try:
            from odoo.http import request
        except ImportError:  # pragma: no cover - defensive, odoo.http is core
            return False, False
        if not request or not getattr(request, "httprequest", None):
            return False, False
        http_request = request.httprequest
        return (
            http_request.remote_addr or False,
            (http_request.user_agent.string if http_request.user_agent else False),
        )

    def _fail(self, result, message, detail=None):
        """Record a failed attempt and raise the message shown to the signer.

        :param str result: A value of ``ls.signature.attempt.result``.
        :param str message: The message shown to the signer.
        :param str detail: Optional technical detail kept in the attempt log.
        :raises UserError: Always.
        """
        self.ensure_one()
        ip_address, user_agent = self._request_context()
        notify = result in (
            "invalid_password",
            "identity_mismatch",
            "not_authorised",
            "locked_out",
        )
        self.env["ls.signature.attempt"].record(
            {
                "user_id": self.env.uid,
                "login_attempted": self.login or "",
                "result": result,
                "res_model": self.res_model,
                "res_id": self.res_id,
                "meaning_id": self.meaning_id.id or False,
                "detail": detail or message,
                "ip_address": ip_address,
                "user_agent": user_agent,
            },
            notify=notify,
        )
        raise UserError(message)

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------
    def action_sign(self):
        """Verify the signer and record the signature.

        :returns dict: An action closing the dialog and reloading the view.
        :raises UserError: On any verification failure.
        """
        self.ensure_one()
        record = self._target_record()
        user = self.env.user
        attempt_model = self.env["ls.signature.attempt"]
        session_model = self.env["ls.signature.session"]

        if not self.consent:
            self._fail(
                "policy_violation",
                _("Acknowledge the binding statement before signing."),
            )

        if attempt_model.is_locked_out(self.login):
            self._fail(
                "locked_out",
                _(
                    "Signing is temporarily blocked for this identification "
                    "code after repeated failures. Contact the system security "
                    "unit."
                ),
            )

        if (self.login or "").strip() != user.login:
            self._fail(
                "identity_mismatch",
                _(
                    "The identification code does not match the account that "
                    "is logged in. A signature may only be executed by its "
                    "genuine owner."
                ),
                detail="session login=%s, submitted login=%s" % (user.login, self.login),
            )

        token_hash = session_model._current_token_hash()
        if self.require_password:
            check = self.sudo()
            if not check.password_check or check.password_check_uid != user:
                self._fail("invalid_password", _("The password is required."))
            if check.password_check == "error":
                self._fail(
                    "system_error",
                    check.password_check_error,
                    detail=check.password_check_error,
                )
            if check.password_check != "ok":
                self._fail("invalid_password", _("The password is incorrect."))
            authentication_method = "full"
        else:
            if not session_model.is_continuous(user, token_hash):
                self._fail(
                    "policy_violation",
                    _(
                        "The continuous period of controlled system access has "
                        "ended. Enter your password to sign."
                    ),
                )
            authentication_method = "single"

        if not (self.meaning_id & self.available_meaning_ids):
            self._fail(
                "not_authorised",
                _(
                    "You are not authorised to sign with the meaning "
                    "'%(meaning)s'.",
                    meaning=self.meaning_id.name,
                ),
            )

        if self.policy_id and self.policy_id.signer_group_ids:
            if not (user.all_group_ids & self.policy_id.signer_group_ids):
                self._fail(
                    "not_authorised",
                    _(
                        "You are not among the authorised signers of policy "
                        "'%(policy)s'.",
                        policy=self.policy_id.name,
                    ),
                )

        if self.meaning_id.require_reason and not (self.reason or "").strip():
            self._fail(
                "reason_missing",
                _(
                    "The meaning '%(meaning)s' requires a reason to be "
                    "recorded.",
                    meaning=self.meaning_id.name,
                ),
            )

        # The session is registered before the signature is created so that the
        # session reference can be inserted with the row. A signature record is
        # append only and must never be completed by a later UPDATE. Should the
        # insertion fail, the whole transaction rolls back and the session
        # counter rolls back with it.
        session = session_model.register_signature(user, token_hash)
        signature = self._create_signature(
            record, authentication_method, session
        )

        ip_address, user_agent = self._request_context()
        attempt_model.record(
            {
                "user_id": user.id,
                "login_attempted": self.login,
                "result": "success",
                "res_model": self.res_model,
                "res_id": self.res_id,
                "meaning_id": self.meaning_id.id,
                "log_id": signature.id,
                "ip_address": ip_address,
                "user_agent": user_agent,
            }
        )

        if self.request_id:
            self.request_id._mark_signed(signature)

        # The verification outcome is consumed by this signature.
        self.sudo().write({"password_check": False, "password_check_uid": False})
        return {"type": "ir.actions.act_window_close"}

    def _create_signature(self, record, authentication_method, session):
        """Build and insert the immutable signature record.

        :param record: The record being signed.
        :param str authentication_method: ``full`` or ``single``.
        :param session: The ``ls.signature.session`` recordset, possibly empty.
        :returns: The created ``ls.signature.log`` recordset.
        """
        self.ensure_one()
        user = self.env.user
        signed_at = fields.Datetime.now()
        payload = record._ls_signature_payload(
            meaning=self.meaning_id,
            signed_at=signed_at,
            signer=user,
        )
        payload_bytes = hashing.canonical_dumps(payload)
        payload_json = payload_bytes.decode("utf-8")
        ip_address, user_agent = self._request_context()
        model_record = self.env["ir.model"]._get(self.res_model)
        return self.env["ls.signature.log"].create(
            {
                "company_id": self.env.company.id,
                "user_id": user.id,
                "signer_name": user.name,
                "signer_login": user.login,
                "signed_at": signed_at,
                "meaning_id": self.meaning_id.id,
                "meaning_code": self.meaning_id.code,
                "meaning_name": self.meaning_id.name,
                "res_model": self.res_model,
                "res_model_name": model_record.name or self.res_model,
                "res_id": self.res_id,
                "res_name": record.display_name,
                "payload_json": payload_json,
                "record_hash": hashing.sha256_hex(payload_bytes),
                "reason": (self.reason or "").strip() or False,
                "policy_id": self.policy_id.id or False,
                "request_id": self.request_id.id or False,
                "authentication_method": authentication_method,
                "session_id": session.id if session else False,
                "ip_address": ip_address,
                "user_agent": user_agent,
            }
        )


class LsSignatureDeclineWizard(models.TransientModel):
    """Records the refusal of a signature request with its justification."""

    _name = "ls.signature.decline.wizard"
    _description = "Decline Electronic Signature Request"

    request_id = fields.Many2one(
        comodel_name="ls.signature.request",
        required=True,
        readonly=True,
    )
    reason = fields.Text(string="Reason for Declining", required=True)

    @api.constrains("reason")
    def _check_reason(self):
        """Refuse an empty justification."""
        for wizard in self:
            if not (wizard.reason or "").strip():
                raise ValidationError(
                    _("A reason must be recorded when declining a request.")
                )

    def action_decline(self):
        """Move the request to declined and record the justification."""
        self.ensure_one()
        if self.env.user not in self.request_id.signer_ids:
            raise UserError(
                _("You are not among the expected signers of this request.")
            )
        self.request_id.write(
            {"state": "declined", "decline_reason": self.reason.strip()}
        )
        self.request_id.message_post(
            body=_(
                "Declined by %(user)s: %(reason)s",
                user=self.env.user.name,
                reason=self.reason.strip(),
            )
        )
        return {"type": "ir.actions.act_window_close"}
