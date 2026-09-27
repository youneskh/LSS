# Part of the Life Sciences Suite. See LICENSE file for full copyright details.
"""Tracking of continuous periods of controlled system access.

21 CFR 11.200(a)(1)(i) permits subsequent signings within "a single, continuous
period of controlled system access" to use only one signature component,
provided the first signing of that period used all components. Paragraph (ii)
requires all components again for any signing outside such a period.

Deciding whether a period is still continuous requires the system to know which
browser session executed the previous signature and when. This model holds that
state. It never stores the raw Odoo session identifier: only a keyed digest of
it, so that a reader of this table cannot impersonate a session.
"""

import hashlib
import logging

from odoo import api, fields, models
from odoo.tools import config

_logger = logging.getLogger(__name__)

#: Default idle timeout, in minutes, after which a period of controlled system
#: access is no longer considered continuous.
DEFAULT_IDLE_TIMEOUT_MINUTES = 15


class LsSignatureSession(models.Model):
    """A continuous period of controlled system access used for signing."""

    _name = "ls.signature.session"
    _description = "Electronic Signature Session"
    _order = "last_signed_at desc, id desc"
    _rec_name = "display_reference"

    user_id = fields.Many2one(
        comodel_name="res.users",
        required=True,
        index=True,
        ondelete="restrict",
    )
    token_hash = fields.Char(
        required=True,
        index=True,
        help="Keyed SHA-256 digest of the web session identifier. The raw "
             "identifier is never stored.",
    )
    display_reference = fields.Char(
        compute="_compute_display_reference",
        string="Reference",
    )
    first_signed_at = fields.Datetime(required=True, readonly=True)
    last_signed_at = fields.Datetime(required=True, readonly=True)
    signature_count = fields.Integer(default=0, readonly=True)
    closed = fields.Boolean(default=False, index=True)
    close_reason = fields.Selection(
        selection=[
            ("idle", "Idle timeout"),
            ("manual", "Closed by administrator"),
            ("logout", "Session ended"),
        ],
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
        ondelete="restrict",
    )

    _user_token_uniq = models.Constraint(
        "UNIQUE(user_id, token_hash)",
        "A signing session is identified once per user and web session.",
    )

    @api.depends("user_id", "first_signed_at")
    def _compute_display_reference(self):
        """Build a human readable reference that leaks no session material."""
        for session in self:
            session.display_reference = "%s / %s" % (
                session.user_id.login or "",
                fields.Datetime.to_string(session.first_signed_at) or "",
            )

    @api.model
    def _idle_timeout_minutes(self):
        """Return the configured idle timeout in minutes."""
        raw = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("ls_electronic_signature.session_idle_minutes")
        )
        try:
            value = int(raw)
        except (TypeError, ValueError):
            return DEFAULT_IDLE_TIMEOUT_MINUTES
        return value if value > 0 else DEFAULT_IDLE_TIMEOUT_MINUTES

    @api.model
    def _hash_session_token(self, raw_token):
        """Return the keyed digest of ``raw_token``.

        The database secret is used as the key so that the digest cannot be
        precomputed by an attacker holding only a copy of this table.

        :param str raw_token: The web session identifier.
        :returns str: A 64 character lowercase hexadecimal digest.
        """
        secret = (
            self.env["ir.config_parameter"].sudo().get_param("database.secret")
            or config.get("admin_passwd")
            or ""
        )
        material = "%s|%s" % (secret, raw_token)
        return hashlib.sha256(material.encode("utf-8")).hexdigest()

    @api.model
    def _current_token_hash(self):
        """Return the digest of the caller's web session, or ``False``.

        ``False`` is returned when there is no web session, for example during
        a scheduled action or an RPC call. In that situation no period of
        controlled system access can be demonstrated, so the caller must
        require all signature components.

        :returns: ``str`` or ``False``.
        """
        try:
            from odoo.http import request
        except ImportError:  # pragma: no cover - defensive, odoo.http is core
            return False
        if not request:
            return False
        session = getattr(request, "session", None)
        raw_token = getattr(session, "sid", None) if session else None
        if not raw_token:
            return False
        return self._hash_session_token(raw_token)

    @api.model
    def is_continuous(self, user, token_hash):
        """Return whether ``user`` is inside a continuous signing period.

        :param user: A single ``res.users`` recordset.
        :param token_hash: Digest returned by :meth:`_current_token_hash`, or
            a falsy value when no web session exists.
        :returns bool: ``True`` only when a prior signature exists in the same
            web session and the idle timeout has not elapsed.
        """
        if not token_hash:
            return False
        session = self.sudo().search(
            [
                ("user_id", "=", user.id),
                ("token_hash", "=", token_hash),
                ("closed", "=", False),
            ],
            limit=1,
        )
        if not session or not session.signature_count:
            return False
        return session._is_within_idle_window()

    def _is_within_idle_window(self):
        """Return whether this session's last signature is recent enough."""
        self.ensure_one()
        timeout = self._idle_timeout_minutes()
        elapsed = fields.Datetime.now() - self.last_signed_at
        return elapsed.total_seconds() <= timeout * 60

    @api.model
    def register_signature(self, user, token_hash):
        """Record that ``user`` executed a signature in the given session.

        :param user: A single ``res.users`` recordset.
        :param token_hash: Digest returned by :meth:`_current_token_hash`.
        :returns: The ``ls.signature.session`` recordset, empty when no web
            session exists.
        """
        if not token_hash:
            return self.browse()
        now = fields.Datetime.now()
        session = self.sudo().search(
            [
                ("user_id", "=", user.id),
                ("token_hash", "=", token_hash),
            ],
            limit=1,
        )
        if session:
            session.write(
                {
                    "last_signed_at": now,
                    "signature_count": session.signature_count + 1,
                    "closed": False,
                    "close_reason": False,
                }
            )
            return session
        return self.sudo().create(
            {
                "user_id": user.id,
                "token_hash": token_hash,
                "first_signed_at": now,
                "last_signed_at": now,
                "signature_count": 1,
                "company_id": user.company_id.id or self.env.company.id,
            }
        )

    @api.model
    def _cron_close_idle_sessions(self):
        """Close signing sessions whose idle timeout has elapsed.

        Closing a session forces the next signature by that user to present all
        signature components, as required by 21 CFR 11.200(a)(1)(ii).
        """
        timeout = self._idle_timeout_minutes()
        cutoff = fields.Datetime.subtract(fields.Datetime.now(), minutes=timeout)
        stale = self.sudo().search(
            [("closed", "=", False), ("last_signed_at", "<", cutoff)]
        )
        if stale:
            stale.write({"closed": True, "close_reason": "idle"})
            _logger.info("Closed %d idle electronic signature session(s).", len(stale))
        return len(stale)

    def action_close(self):
        """Close the selected sessions from the user interface."""
        self.write({"closed": True, "close_reason": "manual"})
        return True
