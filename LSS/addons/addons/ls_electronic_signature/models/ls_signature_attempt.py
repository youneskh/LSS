# Part of the Life Sciences Suite. See LICENSE file for full copyright details.
"""Transaction safeguards for identification codes and passwords.

21 CFR 11.300(d) requires "use of transaction safeguards to prevent
unauthorized use of passwords and/or identification codes, and to detect and
report in an immediate and urgent manner any attempts at their unauthorized use
to the system security unit".

This model records every attempt to execute a signature, successful or not. A
failed attempt normally ends in an exception, which would roll back the
transaction and destroy the very evidence that must be kept. Attempts are
therefore written through an independent cursor that is committed before the
exception is raised.
"""

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

#: Default number of consecutive failures before a signer is locked out.
DEFAULT_MAX_FAILURES = 3

#: Default lockout duration in minutes.
DEFAULT_LOCKOUT_MINUTES = 15


class LsSignatureAttempt(models.Model):
    """One attempt to execute an electronic signature."""

    _name = "ls.signature.attempt"
    _description = "Electronic Signature Attempt"
    _order = "attempted_at desc, id desc"
    _rec_name = "login_attempted"

    attempted_at = fields.Datetime(
        required=True,
        readonly=True,
        index=True,
        default=fields.Datetime.now,
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="Session User",
        readonly=True,
        index=True,
        ondelete="restrict",
        help="The authenticated user whose session issued the attempt.",
    )
    login_attempted = fields.Char(
        required=True,
        readonly=True,
        index=True,
        help="The identification code submitted in the signature dialog.",
    )
    result = fields.Selection(
        selection=[
            ("success", "Signature executed"),
            ("invalid_password", "Incorrect password"),
            ("identity_mismatch", "Identification code does not match the session"),
            ("not_authorised", "Signer not authorised for this meaning or policy"),
            ("locked_out", "Blocked by lockout"),
            ("reason_missing", "Mandatory reason not supplied"),
            ("policy_violation", "Policy precondition not met"),
            ("system_error", "System error during verification"),
        ],
        required=True,
        readonly=True,
        index=True,
    )
    res_model = fields.Char(readonly=True, index=True)
    res_id = fields.Integer(readonly=True)
    meaning_id = fields.Many2one(
        comodel_name="ls.signature.meaning",
        readonly=True,
        ondelete="restrict",
    )
    log_id = fields.Many2one(
        comodel_name="ls.signature.log",
        string="Resulting Signature",
        readonly=True,
        ondelete="restrict",
    )
    detail = fields.Text(readonly=True)
    ip_address = fields.Char(readonly=True)
    user_agent = fields.Char(readonly=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        readonly=True,
        index=True,
        default=lambda self: self.env.company,
        ondelete="restrict",
    )

    def write(self, vals):
        """Refuse every modification.

        :raises UserError: Always.
        """
        raise UserError(
            _("Signature attempt records are a security log and cannot be modified.")
        )

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_signature_attempt(self):
        """Refuse every deletion.

        :raises UserError: Always.
        """
        raise UserError(
            _("Signature attempt records are a security log and cannot be deleted.")
        )

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------
    @api.model
    def _int_parameter(self, key, default):
        """Return an integer system parameter, falling back to ``default``."""
        raw = self.env["ir.config_parameter"].sudo().get_param(key)
        try:
            value = int(raw)
        except (TypeError, ValueError):
            return default
        return value if value > 0 else default

    @api.model
    def _max_failures(self):
        """Return the number of consecutive failures that triggers lockout."""
        return self._int_parameter(
            "ls_electronic_signature.max_failed_attempts", DEFAULT_MAX_FAILURES
        )

    @api.model
    def _lockout_minutes(self):
        """Return the lockout duration in minutes."""
        return self._int_parameter(
            "ls_electronic_signature.lockout_minutes", DEFAULT_LOCKOUT_MINUTES
        )

    @api.model
    def _use_isolated_cursor(self):
        """Return whether attempts are written through an independent cursor.

        The isolated cursor guarantees that a failed attempt survives the
        rollback caused by the exception raised to the signer. It is disabled
        inside the automated test suite, where the test transaction is rolled
        back deliberately and a second connection would observe a database that
        does not yet contain the fixtures.
        """
        value = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("ls_electronic_signature.attempt_isolated_cursor", "1")
        )
        return str(value).strip() not in ("0", "false", "False")

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------
    @api.model
    def record(self, values, notify=False):
        """Record one attempt and optionally raise the security alert.

        :param dict values: Field values for the attempt.
        :param bool notify: Whether to notify the security group. Set for
            results that indicate possible unauthorised use.
        :returns: The created ``ls.signature.attempt`` recordset when written
            on the current cursor, otherwise an empty recordset because the
            row belongs to another transaction.
        """
        values = dict(values)
        values.setdefault("attempted_at", fields.Datetime.now())
        values.setdefault("company_id", self.env.company.id)

        if not self._use_isolated_cursor():
            attempt = self.sudo().create(values)
            if notify:
                attempt._notify_security_unit()
            return attempt

        with self.env.registry.cursor() as cursor:
            isolated_env = api.Environment(cursor, self.env.uid, {})
            attempt = isolated_env["ls.signature.attempt"].sudo().create(values)
            if notify:
                attempt._notify_security_unit()
            cursor.commit()
        return self.browse()

    def _notify_security_unit(self):
        """Send the immediate notification required by 21 CFR 11.300(d)."""
        template = self.env.ref(
            "ls_electronic_signature.mail_template_signature_alert",
            raise_if_not_found=False,
        )
        recipients = self._security_unit_recipients()
        if not template or not recipients:
            _logger.warning(
                "Unauthorised electronic signature attempt by login '%s' "
                "(result: %s) could not be notified: %s.",
                self.login_attempted,
                self.result,
                "no template" if not template else "no recipient",
            )
            return False
        for attempt in self:
            template.sudo().with_context(
                security_recipients=recipients
            ).send_mail(attempt.id, force_send=True)
        return True

    @api.model
    def _security_unit_recipients(self):
        """Return the comma separated e-mail list of the security unit."""
        group = self.env.ref(
            "ls_electronic_signature.group_ls_signature_security",
            raise_if_not_found=False,
        )
        if not group:
            return ""
        addresses = [
            user.email
            for user in group.sudo().all_user_ids
            if user.email and user.active
        ]
        return ",".join(sorted(set(addresses)))

    # ------------------------------------------------------------------
    # Lockout
    # ------------------------------------------------------------------
    @api.model
    def is_locked_out(self, login):
        """Return whether ``login`` is currently blocked from signing.

        A login is blocked when the number of consecutive failures since the
        last success reaches the configured threshold and the most recent
        failure is inside the lockout window.

        :param str login: The identification code being checked.
        :returns bool:
        """
        if not login:
            return False
        threshold = self._max_failures()
        window_start = fields.Datetime.subtract(
            fields.Datetime.now(), minutes=self._lockout_minutes()
        )
        recent = self.sudo().search(
            [
                ("login_attempted", "=", login),
                ("attempted_at", ">=", window_start),
            ],
            # ``id`` breaks ties between attempts recorded within the same
            # second, so that the most recent attempt is always first.
            order="attempted_at desc, id desc",
            limit=threshold,
        )
        if len(recent) < threshold:
            return False
        return all(attempt.result != "success" for attempt in recent)
