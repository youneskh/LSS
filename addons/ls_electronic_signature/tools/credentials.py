# Part of the Life Sciences Suite. See LICENSE file for full copyright details.
"""Password verification adapter for the electronic signature wizard.

Why this module exists
----------------------
21 CFR 11.200(a)(1) requires a non-biometric electronic signature to employ at
least two distinct identification components, "such as an identification code
and password". Executing a signature therefore requires re-verifying the
signer's password at the moment of signing. Odoo exposes password verification
through ``res.users._check_credentials``, which is a *private* method: its
signature is not covered by the public API stability guarantees and it has
changed across supported Odoo versions.

**This information could not be verified from official documentation:** the
exact parameter list of ``res.users._check_credentials`` in Odoo 19.0
Community. Two signatures are known to exist across the Odoo 14.0 to 18.0
range:

``_check_credentials(self, password, env)``
    ``password`` is a plain string.

``_check_credentials(self, credential, env)``
    ``credential`` is a mapping such as
    ``{"login": ..., "password": ..., "type": "password"}`` and an
    authentication information mapping is returned.

Rather than guessing which applies, this adapter inspects the bound method at
run time and builds the call accordingly. The behaviour can be pinned by an
administrator through the ``ls_electronic_signature.credential_api_mode``
system parameter, whose accepted values are ``auto`` (default), ``credential``
and ``password``.

Isolating this single integration point in one small module means that if the
19.0 signature differs from both known forms, exactly one function has to be
adapted and re-qualified, rather than the wizard and every caller.

Verification obligation
-----------------------
Before the module is released into a validated environment, the operational
qualification described in ``doc/07_test_report.md`` (test case OQ-CRED-001)
must be executed against the target Odoo 19.0 build to confirm that a correct
password is accepted and an incorrect password is rejected.
"""

import inspect
import logging

from odoo.exceptions import AccessDenied, UserError
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)

__all__ = ["CredentialApiError", "resolve_mode", "verify_password"]

#: Accepted values of the ``ls_electronic_signature.credential_api_mode``
#: system parameter.
SUPPORTED_MODES = ("auto", "credential", "password")

#: Parameter names understood as "a mapping describing the credential".
_CREDENTIAL_PARAMETER_NAMES = ("credential", "credentials")

#: Parameter names understood as "a plain password string".
_PASSWORD_PARAMETER_NAMES = ("password", "passwd")


class CredentialApiError(UserError):
    """Raised when the host Odoo build exposes an unrecognised credential API.

    This is a configuration fault, not an authentication failure. It must never
    be presented to a signer as "wrong password", because doing so would hide a
    system defect behind a routine user error.
    """


def resolve_mode(env):
    """Return the credential API mode configured for this database.

    :param env: An Odoo environment.
    :returns str: One of :data:`SUPPORTED_MODES`.
    :raises CredentialApiError: If the system parameter holds an unknown value.
    """
    parameter = env["ir.config_parameter"].sudo()
    mode = (parameter.get_param("ls_electronic_signature.credential_api_mode") or "auto").strip()
    if mode not in SUPPORTED_MODES:
        raise CredentialApiError(
            _(
                "System parameter 'ls_electronic_signature.credential_api_mode' "
                "holds the unsupported value '%(mode)s'. Accepted values are: "
                "%(accepted)s.",
                mode=mode,
                accepted=", ".join(SUPPORTED_MODES),
            )
        )
    return mode


def _detect_mode(method):
    """Return the calling convention of ``method`` by inspecting its signature.

    :param method: The bound ``_check_credentials`` method.
    :returns str: ``"credential"`` or ``"password"``.
    :raises CredentialApiError: If neither convention is recognised.
    """
    try:
        parameters = list(inspect.signature(method).parameters)
    except (TypeError, ValueError) as error:
        raise CredentialApiError(
            _(
                "The password verification method of 'res.users' could not be "
                "inspected on this Odoo build (%(error)s). Pin the calling "
                "convention with the system parameter "
                "'ls_electronic_signature.credential_api_mode'.",
                error=error,
            )
        ) from error

    for name in parameters:
        if name in _CREDENTIAL_PARAMETER_NAMES:
            return "credential"
        if name in _PASSWORD_PARAMETER_NAMES:
            return "password"

    raise CredentialApiError(
        _(
            "The password verification method of 'res.users' on this Odoo build "
            "accepts the parameters (%(parameters)s), which match neither "
            "supported calling convention. Set the system parameter "
            "'ls_electronic_signature.credential_api_mode' to 'credential' or "
            "'password' after confirming the correct form against the server "
            "source, and re-run the qualification test OQ-CRED-001.",
            parameters=", ".join(parameters),
        )
    )


def verify_password(user, password):
    """Verify ``password`` against the stored credential of ``user``.

    The check is executed in an environment acting as ``user`` because the core
    implementation resolves the row to inspect from the environment user rather
    than from the recordset.

    :param user: A single ``res.users`` recordset, the signer.
    :param str password: The password submitted in the signature wizard.
    :returns bool: ``True`` if the password is correct, ``False`` otherwise.
    :raises CredentialApiError: If the host build exposes an unrecognised
        credential API. Callers must not treat this as a failed authentication.
    """
    user.ensure_one()
    if not password:
        return False

    signer = user.with_user(user)
    method = signer._check_credentials
    mode = resolve_mode(user.env)
    if mode == "auto":
        mode = _detect_mode(method)

    # ``interactive`` is set so that the core implementation does not emit its
    # "assuming interactive login" deprecation warning. A signature is always
    # executed by a human at a keyboard, so the value is factually correct.
    call_env = {"interactive": True}
    if mode == "credential":
        argument = {
            "login": user.login,
            "password": password,
            "type": "password",
        }
    else:
        argument = password

    try:
        method(argument, call_env)
    except AccessDenied:
        return False
    except TypeError as error:
        raise CredentialApiError(
            _(
                "The password verification method of 'res.users' rejected the "
                "'%(mode)s' calling convention (%(error)s). Set the system "
                "parameter 'ls_electronic_signature.credential_api_mode' "
                "explicitly and re-run the qualification test OQ-CRED-001.",
                mode=mode,
                error=error,
            )
        ) from error
    return True
