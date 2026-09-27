# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Electronic signature log and the mixin used by every signable model.

The signature log is append-only: :meth:`write` and :meth:`unlink` are blocked
for every user, including the system administrator, and each record stores a
SHA-256 hash chained to the previous signature so that a deletion or a direct
database modification becomes detectable.

Regulatory note
---------------
These mechanisms are designed to *support* an organisation implementing
FDA 21 CFR Part 11 and EU GMP Annex 11 expectations. They do not, by
themselves, make a system compliant. Compliance additionally requires
validated implementation, procedures, training and administrative controls
that are outside the scope of any software module.
"""

import hashlib
import inspect
import logging

from odoo import _, api, fields, models
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError

from .ls_validation_constants import PARAM_PASSWORD_REQUIRED

_logger = logging.getLogger(__name__)

GENESIS_HASH = "0" * 64

SIGNATURE_MEANINGS = [
    ("authored", "Authored by"),
    ("reviewed", "Reviewed by"),
    ("approved", "Approved by"),
    ("executed", "Executed by"),
    ("verified", "Verified by"),
    ("rejected", "Rejected by"),
    ("closed", "Closed by"),
]


class LsValidationSignature(models.Model):
    """Append-only electronic signature record."""

    _name = "ls.validation.signature"
    _description = "Validation Electronic Signature"
    _order = "id desc"

    res_model = fields.Char(
        string="Signed Model",
        required=True,
        index=True,
        readonly=True,
    )
    res_id = fields.Many2oneReference(
        string="Signed Record",
        model_field="res_model",
        required=True,
        index=True,
        readonly=True,
    )
    record_label = fields.Char(
        string="Record",
        compute="_compute_record_label",
        help="Human readable name of the signed record, resolved at read time.",
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="Signatory",
        required=True,
        readonly=True,
        ondelete="restrict",
        default=lambda self: self.env.user,
    )
    login_used = fields.Char(required=True,
                             readonly=True,)
    meaning = fields.Selection(
        selection=SIGNATURE_MEANINGS,
        string="Meaning of Signature",
        required=True,
        readonly=True,
    )
    reason = fields.Char(
        string="Reason / Comment",
        readonly=True,
    )
    signed_on = fields.Datetime(required=True,
                                readonly=True,
                                default=fields.Datetime.now,)
    previous_hash = fields.Char(required=True,
                                readonly=True,)
    signature_hash = fields.Char(required=True,
                                 readonly=True,
                                 index=True,)
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 readonly=True,
                                 default=lambda self: self.env.company,)

    _unique_hash = models.Constraint(
        "UNIQUE(signature_hash)",
        "A signature with the same hash already exists.",
    )

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------
    @api.depends("res_model", "res_id")
    def _compute_record_label(self):
        """Resolve the display name of the signed record when still readable."""
        for signature in self:
            label = False
            model = signature.res_model
            if model and model in self.env and signature.res_id:
                record = self.env[model].browse(signature.res_id).exists()
                if record:
                    label = record.display_name
            signature.record_label = label

    @api.depends("meaning", "user_id", "signed_on")
    def _compute_display_name(self):
        """Show meaning, signatory and timestamp in relational widgets."""
        meanings = dict(SIGNATURE_MEANINGS)
        for signature in self:
            signature.display_name = "%s - %s - %s" % (
                meanings.get(signature.meaning, signature.meaning or ""),
                signature.user_id.name or "",
                fields.Datetime.to_string(signature.signed_on) or "",
            )

    # ------------------------------------------------------------------
    # Hash chain
    # ------------------------------------------------------------------
    @api.model
    def _build_hash(self, previous_hash, values):
        """Return the SHA-256 hash of a signature payload.

        :param str previous_hash: hash of the chronologically previous record.
        :param dict values: signature values used to build the payload.
        :return: hexadecimal SHA-256 digest.
        :rtype: str
        """
        payload = "|".join(
            [
                previous_hash,
                str(values.get("res_model") or ""),
                str(values.get("res_id") or ""),
                str(values.get("user_id") or ""),
                str(values.get("login_used") or ""),
                str(values.get("meaning") or ""),
                str(values.get("signed_on") or ""),
                str(values.get("company_id") or ""),
            ]
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @api.model
    def _last_hash(self, company_id):
        """Return the hash of the latest signature of a company."""
        last = self.sudo().search(
            [("company_id", "=", company_id)], order="id desc", limit=1
        )
        return last.signature_hash or GENESIS_HASH

    @api.model_create_multi
    def create(self, vals_list):
        """Chain every new signature to the previous one of the same company."""
        for vals in vals_list:
            vals.setdefault("signed_on", fields.Datetime.now())
            vals.setdefault("user_id", self.env.user.id)
            vals.setdefault("company_id", self.env.company.id)
            vals.setdefault(
                "login_used", self.env["res.users"].browse(vals["user_id"]).login
            )
            previous_hash = self._last_hash(vals["company_id"])
            vals["previous_hash"] = previous_hash
            vals["signature_hash"] = self._build_hash(previous_hash, vals)
        return super().create(vals_list)

    def write(self, vals):
        """Block every modification: the signature log is append-only."""
        raise UserError(
            _("Electronic signatures cannot be modified once recorded.")
        )

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_validation_signature(self):
        """Block every deletion: the signature log is append-only."""
        raise UserError(
            _("Electronic signatures cannot be deleted once recorded.")
        )

    # ------------------------------------------------------------------
    # Integrity verification
    # ------------------------------------------------------------------
    @api.model
    def verify_chain(self, company_id=None):
        """Recompute the hash chain and report the first inconsistency.

        :param int company_id: company to verify, current company when omitted.
        :return: dictionary with the keys ``checked``, ``valid`` and
            ``first_broken_id``.
        :rtype: dict
        """
        company_id = company_id or self.env.company.id
        signatures = self.sudo().search(
            [("company_id", "=", company_id)], order="id asc"
        )
        previous_hash = GENESIS_HASH
        for signature in signatures:
            values = {
                "res_model": signature.res_model,
                "res_id": signature.res_id,
                "user_id": signature.user_id.id,
                "login_used": signature.login_used,
                "meaning": signature.meaning,
                "signed_on": signature.signed_on,
                "company_id": signature.company_id.id,
            }
            expected = self._build_hash(previous_hash, values)
            if (
                signature.previous_hash != previous_hash
                or signature.signature_hash != expected
            ):
                return {
                    "checked": len(signatures),
                    "valid": False,
                    "first_broken_id": signature.id,
                }
            previous_hash = signature.signature_hash
        return {
            "checked": len(signatures),
            "valid": True,
            "first_broken_id": False,
        }


class LsValidationSignatureMixin(models.AbstractModel):
    """Mixin adding electronic signature capability to a model.

    A model inheriting this mixin declares the methods that may be executed
    after a successful signature in :attr:`_ls_signable_callbacks`. Only those
    method names are accepted by the signature wizard, so a crafted context
    cannot trigger an arbitrary method.
    """

    _name = "ls.validation.signature.mixin"
    _description = "Validation Signature Mixin"

    #: Method names that the signature wizard is allowed to call back.
    _ls_signable_callbacks = ()

    signature_ids = fields.Many2many(
        comodel_name="ls.validation.signature",
        string="Electronic Signatures",
        compute="_compute_signature_ids",
    )
    signature_count = fields.Integer(compute="_compute_signature_ids",)

    def _compute_signature_ids(self):
        """Attach the signatures recorded against each record."""
        signature_model = self.env["ls.validation.signature"]
        for record in self:
            signatures = signature_model.search(
                [("res_model", "=", record._name), ("res_id", "=", record.id)]
            )
            record.signature_ids = signatures
            record.signature_count = len(signatures)

    # ------------------------------------------------------------------
    # Credential verification
    # ------------------------------------------------------------------
    @api.model
    def _ls_password_required(self):
        """Return whether the password must be re-entered to sign."""
        value = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(PARAM_PASSWORD_REQUIRED, "1")
        )
        return value not in ("0", "False", "false", "")

    @api.model
    def _ls_verify_credentials(self, login, password):
        """Re-authenticate the current user before recording a signature.

        The signature of ``res.users._check_credentials`` changed between Odoo
        major versions: older versions accept a plain password string while
        recent versions accept a ``credential`` dictionary. The parameter names
        are inspected at runtime so that the module works on the version it is
        deployed on, instead of hard-coding one calling convention.

        :param str login: login typed by the signatory.
        :param str password: password typed by the signatory.
        :raise ValidationError: when the login or the password does not match.
        """
        user = self.env.user
        if login != user.login:
            raise ValidationError(
                _("The login entered does not match the connected user.")
            )
        if not self._ls_password_required():
            return
        if not password:
            raise ValidationError(_("The password is required to sign."))
        method = user._check_credentials
        # The outermost override decides the visible parameter name: Odoo 19
        # base names it ``credential``, while ``auth_totp`` (installed by
        # default) overrides it as ``credentials``. Both take the mapping.
        parameters = inspect.signature(method).parameters
        try:
            if "credential" in parameters or "credentials" in parameters:
                method(
                    {"login": login, "password": password, "type": "password"},
                    {"interactive": True},
                )
            elif "password" in parameters:
                method(password, {"interactive": True})
            else:
                raise UserError(
                    _(
                        "The authentication API of this Odoo build is not "
                        "recognised. Override "
                        "'ls.validation.signature.mixin._ls_verify_credentials' "
                        "for this deployment."
                    )
                )
        except AccessDenied as error:
            raise ValidationError(
                _("Authentication failed. The signature was not recorded.")
            ) from error

    # ------------------------------------------------------------------
    # Signature creation
    # ------------------------------------------------------------------
    def _ls_create_signature(self, meaning, reason=False):
        """Create one signature per record of ``self``.

        :param str meaning: value of the ``meaning`` selection.
        :param str reason: free text comment stored with the signature.
        :return: the created signatures.
        :rtype: recordset of ``ls.validation.signature``
        """
        self.ensure_one()
        signature = self.env["ls.validation.signature"].create(
            {
                "res_model": self._name,
                "res_id": self.id,
                "user_id": self.env.user.id,
                "login_used": self.env.user.login,
                "meaning": meaning,
                "reason": reason,
                "company_id": self._ls_signature_company().id,
            }
        )
        self.invalidate_recordset(["signature_ids", "signature_count"])
        return signature

    def _ls_signature_company(self):
        """Return the company the signature must be attached to."""
        self.ensure_one()
        company = getattr(self, "company_id", False)
        return company or self.env.company

    def _ls_check_group(self, group_xmlid, message):
        """Raise an access error when the user is not member of a group.

        Workflow authority is expressed with groups rather than with access
        rights so that a user may keep write access to a record without being
        entitled to approve it.

        :param str group_xmlid: full external identifier of the group.
        :param str message: message shown when the check fails.
        :raise AccessError: when the current user is not member of the group.
        """
        if not self.env.user.has_group(group_xmlid):
            raise AccessError(message)
        return True

    def _ls_has_signature(self, meaning):
        """Return whether the record already carries a signature of a meaning."""
        self.ensure_one()
        return bool(
            self.env["ls.validation.signature"].search_count(
                [
                    ("res_model", "=", self._name),
                    ("res_id", "=", self.id),
                    ("meaning", "=", meaning),
                ]
            )
        )

    # ------------------------------------------------------------------
    # Wizard entry point
    # ------------------------------------------------------------------
    def _ls_open_sign_wizard(self, meaning, callback, title=None):
        """Return the window action opening the electronic signature wizard.

        :param str meaning: meaning recorded with the signature.
        :param str callback: name of the method executed after signing; it must
            be declared in :attr:`_ls_signable_callbacks`.
        :param str title: optional dialog title.
        :return: an ``ir.actions.act_window`` dictionary.
        :rtype: dict
        """
        self.ensure_one()
        if callback not in self._ls_signable_callbacks:
            raise UserError(
                _("The action '%s' is not a signable action of this model.")
                % callback
            )
        return {
            "type": "ir.actions.act_window",
            "name": title or _("Electronic Signature"),
            "res_model": "ls.validation.sign.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_res_model": self._name,
                "default_res_id": self.id,
                "default_meaning": meaning,
                "default_callback": callback,
            },
        }

    def _ls_execute_signed_callback(self, callback):
        """Execute a whitelisted callback after a successful signature."""
        self.ensure_one()
        if callback not in self._ls_signable_callbacks:
            raise UserError(
                _("The action '%s' is not a signable action of this model.")
                % callback
            )
        return getattr(self, callback)()

    def action_open_signatures(self):
        """Open the signature log filtered on the current record."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Electronic Signatures"),
            "res_model": "ls.validation.signature",
            "view_mode": "list,form",
            "domain": [("res_model", "=", self._name), ("res_id", "=", self.id)],
            "context": {"create": False},
        }
