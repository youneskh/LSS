# Part of the Life Sciences Suite. See LICENSE file for full copyright details.
"""Settings exposed for the electronic signature module."""

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """Electronic signature settings, stored as system parameters."""

    _inherit = "res.config.settings"

    ls_signature_session_idle_minutes = fields.Integer(
        string="Continuous Session Timeout (minutes)",
        config_parameter="ls_electronic_signature.session_idle_minutes",
        default=15,
        help="Idle period after which a period of controlled system access is "
             "no longer continuous, so that the next signature must present "
             "all signature components. See 21 CFR 11.200(a)(1).",
    )
    ls_signature_max_failed_attempts = fields.Integer(
        string="Failures Before Lockout",
        config_parameter="ls_electronic_signature.max_failed_attempts",
        default=3,
        help="Number of consecutive failed signature attempts that blocks "
             "further attempts by that identification code.",
    )
    ls_signature_lockout_minutes = fields.Integer(
        string="Lockout Duration (minutes)",
        config_parameter="ls_electronic_signature.lockout_minutes",
        default=15,
    )
    ls_signature_credential_api_mode = fields.Selection(
        selection=[
            ("auto", "Detect automatically"),
            ("credential", "Credential mapping"),
            ("password", "Password string"),
        ],
        string="Password Verification API",
        config_parameter="ls_electronic_signature.credential_api_mode",
        default="auto",
        help="Calling convention used to verify a password against the Odoo "
             "user account. Leave on automatic detection unless the "
             "qualification test OQ-CRED-001 has shown that a specific "
             "convention must be pinned.",
    )
    ls_signature_binding_statement = fields.Char(
        string="Binding Statement",
        config_parameter="ls_electronic_signature.binding_statement",
        help="Statement displayed above the credential fields in the "
             "signature dialog. 21 CFR 11.100(c) requires the organisation to "
             "certify to the agency that its electronic signatures are the "
             "legally binding equivalent of handwritten signatures; showing "
             "the statement at the point of signing records that the signer "
             "was informed.",
    )
    ls_signature_db_trigger_state = fields.Char(
        string="Database Immutability Trigger",
        compute="_compute_ls_signature_db_trigger_state",
        help="Whether the PostgreSQL trigger refusing UPDATE and DELETE on the "
             "signature log is installed on this database.",
    )

    @api.depends_context("uid")
    def _compute_ls_signature_db_trigger_state(self):
        """Report whether database level immutability is active."""
        state = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("ls_electronic_signature.db_immutability_trigger", "unknown")
        )
        for setting in self:
            setting.ls_signature_db_trigger_state = state
